"""DEV ONLY. Caustics' look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4671): the
picture as a pool floor under moving water, the light the ripples focus lighting it in bright lines, the picture seen
through the water's surface, deeper water bluer.

    uv run --with numpy --with opencv-python-headless dev/protos/caustics/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/caustics/offline

The water is a height field stepped by the damped wave equation (as Evan Wallace's WebGL Water steps it, MIT), at half
the picture's size, disturbed by the picture's change since the last frame (whatever moves pushes the water), by a
light rain (Wind), and by a drop on each beat of the song (lib/audio_callbacks.py as raw audio). The caustics are
Yuksel and Keyser's ("Fast Real-time Caustics from Height Fields", 2009): every sample of the surface, one a pixel of
the caustics map, refracts the sun's light down to the floor, and a one-pixel square around where it lands adds its
overlap to the pixels it covers (their gather over a window, done here as the equivalent splat). Flat water lights
every pixel 1. The floor is seen through the surface (the view refracted the same way) and lit by the caustics, its
colors absorbed with depth (Beer-Lambert, red first).

Variants are named on the command line as name:key=value,...; keys: amp (the waves' height scale), depth (water depth,
a share of the picture's height), wind (raindrops a second), push (how hard movement pushes), kick (a beat's drop),
waves (the wave equation's steps a second, its speed), damp (how much a step keeps), gain (the caustics' strength),
rainbow (spread of the index of refraction), floor (use the clip's depth map for the water's depth: 1). Writes a sheet
(a row a moment, the clip then each variant), a strip, an MP4 with the song, and flash counts per variant against the
clip (dev/flashcount.py's measure on 64 x 36 cells of linear luminance).
"""

import argparse
import importlib.util
import os
import subprocess

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE = (640, 360)
FPS = 30
IOR = 1.333


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


chladni = load('chladni', os.path.join(ROOT, 'dev', 'protos', 'chladni', 'offline.py'))
chladni.SIZE, chladni.FPS = SIZE, FPS
flashcount = load('flashcount', os.path.join(ROOT, 'dev', 'flashcount.py'))

DEFAULTS = dict(amp=1.0, depth=1.0, wind=1.0, push=0.5, kick=0.5, waves=30.0, damp=0.985, gain=0.6, rainbow=0.0,
                floor=0.0, swell=1.0, size=0.12, tint=0.18, refr=0.25, visc=0.15, pushv=0.0, wake=3.0)
# The base sea: SWELLS directional sine waves, wavelengths spread about size x the picture's width, their slope SLOPE each,
# heading roughly along the wind; deep-water dispersion (omega = sqrt(g k)), g set so the size wave takes PERIOD s.
SWELLS, SLOPE, PERIOD = 10, 0.03, 2.5


def refract(ix, iy, iz, nx, ny, nz, eta):
    """GLSL's refract() on arrays: incident (unit) and normal (unit), eta = n1 / n2."""
    d = nx * ix + ny * iy + nz * iz
    k = 1.0 - eta * eta * (1.0 - d * d)
    s = eta * d + np.sqrt(np.maximum(k, 0.0))
    return eta * ix - s * nx, eta * iy - s * ny, eta * iz - s * nz


def normals(h):
    """The surface's unit normal from the height field (heights in pixels of the caustics map)."""
    p = np.pad(h, 1, mode='edge')
    gx = (p[1:-1, 2:] - p[1:-1, :-2]) * 0.5
    gy = (p[2:, 1:-1] - p[:-2, 1:-1]) * 0.5
    n = np.sqrt(gx * gx + gy * gy + 1.0)
    return -gx / n, -gy / n, 1.0 / n


def caustics(h, depth, sun, eta):
    """Yuksel and Keyser's caustics map: every surface sample (one a pixel) refracts the sun's light to the floor, and
    a one-pixel square there adds its overlap with each pixel it covers. depth: the water's depth per pixel (pixels)."""
    H, W = h.shape
    nx, ny, nz = normals(h)
    lx, ly, lz = sun
    tx, ty, tz = refract(lx, ly, lz, nx, ny, nz, eta)
    # the rest surface's refracted light, so the caustics line up with the floor below their own surface point
    rx, ry, rz = refract(lx, ly, lz, 0.0, 0.0, 1.0, eta)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    run = (depth + h) / np.maximum(-tz, 1e-3)
    hx = x + tx * run - rx * depth / -rz
    hy = y + ty * run - ry * depth / -rz
    out = np.zeros((H, W), np.float32)
    x0, y0 = np.floor(hx).astype(int), np.floor(hy).astype(int)
    fx, fy = hx - x0, hy - y0
    for dx, dy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi, yi = x0 + dx, y0 + dy
        ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        np.add.at(out, (yi[ok], xi[ok]), w[ok])
    return out


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def grid(img):
    """64 x 36 cells of relative luminance in linear light, and WCAG's red measure, as dev/flash.py records them."""
    l = lin(np.clip(img, 0, 1))
    b, g, r = l[..., 0], l[..., 1], l[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    s = r + g + b
    red = np.where((s > 0) & (r / np.maximum(s, 1e-9) >= 0.8), np.maximum((r - g - b) * 320, 0), 0)
    H, W = lum.shape
    return (lum.reshape(36, H // 36, 64, W // 64).mean((1, 3)), red.reshape(36, H // 36, 64, W // 64).mean((1, 3)))


class Water:
    def __init__(self, v, depth_map):
        self.v = v
        w, hgt = SIZE
        self.H, self.W = hgt // 2, w // 2
        self.h = np.zeros((self.H, self.W), np.float32)
        self.vel = np.zeros_like(self.h)
        self.depth_map = depth_map
        self.rng = np.random.default_rng(7)
        self.prev = None
        self.acc = 0.0
        self.t = 0.0
        w, hgt = SIZE
        lam0 = v['size'] * w
        wind = self.rng.uniform(0, 2 * np.pi)
        self.swells = []
        for i in range(SWELLS):
            lam = lam0 * 2 ** self.rng.uniform(-1, 1)
            k = 2 * np.pi / lam
            ang = wind + self.rng.normal(0, 1.1)
            g = (2 * np.pi / PERIOD) ** 2 / (2 * np.pi / lam0)
            self.swells.append((k * np.cos(ang), k * np.sin(ang), SLOPE / k, np.sqrt(g * k), self.rng.uniform(0, 2 * np.pi)))

    def drop(self, cx, cy, radius, strength):
        y, x = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        d = np.maximum(0, 1 - np.hypot(x - cx, y - cy) / radius)
        self.h += (0.5 - 0.5 * np.cos(d * np.pi)) * strength

    def step(self, luma, beat):
        v = self.v
        small = cv2.resize(luma, (self.W, self.H), interpolation=cv2.INTER_AREA)
        if self.prev is not None:
            # what moves pushes the water, smoothed so it makes wakes, not grain
            d = cv2.GaussianBlur(small - self.prev, (0, 0), v['wake'])
            self.h += v['push'] * 6.0 * d
            self.vel += v['pushv'] * 6.0 * d               # or into the water's velocity: the surface integrates it
        self.prev = small
        self.t += 1.0 / FPS
        if beat and v['kick'] > 0:
            self.drop(self.rng.uniform(0.2, 0.8) * self.W, self.rng.uniform(0.2, 0.8) * self.H, 12.0, 2.0 * v['kick'])
        self.acc += v['waves'] / FPS
        while self.acc >= 1:
            self.acc -= 1
            avg = 0.25 * (np.roll(self.h, 1, 0) + np.roll(self.h, -1, 0) + np.roll(self.h, 1, 1) + np.roll(self.h, -1, 1))
            self.vel += (avg - self.h) * 2.0
            self.vel *= v['damp']
            self.h += self.vel
            # a little viscosity: the finest ripples (the grid's checkerboard) die first
            self.h += v['visc'] * (avg - self.h)
            self.h -= self.h.mean() * 0.02

    def render(self, pic, depth_frame):
        v = self.v
        w, hgt = SIZE
        h = cv2.resize(self.h, (w, hgt), interpolation=cv2.INTER_CUBIC) * 2.0 * v['amp']   # heights in picture pixels
        y, x = np.mgrid[0:hgt, 0:w].astype(np.float32)
        for kx, ky, a, om, ph in self.swells:
            h = h + v['swell'] * v['amp'] * a * np.sin(kx * x + ky * y - om * self.t * v['wind'] + ph)
        if v['floor'] > 0 and depth_frame is not None:
            near = cv2.GaussianBlur(depth_frame, (0, 0), 6)
            depth = hgt * v['depth'] * (0.5 + 1.0 * (1 - near))
        else:
            depth = np.full((hgt, w), hgt * v['depth'], np.float32)
        sun = np.array([0.25, -0.15, -1.0])
        sun = sun / np.linalg.norm(sun)
        etas = [1 / (IOR + v['rainbow'] * k) for k in (-1, 0, 1)]   # B, G, R: red bends least
        P = 48
        hp = np.pad(h, P, mode='reflect')
        dp = np.pad(depth, P, mode='edge')
        light = np.stack([caustics(hp, dp, sun, e)[P:-P, P:-P] for e in etas], -1)
        light = 1.0 + v['gain'] * (light - 1.0)
        # the floor seen through the surface: the view (straight down) refracted
        nx, ny, nz = normals(h)
        tx, ty, tz = refract(0.0, 0.0, -1.0, nx, ny, nz, 1 / IOR)
        run = v['refr'] * (depth + h) / np.maximum(-tz, 1e-3)
        mx, my = (x + tx * run).astype(np.float32), (y + ty * run).astype(np.float32)
        floor = cv2.remap(pic, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        lit = cv2.remap(light, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        absorb = np.exp(-v['tint'] * (depth / hgt)[..., None] * np.array([2.0, 0.9, 0.5][::-1]))   # BGR: red absorbed most
        out = floor * lit * absorb
        # the sun's glint on the surface
        rz = 2 * nz * (-sun[2]) * nz - (-sun[2])
        out += (np.clip(rz, 0, 1) ** 400 * 0.6)[..., None]
        return np.clip(out, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('variants', nargs='*', help='name:key=value,...')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--out', default='dev/out/caustics/offline')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    rows = chladni.song_channels(a.song, a.seconds)
    counts = [r['beat_count'] for r in rows]
    beats = {i for i in range(1, len(counts)) if counts[i] > counts[i - 1]}
    pics = chladni.frames(a.clip, n)
    dpath = os.path.join(READY, a.clip + '_depth.mp4')
    depths = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in chladni.frames(a.clip + '_depth', n)] \
        if os.path.exists(dpath) else [None] * n
    variants = []
    for spec in a.variants or ['defaults:']:
        name, _, kv = spec.partition(':')
        v = dict(DEFAULTS)
        v.update({k: float(x) for k, x in (p.split('=') for p in kv.split(',') if p)})
        variants.append((name, Water(v, None)))
    outs = {name: [] for name, _ in variants}
    for f in range(n):
        luma = cv2.cvtColor(pics[f], cv2.COLOR_BGR2GRAY)
        for name, water in variants:
            water.step(luma, f in beats)
            outs[name].append(water.render(pics[f], depths[f]).astype(np.float32))
    t = np.arange(n) / FPS
    report = []
    for name, frames in [('clip', pics)] + list(outs.items()):
        g = [grid(im) for im in frames[FPS:]]
        m = flashcount.measure(t[FPS:], np.array([x[0] for x in g]), np.array([x[1] for x in g]))
        report.append('{:<12} whole {:.1f} area {:.1f} red {:.1f} cell {:.1f}'.format(name, m['whole'], m['area'], m['red'], m['cell']))
    open(os.path.join(a.out, a.clip + '_flash.txt'), 'w').write('\n'.join(report) + '\n')
    print('\n'.join(report))
    w, hgt = SIZE
    names = list(outs)
    times = [int(s * FPS) for s in (2.0, 4.0, 6.0, 8.0) if s * FPS < n]
    sheet = [np.hstack([cv2.resize(np.clip(im, 0, 1), (w // 2, hgt // 2), interpolation=cv2.INTER_AREA)
                        for im in [pics[k]] + [outs[nm][k] for nm in names]]) for k in times]
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.jpg'), (np.vstack(sheet) * 255).astype(np.uint8))
    k = times[1]
    cv2.imwrite(os.path.join(a.out, a.clip + '_full.jpg'),
                (np.hstack([pics[k], outs[names[0]][k]]) * 255).astype(np.uint8))
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
