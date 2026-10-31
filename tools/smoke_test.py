#!/usr/bin/env python3
"""Drive the real compression pipelines over pdf_testing/ and check the output.

This is what catches the kind of bug where a mode fails and silently falls back
to copying the input through unchanged, which is easy to miss because the output
file still exists and still opens.

Optional tools that have no prebuilt binary on this platform are skipped rather
than failing the run; Ghostscript is the only hard requirement.

    python tools/smoke_test.py [output-dir]
"""
from __future__ import annotations

import logging
import queue
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pikepdf  # noqa: E402
from constants import ToolNotFound  # noqa: E402
from pdf_optimizer import PdfOptimizer  # noqa: E402
import utils  # noqa: E402

JOBS = [
    ("lossy", "text.pdf"),
    ("lossy", "report.pdf"),
    ("lossy", "image.pdf"),
    ("lossless", "report.pdf"),
    ("pdfa", "text.pdf"),
]


class WarningCatcher(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def optional(finder, name):
    try:
        return finder()
    except ToolNotFound:
        print(f"note: {name} not available on this platform, skipping its step")
        return None


def main(argv):
    outdir = Path(argv[1]) if len(argv) > 1 else Path(tempfile.mkdtemp(prefix="mpdf-smoke-"))
    outdir.mkdir(parents=True, exist_ok=True)
    testdir = ROOT / "pdf_testing"

    catcher = WarningCatcher()
    logging.getLogger().addHandler(catcher)
    logging.getLogger().setLevel(logging.WARNING)

    try:
        gs_path = utils.find_ghostscript()
    except ToolNotFound as exc:
        raise SystemExit(f"Ghostscript is required for the smoke test: {exc}")

    optimizer = PdfOptimizer(
        gs_path,
        optional(utils.find_cpdf, "cpdf"),
        optional(utils.find_pngquant, "pngquant"),
        q=queue.Queue(),
        jpegoptim_path=optional(utils.find_jpegoptim, "jpegoptim"),
        ect_path=optional(utils.find_ect, "ECT"),
        oxipng_path=optional(utils.find_oxipng, "oxipng"),
        fast_mode=True,
    )

    print(f"\noutput: {outdir}\n")
    failures = 0
    for mode, name in JOBS:
        source = testdir / name
        dest = outdir / f"{mode}-{name}"
        before = len(catcher.messages)
        try:
            if mode == "lossy":
                optimizer.optimize_lossy(source, dest, 150)
            elif mode == "lossless":
                optimizer.optimize_lossless(source, dest)
            else:
                optimizer.optimize_pdfa(source, dest)
        except Exception as exc:
            print(f"FAIL  {mode:<9} {name:<12} raised {type(exc).__name__}: {exc}")
            failures += 1
            continue

        new_warnings = catcher.messages[before:]
        fell_back = any("fallback" in m.lower() or "failed" in m.lower() for m in new_warnings)

        try:
            with pikepdf.open(source) as original, pikepdf.open(dest) as result:
                pages_in, pages_out = len(original.pages), len(result.pages)
        except Exception as exc:
            print(f"FAIL  {mode:<9} {name:<12} output is not a readable PDF: {exc}")
            failures += 1
            continue

        size_in, size_out = source.stat().st_size, dest.stat().st_size
        status = "FALLBACK" if fell_back else ("OK" if pages_in == pages_out else "PAGES")
        if status != "OK":
            failures += 1
        print(f"{status:<9} {mode:<9} {name:<12} "
              f"{size_in / 1048576:7.2f} MB -> {size_out / 1048576:7.2f} MB  "
              f"({(1 - size_out / size_in) * 100:+5.1f}%)  pages {pages_in}->{pages_out}")
        for message in new_warnings:
            print(f"           warn: {message[:150]}")

    print(f"\nFAILURES: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
