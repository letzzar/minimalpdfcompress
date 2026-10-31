#!/usr/bin/env python3
"""Fetch and verify the third-party binaries that MinimalPDF Compress bundles.

Every dependency is pinned by SHA-256 in deps.lock.json. A download whose hash
does not match is discarded and the build stops, so anyone can reproduce and
audit exactly what ends up inside a release. Nothing downloaded is executed.

    python tools/fetch_deps.py                 # fetch and verify everything
    python tools/fetch_deps.py --update-lock   # record hashes not pinned yet
    python tools/fetch_deps.py --only cpdf     # one dependency
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = Path(__file__).resolve().parent / "deps.lock.json"
CACHE_DIR = ROOT / "build" / "deps-cache"
DEFAULT_DEST = ROOT / "src"
USER_AGENT = "minimalpdfcompress-build/1.0"
CHUNK = 1 << 20


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    partial = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(request, timeout=180) as response:
        with partial.open("wb") as handle:
            shutil.copyfileobj(response, handle, CHUNK)
    partial.replace(dest)


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


def unpack(archive_kind, archive, workdir):
    """Return the directory holding the unpacked payload."""
    if archive_kind == "raw":
        return archive
    target = workdir / "unpacked"
    target.mkdir(parents=True, exist_ok=True)
    if archive_kind == "zip":
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.namelist():
                resolved = (target / entry).resolve()
                if not str(resolved).startswith(str(target.resolve())):
                    raise SystemExit(f"Refusing to unpack path traversal entry: {entry}")
            bundle.extractall(target)
    elif archive_kind == "nsis":
        subprocess.run(
            [find_7zip(), "x", "-y", f"-o{target}", str(archive)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
    else:
        raise SystemExit(f"Unknown archive kind: {archive_kind}")
    return target


def place(dep, source, dest):
    placed = []
    for member in dep["members"]:
        pattern = member["from"]
        target = dest / member["to"]
        if pattern == ".":
            matches = [source]
        elif any(ch in pattern for ch in "*?"):
            matches = sorted(source.glob(pattern))
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
        placed.append(member["to"])
    return placed


def resolve(dep, force):
    """Download the dependency if needed and return (path, sha256)."""
    cached = CACHE_DIR / f"{dep['name']}-{dep['version']}-{dep['url'].rsplit('/', 1)[-1]}"
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
            f"\nSHA-256 MISMATCH for {dep['name']}\n"
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
    parser.add_argument("--update-lock", action="store_true",
                        help="record the hash of dependencies that are not pinned yet")
    parser.add_argument("--only", action="append", default=[], metavar="NAME",
                        help="fetch only this dependency (repeatable)")
    parser.add_argument("--force", action="store_true",
                        help="re-download even when a valid cached copy exists")
    args = parser.parse_args(argv)

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    selected = [d for d in lock["deps"] if not args.only or d["name"] in args.only]
    unknown = set(args.only) - {d["name"] for d in lock["deps"]}
    if unknown:
        raise SystemExit(f"Unknown dependency: {', '.join(sorted(unknown))}")

    dest = args.dest.resolve()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    newly_pinned = []

    for dep in selected:
        print(f"{dep['name']} {dep['version']}")
        archive, actual = resolve(dep, args.force)

        if dep.get("sha256") is None:
            if not args.update_lock:
                raise SystemExit(
                    f"\n{dep['name']} is not pinned in deps.lock.json.\n"
                    f"  sha256 of what was just downloaded: {actual}\n"
                    "Check that against the publisher, then run:\n"
                    "  python tools/fetch_deps.py --update-lock"
                )
            dep["sha256"] = actual
            newly_pinned.append((dep["name"], actual))
            print(f"  pinned   {actual}")
        else:
            print(f"  verified {actual}")

        with tempfile.TemporaryDirectory(prefix="mpdf-dep-") as workdir:
            source = unpack(dep["archive"], archive, Path(workdir))
            for item in place(dep, source, dest):
                print(f"  -> {item}")

    if newly_pinned:
        LOCK_PATH.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        print(f"\ndeps.lock.json updated with {len(newly_pinned)} hash(es):")
        for name, digest in newly_pinned:
            print(f"  {name}: {digest}")
        print("Review these against the publisher before committing.")

    print(f"\nDependencies ready in {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
