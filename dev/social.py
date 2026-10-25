"""DEV ONLY. The repository's social preview (GitHub, Settings, Social preview: what a shared link
shows): 1280 x 640, the library's name, a line about it and its terms in its own 5 x 7 font over the eight
cells of the tiled preview's still (dev/tile.py --still: the input, its depth map and every effect,
3 x 3 with the first row centered). Upload docs/social-preview.png by hand; GitHub has no API for it.

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
TITLE, LINE = 'TOUCHDESIGNER EFFECTS', 'FREE DROP-IN EFFECTS THAT MOVE WITH YOUR MUSIC'
TERMS = 'MIT LICENSE - NOTHING TO INSTALL - RUNS ON THE FREE LICENSE'
GRAY = (150, 150, 155)


def font():
    spec = importlib.util.spec_from_file_location('font5x7', os.path.join(HERE, '..', 'lib', 'font5x7.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def text(im, s, scale, y, color):
    """s in the 5 x 7 font, scale pixels per font pixel, centered, its top at y."""
    f = font()
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
    text(im, TITLE, 8, 70, INK)
    text(im, LINE, 3, 160, ORANGE)
    text(im, TERMS, 2, 214, GRAY)
    sw, sh = W // 4, W // 4 * 9 // 16          # four across, 16:9
    top = H - 2 * sh
    for i, cell in enumerate(cells):
        im.paste(cell.resize((sw, sh), Image.LANCZOS), ((i % 4) * sw, top + (i // 4) * sh))
    im.save(out, optimize=True)
    print(out, im.size, '{:.0f} KB'.format(os.path.getsize(out) / 1024))


if __name__ == '__main__':
    main()
