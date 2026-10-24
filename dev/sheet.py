"""DEV ONLY. Lay frames saved by dev/capture.py out as a contact sheet: one row per name, one
column per capture time, each row labeled; a name's event frames (<name>_event<k>.png) get a row
of their own, "<name> events".

    uv run --with pillow dev/sheet.py dev/out/blob/round1            # writes .../sheet.png
    uv run --with pillow dev/sheet.py dev/out/blob/round1 --width 480 --names a_trace,b_hud
"""

import argparse
import glob
import os
import re

from PIL import Image, ImageDraw

FRAME = re.compile(r'^(.+?)_(event)?(\d+)\.png$')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--width', type=int, default=400, help='width of each frame on the sheet')
    ap.add_argument('--names', help='rows to show, in this order (default: all, sorted)')
    ap.add_argument('-o', '--out', help='default: <folder>/sheet.png')
    a = ap.parse_args()

    frames = {}
    for path in glob.glob(os.path.join(a.folder, '*.png')):
        m = FRAME.match(os.path.basename(path))
        if m and m.group(1) != 'sheet':
            row = m.group(1) + (' events' if m.group(2) else '')
            frames.setdefault(row, {})[int(m.group(3))] = path
    names = a.names.split(',') if a.names else sorted(frames)
    cols = max(len(frames[n]) for n in names)
    first = Image.open(next(iter(frames[names[0]].values())))
    w = a.width
    h = round(first.height * w / first.width)
    label, pad = 26, 6
    sheet = Image.new('RGB', (cols * (w + pad) + pad, len(names) * (h + label + pad) + pad), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for r, name in enumerate(names):
        y = pad + r * (h + label + pad)
        draw.text((pad, y + 6), name, fill=(240, 240, 240))
        for c, i in enumerate(sorted(frames[name])):
            img = Image.open(frames[name][i]).convert('RGB').resize((w, h), Image.LANCZOS)
            sheet.paste(img, (pad + c * (w + pad), y + label))
    out = a.out or os.path.join(a.folder, 'sheet.png')
    sheet.save(out)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
