# Notice

## Original work

This repository is a fork of
**[deminimis/minimalpdfcompress](https://github.com/deminimis/minimalpdfcompress)**,
created and maintained by [deminimis](https://github.com/deminimis).

The application, its user interface, its compression pipelines and its
documentation are their work. This fork changes a small part of it and adds a
build system; everything else is theirs, and it would not exist without them.

Forked from upstream `main` at commit `2045627`.

## License

**AGPL-3.0-or-later** — the same license as the original work, as the AGPL
requires. [`LICENSE.md`](LICENSE.md) is upstream's license file, unmodified.

If you run a modified version of this program on a server and let users
interact with it over a network, section 13 of the AGPL requires you to offer
those users the corresponding source.

## Statement of changes

Section 5 of the AGPL requires modified versions to carry prominent notices
stating that they were changed and when. [`FORK.md`](FORK.md) is that statement
and documents every change with its reasoning. In summary, as of 2026-11-01:

- Ghostscript is invoked with `-dSAFER` on all five call sites; upstream passes
  `-dNOSAFER` on the compression and PDF/A paths.
- Four functional bugs fixed, including one that made Lossless, True Lossless
  and Remove Images fail and silently copy the input through unchanged.
- Builds produce a standalone folder instead of a onefile self-extractor, which
  takes the VirusTotal detections on the Windows build from 38/71 to 1/71.
- Bundled third-party binaries are pinned by SHA-256 and fetched from their own
  official projects, replacing an undocumented binaries release.
- Builds run in GitHub Actions with a signed provenance attestation, for
  Windows, macOS and Linux on x86_64 and arm64.
- The window icon is set with `iconphoto` so it works outside Windows.
- The embedded base64 icon became a real PNG asset.
- The interface is available in Spanish as well as English, selected in
  Settings; upstream is English only.
- The interface was reworked: one type scale, surfaces instead of outlines, one
  slider control throughout, and four help texts that upstream references but
  never defined.

Upstream has been offered these changes rather than only forking them:
[PR #63](https://github.com/deminimis/minimalpdfcompress/pull/63) for the
security and correctness fixes, and a
[comment on issue #50](https://github.com/deminimis/minimalpdfcompress/issues/50#issuecomment-6550643907)
with the antivirus findings.

## Bundled third-party components

None of these are covered by this project's copyright. They are downloaded at
build time from their own projects, pinned by SHA-256 in
[`tools/deps.lock.json`](tools/deps.lock.json), and redistributed unmodified in
the release archives.

| Component | License | Upstream |
|---|---|---|
| Ghostscript | AGPL-3.0 | <https://www.ghostscript.com/> |
| cpdf | Free for non-commercial use; commercial license available | <https://github.com/coherentgraphics/cpdf-binaries> |
| oxipng | MIT | <https://github.com/shssoichiro/oxipng> |
| pngquant | GPL-3.0-or-later | <https://pngquant.org/> |
| jpegoptim | GPL-3.0 | <https://github.com/tjko/jpegoptim> |
| Efficient Compression Tool | Apache-2.0 | <https://github.com/fhanau/Efficient-Compression-Tool> |
| pikepdf | MPL-2.0 | <https://github.com/pikepdf/pikepdf> |
| Pillow | MIT-CMU | <https://github.com/python-pillow/Pillow> |

**Note on cpdf:** its license is free for non-commercial use only. Commercial
use of a build that bundles it requires a license from
[Coherent Graphics](https://www.coherentpdf.com/). This applies to upstream too.
