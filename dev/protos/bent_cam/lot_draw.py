"""DEV ONLY. Bent Cam's lot as one contact sheet for the docs page: every camera on the same frame (from
dev/protos/bent_cam/lot.py), each over its pins, D7 to D0, with its six shorts drawn one row each in the
order Shorts connects them. Grounded is a triangle pointing down, tied to power one pointing up, and a bridge
is a bar between its two lines ending in the triangles of the side that wins. Blue for the shorts that pull
toward 0 and orange for those that pull toward 1, the library's orange and blue, with the shapes saying it
without the color. Bright rows are connected at the default Shorts, faint ones as Shorts rises.

    uv run --with pillow dev/protos/bent_cam/lot_draw.py dev/out/bent_cam/lot docs/effects/bent_cam_lot.webp
"""

import argparse
import importlib.util
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BG, INK, DIM, GUIDE = (20, 20, 20), (230, 230, 230), (140, 140, 140), (52, 52, 52)
TO_0, TO_1 = (77, 140, 255), (255, 153, 38)
FAINT = 0.3


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FONT = module(os.path.join(ROOT, 'lib', 'font5x7.py'), 'font5x7')
LOT = module(os.path.join(ROOT, 'effects', 'bent_cam', 'src', 'lot.py'), 'lot')


def text(im, xy, s, scale, color, plate=None):
    """s in the library's 5 x 7 font, scale pixels a font pixel, top left at xy; on a dark plate if asked."""
    x0, y0 = xy
    w, h = (len(s) * 6 - 1) * scale, 7 * scale
    if plate is not None:
        im.paste(plate, (x0 - 2 * scale, y0 - 2 * scale, x0 + w + 2 * scale, y0 + h + 2 * scale))
    for i, ch in enumerate(s):
        for y, row in enumerate(FONT.GLYPHS[ch].split()):
            for x, c in enumerate(row):
                if c == '#':
                    px, py = x0 + (i * 6 + x) * scale, y0 + y * scale
                    im.paste(color, (px, py, px + scale, py + scale))
    return w


def mix(c, a):
    return tuple(int(BG[k] + (c[k] - BG[k]) * a) for k in range(3))


def triangle(d, x, y, r, up, color):
    d.polygon([(x - r, y + r), (x + r, y + r), (x, y - r)] if up else [(x - r, y - r), (x + r, y - r), (x, y + r)],
              fill=color)


def pins(im, x0, y0, w, shorts, connected, s):
    """The pin panel under a picture: D7 ... D0 across, a row a short."""
    d = ImageDraw.Draw(im)
    step = w / 8
    col = [x0 + step * (7 - line) + step / 2 for line in range(8)]
    for line in range(8):
        label = 'D{}'.format(line)
        text(im, (int(col[line] - (len(label) * 6 - 1) * s / 2), y0), label, s, DIM)
    top, row_h, r = y0 + 11 * s, 7 * s, 2 * s
    for line in range(8):
        d.line([(col[line], top), (col[line], top + row_h * len(shorts))], fill=GUIDE, width=1)
    for i, (how, a, b) in enumerate(shorts):
        y = top + row_h * i + row_h / 2
        up = how in (LOT.POWER, LOT.HIGH)
        c = mix(TO_1 if up else TO_0, 1.0 if i < connected else FAINT)
        if how in (LOT.GROUND, LOT.POWER):
            triangle(d, col[a], y, r, up, c)
        else:
            d.line([(col[a], y), (col[b], y)], fill=c, width=max(1, s))
            triangle(d, col[a], y, r, up, c)
            triangle(d, col[b], y, r, up, c)
    return top + row_h * len(shorts) - y0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('out')
    ap.add_argument('--cols', type=int, default=5)
    ap.add_argument('--tile', type=int, default=320, help='width of each picture')
    ap.add_argument('--shorts', type=float, default=0.35, help='the Shorts the pictures were taken at')
    a = ap.parse_args()

    s = 2
    lot = LOT.lot()
    connected = int(a.shorts * LOT.SHORTS + 1e-6)
    tw = a.tile
    th = tw * 9 // 16
    panel = 11 * s + 7 * s * LOT.SHORTS + 3 * s
    gap = 12
    head = 7 * 4 + 2 * (7 * 3 + 10) + 30
    rows = (len(lot) + a.cols - 1) // a.cols
    W = a.cols * tw + (a.cols + 1) * gap
    H = head + rows * (th + panel + gap) + gap
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    text(im, (gap, gap), 'THE LOT: {} CAMERAS, EACH SHORTED DIFFERENTLY'.format(len(lot)), 4, INK)
    y = gap + 7 * 4 + 14
    x = gap
    r = 2 * s
    for label, up, bridge in (('GROUNDED, READS 0', False, False), ('TO POWER, READS 1', True, False),
                              ('BRIDGED, LOW WINS', False, True), ('BRIDGED, HIGH WINS', True, True)):
        c = TO_1 if up else TO_0
        cy = y + 7 * 3 / 2
        if bridge:
            d.line([(x + r, cy), (x + 6 * r, cy)], fill=c, width=s)
            triangle(d, x + r, cy, r, up, c)
            triangle(d, x + 6 * r, cy, r, up, c)
            x += 8 * r
        else:
            triangle(d, x + r, cy, r, up, c)
            x += 3 * r
        x += text(im, (int(x), y), label, 3, DIM) + 8 * s
    text(im, (gap, y + 7 * 3 + 10), 'BRIGHT: CONNECTED AT SHORTS {:g}   FAINT: CONNECTED AS SHORTS RISES'.format(a.shorts),
         3, DIM)
    for i, shorts in enumerate(lot):
        rr, cc = divmod(i, a.cols)
        x0 = gap + cc * (tw + gap)
        y0 = head + rr * (th + panel + gap)
        pic = Image.open(os.path.join(a.folder, 'cam_{:02d}.png'.format(i + 1))).convert('RGB').resize((tw, th), Image.LANCZOS)
        im.paste(pic, (x0, y0))
        text(im, (x0 + 3 * s, y0 + 3 * s), str(i + 1), 3, INK, plate=(0, 0, 0))
        pins(im, x0, y0 + th + 3 * s, tw, shorts, connected, s)
    ext = os.path.splitext(a.out)[1].lower()
    im.save(a.out, quality=88, method=6) if ext == '.webp' else im.save(a.out)
    print(a.out, im.size)


main()
