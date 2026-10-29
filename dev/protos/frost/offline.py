"""DEV ONLY. Frost's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4846): ice grown
over the live picture from its edges and the frame's rims, thawing where the subject is near or moves.

    uv run --with numpy --with opencv-python-headless dev/protos/frost/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/frost/offline

The ice is Kobayashi's phase field ("Modeling and numerical simulations of dendritic crystal growth", Physica D 63,
1993): a phase p (0 water vapor's side, 1 ice) and a temperature T on a grid the picture's size here (half of 720p),
the interface's energy eps(theta) = eps_bar (1 + delta cos(j (theta - theta0))) six-fold, the latent heat K raising T
where ice forms. Steered as Kim and Lin steered it for artists (SCA 2003): theta0 follows the picture's edges (the
structure tensor's direction), nuclei form on the picture's edges and the frame's rims, and the pane pulls T toward a
temperature the picture sets (cold where far or dark, warm where near or moving), which thaws the ice there.

Variants are named on the command line as name:key=value,...; see DEFAULTS. Writes a sheet (a row a moment, the clip
then each variant), the middle moment full size, an MP4 with the song, and flash counts per variant against the clip
(dev/flashcount.py's measure on 64 x 36 cells of linear luminance).
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
fogmod = load('fog', os.path.join(ROOT, 'dev', 'protos', 'frost', 'fog.py'))

DEFAULTS = dict(
    # Kobayashi's constants (his Figure 4 set), the grid step and model step
    dx=0.05, dt=2.8e-4, tau=3e-4, eps=0.01, delta=0.05, j=6.0, alpha=0.9, gamma=10.0, K=1.8,
    rate=600.0,      # model steps a second
    sink=0.5,        # how fast the pane pulls T toward its own temperature (per model time unit)
    under=1.0,       # undercooling where coldest (Teq - T_pane)
    warm=0.6,        # how far above Teq the pane is where warmest
    melt=60.0,       # direct melting where warm (per model time unit, times warmth)
    seeds=1.0,       # nuclei a second on the picture's edges, where cold
    rims=20.0,       # nuclei a second along the frame's rims
    kick=8.0,        # nuclei on a beat, along the edges
    cold_from=1.0,   # 1: cold from depth when there is a depth map (far is cold), 0: from darkness
    move=1.0,        # how much movement warms
    near=1.0,        # how much nearness (depth) warms
    follow=1.0,      # 1: crystal axes follow the picture's edges, 0: all one way
    rise=0.15, fall=1.5,   # warmth's rise and fall times (s)
    noise=0.01,      # Kobayashi's noise at the interface, a p (1 - p) (chi - 1/2): it sets off side branches
    push=0.45,       # how far warmth tips the interface toward melting (added to -m)
    body=0.7, blur=4.0, refr=2.0, thick=1.5, scatter=0.8, ambient=0.3, edge=0.3, spine=0.8, spine_w=2.0,
    spine_k=40.0, sparkle=0.4, inner=1.0,
    style=0.0,       # 0 Fern (Kobayashi), 1 Stars (Reiter), 2 Fog (breath figures)
    rbeta=0.4, rgamma=0.0001, supply=0.002, rmelt=0.02,   # Stars: Reiter's vapor, addition, the pane's supply, melting
    fgrow=3.0, fnuc=3.0, fmax=8.0,                     # Fog: radius px/s, nucleation a second a free cell, largest radius px
)


def nb(a):
    """a padded by one cell (the frame's edge held), and its 8 neighbors."""
    q = np.pad(a, 1, mode='edge')
    c = q[1:-1, 1:-1]
    return (q[1:-1, 2:], q[1:-1, :-2], q[2:, 1:-1], q[:-2, 1:-1],
            q[2:, 2:], q[2:, :-2], q[:-2, 2:], q[:-2, :-2], c)


def lap(a):
    e, w, s, n, se, sw, ne, nw, c = nb(a)
    return (e + w + s + n) * 0.5 + (se + sw + ne + nw) * 0.25 - 3.0 * c


def grad(a):
    e, w, s, n, *_ = nb(a)
    return (e - w) * 0.5, (s - n) * 0.5


def tensor_angle(luma, sigma=6.0):
    """The direction the picture's edges run (the structure tensor's minor eigenvector), and how clear it is."""
    g = cv2.GaussianBlur(luma, (0, 0), 1.0)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3) / 8
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3) / 8
    jxx = cv2.GaussianBlur(gx * gx, (0, 0), sigma)
    jxy = cv2.GaussianBlur(gx * gy, (0, 0), sigma)
    jyy = cv2.GaussianBlur(gy * gy, (0, 0), sigma)
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2
    clear = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-6)
    return ang.astype(np.float32), clear.astype(np.float32), np.sqrt(gx * gx + gy * gy)


class Frost:
    def __init__(self, v, seed=3):
        self.v = v
        self.W, self.H = SIZE
        self.p = np.zeros((self.H, self.W), np.float32)
        self.T = np.zeros_like(self.p)
        self.age = np.zeros_like(self.p)
        self.warmth = np.zeros_like(self.p)
        self.prev = None
        self.rng = np.random.default_rng(seed)
        self.acc = 0.0
        self.T[:] = 1.0 - v['under']

    def nucleate(self, n, weight, r=1.5):
        """n tries a frame at random cells, each kept with the chance weight there; a kept one becomes a small disc."""
        if n <= 0:
            return
        k = self.rng.poisson(n)
        if k == 0:
            return
        xs = self.rng.integers(0, self.W, k)
        ys = self.rng.integers(0, self.H, k)
        keep = self.rng.random(k) < weight[ys, xs]
        if self.v['style'] == 1:
            self.seed_hex(ys[keep].astype(np.float32), xs[keep])
            return
        R = int(np.ceil(r))
        for x, y in zip(xs[keep], ys[keep]):
            y0, y1, x0, x1 = max(0, y - R), min(self.H, y + R + 1), max(0, x - R), min(self.W, x + R + 1)
            yy, xx = np.mgrid[y0:y1, x0:x1]
            d = (xx - x) ** 2 + (yy - y) ** 2 <= r * r
            self.p[y0:y1, x0:x1][d] = 1.0

    def step_model(self, theta0, t_pane, warm):
        v = self.v
        dx, dt, tau, eps, delta, j = v['dx'], v['dt'], v['tau'], v['eps'], v['delta'], v['j']
        p, T = self.p, self.T
        gx, gy = grad(p)
        gx /= dx
        gy /= dx
        th = np.arctan2(gy, gx) - theta0
        e = eps * (1 + delta * np.cos(j * th))
        de = -eps * delta * j * np.sin(j * th)
        a1 = e * de * gx
        a2 = -e * de * gy
        _, _, s1, n1, *_ = nb(a1)
        e2_, w2_, *_ = nb(a2)
        term = (s1 - n1) * 0.5 / dx + (e2_ - w2_) * 0.5 / dx
        e2 = e * e
        g2x, g2y = grad(e2)
        m = v['alpha'] / np.pi * np.arctan(v['gamma'] * (1.0 - T)) - v['push'] * warm
        chi = self.rng.random(p.shape, dtype=np.float32) - 0.5
        dp = (e2 * lap(p) / dx ** 2 + (g2x * gx + g2y * gy) / dx + term
              + p * (1 - p) * (p - 0.5 + m + v['noise'] * chi * 2)) * dt / tau
        dp -= v['melt'] * dt * warm * p
        p += dp
        np.clip(p, 0, 1, out=p)
        T += lap(T) / dx ** 2 * dt + v['K'] * dp + v['sink'] * dt * (t_pane - T)

    def frame(self, pic, depth, beat, level):
        v = self.v
        luma = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
        ang, clear, edge = tensor_angle(luma)
        theta0 = ang * v['follow']
        near = cv2.GaussianBlur(depth, (0, 0), 3) if depth is not None else None
        cold = 1 - (near if (near is not None and v['cold_from'] > 0) else cv2.GaussianBlur(luma, (0, 0), 8))
        # warmth: nearness and movement, rising fast and falling slowly
        target = np.zeros_like(luma)
        if near is not None:
            target = np.maximum(target, v['near'] * np.clip((near - 0.45) / 0.2, 0, 1))
        if self.prev is not None:
            mv = cv2.GaussianBlur(np.abs(luma - self.prev), (0, 0), 4)
            target = np.maximum(target, v['move'] * np.clip(mv / 0.04, 0, 1))
        self.prev = luma
        up = target > self.warmth
        k = np.where(up, 1 - np.exp(-1 / (FPS * v['rise'])), 1 - np.exp(-1 / (FPS * v['fall'])))
        self.warmth += (target - self.warmth) * k
        warm = self.warmth
        t_pane = 1.0 - v['under'] * cold * (1 - warm) + v['warm'] * warm
        # nuclei: on the picture's edges where cold, along the rims, and a burst on each beat
        e = np.clip(edge / 0.03, 0, 1) * np.clip(cold, 0, 1) * (1 - warm)
        self.nucleate(v['seeds'] / FPS * 8, e / 8)
        rim = np.zeros_like(luma)
        rim[:2, :] = rim[-2:, :] = rim[:, :2] = rim[:, -2:] = 1
        rimw = rim * (1 - warm)
        self.nucleate(v['rims'] / FPS * self.W * self.H / (2 * (self.W + self.H) * 2), rimw)
        if beat:
            self.nucleate(v['kick'] * 8, e / 8)
        if v['style'] == 2:
            self.fog_frame(cold, warm, level, beat, e)
            return fogmod.render(self.drops, pic)
        self.acc += v['rate'] * (0.6 + 0.8 * level) / FPS
        while self.acc >= 1:
            self.acc -= 1
            if v['style'] == 1:
                self.step_reiter(cold, warm)
            else:
                self.step_model(theta0, t_pane, warm)
        if v['style'] == 1:
            self.p = self.hex_to_grid()
        self.age = np.where(self.p > 0.5, self.age + 1 / FPS, self.age * 0.8)
        return self.render(pic)

    # ---- Stars: Reiter's hexagonal cellular model, its rows sqrt(3)/2 apart over the grid ----
    def hex_setup(self):
        self.HR = int(np.ceil(self.H / 0.8660254))
        self.s = np.full((self.HR, self.W), self.v['rbeta'], np.float32)
        r = np.arange(self.HR)
        self.hy = (r * 0.8660254).astype(np.float32)          # each hex row's y on the grid
        self.odd = (r % 2 == 1)[:, None]

    def nbrs6(self, a):
        up, dn = np.roll(a, 1, 0), np.roll(a, -1, 0)
        left, right = np.roll(a, 1, 1), np.roll(a, -1, 1)
        up_l, up_r = np.roll(up, 1, 1), np.roll(up, -1, 1)
        dn_l, dn_r = np.roll(dn, 1, 1), np.roll(dn, -1, 1)
        o = self.odd
        return left, right, np.where(o, up, up_l), np.where(o, up_r, up), np.where(o, dn, dn_l), np.where(o, dn_r, dn)

    def to_hex(self, m):
        return cv2.resize(m, (self.W, self.HR), interpolation=cv2.INTER_LINEAR)

    def step_reiter(self, cold, warm):
        v = self.v
        if not hasattr(self, 's'):
            self.hex_setup()
        s = self.s
        c, w = self.to_hex(cold), self.to_hex(warm)
        ice = s >= 1
        rec = ice.copy()
        for n in self.nbrs6(ice):
            rec |= n
        u = np.where(rec, 0, s)
        vv = np.where(rec, s + v['rgamma'] * (1 - w), 0)
        avg = sum(self.nbrs6(u)) / 6.0
        u = u + 0.5 * (avg - u)
        # the pane keeps condensing vapor where it is cold, and none where it is warm; warm ice melts
        u = u + v['supply'] * (v['rbeta'] * c * (1 - w) - u) * (~rec)
        vv = np.where(rec, np.maximum(vv - v['rmelt'] * w * 4, 0), 0)
        self.s = (u + vv).astype(np.float32)

    def hex_to_grid(self):
        # each grid pixel reads the hex cell it falls in (rows shifted half a cell on odd rows)
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        r = np.clip(np.round(yy / 0.8660254).astype(int), 0, self.HR - 1)
        x = np.clip(np.round(xx - 0.5 * (r % 2)).astype(int), 0, self.W - 1)
        s = self.s[r, x]
        self.thick_hex = np.clip(s - 1, 0, 1)
        return (s >= 1).astype(np.float32)

    def seed_hex(self, ys, xs):
        if not hasattr(self, 's'):
            self.hex_setup()
        r = np.clip(np.round(ys / 0.8660254).astype(int), 0, self.HR - 1)
        self.s[r, np.clip(xs, 0, self.W - 1)] = 1.0

    # ---- Fog: breath figures ----
    def fog_frame(self, cold, warm, level, beat, edge):
        v = self.v
        if not hasattr(self, 'drops'):
            self.drops = fogmod.Droplets(self.W, self.H)
        g = v['fgrow'] * (0.6 + 0.8 * level)
        c0 = cv2.resize(cold, self.drops.lv[0]['r'].shape[::-1], interpolation=cv2.INTER_AREA)
        w0 = cv2.resize(warm, self.drops.lv[0]['r'].shape[::-1], interpolation=cv2.INTER_AREA)
        self.drops.step(1 / FPS, g, c0, w0, v['fnuc'] * (4.0 if beat else 1.0), v['fmax'])

    def render(self, pic):
        """Frost as it looks on glass: a translucent body that scatters the light behind it, crisp bright edges, a
        bright spine down the middle of each arm, and a faint sparkle of small crystals."""
        v = self.v
        p = cv2.GaussianBlur(self.p, (0, 0), 0.6)
        body = np.clip((p - 0.35) / 0.3, 0, 1)
        body = body * body * (3 - 2 * body)
        thick = 1 - np.exp(-self.age / v['thick'])
        if v['style'] == 1:
            thick = np.clip(thick * 0.3 + cv2.GaussianBlur(self.thick_hex, (0, 0), 0.6) * 1.5, 0, 1)
        gx = cv2.Sobel(p, cv2.CV_32F, 1, 0, ksize=3) / 8
        gy = cv2.Sobel(p, cv2.CV_32F, 0, 1, ksize=3) / 8
        edge = np.clip(np.sqrt(gx * gx + gy * gy) * 2.5, 0, 1) * (body if v['inner'] > 0 else 1)
        s2 = cv2.GaussianBlur(self.p, (0, 0), v['spine_w'])
        spine = np.clip(-cv2.Laplacian(s2, cv2.CV_32F) * v['spine_k'], 0, 1) * body
        H, W = p.shape
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        sg = cv2.GaussianBlur(self.p, (0, 0), 2.0)
        rx = cv2.Sobel(sg, cv2.CV_32F, 1, 0, ksize=3) / 8
        ry = cv2.Sobel(sg, cv2.CV_32F, 0, 1, ksize=3) / 8
        bent = cv2.remap(pic, x + rx * v['refr'] * 8, y + ry * v['refr'] * 8, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT)
        blur = cv2.GaussianBlur(bent, (0, 0), v['blur'])
        glow = cv2.GaussianBlur(pic, (0, 0), 14)
        lit = cv2.cvtColor(glow, cv2.COLOR_BGR2GRAY)[..., None]
        white = np.array([1.0, 0.97, 0.93], np.float32)   # BGR: a cold white
        light = (v['ambient'] + v['scatter'] * lit) * white
        if not hasattr(self, 'grain'):
            self.grain = self.rng.random((H, W), dtype=np.float32)
        spark = np.clip((self.grain - 0.97) / 0.03, 0, 1) * body * v['sparkle']
        a = (body * (v['body'] + 0.25 * thick))[..., None]
        out = pic * (1 - a) + (blur * 0.5 + light * 0.7) * a
        out = out + light * (edge * v['edge'] + spine * v['spine'] + spark)[..., None]
        return np.clip(out, 0, 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('variants', nargs='*', help='name:key=value,...')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'frost', 'offline'))
    ap.add_argument('--at', default='2,4,6,8')
    ap.add_argument('--looks', default='', help="name:key=value,...;name:...: render settings tried on the first "
                    "variant's ice at the last --at moment (a sheet of looks)")
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
        variants.append((name, Frost(v)))
    outs = {name: [] for name, _ in variants}
    t0 = time.time()
    for f in range(n):
        for name, fr in variants:
            outs[name].append(fr.frame(pics[f], depths[f], f in beats, levels[min(f, len(levels) - 1)]).astype(np.float32))
        if f % FPS == 0:
            print('frame', f, round(time.time() - t0, 1), 's', flush=True)
        if a.looks and f == int(float(a.at.split(',')[-1]) * FPS):
            fr = variants[0][1]
            tiles = []
            for spec in a.looks.split(';'):
                name, _, kv = spec.partition(':')
                keep = dict(fr.v)
                fr.v.update({k: float(x) for k, x in (q.split('=') for q in kv.split(',') if q)})
                im = (fr.render(pics[f]) * 255).astype(np.uint8)
                fr.v = keep
                cv2.putText(im, name, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                tiles.append(im)
            tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 2)
            cv2.imwrite(os.path.join(a.out, a.clip + '_looks.jpg'),
                        np.vstack([np.hstack(tiles[i:i + 2]) for i in range(0, len(tiles), 2)]))
    t = np.arange(n) / FPS
    report = []
    for name, frames in [('clip', pics)] + list(outs.items()):
        g = [caustics.grid(im) for im in frames[FPS:]]
        m = flashcount.measure(t[FPS:], np.array([x[0] for x in g]), np.array([x[1] for x in g]))
        report.append('{:<12} whole {:.1f} area {:.1f} red {:.1f} cell {:.1f}'.format(name, m['whole'], m['area'], m['red'], m['cell']))
    open(os.path.join(a.out, a.clip + '_flash.txt'), 'w').write('\n'.join(report) + '\n')
    print('\n'.join(report))
    w, hgt = SIZE
    names = list(outs)
    times = [int(float(s) * FPS) for s in a.at.split(',') if float(s) * FPS < n]
    sheet = [np.hstack([cv2.resize(np.clip(im, 0, 1), (w // 2, hgt // 2), interpolation=cv2.INTER_AREA)
                        for im in [pics[k]] + [outs[nm][k] for nm in names]]) for k in times]
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.jpg'), (np.vstack(sheet) * 255).astype(np.uint8))
    for nm in names:
        k = times[-1]
        cv2.imwrite(os.path.join(a.out, '{}_{}_full.jpg'.format(a.clip, nm)), (outs[nm][k] * 255).astype(np.uint8))
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
