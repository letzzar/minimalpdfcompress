# Security

## Reporting a vulnerability

Open a [security advisory](../../security/advisories/new) rather than a public
issue. Include the version, the PDF or input that triggers it where that is safe
to share, and what you observed.

## Threat model

This application's whole job is to open PDFs from arbitrary, untrusted sources
and hand them to several C programs. The realistic attack is a malformed PDF
that exploits one of those parsers, not the Python layer.

What follows from that:

- **Ghostscript always runs with `-dSAFER`.** Every one of the five Ghostscript
  invocations passes it explicitly. `-dSAFER` keeps the PostScript interpreter
  from reading and writing arbitrary files, which is what turns a Ghostscript
  parser bug into a system compromise. The PDF/A path needs one ICC profile that
  is not on the command line, so it is granted with a narrow
  `--permit-file-read=<that one file>` rather than by disabling the sandbox.
  Upstream passes `-dNOSAFER` on the main compression and PDF/A paths.
- **No command ever reaches a shell.** `utils.run_command()` rejects strings and
  runs `subprocess` with `shell=False`, so no filename can be interpreted as a
  shell metacharacter.
- **The application makes no network connections.** There is no HTTP client, no
  socket use and no update check that phones home. The two links in the UI are
  handed to the system browser only when the user clicks them. Blocking the app
  in a firewall changes nothing about how it works.
- **Keep Ghostscript current.** It is the largest attack surface here by far.
  `tools/deps.lock.json` records the exact version bundled, so you can check it
  against the [Ghostscript security advisories](https://ghostscript.readthedocs.io/en/latest/Security.html).

## Supply chain

- Every bundled third-party binary is pinned by SHA-256 in
  `tools/deps.lock.json` and fetched from its own official project. A download
  that does not match the pin aborts the build.
- Releases are built by GitHub Actions from a tagged commit, and carry a signed
  provenance attestation. Verify one with:

  ```
  gh attestation verify MinimalPDF_Compress-<version>-win64.zip --repo <owner>/<repo>
  ```

- `SHA256SUMS.txt` inside each build lists every file it contains.

## Antivirus detections

Windows builds of this application have historically been flagged by a number of
engines. Those detections are generic packer and machine-learning heuristics
reacting to an unsigned self-extracting executable that unpacks console tools at
runtime. `FORK.md` documents the evidence and what this fork changes to reduce
them. If you find a detection you believe is *not* a false positive, please open
an advisory with the engine name, the exact verdict string and the file hash.
