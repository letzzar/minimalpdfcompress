<div align="center">
<img src="assets/pdf1.png" alt="MinimalPDF Compress" width="120">

# MinimalPDF Compress

**A Windows desktop app for compressing and manipulating PDFs, entirely offline.**

Hardened fork of [deminimis/minimalpdfcompress](https://github.com/deminimis/minimalpdfcompress) ·
[What changed and why](FORK.md) · [Security](SECURITY.md)

</div>

---

## What it is

A Tkinter front-end over a pipeline of best-in-class command line tools —
Ghostscript, cpdf, oxipng, pngquant, jpegoptim and ECT — wrapped so you never
have to touch a command line. Everything runs locally. The application opens no
network connections at all; you can firewall it completely and nothing changes.

For lossy compression it rebuilds the PDF with Ghostscript at your chosen DPI,
then optimises each embedded image individually with the specialised tools. For
lossless it walks the document with pikepdf, re-compressing streams and images
without touching pixels. Every mode finishes with cpdf, which linearises the
file for fast web viewing and squeezes out structural redundancy.

## Why this fork exists

Two things, documented in full in **[FORK.md](FORK.md)**:

- **The published `.exe` is flagged by antivirus engines.** It is a false
  positive — the detections are packer and machine-learning heuristics reacting
  to an unsigned, self-extracting onefile binary, and two engines literally name
  Nuitka as the "threat". This fork builds a **standalone folder** instead of a
  self-extracting executable, builds it in CI with a verifiable provenance
  attestation, pins every bundled binary by SHA-256, and removes the base64 blob
  from the source so a reader does not have to take anything on trust.
- **Ghostscript ran with its sandbox disabled.** Upstream passes `-dNOSAFER` on
  the main compression and PDF/A paths. For a tool that exists to open PDFs from
  arbitrary sources, that turns any Ghostscript parser bug into filesystem
  access. All five invocations now pass `-dSAFER`.

## Install

Download the latest `MinimalPDF_Compress-<version>-win64.zip` from
[Releases](../../releases), unzip it anywhere, and run
`MinimalPDF_Compress.exe`. There is no installer and nothing is written outside
the folder except your settings.

### Verify what you downloaded

Releases are built by GitHub Actions and carry a signed provenance attestation
tying the zip to the exact commit and workflow that produced it:

```bash
gh attestation verify MinimalPDF_Compress-<version>-win64.zip --repo <owner>/<repo>
```

Each build also ships `SHA256SUMS.txt` listing every file inside it.

> **Note on antivirus.** The binary is unsigned, so some engines may still warn.
> [FORK.md](FORK.md) explains exactly what the detections are and how to read
> them. If something does not add up, do not run it — rebuild from source with
> the steps below and compare.

## Features

<img src="assets/Compress.png" alt="Compression tab" width="70%">
<img src="assets/live preview.png" alt="Live preview" width="70%">

### Compression modes

| Mode | What it does |
|---|---|
| **Compression** | Rebuilds the PDF with Ghostscript, downsampling images to a DPI you pick with a slider. Optional lossless (Flate) image encoding avoids JPEG artefacts. |
| **Lossless** | Re-compresses streams and optimises embedded images with oxipng, ECT and jbig2 without reducing quality. |
| **PDF/A** | Converts to the PDF/A-2b archival format. May increase file size. |
| **Remove Images** | Strips image data, leaving blank placeholders — useful for text-only archival. |

All modes support password protection, metadata stripping, darkening scanned
text, grayscale conversion, linearisation for fast web view, and a
"don't save if larger than the original" guard.

### Utilities

**Merge** · **Split / Extract** (single pages, every N pages, or ranges like
`1-5, 8, 12-end`) · **Rotate** with live preview · **Delete pages** ·
**Password** encrypt and decrypt · **Stamp / Watermark** with image or text,
full control of position, opacity, font, colour and scale · **Header / Footer**
with page numbers, dates and filenames · **Table of Contents** generated from
existing bookmarks · **Metadata** editor · **PDF to Image** (PNG, JPEG, TIFF at
a custom DPI) · **PDF Repair**.

<img src="assets/output.png" alt="Output settings" width="70%">

## Build from source

You need Python 3.10+ (3.13 recommended), 7-Zip, and a C compiler for Nuitka —
either the Visual Studio Build Tools with the "Desktop development with C++"
workload, or MinGW-w64, which Nuitka offers to download on first run.

```bash
git clone <your fork url>
cd minimalpdfcompress
python -m pip install -r src/requirements.txt -r requirements-build.txt
python build.py
```

`build.py` fetches and hash-verifies the bundled binaries, compiles with Nuitka
in standalone mode, assembles the folder, writes `SHA256SUMS.txt` and zips the
result into `dist/`.

```bash
python build.py --skip-deps   # reuse binaries already fetched into src/
python build.py --onefile     # also emit a single .exe (the AV-noisy variant)
python tools/fetch_deps.py    # fetch and verify dependencies only
```

To run straight from source without building:

```bash
python -m pip install -r src/requirements.txt
python tools/fetch_deps.py
python src/main.py
```

### Bundled binaries

Every third-party tool is pinned by SHA-256 in
[`tools/deps.lock.json`](tools/deps.lock.json) and downloaded from its own
official project. A download that does not match its pin aborts the build.

| Tool | Version | Upstream |
|---|---|---|
| Ghostscript | 10.08.0 | [ArtifexSoftware/ghostpdl-downloads](https://github.com/ArtifexSoftware/ghostpdl-downloads) |
| cpdf | `4d44a0da` | [coherentgraphics/cpdf-binaries](https://github.com/coherentgraphics/cpdf-binaries) |
| oxipng | 10.2.1 | [shssoichiro/oxipng](https://github.com/shssoichiro/oxipng) |
| jpegoptim | 1.5.6-rel1 | [XhmikosR/jpegoptim-windows](https://github.com/XhmikosR/jpegoptim-windows) |
| ECT | 0.9.5 | [fhanau/Efficient-Compression-Tool](https://github.com/fhanau/Efficient-Compression-Tool) |
| pngquant | 3.0.3 | [pngquant.org](https://pngquant.org/) |

A dependency that is not pinned yet shows `"sha256": null`. Run
`python tools/fetch_deps.py --update-lock` once, check the hash it records
against the publisher, and commit it.

## Code structure

```
src/main.py            entry point: logging, DPI awareness, launches the GUI
src/gui.py             the entire Tkinter UI, previews, threading
src/backend.py         non-GUI logic for the utility tabs
src/pdf_optimizer.py   the compression pipelines
src/utils.py           tool discovery, subprocess wrapper, paths
src/constants.py       shared constants and the version number
src/styles.py          light and dark themes
src/ui_components.py   custom widgets (gauge, toggle, slider, position picker)
src/tooltips.py        all tooltip text
build.py               standalone build
tools/fetch_deps.py    hash-verified dependency fetcher
tools/deps.lock.json   every bundled binary, pinned
```

## FAQ

**Does it connect to the internet?**
No. There is no HTTP client, no socket use, no telemetry and no update check
that phones home. The only network activity is your system browser opening,
after you click a link in the Settings tab.

**Where are my settings stored?**
`%APPDATA%\MinimalPDF Compress\settings.json`. If a `settings.json` sits next to
the executable it is used instead, so portable installs on a USB stick work.

**Do I need to install Ghostscript separately?**
No. Everything is bundled.

**Why did my file get bigger?**
The original was probably already optimised, or you converted to PDF/A, which
adds structural data. Enable "Don't save if larger than original" in Output
Settings.

**Why Python and not C++?**
The heavy lifting is done by C/C++ programs. Python only drives the UI, so the
performance difference in actual PDF processing is negligible.

## Contributing

Issues and pull requests welcome. Changes that affect the build or the bundled
binaries should update `tools/deps.lock.json` and say where the new hash came
from.

## Credits

This project is a thin wrapper around other people's work:
[Ghostscript](https://www.ghostscript.com/) ·
[cpdf](https://github.com/coherentgraphics/cpdf-binaries) ·
[oxipng](https://github.com/shssoichiro/oxipng) ·
[pngquant](https://pngquant.org/) ·
[jpegoptim](https://github.com/tjko/jpegoptim) ·
[zopfli](https://github.com/google/zopfli) ·
[ECT](https://github.com/fhanau/Efficient-Compression-Tool) ·
[jbig2enc](https://github.com/agl/jbig2enc) ·
[pikepdf](https://github.com/pikepdf/pikepdf)

Original application by [deminimis](https://github.com/deminimis/minimalpdfcompress).
Test PDFs from [sample-files.com](https://sample-files.com/documents/pdf/) and
contributions by [cisko99za](https://github.com/cisko99za) and
[necros2k7](https://github.com/necros2k7).

## License

AGPL-3.0, inherited from upstream. See [LICENSE.md](LICENSE.md).
