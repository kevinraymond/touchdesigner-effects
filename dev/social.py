"""DEV ONLY. The repository's social preview (GitHub, Settings, Social preview: what a shared link
shows): 1280 x 640, the library's name and a line about it in its own 5 x 7 font, then a sum: input +
depth map (optional) = every effect, in two rows under it, each row centered, all at one moment of
dev/record.py's takes (the frames come unlabeled from the recordings and are named here, at a size
that reads in a small cell), with an orange "& MORE" in the last one's top-right corner. The effects
are every effects/<n>/ that has a take, in name order. Cells are CELL_W wide, a quarter smaller than
the 285 px of the eight-cell layout before, so up to 5 fit a row; 11 or 12 effects take 6 a row in
narrower cells, and more need another layout. Upload docs/social-preview.png by hand; GitHub has no
API for it.

    uv run --with pillow dev/social.py dev/out/previews_fluid_hero docs/social-preview.png --at 6.5
"""

import argparse
import glob
import importlib.util
import os
import subprocess
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1280, 640
BG = (10, 10, 14)
INK = (230, 230, 230)                       # the labels' 0.9
ORANGE = (255, 148, 41)                     # ASCII's ORANGE, (1.0, 0.58, 0.16)
CELL_W, MARGIN, GAP = 214, 24, 8             # a cell's width; the least margin; between cells and rows
LABEL, PAD, PLATE = 2, 3, 0.6                # a label: pixels per font pixel, padding in font pixels, plate opacity
SIGN = 5                                     # pixels per font pixel of the + and =
SLOT = 5 * SIGN + 24                         # the room a + or = takes between two cells
MORE, MORE_SCALE, MORE_PAD = '& MORE', 2, 6  # the badge in the last cell's corner: orange, dark text
TITLE, LINE = 'TOUCHDESIGNER EFFECTS', 'MIT DROP-IN EFFECTS THAT LOVE YOUR AUDIO'
TITLE_SCALE, LINE_SCALE = 8, 4
INPUTS = (('input', ('INPUT',)), ('depth', ('DEPTH MAP', '(OPTIONAL)')))
TITLES = {'datamosh': 'DATAMOSH-STYLE'}      # as the effects title themselves; the rest are their names


def font():
    spec = importlib.util.spec_from_file_location('font5x7', os.path.join(ROOT, 'lib', 'font5x7.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GLYPHS = font().GLYPHS


def text(im, s, scale, x0, y, color):
    """s in the 5 x 7 font, scale pixels per font pixel, its top-left corner at x0, y."""
    for i, ch in enumerate(s):
        for gy, row in enumerate(GLYPHS[ch].split()):
            for gx, c in enumerate(row):
                if c == '#':
                    x, yy = x0 + (i * 6 + gx) * scale, y + gy * scale
                    im.paste(color, (x, yy, x + scale, yy + scale))


def width(s, scale):
    return (len(s) * 6 - 1) * scale


def label(cell, lines):
    """The name in the cell's bottom-left corner, white on a dark plate, as the Showreel names effects."""
    s = LABEL
    w = max(width(t, s) for t in lines) + 2 * PAD * s
    h = (len(lines) * 9 - 2 + 2 * PAD) * s
    x, y = PAD * s, cell.height - h - PAD * s
    plate = Image.new('RGB', (w, h), (0, 0, 0))
    cell.paste(Image.blend(cell.crop((x, y, x + w, y + h)), plate, PLATE), (x, y))
    for k, t in enumerate(lines):
        text(cell, t, s, x + PAD * s, y + (PAD + 9 * k) * s, INK)


def frame(folder, name, clip, at, tmp):
    mov = os.path.join(folder, '{}_{}.mov'.format(name, clip))
    if not os.path.exists(mov):
        raise SystemExit('no take {} (dev/record.py records <name>_<clip>.mov)'.format(mov))
    png = os.path.join(tmp, name + '.png')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(at), '-i', mov, '-frames:v', '1', png], check=True)
    return Image.open(png).convert('RGB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', help="dev/record.py's takes: input, depth and every effect")
    ap.add_argument('out')
    ap.add_argument('--clip', default='b1_dancer')
    ap.add_argument('--at', type=float, default=6.5, help='seconds into the takes')
    a = ap.parse_args()
    effects = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, 'effects', '*', '*.tox')))
    if len(effects) > 12:
        raise SystemExit('{} effects: the layout holds 12'.format(len(effects)))
    top = (len(effects) + 1) // 2
    rows = [effects[:top], effects[top:]]
    across = max(len(r) for r in rows)
    cw = CELL_W if across <= 5 else (W - 2 * MARGIN - (across - 1) * GAP) // across
    ch = cw * 9 // 16

    tmp = tempfile.mkdtemp()
    cells = {}
    for name, lines in INPUTS + tuple((n, (TITLES.get(n, n.upper().replace('_', ' ')),)) for n in effects):
        cells[name] = frame(a.folder, name, a.clip, a.at, tmp).resize((cw, ch), Image.LANCZOS)
        label(cells[name], lines)

    im = Image.new('RGB', (W, H), BG)
    # Top to bottom: the title, the line, input + depth map =, two rows of effects; centered as a block.
    title_h, line_h = 7 * TITLE_SCALE, 7 * LINE_SCALE
    gaps = (24, 36, 18, GAP)                 # title-line, line-sum, sum-effects, between the effect rows
    total = title_h + line_h + 3 * ch + sum(gaps)
    y = (H - total) // 2
    text(im, TITLE, TITLE_SCALE, (W - width(TITLE, TITLE_SCALE)) // 2, y, INK)
    y += title_h + gaps[0]
    text(im, LINE, LINE_SCALE, (W - width(LINE, LINE_SCALE)) // 2, y, ORANGE)
    y += line_h + gaps[1]
    # The sum: input + depth map =, each sign in its slot after a cell.
    x = (W - (2 * cw + 2 * SLOT)) // 2
    for name, sign in (('input', '+'), ('depth', '=')):
        im.paste(cells[name], (x, y))
        text(im, sign, SIGN, x + cw + (SLOT - 5 * SIGN) // 2, y + (ch - 7 * SIGN) // 2, ORANGE)
        x += cw + SLOT
    y += ch + gaps[2]
    for row in rows:
        x = (W - (len(row) * cw + (len(row) - 1) * GAP)) // 2
        for name in row:
            im.paste(cells[name], (x, y))
            x += cw + GAP
        last = (x - GAP - cw, y)
        y += ch + gaps[3]
    # The library grows: a badge in the last cell's top-right corner (the label is bottom-left).
    bw, bh = width(MORE, MORE_SCALE) + 2 * MORE_PAD, 7 * MORE_SCALE + 2 * MORE_PAD
    bx, by = last[0] + cw - bw, last[1]
    im.paste(ORANGE, (bx, by, bx + bw, by + bh))
    text(im, MORE, MORE_SCALE, bx + MORE_PAD, by + MORE_PAD, BG)
    im.save(a.out, optimize=True)
    print(a.out, im.size, '{} effects, {} x {} cells, {:.0f} KB'.format(len(effects), cw, ch, os.path.getsize(a.out) / 1024))


if __name__ == '__main__':
    main()
