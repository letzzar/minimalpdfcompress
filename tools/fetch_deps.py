#!/usr/bin/env python3
"""Fetch and verify the third-party binaries that MinimalPDF Compress bundles.

Every dependency is pinned by SHA-256 in deps.lock.json, per platform. A
download whose hash does not match is discarded and the build stops, so anyone
can reproduce and audit exactly what ends up inside a release. Nothing
downloaded is executed.

    python tools/fetch_deps.py                          # this platform
    python tools/fetch_deps.py --platform linux-aarch64 # another one
    python tools/fetch_deps.py --update-lock            # record missing hashes
    python tools/fetch_deps.py --update-lock --pin-only --platform all
                                                        # pin every platform
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = Path(__file__).resolve().parent / "deps.lock.json"
CACHE_DIR = ROOT / "build" / "deps-cache"
DEFAULT_DEST = ROOT / "src"
USER_AGENT = "minimalpdfcompress-build/1.0"
CHUNK = 1 << 20

OS_NAMES = {"windows": "windows", "linux": "linux", "darwin": "macos"}
ARCH_NAMES = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}

# Tools the app can use but that have no official prebuilt binary everywhere.
# Anything missing from bin/ is looked up on PATH at runtime.
SYSTEM_TOOLS = {
    "linux": "sudo apt install ghostscript pngquant jpegoptim    # or your distro's equivalent",
    "macos": "brew install ghostscript pngquant jpegoptim",
}


def host_platform():
    os_name = OS_NAMES.get(platform.system().lower())
    arch = ARCH_NAMES.get(platform.machine().lower())
    if not os_name or not arch:
        raise SystemExit(f"Unsupported platform: {platform.system()} {platform.machine()}")
    return f"{os_name}-{arch}"


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url, dest, attempts=4):
    """Fetch a URL, retrying on transient network failures.

    CI runners time out on these often enough to break a release build, and a
    failed download here is never a reason to stop the whole thing on the
    first try. The hash check afterwards is what decides whether the bytes are
    acceptable, so retrying is safe.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    partial = dest.with_name(dest.name + ".part")
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                with partial.open("wb") as handle:
                    shutil.copyfileobj(response, handle, CHUNK)
            partial.replace(dest)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            partial.unlink(missing_ok=True)
            if attempt == attempts:
                raise SystemExit(f"Could not download {url} after {attempts} attempts: {exc}")
            delay = 2 ** attempt
            print(f"  attempt {attempt} failed ({exc}); retrying in {delay}s")
            time.sleep(delay)


def find_7zip():
    found = shutil.which("7z") or shutil.which("7za")
    if found:
        return found
    for base in ("ProgramFiles", "ProgramFiles(x86)"):
        candidate = Path(os.environ.get(base, "")) / "7-Zip" / "7z.exe"
        if candidate.is_file():
            return str(candidate)
    raise SystemExit(
        "7-Zip is needed to unpack the Ghostscript installer.\n"
        "Install it from https://www.7-zip.org/ or run:  winget install 7zip.7zip"
    )


def _refuse_traversal(names, target):
    root = target.resolve()
    for name in names:
        if not str((target / name).resolve()).startswith(str(root)):
            raise SystemExit(f"Refusing to unpack path traversal entry: {name}")


def unpack(archive_kind, archive, workdir):
    """Return the path holding the unpacked payload."""
    if archive_kind == "raw":
        return archive
    target = workdir / "unpacked"
    target.mkdir(parents=True, exist_ok=True)
    if archive_kind == "zip":
        with zipfile.ZipFile(archive) as bundle:
            _refuse_traversal(bundle.namelist(), target)
            bundle.extractall(target)
    elif archive_kind == "targz":
        with tarfile.open(archive, "r:gz") as bundle:
            _refuse_traversal(bundle.getnames(), target)
            try:
                bundle.extractall(target, filter="data")
            except TypeError:  # Python < 3.12
                bundle.extractall(target)
    elif archive_kind == "nsis":
        subprocess.run(
            [find_7zip(), "x", "-y", f"-o{target}", str(archive)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
    else:
        raise SystemExit(f"Unknown archive kind: {archive_kind}")
    return target


def build_ghostscript(source, workdir):
    """Compile Ghostscript from the official source release.

    Artifex publishes installers for Windows but only source for Linux and
    macOS, so compiling is the only way to bundle a known, pinned version there
    instead of telling the user to install one themselves.
    """
    trees = [p for p in source.iterdir() if p.is_dir() and p.name.startswith("ghostscript")]
    if not trees:
        raise SystemExit("No ghostscript-* directory inside the source archive")
    tree, stage = trees[0], workdir / "stage"
    log = workdir / "build.log"
    env = os.environ.copy()
    if sys.platform == "darwin":
        env.setdefault("MACOSX_DEPLOYMENT_TARGET", "11.0")
    steps = [
        ["./configure", f"--prefix={stage}",
         "--without-x", "--disable-cups", "--disable-gtk", "--disable-dbus",
         "--without-tesseract", "--without-libidn", "--without-libpaper"],
        ["make", f"-j{os.cpu_count() or 2}"],
        ["make", "install"],
    ]
    with log.open("w", encoding="utf-8", errors="ignore") as handle:
        for step in steps:
            print(f"    {' '.join(step)}")
            result = subprocess.run(step, cwd=tree, env=env, stdout=handle,
                                    stderr=subprocess.STDOUT, text=True)
            if result.returncode != 0:
                tail = log.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]
                raise SystemExit("Ghostscript build failed:\n  " + "\n  ".join(tail))
    return stage


BUILDERS = {"ghostscript": build_ghostscript}


def place(dep, source, dest):
    placed = []
    for member in dep["members"]:
        pattern = member["from"]
        target = dest / member["to"]
        if pattern == ".":
            matches = [source]
        elif any(ch in pattern for ch in "*?"):
            matches = sorted(p for p in source.glob(pattern) if p.is_file() or p.is_dir())
        else:
            candidate = source / pattern
            matches = [candidate] if candidate.exists() else []
        if not matches:
            if member.get("optional"):
                continue
            raise SystemExit(f"{dep['name']}: '{pattern}' is not in the downloaded archive")
        origin = matches[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        if origin.is_dir():
            shutil.copytree(origin, target, dirs_exist_ok=True)
        else:
            shutil.copy2(origin, target)
        if member.get("executable") and os.name != "nt":
            mode = target.stat().st_mode
            target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        placed.append(member["to"])
    return placed


def resolve(dep, force):
    """Download the dependency if needed and return (path, sha256)."""
    filename = dep["url"].rsplit("/", 1)[-1]
    cached = CACHE_DIR / f"{dep['name']}-{dep['platform']}-{dep['version']}-{filename}"
    pinned = dep.get("sha256")

    if cached.is_file() and not force:
        actual = sha256_file(cached)
        if pinned is None or actual == pinned:
            print(f"  cached   {cached.name}")
            return cached, actual
        print(f"  stale cache ({actual[:12]}...), re-downloading")

    print(f"  download {dep['url']}")
    download(dep["url"], cached)
    actual = sha256_file(cached)

    if pinned is not None and actual != pinned:
        cached.unlink(missing_ok=True)
        raise SystemExit(
            f"\nSHA-256 MISMATCH for {dep['name']} ({dep['platform']})\n"
            f"  url      {dep['url']}\n"
            f"  expected {pinned}\n"
            f"  got      {actual}\n"
            "The download was discarded. Do not build from it. Either the publisher\n"
            "replaced the file or the download was tampered with -- verify upstream first."
        )
    return cached, actual


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST,
                        help="where bin/, lib/ and Resource/ are written (default: src/)")
    parser.add_argument("--platform", default=None, metavar="KEY",
                        help="platform to fetch for, or 'all' (default: this host)")
    parser.add_argument("--update-lock", action="store_true",
                        help="record the hash of dependencies that are not pinned yet")
    parser.add_argument("--pin-only", action="store_true",
                        help="download and hash, but do not unpack or install anything")
    parser.add_argument("--only", action="append", default=[], metavar="NAME",
                        help="fetch only this dependency (repeatable)")
    parser.add_argument("--force", action="store_true",
                        help="re-download even when a valid cached copy exists")
    args = parser.parse_args(argv)

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    # An entry with no "name" is disabled; the entry itself says why.
    active = [d for d in lock["deps"] if "name" in d]
    known = {d["platform"] for d in active}
    wanted = args.platform or host_platform()
    if wanted != "all" and wanted not in known:
        raise SystemExit(f"Unknown platform '{wanted}'. Known: {', '.join(sorted(known))}")

    selected = [d for d in active if wanted == "all" or d["platform"] == wanted]
    if args.only:
        unknown = set(args.only) - {d["name"] for d in active}
        if unknown:
            raise SystemExit(f"Unknown dependency: {', '.join(sorted(unknown))}")
        selected = [d for d in selected if d["name"] in args.only]

    dest = args.dest.resolve()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    newly_pinned = []

    print(f"platform: {wanted}\n")
    for dep in selected:
        print(f"{dep['name']} {dep['version']} ({dep['platform']})")
        archive, actual = resolve(dep, args.force)

        if dep.get("sha256") is None:
            if not args.update_lock:
                raise SystemExit(
                    f"\n{dep['name']} ({dep['platform']}) is not pinned in deps.lock.json.\n"
                    f"  sha256 of what was just downloaded: {actual}\n"
                    "Check that against the publisher, then run:\n"
                    "  python tools/fetch_deps.py --update-lock"
                )
            dep["sha256"] = actual
            newly_pinned.append((dep["name"], dep["platform"], actual))
            print(f"  pinned   {actual}")
        else:
            print(f"  verified {actual}")

        if args.pin_only:
            continue

        with tempfile.TemporaryDirectory(prefix="mpdf-dep-") as workdir:
            source = unpack(dep["archive"], archive, Path(workdir))
            recipe = dep.get("build")
            if recipe:
                builder = BUILDERS.get(recipe)
                if builder is None:
                    raise SystemExit(f"{dep['name']}: unknown build recipe '{recipe}'")
                print(f"  compiling from source, this takes a few minutes")
                source = builder(source, Path(workdir))
            for item in place(dep, source, dest):
                print(f"  -> {item}")

    if newly_pinned:
        LOCK_PATH.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        print(f"\ndeps.lock.json updated with {len(newly_pinned)} hash(es):")
        for name, plat, digest in newly_pinned:
            print(f"  {name} ({plat}): {digest}")
        print("Review these against the publisher before committing.")

    if args.pin_only:
        print("\nHashes recorded; nothing was installed (--pin-only).")
        return 0

    host_os = wanted.split("-")[0]
    hint = SYSTEM_TOOLS.get(host_os)
    if hint:
        print(f"\nNot every tool ships a prebuilt binary for {host_os}. Install the rest with:\n  {hint}")
    print(f"\nDependencies ready in {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
