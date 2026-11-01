#!/usr/bin/env python3
"""Turn the build in dist/ into an installable package for this platform.

    Windows   an Inno Setup installer offering two modes, chosen before
              anything is elevated: per-user into %LOCALAPPDATA%\\Programs with
              no UAC at all, or all-users into Program Files, which prompts for
              admin only once that choice is made.
    Linux     a .deb installing to /opt with a menu entry and icon.
    macOS     nothing; the .app inside the zip already is the installable form.

Run it after build.py:

    python build.py
    python tools/package.py
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
PACKAGING = ROOT / "packaging"

sys.path.insert(0, str(ROOT / "tools"))
from fetch_deps import host_platform  # noqa: E402

APP_NAME = "MinimalPDF_Compress"
DEB_NAME = "minimalpdf-compress"
PLATFORM = host_platform()
DEB_ARCH = {"x86_64": "amd64", "aarch64": "arm64"}


def app_version():
    text = (SRC / "constants.py").read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("Could not read APP_VERSION from src/constants.py")
    return match.group(1)


def run(command, **kwargs):
    print("+ " + " ".join(str(part) for part in command))
    subprocess.run(command, check=True, **kwargs)


def built_folder():
    folder = DIST / APP_NAME
    if not folder.is_dir():
        raise SystemExit(f"{folder} does not exist. Run build.py first.")
    return folder


def find_iscc():
    found = shutil.which("ISCC") or shutil.which("iscc")
    if found:
        return found
    for base in ("ProgramFiles(x86)", "ProgramFiles"):
        for version in ("6", "5"):
            candidate = Path(os.environ.get(base, "")) / f"Inno Setup {version}" / "ISCC.exe"
            if candidate.is_file():
                return str(candidate)
    raise SystemExit(
        "Inno Setup is needed to build the Windows installer.\n"
        "Install it with:  winget install JRSoftware.InnoSetup"
    )


def package_windows(version):
    script = PACKAGING / "windows" / "installer.iss"
    base = f"{APP_NAME}-{version}-{PLATFORM}-setup"
    run([
        find_iscc(),
        f"/DAppVersion={version}",
        f"/DSourceDir={built_folder()}",
        f"/DOutputDir={DIST}",
        f"/DOutputBaseFilename={base}",
        str(script),
    ])
    return DIST / f"{base}.exe"


def package_linux(version):
    arch = DEB_ARCH.get(PLATFORM.split("-", 1)[1])
    if arch is None:
        raise SystemExit(f"No Debian architecture mapping for {PLATFORM}")
    if not shutil.which("dpkg-deb"):
        raise SystemExit("dpkg-deb is needed to build the .deb (apt install dpkg)")

    staging = BUILD / f"deb-{arch}"
    shutil.rmtree(staging, ignore_errors=True)

    install_dir = staging / "opt" / DEB_NAME
    shutil.copytree(built_folder(), install_dir)

    # Launcher on PATH. A relative symlink keeps it valid wherever dpkg unpacks.
    bin_dir = staging / "usr" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / DEB_NAME).symlink_to(f"/opt/{DEB_NAME}/{APP_NAME}")

    desktop_dir = staging / "usr" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PACKAGING / "linux" / f"{DEB_NAME}.desktop", desktop_dir)

    icon_dir = staging / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC / "assets" / "icon.png", icon_dir / f"{DEB_NAME}.png")

    doc_dir = staging / "usr" / "share" / "doc" / DEB_NAME
    doc_dir.mkdir(parents=True, exist_ok=True)
    for name in ("LICENSE.md", "NOTICE.md"):
        shutil.copy2(ROOT / name, doc_dir / name)

    size_kb = sum(p.stat().st_size for p in staging.rglob("*") if p.is_file()) // 1024
    control_dir = staging / "DEBIAN"
    control_dir.mkdir(parents=True, exist_ok=True)
    (control_dir / "control").write_text(
        f"""Package: {DEB_NAME}
Version: {version}
Section: utils
Priority: optional
Architecture: {arch}
Installed-Size: {size_kb}
Maintainer: MinimalPDF Compress contributors <noreply@github.com>
Recommends: pngquant, jpegoptim
Homepage: https://github.com/letzzar/minimalpdfcompress
Description: Compress and manipulate PDF files offline
 A desktop application that compresses PDFs and performs common PDF tasks
 entirely on your own machine, wrapping Ghostscript, cpdf and oxipng behind a
 single interface. It makes no network connections.
 .
 Ghostscript, cpdf and oxipng are bundled, so there is nothing else to install.
 pngquant and jpegoptim are used for extra image optimisation when present.
""", encoding="utf-8")

    # Everything dpkg ships has to be readable, and the executables runnable,
    # whatever umask the build ran under.
    for path in staging.rglob("*"):
        if path.is_symlink():
            continue
        mode = path.stat().st_mode
        path.chmod(mode | (0o755 if (path.is_dir() or mode & stat.S_IXUSR) else 0o644))

    output = DIST / f"{DEB_NAME}_{version}_{arch}.deb"
    output.unlink(missing_ok=True)
    run(["dpkg-deb", "--root-owner-group", "--build", str(staging), str(output)])
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.parse_args(argv)

    version = app_version()
    print(f"packaging MinimalPDF Compress {version} for {PLATFORM}\n")

    if PLATFORM.startswith("windows"):
        produced = package_windows(version)
    elif PLATFORM.startswith("linux"):
        produced = package_linux(version)
    else:
        print("macOS needs no separate installer: the .app in the zip is it.")
        return 0

    print(f"\n{produced.name}  ({produced.stat().st_size / 1_048_576:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
