"""DEV ONLY. Marbling outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4848): the live
picture floated on the size, inks dropped on the beats and combed on the bars.

    uv run --with numpy --with opencv-python-headless dev/protos/marbling/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 12 --out dev/out/marbling/offline

Lu, Jaffer, Jin, Zhao and Mao, "Mathematical Marbling" (IEEE CG&A 32(6), 2012): every tool is a closed-form
homeomorphism of the plane that keeps areas, so a pixel's color is found by undoing the tools one by one, newest first,
until it lands inside a drop (that drop's ink) or runs out of tools (the picture there). Nothing is carried from frame
to frame: the tools' list is the whole state, and each tool's strength rises when it is made and falls back to nothing
a few bars later, so the picture comes back.

    drop   P' = C + (P - C) sqrt(1 + r^2 / |P - C|^2)       inverse: C + (Q - C) sqrt(1 - r^2 / |Q - C|^2)
    comb   P' = P + a l / (d + l) M, d the distance to the nearest of tines s apart (the paper's fmod), minus the
           comb's mean shift so the tray doesn't drift (pst-marble's shift)
    wave   P' = P + A sin(w (P . N) + phi) M             (the paper's wavy pattern, after a comb)

Units: the frame is 1 high. Variants are named on the command line as name:key=value,...; see DEFAULTS.
"""

import argparse
import importlib.util
import math
import os
import subprocess
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE = (640, 360)
FPS = 30


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


chladni = load('chladni', os.path.join(ROOT, 'dev', 'protos', 'chladni', 'offline.py'))
chladni.SIZE, chladni.FPS = SIZE, FPS
caustics = load('caustics', os.path.join(ROOT, 'dev', 'protos', 'caustics', 'offline.py'))
flashcount = load('flashcount', os.path.join(ROOT, 'dev', 'flashcount.py'))

BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')
# Traditional pigments (sRGB): indigo, ochre, rose madder (kept off WCAG's red line), off-white, umber, sea green.
EBRU = np.array([(0.16, 0.20, 0.42), (0.80, 0.62, 0.25), (0.75, 0.38, 0.42), (0.93, 0.90, 0.82), (0.33, 0.24, 0.17),
                 (0.25, 0.48, 0.45)], np.float32)[:, ::-1]   # BGR

DEFAULTS = dict(
    pattern=3,       # how far each tray's combing goes: 0 stone (drops only), 1 gel-git, 2 nonpareil, 3 bouquet
    ink=0,           # 0: each drop the picture's color where it lands; 1: the ebru palette; 2: clear (no ink)
    drops=1.0,       # a drop on every beat (0 none); at most 3 a second
    size=0.07,       # a drop's radius at full loudness, in frame heights
    spread=0.25,     # seconds a drop takes to spread
    comb=0.3,        # a comb's pull (the paper's alpha), in frame heights
    sharp=0.02,      # the paper's lambda: how sharply the pull falls off from a tine, in frame heights
    wide=0.25,       # gel-git's tine spacing, in frame heights; nonpareil's is a quarter of it
    stroke=1.0,      # beats a comb stroke takes
    hold=6.0,        # bars a tool holds before it relaxes
    relax=2.0,       # bars it takes to relax
    ss=2,            # supersampling (2: 2 x 2)
)


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class Marbling:
    def __init__(self, v):
        self.v = v
        self.tools = []      # dicts: kind, t0, life (rise, hold, relax), params, ink
        self.rng = np.random.default_rng(3)
        self.ndrop = 0
        self.bars = 0
        w, h = SIZE
        s = int(v['ss'])
        y, x = np.mgrid[0:h * s, 0:w * s].astype(np.float32)
        self.px = (x + 0.5) / (h * s)
        self.py = (y + 0.5) / (h * s)
        self.aspect = w / h

    def strength(self, tool, t):
        rise, hold, relax = tool['life']
        age = t - tool['t0']
        return smooth(age / rise) * (1 - smooth((age - hold) / relax))

    def drop(self, t, pic, level, bands, period):
        v = self.v
        k = self.ndrop
        self.ndrop += 1
        # Across the frame by the R2 low-discrepancy sequence (evenly spread, never a grid); up and down by the
        # bands: the more of the sound is high, the higher the drop lands.
        g = 1.32471795724474602596
        x = (0.5 + k / g) % 1.0
        hi = sum(i * b for i, b in enumerate(bands)) / max(sum(bands), 1e-6) / 6.0
        y = 0.85 - 0.7 * hi + 0.15 * (((0.5 + k / (g * g)) % 1.0) - 0.5)
        cx, cy = x * self.aspect, y
        r = v['size'] * (0.4 + 0.6 * min(level, 1.0))
        if v['ink'] == 0:
            hgt, wid = pic.shape[:2]
            blur = cv2.GaussianBlur(pic, (0, 0), 3)
            ink = blur[int(min(cy, 0.999) * hgt), int(min(cx / self.aspect, 0.999) * wid)].copy()
        elif v['ink'] == 1:
            ink = EBRU[k % len(EBRU)]
        else:
            ink = None
        bars = period * 4
        self.tools.append(dict(kind='drop', t0=t, life=(v['spread'], v['hold'] * bars, v['relax'] * bars),
                               c=(cx, cy), r=r, ink=ink))

    def bar(self, t, period):
        """The tray's next stroke, in the classic order: gel-git right, gel-git back (tines offset half a spacing),
        nonpareil down, bouquet (a comb drawn along a wave); then the tray starts over."""
        v = self.v
        step = self.bars % 4
        self.bars += 1
        if step >= v['pattern']:
            return
        bars = period * 4
        life = (v['stroke'] * period, v['hold'] * bars, v['relax'] * bars)
        wide = v['wide']
        if step == 0:
            self.tools.append(dict(kind='comb', t0=t, life=life, m=(1.0, 0.0), sp=wide, off=0.0, a=v['comb']))
        elif step == 1:
            self.tools.append(dict(kind='comb', t0=t, life=life, m=(-1.0, 0.0), sp=wide, off=wide / 2, a=v['comb']))
        elif step == 2:
            self.tools.append(dict(kind='comb', t0=t, life=life, m=(0.0, 1.0), sp=wide / 4, off=0.0,
                                   a=v['comb'] * 0.5))
        else:
            self.tools.append(dict(kind='comb', t0=t, life=life, m=(0.0, -1.0), sp=wide, off=wide / 4,
                                   a=v['comb'] * 0.7))
            self.tools.append(dict(kind='wave', t0=t, life=life, m=(0.0, 1.0), amp=wide * 0.3,
                                   w=2 * math.pi / (wide * 2), ph=0.0))

    def frame(self, t, pic):
        self.tools = [tl for tl in self.tools if t - tl['t0'] < tl['life'][1] + tl['life'][2]]
        x, y = self.px.copy(), self.py.copy()
        col = None
        done = np.zeros(x.shape, bool)
        out = np.zeros(x.shape + (3,), np.float32)
        for tl in reversed(self.tools):
            s = self.strength(tl, t)
            if s <= 0:
                continue
            if tl['kind'] == 'drop':
                cx, cy = tl['c']
                r2 = tl['r'] ** 2 * s
                dx, dy = x - cx, y - cy
                q2 = dx * dx + dy * dy
                inside = (q2 < r2) & ~done
                if tl['ink'] is not None:
                    out[inside] = tl['ink']
                    done |= inside
                k = np.sqrt(np.maximum(1 - r2 / np.maximum(q2, 1e-12), 0))
                x, y = np.where(done, x, cx + dx * k), np.where(done, y, cy + dy * k)
            elif tl['kind'] == 'comb':
                mx, my = tl['m']
                nx, ny = -my, mx
                sp, lam, a = tl['sp'], self.v['sharp'], tl['a'] * s
                d = (x * nx + y * ny + tl['off']) % sp
                d = sp / 2 - np.abs(d - sp / 2)
                mean = 2 * lam / sp * math.log(1 + sp / (2 * lam))
                disp = a * (lam / (d + lam) - mean)
                x, y = x - disp * mx, y - disp * my
            else:
                mx, my = tl['m']
                nx, ny = -my, mx
                disp = tl['amp'] * s * np.sin(tl['w'] * (x * nx + y * ny) + tl['ph'])
                x, y = x - disp * mx, y - disp * my
        hgt, wid = pic.shape[:2]
        # The tray runs on past the frame: the picture mirrored.
        u = x / self.aspect
        u = 1 - np.abs((u % 2) - 1)
        vv = 1 - np.abs((y % 2) - 1)
        seen = cv2.remap(pic, (u * wid - 0.5).astype(np.float32), (vv * hgt - 0.5).astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REPLICATE)
        img = np.where(done[..., None], out, seen)
        return cv2.resize(img, SIZE, interpolation=cv2.INTER_AREA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('variants', nargs='*', help='name:key=value,...')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=12)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'marbling', 'offline'))
    ap.add_argument('--at', default='3,6,9,11.5')
    ap.add_argument('--novideo', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    rows = chladni.song_channels(a.song, a.seconds)
    pics = chladni.frames(a.clip, n)
    variants = []
    for spec in a.variants or ['defaults:']:
        name, _, kv = spec.partition(':')
        v = dict(DEFAULTS)
        v.update({k: float(x) for k, x in (p.split('=') for p in kv.split(',') if p)})
        variants.append((name, Marbling(v)))
    outs = {name: [] for name, _ in variants}
    last_drop = {name: -9.0 for name, _ in variants}
    t0 = time.time()
    for f in range(n):
        r = rows[min(f, len(rows) - 1)]
        rp = rows[min(f - 1, len(rows) - 1)] if f else r
        t = f / FPS
        beat = f and r['beat_count'] > rp['beat_count']
        bar = f and r['bar_count'] > rp['bar_count']
        period = r.get('beat_period', 0.5) or 0.5
        for name, m in variants:
            if beat and m.v['drops'] > 0 and t - last_drop[name] >= 1 / 3:
                m.drop(t, pics[f], r['level'], [r.get(b, 0.0) for b in BANDS], period)
                last_drop[name] = t
            if bar:
                m.bar(t, period)
            outs[name].append(m.frame(t, pics[f]))
        if f % FPS == 0:
            print('frame', f, round(time.time() - t0, 1), 's', ' '.join('{}={}'.format(nm, len(m.tools))
                                                                       for nm, m in variants), flush=True)
    t = np.arange(n) / FPS
    report = []
    for name, frames in [('clip', pics)] + list(outs.items()):
        g = [caustics.grid(im) for im in frames[FPS:]]
        m = flashcount.measure(t[FPS:], np.array([x[0] for x in g]), np.array([x[1] for x in g]))
        report.append('{:<12} whole {:.1f} area {:.1f} red {:.1f} cell {:.1f}'.format(name, m['whole'], m['area'],
                                                                                     m['red'], m['cell']))
    open(os.path.join(a.out, a.clip + '_flash.txt'), 'w').write('\n'.join(report) + '\n')
    print('\n'.join(report))
    w, hgt = SIZE
    names = list(outs)
    times = [int(float(s) * FPS) for s in a.at.split(',') if float(s) * FPS < n]
    sheet = [np.hstack([cv2.resize(np.clip(im, 0, 1), (w // 2, hgt // 2), interpolation=cv2.INTER_AREA)
                        for im in [pics[k]] + [outs[nm][k] for nm in names]]) for k in times]
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.jpg'), (np.vstack(sheet) * 255).astype(np.uint8))
    for nm in names:
        cv2.imwrite(os.path.join(a.out, '{}_{}_full.jpg'.format(a.clip, nm)),
                    (np.clip(outs[nm][times[-1]], 0, 1) * 255).astype(np.uint8))
    if a.novideo:
        return
    raw = os.path.join(a.out, a.clip + '_raw.mp4')
    cols = min(len(names) + 1, 3)
    rows_n = -(-(len(names) + 1) // cols)
    vw = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (w // 2 * cols, hgt // 2 * rows_n))
    for f in range(n):
        cells = [pics[f]] + [outs[nm][f] for nm in names]
        cells += [np.zeros_like(pics[f])] * (cols * rows_n - len(cells))
        frame = np.vstack([np.hstack([cv2.resize(np.clip(c, 0, 1), (w // 2, hgt // 2)) for c in cells[r * cols:(r + 1) * cols]])
                           for r in range(rows_n)])
        vw.write((frame * 255).astype(np.uint8))
    vw.release()
    out = os.path.join(a.out, a.clip + '.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-i', os.path.join(READY, a.song + '.wav'),
                    '-shortest', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', out], check=True)
    os.remove(raw)
    print('wrote', out)


if __name__ == '__main__':
    main()
