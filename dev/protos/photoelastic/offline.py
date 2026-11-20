"""DEV ONLY. Photoelastic outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4853): the
picture as clear plastic between polarizers, stressed by its shape and its movement, in Michel-Levy's interference
colors.

    uv run --with numpy --with opencv-python-headless dev/protos/photoelastic/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/photoelastic/offline

Stress is kept as its deviatoric part, a = (sxx - syy) / 2 and b = sxy, in fringe orders (one order is a retardation
of LAMBDA0 nm), so the principal stress difference is N = 2 sqrt(a^2 + b^2) and the first principal direction
theta = atan2(b, a) / 2. Loads superpose, so each source adds its own a, b:

    bend: the plastic is a sheet pressed into the depth (or the brightness): a bent plate's surface stress follows
          its curvature (Kirchhoff), so a, b come from the Hessian of the height smoothed at a scale.
    flow: the plastic as a viscoelastic liquid (Maxwell, 1873, saw flowing Canada balsam turn birefringent): the
          picture's optical flow's strain rate loads it, and the stress relaxes over tau seconds, kept per pixel.

Light through the polariscope: circular dark field T = sin^2(pi delta / lambda), light field 1 - that, plane crossed
sin^2(2 (theta - alpha)) sin^2(pi delta / lambda); the tint plate (a full wave at LAMBDA_TINT, at 45 degrees) by Jones
calculus. Summed over wavelengths through Wyman, Sloan and Shirley's CIE fit (lib spectrum.glsl).

    heat: the plastic warmed by what stands out (depth), the light and what moves, its thermal stress from Goodier's
          potential, lap psi = warmth, solved exactly here (a DST on a padded grid). The effect builds on this one:
          bend and flow drew fringes over every bit of noise (board #4853).

Variants are named on the command line as name:key=value,...; see DEFAULTS.
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
LAMBDA0 = 550.0
LAMBDA_TINT = 550.0


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


chladni = load('chladni', os.path.join(ROOT, 'dev', 'protos', 'chladni', 'offline.py'))
chladni.SIZE, chladni.FPS = SIZE, FPS
caustics = load('caustics', os.path.join(ROOT, 'dev', 'protos', 'caustics', 'offline.py'))
flashcount = load('flashcount', os.path.join(ROOT, 'dev', 'flashcount.py'))

STYLES = ('dark', 'light', 'plane', 'tint')
DEFAULTS = dict(
    style=0,        # index into STYLES
    bend=1.0,       # orders of the bend stress at its strongest typical curvature
    scale=0.03,     # the bend's smoothing, a share of the frame height
    scale2=0.0,     # a second, broader scale added (0: none)
    flow=1.0,       # orders a second of strain rate 1 / s... times this gain
    tau=1.0,        # the flow stress relaxes over tau s
    cap=4.0,        # the orders shown saturate softly toward this
    leak=0.15,      # how much of the picture the polarizers let through anyway
    white=0.5,      # the backlight: 0 the picture, 1 white at the picture's mean brightness
    gain=1.4,       # the transmitted light's brightness
    alpha=0.0,      # the polarizers' angle, degrees
    bass=0.0,       # how much the bass scales the load
    beat=0.0,       # a beat's squeeze (share of the load), over 0.3 s
    luma=0.0,       # 1: bend from brightness even with depth
    heat=0.0,       # thermal stress: orders per unit of warmth (Goodier's potential solved exactly here)
    move=1.0,       # how much what moves warms (frame difference past a dead zone)
    fall=1.5,       # warmth falls over this many s (rises over 0.15)
    stand=0.1,      # depth: what stands nearer than its row's surroundings by this much is the subject
    light=0.55,     # no depth: brightness from this warms
)


def poisson(f, pad=0.5):
    """psi with lap psi = f, psi = 0 on a border pad x the size away (DST), pixels as the unit."""
    H, W = f.shape
    ph, pw = int(H * pad), int(W * pad)
    g = np.zeros((H + 2 * ph, W + 2 * pw), np.float64)
    g[ph:ph + H, pw:pw + W] = f
    Hh, Ww = g.shape
    # DST-I through an odd extension and the FFT.
    ext = np.zeros((2 * Hh + 2, 2 * Ww + 2))
    ext[1:Hh + 1, 1:Ww + 1] = g
    ext[Hh + 2:, 1:Ww + 1] = -g[::-1]
    ext[1:Hh + 1, Ww + 2:] = -g[:, ::-1]
    ext[Hh + 2:, Ww + 2:] = g[::-1, ::-1]
    F = np.fft.fft2(ext)
    ky = 2 * np.pi * np.fft.fftfreq(2 * Hh + 2)
    kx = 2 * np.pi * np.fft.fftfreq(2 * Ww + 2)
    den = (2 * np.cos(ky)[:, None] - 2) + (2 * np.cos(kx)[None] - 2)
    den[0, 0] = 1
    P = np.real(np.fft.ifft2(F / den))
    return P[1:Hh + 1, 1:Ww + 1][ph:ph + H, pw:pw + W].astype(np.float32)


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def cmf(l):
    def lobe(mu, s1, s2):
        t = (l - mu) / np.where(l < mu, s1, s2)
        return np.exp(-0.5 * t * t)
    return np.stack([1.056 * lobe(599.8, 37.9, 31.0) + 0.362 * lobe(442.0, 16.0, 26.7) - 0.065 * lobe(501.1, 20.4, 26.2),
                     0.821 * lobe(568.8, 46.9, 40.5) + 0.286 * lobe(530.9, 16.3, 31.1),
                     1.217 * lobe(437.0, 11.8, 36.0) + 0.681 * lobe(459.0, 26.0, 13.8)], -1)


XYZ2RGB = np.array([[3.2404542, -1.5371385, -0.4985314], [-0.9692660, 1.8760108, 0.0415560],
                    [0.0556434, -0.2040259, 1.0572252]])


def charts(cap, n_orders=512, n_angles=64, n_lam=41):
    """Per style, linear RGB transmission over (angle of the first principal direction to the polarizer, 0-180
    degrees; orders 0..cap + 1), white light through it = 1."""
    lam = np.linspace(380, 780, n_lam)
    rgb = cmf(lam) @ XYZ2RGB.T
    white = rgb.sum(0)
    N = np.linspace(0, cap + 1, n_orders)
    th = np.linspace(0, np.pi, n_angles, endpoint=False)
    phi = 2 * np.pi * N[None, :, None] * LAMBDA0 / lam[None, None, :]          # sample retardance, radians
    s2 = np.sin(phi / 2) ** 2
    out = {}
    out['dark'] = np.broadcast_to(s2, (n_angles,) + s2.shape[1:])
    out['light'] = 1 - out['dark']
    out['plane'] = np.sin(2 * th)[:, None, None] ** 2 * s2
    # Tint: polarizer along x, the sample (fast axis at th), a full-wave plate at 45 degrees, analyzer along y.
    c, s = np.cos(th)[:, None, None], np.sin(th)[:, None, None]
    e = np.exp(1j * phi)
    # sample Jones on (1, 0): R(-th) diag(1, e) R(th) (1, 0) = (c^2 + s^2 e, c s (1 - e))... with R(th) = [[c, s], [-s, c]]
    ex = c * c + s * s * e
    ey = c * s * (1 - e)
    p = np.exp(1j * 2 * np.pi * LAMBDA_TINT / lam)[None, None, :]
    # plate at 45 degrees: 0.5 [[1 + p, 1 - p], [1 - p, 1 + p]]
    fy = 0.5 * ((1 - p) * ex + (1 + p) * ey)
    out['tint'] = np.abs(fy) ** 2
    return {k: (v @ rgb) / white for k, v in out.items()}, N, th


def blur(a, sigma):
    return cv2.GaussianBlur(a, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)


def hessian_ab(h, sigma):
    """The deviatoric part of h's Hessian at scale sigma (pixels), scale-normalized (x sigma^2)."""
    g = blur(h, sigma)
    hxx = cv2.Sobel(g, cv2.CV_32F, 2, 0, ksize=3, borderType=cv2.BORDER_REFLECT) * sigma * sigma
    hyy = cv2.Sobel(g, cv2.CV_32F, 0, 2, ksize=3, borderType=cv2.BORDER_REFLECT) * sigma * sigma
    hxy = cv2.Sobel(g, cv2.CV_32F, 1, 1, ksize=3, borderType=cv2.BORDER_REFLECT) * sigma * sigma / 4
    return (hxx - hyy) / 2, hxy


class Photo:
    def __init__(self, v):
        self.v = v
        self.style = STYLES[int(v['style'])]
        self.chart, self.N, self.th = charts(v['cap'])
        self.chart = self.chart[self.style]
        self.prev = None
        self.fa = self.fb = None
        self.beat_env = 0.0
        self.warm = None
        self.lprev = None
        self.level = 0.0

    def frame(self, pic, depth, beat, level):
        v = self.v
        H, W = pic.shape[:2]
        luma = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
        h = luma if (depth is None or v['luma']) else depth.astype(np.float32) / 255
        a, b = hessian_ab(h, v['scale'] * H)
        a, b = a * 8 * v['bend'], b * 8 * v['bend']
        if v['heat'] > 0:
            if depth is not None:
                d = depth.astype(np.float32) / 255
                row = cv2.blur(d, (W // 4 * 2 + 1, 1))
                subj = np.clip((d - row - v['stand']) / 0.05, 0, 1)
            else:
                subj = np.clip((luma - v['light']) / 0.2, 0, 1)
            mv = np.zeros_like(luma) if self.lprev is None else \
                np.clip((np.abs(blur(luma, 2) - blur(self.lprev, 2)) - 0.03) / 0.07, 0, 1) * v['move']
            self.lprev = luma
            src = np.maximum(subj, mv)
            if self.warm is None:
                self.warm = src.copy()
            up = src > self.warm
            k_up, k_dn = 1 - np.exp(-1 / FPS / 0.15), 1 - np.exp(-1 / FPS / v['fall'])
            self.warm += (src - self.warm) * np.where(up, k_up, k_dn)
            q = 4
            psi = poisson(cv2.resize(self.warm, (W // q, H // q), interpolation=cv2.INTER_AREA))
            hxx = psi[:, 2:] - 2 * psi[:, 1:-1] + psi[:, :-2]
            hxx = np.pad(hxx, ((0, 0), (1, 1)), mode='edge')
            hyy = np.pad(psi[2:] - 2 * psi[1:-1] + psi[:-2], ((1, 1), (0, 0)), mode='edge')
            hxy = np.pad((psi[2:, 2:] - psi[2:, :-2] - psi[:-2, 2:] + psi[:-2, :-2]) / 4, 1, mode='edge')
            hxx, hyy, hxy = (cv2.resize(x, (W, H), interpolation=cv2.INTER_LINEAR) for x in (hxx, hyy, hxy))

            a, b = a + v['heat'] * (hxx - hyy) / 2, b + v['heat'] * hxy
        if v['scale2'] > 0:
            a2, b2 = hessian_ab(h, v['scale2'] * H)
            a, b = a + a2 * 8 * v['bend'], b + b2 * 8 * v['bend']
        # Flow at a quarter size, as lk4 would give it.
        small = cv2.resize(luma, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        if self.fa is None:
            self.fa = np.zeros((H // 4, W // 4), np.float32)
            self.fb = np.zeros_like(self.fa)
        if self.prev is not None and v['flow'] > 0:
            f = cv2.calcOpticalFlowFarneback((self.prev * 255).astype(np.uint8), (small * 255).astype(np.uint8),
                                             None, 0.5, 2, 9, 3, 5, 1.1, 0)
            f = cv2.GaussianBlur(f, (0, 0), 1.5) * FPS / (H // 4)        # frame heights a second
            ux = np.gradient(f[..., 0], axis=1) * (H // 4)
            uy = np.gradient(f[..., 0], axis=0) * (H // 4)
            vx = np.gradient(f[..., 1], axis=1) * (H // 4)
            vy = np.gradient(f[..., 1], axis=0) * (H // 4)
            da, db = (ux - vy) / 2, (uy + vx) / 2                       # deviatoric strain rate, 1 / s
            dt = 1.0 / FPS
            k = np.exp(-dt / v['tau'])
            self.fa = self.fa * k + v['flow'] * da * dt
            self.fb = self.fb * k + v['flow'] * db * dt
        self.prev = small
        a = a + cv2.resize(self.fa, (W, H))
        b = b + cv2.resize(self.fb, (W, H))
        self.level += (level - self.level) * (1 - np.exp(-1 / FPS / 1.0))
        if beat:
            self.beat_env = 1.0
        load = (1 - v['bass'] / 2 + v['bass'] * self.level) * (1 + v['beat'] * self.beat_env)
        self.beat_env = max(0.0, self.beat_env - 1 / FPS / 0.3)
        N = 2 * np.sqrt(a * a + b * b) * load
        N = v['cap'] * np.tanh(N / v['cap'])
        th = (0.5 * np.arctan2(b, a) - np.radians(v['alpha'])) % np.pi
        ni = np.clip(N / (v['cap'] + 1) * (len(self.N) - 1), 0, len(self.N) - 1).astype(int)
        ti = (th / np.pi * len(self.th)).astype(int) % len(self.th)
        T = self.chart[ti, ni][..., ::-1]                                # BGR
        pl = lin(pic)
        mean = pl.mean()
        back = pl * (1 - v['white']) + v['white'] * mean
        if self.style == 'light':
            out = pl * T
        else:
            out = v['gain'] * back * T + v['leak'] * pl
        return srgb(out).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('variants', nargs='*', help='name:key=value,...')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'photoelastic', 'offline'))
    ap.add_argument('--at', default='2,4,6,8')
    ap.add_argument('--novideo', action='store_true')
    ap.add_argument('--noflash', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    rows = chladni.song_channels(a.song, a.seconds)
    counts = [r['beat_count'] for r in rows]
    beats = {i for i in range(1, len(counts)) if counts[i] > counts[i - 1]}
    levels = [r['level'] for r in rows]
    pics = chladni.frames(a.clip, n)
    dpath = os.path.join(READY, a.clip + '_depth.mp4')
    depths = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) * 255 for f in chladni.frames(a.clip + '_depth', n)] \
        if os.path.exists(dpath) else [None] * n
    variants = []
    for spec in a.variants or ['defaults:']:
        name, _, kv = spec.partition(':')
        v = dict(DEFAULTS)
        v.update({k: float(x) for k, x in (p.split('=') for p in kv.split(',') if p)})
        variants.append((name, Photo(v)))
    outs = {name: [] for name, _ in variants}
    t0 = time.time()
    for f in range(n):
        for name, ph in variants:
            outs[name].append(ph.frame(pics[f], depths[f], f in beats, levels[min(f, len(levels) - 1)]))
        if f % FPS == 0:
            print('frame', f, round(time.time() - t0, 1), 's', flush=True)
    t = np.arange(n) / FPS
    if not a.noflash:
        report = []
        for name, frames in [('clip', pics)] + list(outs.items()):
            g = [caustics.grid(im) for im in frames[FPS:]]
            m = flashcount.measure(t[FPS:], np.array([x[0] for x in g]), np.array([x[1] for x in g]))
            report.append('{:<12} whole {:.1f} area {:.1f} red {:.1f} cell {:.1f}'.format(
                name, m['whole'], m['area'], m['red'], m['cell']))
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
