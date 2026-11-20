"""DEV ONLY. Ferrofluid outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4849): a black
glossy liquid over the picture that bristles into spikes where the picture is bright or near, on the bass.

    uv run --with numpy --with opencv-python-headless dev/protos/ferrofluid/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/ferrofluid/offline

The surface is a height field h on a grid a quarter of the picture's size, stepped as the GPU would step it (one
explicit step a pass) by a Swift-Hohenberg equation (Swift and Hohenberg, Phys. Rev. A 15, 1977) in units where the
spikes' wavenumber is 1:

    dh/dt = r(x) h - (1 + lap / k0^2)^2 h + g h^2 - h^3

k0 = 2 pi / (wavelength in cells). Past r = 0 a lattice of spikes grows (hexagons with g > 0, the Rosensweig pattern:
Cowley and Rosensweig, JFM 30, 1967); the quadratic term makes the onset subcritical, so spikes snap up and linger as
r falls back (Gollwitzer, Rehberg and Richter 2006 measured that hysteresis). r is the local field: low everywhere,
higher where the picture is bright (or near, from input 3), raised by the bass.

Variants are named on the command line as name:key=value,...; see DEFAULTS. Writes a sheet (a row a moment, the clip
then each variant), the last moment full size, an MP4 with the song, and flash counts per variant against the clip.
"""

import argparse
import importlib.util
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

DEFAULTS = dict(
    grid=2.0,        # grid cells are this many prototype pixels (640 x 360 here: 2 is a quarter of 1280 x 720)
    wave=6.0,        # the pattern's wavelength in cells
    dt=0.1,          # model time a step
    rate=1200.0,     # steps a second (20 a frame at 60 fps)
    g=1.0,           # the quadratic term: hexagons, and the subcritical onset
    rlo=-0.3,        # r where nothing drives it (flat: hexagons hold above about 0 for g = 1, dev/out/ferrofluid/regimes.png)
    rhi=0.25,        # r where fully driven (hexagons to about 0.3, stripes from about 0.5)
    bass=0.6,        # how much of the drive the bass sets (the rest is always there)
    beat=0.4,        # a beat's lift of r, falling over 0.3 s
    from_depth=1.0,  # 1: the drive is nearness when there is a depth map, else brightness
    soft=3.0,        # the drive is blurred over this many cells (a field doesn't stop at an edge)
    stand=0.1,       # depth: what stands nearer than what lies left and right by this much (lib depth_find's idea)
    # the look
    cone=1.0,        # 1: spikes as cones (height from the distance to the peak), 0: the field's own bumps
    sharp=1.0,       # the cone's profile: 1 straight flanks, 2 concave (a sharp tip on a flared base)
    tilt=0.0,        # the view leans: a spike's tip shows tilt x its height above its base (0: straight on)
    height=6.0,      # spike height in cells (sets how steep the flanks are)
    box=1.0,         # a soft overhead light (a softbox) in what the liquid reflects, beside the picture
    f0=0.06,         # Fresnel reflectance facing the camera
    bend=0.08,       # how far the reflection slides with the surface's slope (fraction of the frame)
    tint=0.0,        # 0: black liquid; 1: the liquid takes the picture's colors (Tinted)
    spec=1.0,        # the light's highlight
    under=0.0,       # how much of the picture shows through where the liquid lies flat
)


def lap9(a):
    """The isotropic 9-point Laplacian (Oono and Puri 1988), cells as the unit, edges held."""
    p = np.pad(a, 1, mode='edge')
    e = p[1:-1, 2:] + p[1:-1, :-2] + p[2:, 1:-1] + p[:-2, 1:-1]
    c = p[2:, 2:] + p[2:, :-2] + p[:-2, 2:] + p[:-2, :-2]
    return (4 * e + c - 20 * a) / 6


class Ferro:
    def __init__(self, v):
        self.v = v
        w, h = SIZE
        self.gw, self.gh = int(w / v['grid']), int(h / v['grid'])
        rng = np.random.default_rng(1)
        self.h = (rng.standard_normal((self.gh, self.gw)) * 0.01).astype(np.float32)
        self.carry = 0.0
        self.beat_t = 9.0
        self.steps = 0

    def drive(self, pic, depth):
        v = self.v
        if depth is not None and v['from_depth'] > 0:
            d = depth.astype(np.float32)
            w = d.shape[1]
            side = cv2.blur(d, (w // 3 | 1, 1))
            d = np.clip((d - side - v['stand']) / v['stand'], 0, 1)
        else:
            d = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
            d = np.clip((d - 0.25) / 0.5, 0, 1)
        d = cv2.resize(d, (self.gw, self.gh), interpolation=cv2.INTER_AREA)
        return cv2.GaussianBlur(d, (0, 0), v['soft'])

    def step_field(self, r, n):
        v = self.v
        k2 = (2 * np.pi / v['wave']) ** 2
        h = self.h
        for _ in range(n):
            l1 = h + lap9(h) / k2
            l2 = l1 + lap9(l1) / k2
            h = h + v['dt'] * (r * h - l2 + v['g'] * h * h - h * h * h)
        self.h = h.astype(np.float32)

    def frame(self, pic, depth, beat, level):
        v = self.v
        if beat:
            self.beat_t = 0.0
        self.beat_t += 1 / FPS
        lift = v['beat'] * max(0.0, 1 - self.beat_t / 0.3)
        amount = (1 - v['bass']) + v['bass'] * level
        d = self.drive(pic, depth)
        r = v['rlo'] + (v['rhi'] - v['rlo']) * d * amount + lift * d
        self.carry += v['rate'] / FPS
        n = int(self.carry)
        self.carry -= n
        self.step_field(r.astype(np.float32), n)
        return self.render(pic)

    def surface(self):
        """The height at the picture's size, in cells: cones whose tips sit on the field's peaks."""
        v = self.v
        w, hgt = SIZE
        h = cv2.resize(self.h, (w, hgt), interpolation=cv2.INTER_CUBIC)
        if v['cone'] > 0:
            # the peak's own height nearby (a dilation over half a wavelength), and how far below it this point is:
            # near a peak h ~ peak (1 - (d / R)^2), so d / R ~ sqrt(1 - h / peak) and the cone is 1 - that.
            rad = max(1, int(v['wave'] * v['grid'] / 2))
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            peak = cv2.dilate(h, ker)
            frac = np.clip(h / np.maximum(peak, 1e-3), 0, 1)
            z = np.clip(peak, 0, None) * (1 - np.sqrt(1 - frac)) ** v['sharp']
        else:
            z = np.clip(h, 0, None)
        return z * v['height']

    def render(self, pic):
        v = self.v
        w, hgt = SIZE
        z = self.surface()
        y, x = np.mgrid[0:hgt, 0:w].astype(np.float32)
        bx, by = x, y
        if v['tilt'] > 0:
            # steep parallax: march down from the tallest spike; the first base whose height reaches the ray is seen
            zp = z * v['grid']                      # height in pixels
            top = float(zp.max()) + 1
            steps = 24
            hit = np.zeros(z.shape, bool)
            bx, by = x.copy(), y.copy()
            for k in range(steps + 1):
                s_ = top * (1 - k / steps)
                qy = y + s_ * v['tilt']
                zq = chladni.sample(zp, x, qy)
                new = (~hit) & (zq >= s_)
                by = np.where(new, qy, by)
                hit |= new
            z = chladni.sample(z, bx, by)
            pic_seen = chladni.sample(pic, bx, by)
        else:
            pic_seen = pic
        # slope in cells of height per picture pixel; one cell is grid prototype pixels
        zs = self.surface() if v['tilt'] > 0 else z
        gx = cv2.Sobel(zs, cv2.CV_32F, 1, 0, ksize=3) / 8 * v['grid']
        gy = cv2.Sobel(zs, cv2.CV_32F, 0, 1, ksize=3) / 8 * v['grid']
        if v['tilt'] > 0:
            gx, gy = chladni.sample(gx, bx, by), chladni.sample(gy, bx, by)
        n = np.stack([-gx, -gy, np.ones_like(z)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        cos = n[..., 2]
        fres = v['f0'] + (1 - v['f0']) * (1 - cos) ** 5
        # the reflection: the picture seen in a curved mirror, sliding with the slope
        rx = x + n[..., 0] * v['bend'] * hgt * 4
        ry = y + n[..., 1] * v['bend'] * hgt * 4
        env = chladni.sample(cv2.GaussianBlur(pic, (0, 0), 2), rx, ry)
        # the softbox: bright where the surface faces up and toward the camera (n.y < 0 is up in the picture)
        box = np.clip(-n[..., 1] * 1.4 - 0.1, 0, 1) ** 2 * v['box']
        env = env + box[..., None]
        light = np.array([-0.4, -0.5, 0.77], np.float32)
        light /= np.linalg.norm(light)
        half = light + np.array([0, 0, 1], np.float32)
        half /= np.linalg.norm(half)
        spec = np.clip((n * half).sum(-1), 0, 1) ** 60 * v['spec']
        diffuse = np.clip((n * light).sum(-1), 0, 1)[..., None]
        base = pic_seen * v['tint'] * (0.3 + 0.9 * diffuse) + pic_seen * v['under']
        out = base * (1 - fres[..., None]) + env * fres[..., None] + spec[..., None]
        return np.clip(out, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('variants', nargs='*', help='name:key=value,...')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'ferrofluid', 'offline'))
    ap.add_argument('--at', default='2,4,6,8')
    ap.add_argument('--novideo', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    rows = chladni.song_channels(a.song, a.seconds)
    counts = [r['beat_count'] for r in rows]
    beats = {i for i in range(1, len(counts)) if counts[i] > counts[i - 1]}
    levels = [r['level'] for r in rows]
    pics = chladni.frames(a.clip, n)
    dpath = os.path.join(READY, a.clip + '_depth.mp4')
    depths = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in chladni.frames(a.clip + '_depth', n)] \
        if os.path.exists(dpath) else [None] * n
    variants = []
    for spec in a.variants or ['defaults:']:
        name, _, kv = spec.partition(':')
        v = dict(DEFAULTS)
        v.update({k: float(x) for k, x in (p.split('=') for p in kv.split(',') if p)})
        variants.append((name, Ferro(v)))
    outs = {name: [] for name, _ in variants}
    t0 = time.time()
    for f in range(n):
        for name, fe in variants:
            outs[name].append(fe.frame(pics[f], depths[f], f in beats, levels[min(f, len(levels) - 1)]))
        if f % FPS == 0:
            amps = ' '.join('{}={:.2f}'.format(nm, float(np.abs(fe.h).max())) for nm, fe in variants)
            print('frame', f, round(time.time() - t0, 1), 's', amps, flush=True)
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
                    (outs[nm][times[-1]] * 255).astype(np.uint8))
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
