#!/usr/bin/env python3
"""Regenerate the application icons from the source artwork.

The artwork is a light rounded tile, and upstream's icons bake a black
background into the four corners outside it. That is invisible against a dark
title bar and very visible in a taskbar or a Dock, which is where the window
icon now also appears.

Removing it with a global colour key would also erase the dark PDF clamp in
the middle of the logo. Filling from the four corners instead only clears the
background that is actually connected to the edge, so the artwork survives
untouched. Measured: it removes 11.6% of the canvas, which is exactly the
corner area outside the tile.

    python tools/make_icons.py

Writes src/assets/icon.png (used at runtime by iconphoto, by the .deb and by
the macOS .icns) and src/pdf.ico (used by iconbitmap, by Nuitka for the
executable, and by Inno Setup for the installer).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "pdf1.png"
PNG_OUT = ROOT / "src" / "assets" / "icon.png"
ICO_OUT = ROOT / "src" / "pdf.ico"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
PNG_SIZE = 256
# Not present in the artwork, so it cannot be confused with a real pixel.
SENTINEL = (255, 0, 255)
# The corners are uniform black; a small margin catches any antialiasing.
TOLERANCE = 30


def cut_corner_background(im):
    """Clear the background connected to the four corners."""
    im = im.convert("RGBA")
    probe = im.convert("RGB")
    if SENTINEL in set(probe.getdata()):
        raise SystemExit("The sentinel colour occurs in the artwork; choose another.")
    width, height = probe.size
    for corner in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        ImageDraw.floodfill(probe, corner, SENTINEL, thresh=TOLERANCE)

    cut = im.copy()
    source, target = probe.load(), cut.load()
    removed = 0
    for y in range(height):
        for x in range(width):
            if source[x, y] == SENTINEL:
                target[x, y] = (0, 0, 0, 0)
                removed += 1
    return cut, removed


def main():
    if not SOURCE.is_file():
        raise SystemExit(f"Source artwork not found: {SOURCE}")

    original = Image.open(SOURCE)
    cut, removed = cut_corner_background(original)
    total = cut.size[0] * cut.size[1]
    print(f"source {SOURCE.name} {cut.size[0]}x{cut.size[1]}")
    print(f"  background removed: {100 * removed / total:.1f}% of the canvas")

    if not 5 < 100 * removed / total < 30:
        raise SystemExit(
            "That is not the corner area. Either the artwork changed or the fill "
            "escaped into the logo; check before committing the result.")

    resample = Image.Resampling.LANCZOS
    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)
    cut.resize((PNG_SIZE, PNG_SIZE), resample).save(PNG_OUT, optimize=True)
    print(f"  -> {PNG_OUT.relative_to(ROOT)} ({PNG_SIZE}x{PNG_SIZE})")

    frames = [cut.resize((size, size), resample) for size in ICO_SIZES]
    frames[-1].save(ICO_OUT, format="ICO",
                    sizes=[(size, size) for size in ICO_SIZES])
    print(f"  -> {ICO_OUT.relative_to(ROOT)} ({', '.join(str(s) for s in ICO_SIZES)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
