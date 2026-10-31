#!/usr/bin/env python3
"""Build MinimalPDF Compress into a standalone folder, plus a zip of it.

Builds on Windows, macOS and Linux, x86_64 and arm64. The output is a *folder*,
not a single self-extracting executable. That is the point of this fork: a
onefile build carries a bootstrap that unpacks ~30 MB of console tools into a
temp directory on every launch, and that behaviour -- not anything the
application does -- is what antivirus heuristics score as packed malware. A
folder build has nothing to unpack. See FORK.md for the measured difference.

    python build.py                # standalone folder + zip  (recommended)
    python build.py --onefile      # additionally a single file (expect AV noise)
    python build.py --skip-deps    # reuse the binaries already fetched into src/
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
BUILD = ROOT / "build"
DIST = ROOT / "dist"

sys.path.insert(0, str(ROOT / "tools"))
from fetch_deps import host_platform  # noqa: E402

APP_NAME = "MinimalPDF_Compress"
PLATFORM = host_platform()
IS_WINDOWS = PLATFORM.startswith("windows")
IS_MACOS = PLATFORM.startswith("macos")
EXE_SUFFIX = ".exe" if IS_WINDOWS else ""
PAYLOAD_DIRS = ("bin", "lib", "Resource", "iccprofiles")


def app_version():
    text = (SRC / "constants.py").read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("Could not read APP_VERSION from src/constants.py")
    return match.group(1)


def numeric_version(version):
    parts = re.findall(r"\d+", version)[:4]
    while len(parts) < 4:
        parts.append("0")
    return ".".join(parts)


def run(command, **kwargs):
    print("+ " + " ".join(str(part) for part in command))
    subprocess.run(command, check=True, **kwargs)


def ensure_dependencies(skip):
    if not skip:
        run([sys.executable, str(ROOT / "tools" / "fetch_deps.py")])

    gs = "gswin64c.exe" if IS_WINDOWS else "gs"
    if (SRC / "bin" / gs).is_file():
        return
    if IS_WINDOWS:
        # On Windows Ghostscript is bundled, so a missing one is a broken build.
        raise SystemExit(
            f"Ghostscript ({gs}) was not fetched into src/bin.\n"
            "Run:  python tools/fetch_deps.py"
        )
    # Elsewhere Artifex publishes no prebuilt binary, so the app resolves gs from
    # the end user's PATH at runtime. The build machine having it is irrelevant.
    hint = "brew install ghostscript" if IS_MACOS else "sudo apt install ghostscript"
    found = shutil.which(gs)
    print(f"note: Ghostscript is not bundled on {PLATFORM}; the app will use the "
          f"one on the user's PATH at runtime"
          + (f" (this machine has {found})" if found else f" -- users install it with: {hint}"))


def nuitka_command(version, onefile):
    command = [
        sys.executable, "-m", "nuitka",
        "--assume-yes-for-downloads",
        "--enable-plugin=tk-inter",
        "--output-dir=" + str(BUILD),
        "--output-filename=" + APP_NAME + EXE_SUFFIX,
        "--company-name=MinimalPDF Compress contributors",
        "--product-name=MinimalPDF Compress",
        "--file-description=PDF compression and utilities",
        "--product-version=" + numeric_version(version),
        "--file-version=" + numeric_version(version),
        "--copyright=AGPL-3.0",
        "--include-data-dir=" + str(SRC / "assets") + "=assets",
        "--include-data-files=" + str(SRC / "pdf.ico") + "=pdf.ico",
        "--remove-output",
        "--onefile" if onefile else "--standalone",
    ]
    if IS_WINDOWS:
        command += [
            "--windows-console-mode=disable",
            "--windows-icon-from-ico=" + str(SRC / "pdf.ico"),
        ]
    elif IS_MACOS:
        # The window icon comes from iconphoto at runtime, which works on every
        # platform. A proper Dock icon would need --macos-create-app-bundle,
        # which changes the output layout; not done here yet.
        pass
    else:
        command.append("--linux-icon=" + str(SRC / "assets" / "icon.png"))
    command.append(str(SRC / "main.py"))
    return command


def copy_payload(target):
    for name in PAYLOAD_DIRS:
        source = SRC / name
        if source.is_dir():
            shutil.copytree(source, target / name, dirs_exist_ok=True)
            print(f"  payload {name}/")


def write_checksums(folder):
    lines = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        if path.name == "SHA256SUMS.txt":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(folder).as_posix()}")
    (folder / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  SHA256SUMS.txt ({len(lines)} files)")


def make_zip(folder, archive):
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            arcname = (Path(folder.name) / path.relative_to(folder)).as_posix()
            info = zipfile.ZipInfo.from_file(path, arcname)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Keep the mode bits, or the app and the bundled tools lose their
            # executable bit on macOS and Linux when the zip is unpacked.
            info.external_attr = (path.stat().st_mode & 0xFFFF) << 16
            with path.open("rb") as source, bundle.open(info, "w") as target:
                shutil.copyfileobj(source, target, 1 << 20)
    return archive


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--onefile", action="store_true",
                        help="also produce a single self-extracting executable")
    parser.add_argument("--skip-deps", action="store_true",
                        help="do not run tools/fetch_deps.py first")
    parser.add_argument("--no-zip", action="store_true", help="skip the zip step")
    args = parser.parse_args(argv)

    version = app_version()
    print(f"MinimalPDF Compress {version} for {PLATFORM}\n")

    ensure_dependencies(args.skip_deps)

    shutil.rmtree(BUILD / "main.dist", ignore_errors=True)
    run(nuitka_command(version, onefile=False))

    DIST.mkdir(parents=True, exist_ok=True)
    folder = DIST / APP_NAME
    shutil.rmtree(folder, ignore_errors=True)
    shutil.move(str(BUILD / "main.dist"), str(folder))

    print("\nassembling folder build")
    copy_payload(folder)
    write_checksums(folder)

    if not args.no_zip:
        archive = make_zip(folder, DIST / f"{APP_NAME}-{version}-{PLATFORM}.zip")
        print(f"  {archive.name} ({archive.stat().st_size / 1_048_576:.1f} MB)")

    if args.onefile:
        print("\nbuilding onefile (this variant is the one antivirus heuristics dislike)")
        run(nuitka_command(version, onefile=True))
        produced = BUILD / (APP_NAME + EXE_SUFFIX)
        if produced.is_file():
            shutil.move(str(produced), str(DIST / (APP_NAME + EXE_SUFFIX)))

    print("\nBuilt into " + str(DIST))
    for path in sorted(DIST.iterdir()):
        if path.is_file():
            print(f"  {path.name}  sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
