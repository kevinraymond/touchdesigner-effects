"""DEV ONLY. Tile dev/record.py's recordings of several effects into one labeled grid, for a docs
preview that shows them side by side (the Showreel's page): each recording scaled to a cell, named
bottom left in the library's 5 x 7 font on a dark plate as the Showreel names them, the cells
packed in rows. Writes <out>.mp4 (silent) and <out>.webp (PREVIEW_SECONDS from --start).

    uv run --with pillow dev/tile.py dev/out/record --names ascii,blob_track,... \\
        --titles 'ASCII,BLOB TRACK,...' --clip b1_dancer --out docs/effects/showreel

The recordings start together (dev/record.py restarts the clip and the track for each), so the
cells stay in step.
"""

import argparse
import importlib.util
import os
import subprocess
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PREVIEW_SECONDS = 6
PAD, INK, PLATE = 3, 0.9, 0.6   # as bundles/showreel/src/names.glsl


def font():
    spec = importlib.util.spec_from_file_location('font5x7', os.path.join(HERE, '..', 'lib', 'font5x7.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def label(text, s, path):
    """The name on its plate: white text (INK) over black at PLATE opacity, s pixels per font pixel."""
    f = font()
    w, h = (len(text) * 6 - 1 + 2 * PAD) * s, (7 + 2 * PAD) * s
    im = Image.new('RGBA', (w, h), (0, 0, 0, int(255 * PLATE)))
    ink = (int(255 * INK),) * 3 + (255,)
    for i, ch in enumerate(text):
        rows = f.GLYPHS[ch].split()
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                if c == '#':
                    x0, y0 = (PAD + i * 6 + x) * s, (PAD + y) * s
                    im.paste(ink, (x0, y0, x0 + s, y0 + s))
    im.save(path)
    return w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--names', required=True, help='effects, in order (<name>_<clip>.mov in the folder)')
    ap.add_argument('--titles', required=True, help='their labels, comma separated, in the same order')
    ap.add_argument('--clip', default='b1_dancer')
    ap.add_argument('--cols', type=int, default=3)
    ap.add_argument('--cell', default='640x360')
    ap.add_argument('--scale', type=int, default=3, help='pixels per font pixel in a cell')
    ap.add_argument('--start', type=float, default=1.0)
    ap.add_argument('--width', type=int, default=1000, help="the preview's width")
    ap.add_argument('--quality', type=int, default=75)
    ap.add_argument('--out', required=True, help='path without extension')
    a = ap.parse_args()
    names, titles = a.names.split(','), a.titles.split(',')
    assert len(names) == len(titles), (names, titles)
    cw, ch = map(int, a.cell.split('x'))
    rows = -(-len(names) // a.cols)
    tmp = tempfile.mkdtemp()
    cmd, chains, cells = ['ffmpeg', '-y', '-v', 'error'], [], []
    for i, (n, t) in enumerate(zip(names, titles)):
        cmd += ['-i', os.path.join(a.folder, '{}_{}.mov'.format(n, a.clip))]
    for i, t in enumerate(titles):
        png = os.path.join(tmp, '{}.png'.format(i))
        lw, lh = label(t, a.scale, png)
        cmd += ['-i', png]
        k = len(names) + i
        chains.append('[{0}:v]scale={1}:{2}:flags=lanczos,setsar=1[s{0}];[s{0}][{3}:v]overlay={4}:{5}[c{0}]'.format(
            i, cw, ch, k, 6 * a.scale, ch - lh - 6 * a.scale))
        cells.append('[c{}]'.format(i))
    # A short last row is centered under the rest; empty cells stay black.
    layout = []
    for i in range(len(names)):
        r, c = divmod(i, a.cols)
        in_row = min(a.cols, len(names) - r * a.cols)
        layout.append('{}_{}'.format(int((c + (a.cols - in_row) / 2) * cw), r * ch))
    chains.append('{}xstack=inputs={}:layout={}:fill=black,pad={}:{}:0:0:black[g]'.format(
        ''.join(cells), len(names), '|'.join(layout), a.cols * cw, rows * ch))
    mp4 = a.out + '.mp4'
    subprocess.run(cmd + ['-filter_complex', ';'.join(chains), '-map', '[g]', '-an', '-c:v', 'libx264', '-crf', '18',
                          '-pix_fmt', 'yuv420p', mp4], check=True)
    webp = a.out + '.webp'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(a.start), '-t', str(PREVIEW_SECONDS), '-i', mp4,
                    '-vf', 'fps=20,scale={}:-2:flags=lanczos'.format(a.width), '-c:v', 'libwebp_anim',
                    '-quality', str(a.quality), '-loop', '0', webp], check=True)
    for p in (mp4, webp):
        print('{} ({:.1f} MB)'.format(p, os.path.getsize(p) / 1e6))


if __name__ == '__main__':
    main()
