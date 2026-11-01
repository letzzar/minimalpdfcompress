# What this fork changes, and why

Fork of [deminimis/minimalpdfcompress](https://github.com/deminimis/minimalpdfcompress).
Upstream is a legitimate, useful project; nothing here suggests otherwise. This
fork exists to fix two unrelated things that the upstream release has:

1. Windows builds get flagged by antivirus engines, and the published binary
   cannot be checked against the source.
2. Ghostscript is invoked with its sandbox turned off.

Everything below is a change against upstream `main` (commit `2045627`).

---

## 1. The antivirus detections are false positives

The v1.9.7 release asset
(`sha256 fc96099246833d0aaac7d0b0f7b6bc26c4bcfe58509793991a0d509e4ec47c6a`)
scores 38/71 on VirusTotal. The verdicts say what is actually happening:

| Engine | Verdict |
|---|---|
| Alibaba | `Packed:Python/Nuitka.72dee553` |
| ESET-NOD32 | `Python/Packed.Nuitka.AI.Suspicious` |
| Microsoft | `Trojan:Win32/Ravartar!rfn` (`!rfn` = reputation heuristic) |
| Symantec | `ML.Attribute.HighConfidence` |
| SentinelOne | `Static AI - Suspicious PE` |
| Palo Alto | `Generic.ml` |
| Fortinet | `Riskware/Application` |
| K7 | `Unwanted-Program` |

Two engines name the *packer*. The rest are machine-learning or generic
signatures. The `Gen:Variant.Giant.Mikey.505` label that appears six times is
one BitDefender engine counted once per OEM licensee. Meanwhile Kaspersky,
Dr.Web, Malwarebytes, CrowdStrike Falcon, Trellix, TrendMicro, Emsisoft and
Ikarus all return clean.

The sandbox behaviour agrees: one contacted IP (`162.159.36.2`, Cloudflare,
0/92 detections), no domains, no URLs, and the dropped files are the CPython
runtime plus Ghostscript resources (`PDFX_def.ps`, `Fontmap.OSF`, `afmdiff.awk`,
`*.upp`). The `.text` section is 140 KB at entropy 6.49 inside a 31.6 MB file —
nothing is encrypted; the bulk is an appended archive.

A source audit of upstream `main` found no network code (`urllib`, `requests`,
`socket`, `urlopen` all absent), no `eval`/`exec`/`pickle`/`marshal`, no registry
or persistence, no shell invocation, and no injection APIs.

### What actually drives the detections, and what this fork does

| Cause | Fix here |
|---|---|
| **onefile self-extraction** — a bootstrap unpacks ~30 MB of console `.exe` into a temp dir on every launch. This is the single biggest trigger. | `build.py` produces a **standalone folder** by default and ships it as a zip. Nothing unpacks at runtime. `--onefile` still exists, but is opt-in and documented as the noisy variant. |
| **Unsigned binary** — no SmartScreen reputation, and every new build starts from zero. | Not fixable without a certificate. [SignPath](https://signpath.io/) is free for OSS projects and is the recommended next step. |
| **Hand-built binary** — upstream has no CI, so the published `.exe` cannot be tied to any commit. | `.github/workflows/build.yml` builds on GitHub Actions and attaches a signed provenance attestation (`gh attestation verify`). |
| **Opaque bundled binaries** — upstream's `Win_Binaries` release has 15 `.exe` with no versions, no source URLs and no hashes. | `tools/deps.lock.json` pins every bundled tool by SHA-256, fetched from its own official project. A mismatch aborts the build. Only the 6 tools the code actually calls are bundled. |
| **An 1800-character base64 blob in the source** — benign (it decodes to a 48×48 PNG) but indistinguishable at a glance from a packed payload. | Removed. The icon is now `src/assets/coffee.png`, a real file. `base64` and `BytesIO` are no longer imported by the GUI. |

### Measured result

Both artefacts of this fork's build were submitted to VirusTotal on
2026-10-31 and scanned against the same engine set as the upstream release:

| Artefact | sha256 | Detections |
|---|---|---|
| upstream v1.9.7 `MinimalPDF_Compress.exe` (onefile) | `fc96099246…` | **38 / 71** |
| this fork `MinimalPDF_Compress.exe` (standalone) | `ac7e6870e5…` | **1 / 71** |
| this fork `MinimalPDF_Compress-1.10.0-win64.zip` | `39d8d6bc3d…` | **1 / 68** |

The single remaining hit on the executable is Microsoft,
`Trojan:Win32/Wacatac.C!ml` — a machine-learning signature, which is what an
unsigned binary attracts. On the zip the only hit is Zillya,
`Trojan.AgentAGen.Win64.25905`, and Microsoft is clean there.

Everything that flagged the onefile build now returns clean: ESET, Alibaba
(both of which previously named Nuitka outright), Symantec, SentinelOne,
Sophos, Avast, AVG, BitDefender and its five OEM licensees, Fortinet, Google,
Rising, GData and Arcabit.

Windows Defender on a real endpoint, engine 1.1.26100.4 with signatures
1.463.63.0 and real-time protection on, scans the whole 120 MB build folder
clean: `found no threats`. Note this disagrees with Microsoft's VirusTotal
engine, which runs without the cloud and reputation context an endpoint has.

What this still does **not** promise: an unsigned binary keeps attracting
machine-learning verdicts, and SmartScreen reputation is a separate layer that
only builds up over downloads. Code signing is the part that actually ends it.

## 2. Ghostscript now runs sandboxed

Upstream passes `-dNOSAFER` — which disables the PostScript file-access
sandbox — on the two paths that process user PDFs most often:

- `pdf_optimizer.py:459`, the main compression pipeline
- `pdf_optimizer.py:575`, PDF/A conversion

The preview path (`backend.py:198`) and the preset fallback already used
`-dSAFER`, so the inconsistency looks accidental rather than deliberate.

For an application whose entire purpose is processing PDFs of unknown origin,
`-dNOSAFER` means any Ghostscript PostScript vulnerability gets full filesystem
access. This fork passes `-dSAFER` on **all five** Ghostscript invocations, and
also adds it explicitly to the PDF-to-image path (`backend.py:536`), which
previously passed neither flag.

PDF/A needs to read one ICC profile that is not named on the command line, so
instead of disabling the sandbox it is granted exactly that one file:

```python
f'--permit-file-read={srgb_profile}', '-dPDFA=1', ..., '-dSAFER',
```

> **Needs real-world testing.** `-dSAFER` is a behaviour change. The PDF/A path
> in particular should be exercised against real documents before a release.

## 3. Smaller hardening

| Change | Why |
|---|---|
| `run_command()` rejects string commands and always runs with `shell=False`. | Upstream set `shell=True` whenever a command came in as a string. No caller did that, but it was one refactor away from turning a filename into shell input. |
| `settings.json` moved to `%APPDATA%\MinimalPDF Compress\`. | Upstream wrote it to the current working directory, which fails in `Program Files` and scatters files. A `settings.json` next to the executable still wins, so portable use keeps working. |
| `resource_path()` now checks the PyInstaller temp dir, the module directory and the executable directory. | Makes bundled resources resolve under PyInstaller, Nuitka standalone and a plain source checkout alike. |

## 4. Functional bugs found while verifying the change

Checking that `-dSAFER` did not break anything meant actually running the
pipelines over `pdf_testing/`. That surfaced four real bugs in upstream `main`.
All of them reproduce on a pristine upstream checkout, so none are caused by
the changes above.

**Lossless, True Lossless and Remove Images were completely broken.**
`_process_with_pikepdf()` creates its working file *inside* a
`tempfile.TemporaryDirectory()`, but called `_post_process_pdf()` **after** the
`with` block had already deleted that directory, so cpdf received a path that
no longer existed:

```
ProcessingError: Tool failed: File C:\...\Temp\tmpXXXX\tmpYYYY.pdf does not exist
```

Every mode that goes through pikepdf failed and fell back to copying the input
unchanged. Fixed by moving the cpdf step inside the block.

**Every palette image was skipped.** `_optimize_image_stream()` had:

```python
convert('RGBA' if 'A' in final_pil_image.info.get('transparency', '') else 'RGB')
```

Pillow reports palette transparency as `bytes`, so `'A' in b'...'` raises
`TypeError: a bytes-like object is required, not 'str'`. The exception was
caught and logged per image, so palette PNGs were silently left unoptimised.
Now it tests `'transparency' in info`.

**`/Length` deletion.** `_apply_flate_image()` deleted every key of the stream
dictionary, but pikepdf manages `/Length` and raises `'/Length' may not be
deleted` — again skipping the image. `/Length` is now left alone.

**pikepdf API drift.** `Pdf.new_stream()` was removed in pikepdf 9, so the
SMask path for transparent images raised `'pikepdf._core.Pdf' object has no
attribute 'new_stream'`. Replaced with `pikepdf.Stream(pdf, data)`.

**Also removed:** `_run_lossless_optimization()` called
`_process_with_pikepdf()` twice with identical arguments — a copy-paste
duplication that did the whole job a second time.

### Verification

Driving the real `PdfOptimizer` pipelines with Ghostscript 10.08.0 and
pikepdf 10.17.0:

| Job | Upstream `main` | This fork |
|---|---|---|
| lossy `text.pdf` | 0.07 → 0.05 MB | 0.07 → 0.05 MB |
| lossy `report.pdf` | 2.40 → 0.57 MB, 6 images skipped | 2.40 → 0.57 MB, none skipped |
| lossy `image.pdf` | 7.97 → 1.33 MB | 7.97 → 1.33 MB |
| lossless `report.pdf` | **fails**, input copied unchanged | 2.40 → 1.82 MB |
| PDF/A `text.pdf` | 0.07 → 0.05 MB | 0.07 → 0.05 MB |

Page counts are preserved in every case and no run falls back silently.

That the sandbox is genuinely active was checked separately — a PostScript
probe that tries to read `C:/Windows/win.ini` under `-dSAFER` is refused:

```
Error: /invalidfileaccess in --file--
```

## 5. Dependency versions

All pinned, all current as of 2026-10-31:

| Component | Version | Source |
|---|---|---|
| Ghostscript | 10.08.0 | ArtifexSoftware/ghostpdl-downloads |
| cpdf | commit `4d44a0da` | coherentgraphics/cpdf-binaries |
| oxipng | 10.2.1 | shssoichiro/oxipng |
| jpegoptim | 1.5.6-rel1 | XhmikosR/jpegoptim-windows |
| ECT | 0.9.5 | fhanau/Efficient-Compression-Tool |
| pngquant | 3.0.3 | pngquant.org |
| pikepdf | 10.17.0 | PyPI |
| Pillow | 13.0.0 | PyPI |
| pyoxipng | 9.1.1 | PyPI |
| Nuitka | 4.3.3 | PyPI |

Upstream's `Win_Binaries` release also carried `advpng`, `optipng`, `pngout`,
`qpdf`, `sam2p`, `zopfli`, `jbig2` and `gswin64.exe`. The source never invokes
any of them, so they are not bundled here — fewer console executables in the
package is also fewer heuristic triggers.

### Platforms

All five targets build green in CI and produce an attested archive:
`windows-x86_64`, `linux-x86_64`, `linux-aarch64`, `macos-x86_64`,
`macos-aarch64`. Each is built on its own runner; nothing is cross-compiled.

Getting there needed four fixes beyond the build matrix, each found by running
the pipelines on the runner rather than by assuming:

- **The window icon never worked outside Windows.** `root.iconbitmap()` only
  accepts `.ico`, and only on Windows. It is now `iconphoto()` with a real PNG,
  which every platform understands; the `.ico` is still used on Windows for a
  sharper taskbar icon.
- **`find_executable()` returned the bare command name** when a tool came from
  `PATH` rather than the bundled `bin/`. `optimize_pdfa()` derives the
  Ghostscript root from that path, so on Linux and macOS it resolved `gs`
  against the working directory. It now returns what `shutil.which()` found.
- **The ICC profile lookup only knew the Windows layout.** It now also walks
  `share/ghostscript/<version>/` under the Ghostscript root, `/usr`,
  `/usr/local` and `/opt/homebrew`. Homebrew's Ghostscript ships no profiles at
  all, so a copy is bundled at `src/assets/srgb.icc` as the final fallback.
- **cpdf for Linux arm64 is unusable.** Upstream links it against `GLIBC_2.42`,
  which no current distribution ships, so it cannot start. That entry is
  disabled in the manifest with its hash and the reason kept; on that platform
  linearisation and the final squeeze are skipped and everything else works.

Windows arm64 is deliberately absent: Ghostscript publishes no arm64 Windows
binary, and Windows on ARM runs the x86_64 build under emulation.

The icon is now native on each platform, from one 256×256 source
(`src/assets/icon.png`, extracted from the largest frame of `pdf.ico`):
the `.ico` is embedded on Windows, `--linux-icon` on Linux, and on macOS the
build generates a full `.icns` iconset with `sips` and `iconutil` — every size
from 16×16 to 512×512@2x — for the bundle. At runtime `iconphoto()` sets the
window icon from the PNG on all three.

macOS gets a real `MinimalPDF_Compress.app` bundle, with the bundled tools in
`Contents/MacOS` beside the executable, which is where `app_dir()` looks. The
archive is made with `ditto` rather than Python's `zipfile`, because that is
the only thing that reliably carries a bundle's symlinks, permissions and
resource forks through a zip round trip.

What is still rough on macOS: the app is unsigned and unnotarised, so first run
needs `xattr -dr com.apple.quarantine MinimalPDF_Compress.app`.

## 6. Files added

```
build.py                      standalone build (folder by default)
requirements-build.txt        Nuitka + zstandard
tools/fetch_deps.py           hash-verified dependency fetcher
tools/deps.lock.json          every bundled binary, pinned by SHA-256
.github/workflows/build.yml   CI build + provenance attestation
SECURITY.md                   threat model and reporting
FORK.md                       this file
src/assets/coffee.png         the icon that used to be a base64 string
```

## Reporting the false positive

The right channels, in order:

1. Microsoft Defender: <https://www.microsoft.com/en-us/wdsi/filesubmission>,
   as "Software developer", with the file hash.
2. The other engines' individual false-positive forms.
3. Upstream issue [#50](https://github.com/deminimis/minimalpdfcompress/issues/50),
   which is already open and tracking this.

Reporting the repository to GitHub Abuse is **not** appropriate. There is
nothing malicious in it.
