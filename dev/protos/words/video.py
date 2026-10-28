"""DEV ONLY. Words on video outside TouchDesigner (board #4673): offline.py's layouts kept from frame to frame.

    uv run --with numpy --with opencv-python-headless --with pillow dev/protos/words/video.py b1_dancer \\
        --layout cloud --seconds 8 --out dev/out/words/video

Each frame, at FPS with the clip's frames held between its own (as TouchDesigner shows a 16 fps clip at 60):
  carry     on a new input frame, every word moves by the mean optical flow over its box (Farneback, a quarter size);
  check     a word is out when its box leaves its region (cloud: the subject; portrait: cells whose detail allows its
            size) or overlaps an older word; out for HOLD seconds in a row, it starts to fade out (FADE seconds) and
            its cells stay taken while it fades;
  fill      up to PER_FRAME new words go into the free cells, largest first (offline.layout), each fading in.

Writes an MP4, a sheet at a few moments and <name>.npz in dev/flashcount.py's format (luminance and WCAG's red
measure on its 64 x 36 grid), with the clip's own as clip_<clip>.npz for the baseline.
"""

import argparse
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import offline as o  # noqa: E402

FPS = 30
CLIP_FPS = 16


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def flash_grid(img):
    """dev/flash.py's measures on a 64 x 36 grid: relative luminance and the red measure, averaged in linear light."""
    c = lin(img.astype(np.float32) / 255)
    lum = c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    s = c.sum(2) + 1e-6
    red = np.where(c[..., 0] / s >= 0.8, (c[..., 0] - c[..., 1] - c[..., 2]) * 320, 0)
    g = lambda a: cv2.resize(a.astype(np.float32), (64, 36), interpolation=cv2.INTER_AREA)
    return g(lum), g(red)


class Words:
    def __init__(self, layout, glyphs, order, sizes, per_frame, hold=0.15, fade=0.4):
        self.layout, self.glyphs, self.order, self.sizes = layout, glyphs, order, sizes
        self.per_frame, self.hold, self.fade = per_frame, hold, fade
        self.words = []
        self.next = 0
        self.born = self.died = 0
        self.why = {'out': 0, 'hit': 0}

    def cells(self, w):
        """The cells a word's box touches (conservative)."""
        x0 = int(np.floor(w['x'] / o.CELL))
        y0 = int(np.floor(w['y'] / o.CELL))
        x1 = int(np.ceil((w['x'] + w['w']) / o.CELL))
        y1 = int(np.ceil((w['y'] + w['h']) / o.CELL))
        return max(x0, 0), max(y0, 0), min(x1, o.GW), min(y1, o.GH), (x0 < 0 or y0 < 0 or x1 > o.GW or y1 > o.GH)

    def step(self, dt, flow, region, allowed, score):
        # carry
        if flow is not None:
            fh, fw = flow.shape[:2]
            for w in self.words:
                sx, sy = fw / o.W, fh / o.H
                a = flow[int(w['y'] * sy):max(int((w['y'] + w['h']) * sy), int(w['y'] * sy) + 1),
                         int(w['x'] * sx):max(int((w['x'] + w['w']) * sx), int(w['x'] * sx) + 1)]
                if a.size:
                    d = a.reshape(-1, 2).mean(0)
                    w['x'] += d[0] / sx
                    w['y'] += d[1] / sy
        # check, oldest first
        occ = np.zeros((o.GH, o.GW), bool)
        kept = []
        for w in self.words:
            x0, y0, x1, y1, off = self.cells(w)
            ok = not off and x1 > x0 and y1 > y0
            if ok and w['alpha_dir'] > 0:
                inside = region[y0:y1, x0:x1] if allowed is None else (region & allowed[w['level']])[y0:y1, x0:x1]
                # overlap with an older word's box, past a tolerance of a fifth of the smaller height
                hit = any(min(w['x'] + w['w'], v['x'] + v['w']) - max(w['x'], v['x']) > 0.2 * min(w['h'], v['h'])
                          and min(w['y'] + w['h'], v['y'] + v['h']) - max(w['y'], v['y']) > 0.2 * min(w['h'], v['h'])
                          for v in kept)
                ok = inside.mean() >= 0.85 and not hit
                if not ok:
                    self.why['out' if inside.mean() < 0.85 else 'hit'] += 1
            if w['alpha_dir'] > 0 and ok:
                kept.append(w)
            if w['alpha_dir'] > 0:
                w['bad'] = 0 if ok else w['bad'] + dt
                if w['bad'] > self.hold or off:
                    w['alpha_dir'] = -1
                    self.died += 1
            if x1 > x0 and y1 > y0:
                if w['alpha_dir'] > 0:
                    occ[y0:y1, x0:x1] = True
                else:
                    occ[y0:y1, x0:x1] |= True
        # fade
        for w in self.words:
            w['alpha'] = float(np.clip(w['alpha'] + w['alpha_dir'] * dt / self.fade, 0, 1))
        self.words = [w for w in self.words if not (w['alpha_dir'] < 0 and w['alpha'] <= 0)]
        # fill
        reg = region & ~occ
        new = o.layout(reg, score, allowed, self.glyphs, self.order[self.next:] + self.order[:self.next], self.sizes,
                       10 ** 6, per_frame=self.per_frame)
        for p in new:
            x, y, bw, bh = p['cell']
            ww = p['h'] * self.glyphs.aspect(p['word'])
            level = list(self.sizes).index(p['h'])
            self.words.append({'word': p['word'], 'x': x * o.CELL + (bw * o.CELL - ww) / 2,
                               'y': y * o.CELL + (bh * o.CELL - p['h']) / 2, 'w': ww, 'h': p['h'], 'level': level,
                               'alpha': 0.0, 'alpha_dir': 1, 'bad': 0.0})
            self.born += 1
        self.next = (self.next + len(new)) % len(self.order)

    def render(self, picture, backdrop, boost=1.4):
        m = Image.new('L', (o.W, o.H), 0)
        for w in sorted(self.words, key=lambda w: w['alpha']):
            if w['alpha'] > 0:
                self.glyphs.draw(m, w['word'], w['x'], w['y'], w['h'], int(255 * w['alpha']))
        m = np.asarray(m, np.float32)[..., None] / 255
        col = np.clip(picture * boost, 0, 1)
        return (np.clip(col * m + picture * backdrop * (1 - m), 0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--layout', default='cloud', choices=('cloud', 'portrait'))
    ap.add_argument('--seconds', type=float, default=6)
    ap.add_argument('--per-frame', type=int, default=12)
    ap.add_argument('--hold', type=float, default=0.15)
    ap.add_argument('--fade', type=float, default=0.4)
    ap.add_argument('--grow', type=int, default=2, help='cloud: cells the subject grows by')
    ap.add_argument('--no-flow', action='store_true')
    ap.add_argument('--out', default=os.path.join(o.ROOT, 'dev', 'out', 'words', 'video'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    clip = o.frames(a.clip, int(a.seconds * CLIP_FPS) + 2)
    order, toks = o.words_from(o.TEXT, stop=a.layout == 'cloud')
    glyphs = o.Glyphs(set(order) | set(toks), False)
    name = '{}_{}{}'.format(a.clip, a.layout, '_noflow' if a.no_flow else '')
    if a.layout == 'cloud':
        sizes = (104, 84, 68, 56, 46, 38, 32, 26, 21, 17)
        words = Words('cloud', glyphs, order, sizes, a.per_frame, a.hold, a.fade)
    else:
        sizes = (96, 72, 56, 44, 34, 26, 20, 16)
        words = Words('portrait', glyphs, toks, sizes, a.per_frame, a.hold, a.fade)
    tmp = os.path.join(a.out, name + '_frames')
    os.makedirs(tmp, exist_ok=True)
    lums, reds, ts = [], [], []
    clums, creds = [], []
    prev_k, prev_gray = -1, None
    shots = []
    for f in range(n):
        t = f / FPS
        k = int(t * CLIP_FPS)
        pic = clip[k]
        flow = None
        gray = cv2.resize(pic.mean(2), (o.W // 4, o.H // 4))
        if k != prev_k:
            if prev_gray is not None and not a.no_flow:
                fl = cv2.calcOpticalFlowFarneback((prev_gray * 255).astype(np.uint8), (gray * 255).astype(np.uint8),
                                                  None, 0.5, 3, 15, 3, 5, 1.2, 0)
                flow = fl
            prev_gray, prev_k = gray, k
            if a.layout == 'cloud':
                m = o.subject_mask(a.clip, k, cells=True)
                if a.grow:
                    m = cv2.dilate(m.astype(np.uint8), np.ones((2 * a.grow + 1, 2 * a.grow + 1), np.uint8)) > 0
                region = m
                score = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5)
                allowed = None
            else:
                region = np.ones((o.GH, o.GW), bool)
                det = o.detail_map(pic)
                q = np.quantile(det, (0.15, 0.25, 0.35, 0.45, 0.55, 0.7, 0.85, 1.0))
                allowed = [det <= q[i] for i in range(len(sizes))]
                allowed[-1][:] = True
                score = -np.arange(o.GH)[:, None] * 0.001 + np.random.default_rng(1).random((o.GH, o.GW)) * 0.01
        words.step(1 / FPS, flow, region, allowed, score)
        img = words.render(pic, backdrop=0.15 if a.layout == 'cloud' else 0.0)
        Image.fromarray(img).save(os.path.join(tmp, '{:04d}.png'.format(f)))
        lum, red = flash_grid(img)
        lums.append(lum), reds.append(red), ts.append(t)
        cl, cr = flash_grid((pic * 255).astype(np.uint8))
        clums.append(cl), creds.append(cr)
        if f in (int(n * 0.1), int(n * 0.4), int(n * 0.7), n - 1):
            shots.append(img)
        if f % 30 == 0:
            print('t {:.1f} words {} born {} died {}'.format(t, len(words.words), words.born, words.died), flush=True)
    np.savez(os.path.join(a.out, name + '.npz'), t=np.array(ts), lum=np.array(lums), red=np.array(reds))
    np.savez(os.path.join(a.out, 'clip_source.npz'), t=np.array(ts), lum=np.array(clums), red=np.array(creds))
    sheet = np.concatenate([np.concatenate(shots[:2], 1), np.concatenate(shots[2:4], 1)], 0)
    Image.fromarray(sheet).resize((1280, 720)).save(os.path.join(a.out, name + '_sheet.png'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(tmp, '%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', os.path.join(a.out, name + '.mp4')],
                   check=True)
    print(words.why)
    print(name, 'born', words.born, 'died', words.died, 'per second', words.born / a.seconds)


if __name__ == '__main__':
    main()
