"""DEV ONLY. The repository's social preview (GitHub, Settings, Social preview: what a shared link
shows): 1280 x 640, the library's name and a line about it in its own 5 x 7 font over the eight cells
of the tiled preview's still (dev/tile.py --still: the input, its depth map and every effect, 3 x 3
with the first row centered), laid out as a sum: input + depth map = ASCII, Blob Track, and under
them the other four effects, the six right-aligned as one block with slight gaps between them. Upload
docs/social-preview.png by hand; GitHub has no API for it.

    uv run --with pillow dev/social.py dev/out/record/hero_still.png docs/social-preview.png
"""

import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 640
BG = (10, 10, 14)
INK = (230, 230, 230)                       # the labels' 0.9
ORANGE = (255, 148, 41)                     # ASCII's ORANGE, (1.0, 0.58, 0.16)
MARGIN, GAP = 16, 8                          # around the cells; between the effects' cells and the rows
SIGN = 6                                     # pixels per font pixel of the + and =
SLOT = 5 * SIGN + 20                         # the room a + or = takes between two cells
TITLE, LINE = 'TOUCHDESIGNER EFFECTS', 'MIT DROP-IN EFFECTS THAT LOVE YOUR AUDIO'


def font():
    spec = importlib.util.spec_from_file_location('font5x7', os.path.join(HERE, '..', 'lib', 'font5x7.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def text(im, s, scale, y, color, x0=None):
    """s in the 5 x 7 font, scale pixels per font pixel, its top at y: centered, or from x0."""
    f = font()
    if x0 is None:
        x0 = (im.width - (len(s) * 6 - 1) * scale) // 2
    for i, ch in enumerate(s):
        for gy, row in enumerate(f.GLYPHS[ch].split()):
            for gx, c in enumerate(row):
                if c == '#':
                    x, yy = x0 + (i * 6 + gx) * scale, y + gy * scale
                    im.paste(color, (x, yy, x + scale, yy + scale))


def main():
    still, out = sys.argv[1], sys.argv[2]
    src = Image.open(still).convert('RGB')
    cw, ch = src.width // 3, src.height // 3
    # The still's cells: row 0 holds two, centered (input, depth); rows 1 and 2 three each.
    boxes = [(cw // 2, 0), (cw // 2 + cw, 0)] + [(c * cw, r * ch) for r in (1, 2) for c in range(3)]
    cells = [src.crop((x, y, x + cw, y + ch)) for x, y in boxes]
    im = Image.new('RGB', (W, H), BG)
    # Row 1: input + depth map = ASCII, Blob Track; row 2: the other four effects, right-aligned with
    # row 1 so the six effects make one block. Every cell 16:9, as wide as row 1 allows.
    sw = (W - 2 * MARGIN - 2 * SLOT - GAP) // 4
    sh = sw * 9 // 16
    row1 = 4 * sw + 2 * SLOT + GAP
    x1 = (W - row1) // 2
    x2 = x1 + row1 - (4 * sw + 3 * GAP)
    y2 = H - MARGIN - sh
    y1 = y2 - GAP - sh
    places = [(x1, y1), (x1 + sw + SLOT, y1), (x1 + 2 * sw + 2 * SLOT, y1), (x1 + 3 * sw + 2 * SLOT + GAP, y1)]
    places += [(x2 + k * (sw + GAP), y2) for k in range(4)]
    for cell, xy in zip(cells, places):
        im.paste(cell.resize((sw, sh), Image.LANCZOS), xy)
    for k, sign in enumerate('+='):
        text(im, sign, SIGN, y1 + (sh - 7 * SIGN) // 2, ORANGE, x1 + (k + 1) * sw + k * SLOT + (SLOT - 5 * SIGN) // 2)
    # The title (8 pixels per font pixel) and the line (4) centered in the band above the cells.
    y = (y1 - (7 * 8 + 40 + 7 * 4)) // 2
    text(im, TITLE, 8, y, INK)
    text(im, LINE, 4, y + 7 * 8 + 40, ORANGE)
    im.save(out, optimize=True)
    print(out, im.size, '{:.0f} KB'.format(os.path.getsize(out) / 1024))


if __name__ == '__main__':
    main()
