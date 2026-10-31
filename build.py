#!/usr/bin/env python3
"""Build MinimalPDF Compress into a standalone folder, plus a zip of it.

The default output is a *folder*, not a single self-extracting .exe. That is the
point of this fork: a onefile build carries a bootstrap that unpacks ~30 MB of
console tools into a temp directory on every launch, and that behaviour -- not
anything the application does -- is what antivirus heuristics score as packed
malware. A folder build has nothing to unpack. See FORK.md.

    python build.py                # standalone folder + zip  (recommended)
    python build.py --onefile      # additionally a single .exe (expect AV noise)
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
APP_NAME = "MinimalPDF_Compress"
PAYLOAD_DIRS = ("bin", "lib", "Resource", "iccprofiles")
REQUIRED_TOOLS = ("gswin64c.exe",)
OPTIONAL_TOOLS = ("cpdf.exe", "oxipng.exe", "pngquant.exe", "jpegoptim.exe", "ect.exe")


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
    missing = [tool for tool in REQUIRED_TOOLS if not (SRC / "bin" / tool).is_file()]
    if missing:
        raise SystemExit(
            f"Missing required tool(s): {', '.join(missing)}\n"
            "Run:  python tools/fetch_deps.py"
        )
    absent = [tool for tool in OPTIONAL_TOOLS if not (SRC / "bin" / tool).is_file()]
    if absent:
        print(f"note: optional tools not bundled: {', '.join(absent)}")


def nuitka_command(version, onefile):
    command = [
        sys.executable, "-m", "nuitka",
        "--assume-yes-for-downloads",
        "--enable-plugin=tk-inter",
        "--output-dir=" + str(BUILD),
        "--output-filename=" + APP_NAME + ".exe",
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
    if sys.platform == "win32":
        command += [
            "--windows-console-mode=disable",
            "--windows-icon-from-ico=" + str(SRC / "pdf.ico"),
        ]
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
            bundle.write(path, Path(folder.name) / path.relative_to(folder))
    return archive


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--onefile", action="store_true",
                        help="also produce a single self-extracting .exe")
    parser.add_argument("--skip-deps", action="store_true",
                        help="do not run tools/fetch_deps.py first")
    parser.add_argument("--no-zip", action="store_true", help="skip the zip step")
    args = parser.parse_args(argv)

    version = app_version()
    print(f"MinimalPDF Compress {version}\n")

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
        archive = make_zip(folder, DIST / f"{APP_NAME}-{version}-win64.zip")
        print(f"  {archive.name} ({archive.stat().st_size / 1_048_576:.1f} MB)")

    if args.onefile:
        print("\nbuilding onefile (this variant is the one antivirus heuristics dislike)")
        run(nuitka_command(version, onefile=True))
        produced = BUILD / f"{APP_NAME}.exe"
        if produced.is_file():
            shutil.move(str(produced), str(DIST / f"{APP_NAME}.exe"))

    print("\nBuilt into " + str(DIST))
    for path in sorted(DIST.iterdir()):
        if path.is_file():
            print(f"  {path.name}  sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
