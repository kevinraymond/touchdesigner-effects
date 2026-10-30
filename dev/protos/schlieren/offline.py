"""DEV ONLY. Schlieren's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4847): the
warm air rising off the picture's subject made visible, as a schlieren camera shows it.

    uv run --with numpy --with opencv-python-headless dev/protos/schlieren/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/schlieren/offline

The air is a small stable-fluids solver (Stam 1999) on a grid of 320 x 180, a quarter of 1280 x 720 as TouchDesigner will
run it, and what it carries is heat on a grid twice as fine. Warmth comes off the picture as lib warmth() makes it (what
stands out in front in the depth, what moves, and optionally what is bright), and the air rises in a column above
whatever is warm: the lift is worked out from the picture's warmth at the source, never from the heat the air carries
(Huawei's pending US 2025/0117558 claims a velocity obtained from the very density it advects). The picture's motion
stirs the air, a beat (gated to 1 a second, as Calm) puffs it up, the bands warm heights from the feet to the head, and
bars turn the knife edge.

The heat lowers the air's refractive index, n = n0 - k h, so light through it bends by -k grad h (Settles 2001). The
looks follow Settles and Brownlee et al. (TVCG 2011): Knife Edge (the deflection across the edge, clipped as a real
cutoff saturates), Rainbow (a color filter in place of the edge), Shadowgraph (the Laplacian) and Interferogram (fringes
of the optical path). The picture is seen through the same air, displaced by the deflection.

Variants are named on the command line as name:key=value,...; see DEFAULTS. Writes a sheet (a row a moment, the clip then
each variant), the last moment full size, an MP4 with the song, and flash counts per variant against the clip.
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
AIR = (320, 180)
FPS = 30
DT = 1.0 / FPS
BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')
LOOKS = ('knife', 'rainbow', 'shadow', 'fringe', 'rheinberg')


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
    look=0,          # index into LOOKS
    lift=0.8,        # frame heights a second^2 of lift where fully warm
    reach=0.35,      # how far above what is warm the lift reaches, frame heights (it falls off over it)
    wobble=0.6,      # how much slow noise wavers the lift, 0-1
    swirl=0.03,      # vorticity confinement, frame heights (Fluid's 0.4 blew up; it runs 0.02-0.06)
    stir=1.0,        # how much the picture's motion drags the air
    half=1.0,        # the air's velocity half-life (s)
    passes=30,       # Jacobi iterations of the pressure
    heat=6.0,        # how fast a warm source heats the air above it (per second)
    cool=1.5,        # the heat's half-life once carried away (s)
    near=1.0,        # how much what stands out in the depth warms
    move=1.0,        # how much what moves warms
    dead=0.03,       # a change in luma a frame (at 1/8) below which nothing warms
    full=0.1,        # the change that warms fully
    light=0.0,       # how much what is bright warms (lamps)
    eddies=0.0,      # how much the warm air comes off in eddies (noise on the heating), 0-1
    sharp=0.0,       # 1: the source's edge sharpened (heats fully past half warm)
    soft=1.0,        # 1: the relief saturates softly (tanh) rather than clipping
    opaque=1.0,      # how much the subject hides the air behind it (no relief, no shift on it), 0-1
    puff=1.0,        # a beat's puff, 0-1
    bands=0.5,       # how much the bands warm heights, feet to head
    loud=0.5,        # how much loudness sets the heat
    gain=1.5,        # the knife edge's sensitivity
    angle=0.0,       # the knife edge's angle (degrees; 0 is upright, so the plume's sides show)
    turn=45.0,       # degrees a bar turns the knife edge (0 never)
    comp=2,          # how the relief meets the picture: 0 multiply, 1 gray field, 2 add
    backdrop=1.0,    # how much of the picture shows behind the relief
    refract=3.0,     # pixels the picture shifts at a deflection of 1
    fringes=8.0,     # Interferogram: fringes across the full heat
    tilt=0.0,        # Interferogram: reference fringes across the frame a frame height (0: infinite fringe)
    fstyle=1.0,      # Interferogram: 1 bright fringes added, 2 dark fringes
)


def advect(field, u, v, dt):
    """Semi-Lagrangian: each cell takes what was where its velocity came from. u, v in cells a second, v up."""
    h, w = field.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(field, x - dt * u, y + dt * v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def ddx(a):
    return 0.5 * (np.roll(a, -1, 1) - np.roll(a, 1, 1))


def ddy_up(a):
    """d/dy with y up (rows run down)."""
    return 0.5 * (np.roll(a, 1, 0) - np.roll(a, -1, 0))


_NOISE = {}


def noise(t, shape, seed=0, scale=0.12, rise=0.25):
    """Slow value noise drifting up, -1..1: cells of `scale` frame heights, rising at `rise` frame heights a second."""
    h, w = shape
    if (seed, h, w) not in _NOISE:
        rng = np.random.default_rng(seed)
        cy, cx = 80, int(w / h / scale) + 2
        cell = max(int(scale * h), 1)
        _NOISE[seed, h, w] = cv2.resize(rng.uniform(-1, 1, (cy, cx)).astype(np.float32), (cx * cell, cy * cell),
                                        interpolation=cv2.INTER_CUBIC)
    big = _NOISE[seed, h, w]
    start = int(t * rise * h) % (big.shape[0] - h)
    return big[start:start + h, :w]


class Air:
    def __init__(self, v):
        self.v = v
        W, H = AIR
        self.u = np.zeros((H, W), np.float32)
        self.w = np.zeros((H, W), np.float32)   # vertical velocity, up
        self.p = np.zeros((H, W), np.float32)
        self.heat = np.zeros((SIZE[1], SIZE[0]), np.float32)
        self.warm = np.zeros((H, W), np.float32)
        self.prev = None
        self.t = 0.0
        self.last_puff = -9.0
        self.angle = v['angle']
        self.angle_to = v['angle']

    def warmth(self, pic, depth):
        v = self.v
        W, H = AIR
        lum = cv2.resize(cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY), (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        moved = np.zeros_like(lum) if self.prev is None else np.clip((np.abs(lum - self.prev) - v['dead']) / (v['full'] - v['dead']), 0, 1)
        self.prev = lum
        moved = cv2.resize(cv2.GaussianBlur(moved, (3, 3), 0), (W, H))
        target = v['move'] * moved
        self.subject = np.zeros((H, W), np.float32)
        if depth is not None:
            near = cv2.resize(depth.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)   # 0-1 already
            d = W // 6
            side = np.maximum(np.roll(near, d, 1), np.roll(near, -d, 1))
            stand = np.clip((near - side - 0.03) / 0.07, 0, 1) * (near > 0.2)
            self.subject = stand
            target = np.maximum(target, v['near'] * cv2.GaussianBlur(stand, (5, 5), 0))
        if v['light']:
            bright = cv2.resize(cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY), (W, H), interpolation=cv2.INTER_AREA)
            target = np.maximum(target, v['light'] * np.clip((bright - 0.55) / 0.35, 0, 1))
        rate = np.where(target > self.warm, 0.15, 1.5)
        self.warm = target + (self.warm - target) * np.exp(-DT / rate)
        return self.warm

    def column(self, warm):
        """The lift: above what is warm, falling off over reach frame heights (from the bottom row up)."""
        H = warm.shape[0]
        decay = math.exp(-1.0 / (self.v['reach'] * H))
        out = np.empty_like(warm)
        out[-1] = warm[-1]
        for r in range(H - 2, -1, -1):
            out[r] = np.maximum(warm[r], out[r + 1] * decay)
        return cv2.GaussianBlur(out, (0, 0), 2)

    def step(self, pic, depth, flow, beat_ok, row):
        v = self.v
        W, H = AIR
        self.t += DT
        warm = self.warmth(pic, depth)
        lift = self.column(warm) * (1 + v['wobble'] * noise(self.t, (H, W), seed=3))
        # A beat (as often as the gate lets it) puffs the warm air up at once.
        if beat_ok:
            self.last_puff = self.t
        env = math.exp(-(self.t - self.last_puff) / 0.15) * v['puff']
        u = advect(self.u, self.u, self.w, DT)
        w = advect(self.w, self.u, self.w, DT)
        # Vorticity confinement (Fedkiw, Stam and Jensen 2001).
        curl = ddx(w) - ddy_up(u)
        ac = np.abs(curl)
        gx, gy = ddx(ac), ddy_up(ac)
        n = np.sqrt(gx * gx + gy * gy) + 1e-5
        u += DT * v['swirl'] * H * curl * (gy / n)
        w += DT * v['swirl'] * H * curl * (-gx / n)
        w += DT * H * (v['lift'] * lift + 6.0 * env * cv2.GaussianBlur(warm, (0, 0), 3))
        # The picture's motion stirs the air where it moves.
        if flow is not None:
            fu, fw = flow
            sure = np.clip((np.hypot(fu, fw) / H - 0.02) / 0.06, 0, 1)
            k = 1 - np.exp(-DT * 10 * sure * v['stir'])
            u += (fu - u) * k
            w += (fw - w) * k
        damp = 2 ** (-DT / v['half'])
        u *= damp
        w *= damp
        s = np.hypot(u, w)
        cap = 1.0 * H
        f = np.where(s > cap, cap / np.maximum(s, 1e-6), 1)
        u *= f
        w *= f
        # Projection: Jacobi iterations of the pressure from last frame's, zero off the edges.
        div = ddx(u) + ddy_up(w)
        div[:, 0] = div[:, -1] = 0
        p = self.p
        for _ in range(int(v['passes'])):
            pp = np.pad(p, 1)
            p = 0.25 * (pp[1:-1, 2:] + pp[1:-1, :-2] + pp[2:, 1:-1] + pp[:-2, 1:-1] - div)
        self.p = p
        pp = np.pad(p, 1)
        u -= 0.5 * (pp[1:-1, 2:] - pp[1:-1, :-2])
        w -= 0.5 * (pp[:-2, 1:-1] - pp[2:, 1:-1])
        self.u, self.w = u, w
        # Heat at twice the air's size: carried, then heated where warm (bands by height, louder hotter), cooling.
        hu = cv2.resize(u, SIZE) * 2
        hw = cv2.resize(w, SIZE) * 2
        heat = advect(self.heat, hu, hw, DT)
        src = cv2.resize(warm, SIZE, interpolation=cv2.INTER_LINEAR)
        if v['sharp']:
            src = np.clip((src - 0.25) / 0.3, 0, 1) ** 2 * (3 - 2 * np.clip((src - 0.25) / 0.3, 0, 1))
        if v['eddies']:
            e = noise(self.t, (SIZE[1], SIZE[0]), seed=7, scale=0.05, rise=0.6)
            src = src * np.clip(1 - v['eddies'] + v['eddies'] * (e * 2 + 0.5), 0, 1)
        yf = 1 - (np.arange(SIZE[1], dtype=np.float32) + 0.5) / SIZE[1]
        bv = np.interp(yf, (np.arange(7) + 0.5) / 7, [row.get(b, 0) for b in BANDS])
        band = 1 + v['bands'] * (2 * bv[:, None] - 1)
        loud = 1 - v['loud'] / 2 + v['loud'] * row.get('level', 0) if row.get('source', 0) else 1
        rate = v['heat'] * loud * band * (1 + 3 * env)
        heat += (1 - np.exp(-DT * rate * src)) * (src - heat).clip(0)
        heat *= 2 ** (-DT / v['cool'])
        self.heat = heat
        return heat

    def render(self, pic):
        v = self.v
        Hh = SIZE[1]
        h = self.heat
        # Deflection: hot air bends light away from itself (n falls with heat), per frame height.
        ex = -ddx(h) * Hh / 50
        ey = -ddy_up(h) * Hh / 50
        # The subject is opaque: the camera sees the air around it, not through it.
        sub = cv2.resize(cv2.GaussianBlur(self.subject, (0, 0), 1), SIZE)
        clear = 1 - v['opaque'] * np.clip((sub - 0.3) / 0.4, 0, 1)
        ex *= clear
        ey *= clear
        y, x = np.mgrid[0:SIZE[1], 0:SIZE[0]].astype(np.float32)
        seen = cv2.remap(pic, x + v['refract'] * ex, y - v['refract'] * ey, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REPLICATE)
        self.angle += (self.angle_to - self.angle) * (1 - math.exp(-DT / 0.5))
        a = math.radians(self.angle)
        look = LOOKS[int(v['look'])]
        gray = cv2.cvtColor(seen, cv2.COLOR_BGR2GRAY)[..., None]
        comp = int(v['comp'])
        if comp == 1:
            base = np.repeat(0.5 + v['backdrop'] * (gray - 0.5), 3, -1)
        else:
            base = seen * v['backdrop'] + (1 - v['backdrop']) * 0.5
        if look == 'knife':
            s = v['gain'] * (ex * math.cos(a) + ey * math.sin(a))
            rel = (0.5 + 0.5 * np.tanh(2 * s) if v['soft'] else np.clip(0.5 + s, 0, 1))[..., None]
            out = base * 2 * rel if comp != 2 else seen + (rel - 0.5) * 1.2
        elif look == 'shadow':
            lap = (np.roll(h, 1, 0) + np.roll(h, -1, 0) + np.roll(h, 1, 1) + np.roll(h, -1, 1) - 4 * h) * Hh * Hh / 2500
            rel = np.clip(1 + 0.6 * v['gain'] * lap, 0, 2)[..., None]
            out = base * rel if comp != 2 else seen + (rel - 1) * 0.6
        elif look == 'fringe':
            phase = v['fringes'] * h + v['tilt'] * x / SIZE[1]
            d = np.abs(phase - np.round(phase))
            line = (1 - np.clip(d / 0.12, 0, 1)) ** 2
            vis = np.clip(h * 8, 0, 1) if v['tilt'] == 0 else 1
            line = (line * vis)[..., None]
            out = seen + 0.45 * line * (1.2 - seen) if v['fstyle'] == 1 else seen * (1 - 0.7 * line)
        elif look == 'rainbow':
            # A linear rainbow filter (Howes 1984) in place of the edge: the deflection across it picks a wavelength.
            s = v['gain'] * (ex * math.cos(a) + ey * math.sin(a))
            lam = 550 + 110 * np.clip(s * 2, -1, 1)
            col = spectral(lam)
            sat = np.clip(np.abs(s) * 3, 0, 1)[..., None]
            lit = np.clip(1 + 1.2 * np.abs(s), 1, 2)[..., None]
            out = base * ((1 - sat) + sat * col * lit)
        else:   # rheinberg: the deflection's direction picks a hue on a wheel of spectral colors, its size how much
            ang = (np.arctan2(ey, ex) / (2 * math.pi)) % 1
            mag = np.clip(v['gain'] * np.hypot(ex, ey) * 2, 0, 1)[..., None]
            spec = spectral(640 - 200 * np.clip(ang / 0.8, 0, 1))
            purple = 0.5 * (spectral(np.full_like(ang, 440.0)) + spectral(np.full_like(ang, 640.0)))
            k = np.clip((ang - 0.8) / 0.2, 0, 1)[..., None]
            col = spec * (1 - k) + purple * k
            out = seen * (1 - 0.6 * mag) + mag * col * (0.35 + 0.65 * gray)
        return np.clip(out, 0, 1)


def spectral(lam):
    """sRGB (BGR order, gamma-encoded, normalized to its brightest channel) of a wavelength, Wyman et al.'s CIE fit."""
    def lobe(mu, s1, s2):
        t = (lam - mu) / np.where(lam < mu, s1, s2)
        return np.exp(-0.5 * t * t)
    X = 1.056 * lobe(599.8, 37.9, 31.0) + 0.362 * lobe(442.0, 16.0, 26.7) - 0.065 * lobe(501.1, 20.4, 26.2)
    Y = 0.821 * lobe(568.8, 46.9, 40.5) + 0.286 * lobe(530.9, 16.3, 31.1)
    Z = 1.217 * lobe(437.0, 11.8, 36.0) + 0.681 * lobe(459.0, 26.0, 13.8)
    r = 3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z
    g = -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z
    b = 0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z
    rgb = np.clip(np.stack([b, g, r], -1), 0, None)
    rgb = rgb / np.maximum(rgb.max(-1, keepdims=True), 1e-6)
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('variants', nargs='*', help='name:key=value,...')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'schlieren', 'offline'))
    ap.add_argument('--at', default='2,4,6,8')
    ap.add_argument('--looks', default='', help="name:key=value,...;name:...: render settings tried on the first "
                    "variant's air at the last --at moment (a sheet of looks)")
    ap.add_argument('--nodepth', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    rows = chladni.song_channels(a.song, a.seconds) if a.song else [{}] * n
    counts = [r.get('beat_count', 0) for r in rows]
    beats = {i for i in range(1, len(counts)) if counts[i] > counts[i - 1]}
    bars_c = [r.get('bar_count', 0) for r in rows]
    bars = {i for i in range(1, len(bars_c)) if bars_c[i] > bars_c[i - 1]}
    pics = chladni.frames(a.clip, n)
    dpath = os.path.join(READY, a.clip + '_depth.mp4')
    depths = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in chladni.frames(a.clip + '_depth', n)] \
        if os.path.exists(dpath) and not a.nodepth else [None] * n
    variants = []
    for spec in a.variants or ['defaults:']:
        name, _, kv = spec.partition(':')
        v = dict(DEFAULTS)
        v.update({k: float(x) for k, x in (p.split('=') for p in kv.split(',') if p)})
        variants.append((name, Air(v)))
    outs = {name: [] for name, _ in variants}
    t0 = time.time()
    small_prev = None
    last_gate = -9.0
    for f in range(n):
        small = cv2.resize(cv2.cvtColor(pics[f], cv2.COLOR_BGR2GRAY), (AIR[0] // 2, AIR[1] // 2), interpolation=cv2.INTER_AREA)
        flow = None
        if small_prev is not None:
            fl = cv2.calcOpticalFlowFarneback((small_prev * 255).astype(np.uint8), (small * 255).astype(np.uint8),
                                              None, 0.5, 2, 9, 2, 5, 1.1, 0)
            fl = cv2.resize(fl, AIR) * 2 * FPS
            flow = (fl[..., 0], -fl[..., 1])
        small_prev = small
        beat_ok = f in beats and (f / FPS - last_gate) >= 1.0
        if beat_ok:
            last_gate = f / FPS
        row = rows[min(f, len(rows) - 1)]
        for name, air in variants:
            if f in bars and air.v['turn']:
                air.angle_to += air.v['turn']
            air.step(pics[f], depths[f], flow, beat_ok, row)
            outs[name].append(air.render(pics[f]).astype(np.float32))
        if f % FPS == 0:
            print('frame', f, round(time.time() - t0, 1), 's', flush=True)
        if a.looks and f == int(float(a.at.split(',')[-1]) * FPS):
            air = variants[0][1]
            tiles = []
            for spec in a.looks.split(';'):
                name, _, kv = spec.partition(':')
                keep = dict(air.v)
                air.v.update({k: float(x) for k, x in (q.split('=') for q in kv.split(',') if q)})
                im = (air.render(pics[f]) * 255).astype(np.uint8)
                air.v = keep
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
    if a.song:
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-i', os.path.join(READY, a.song + '.wav'),
                        '-shortest', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', out],
                       check=True)
        os.remove(raw)
    print('wrote', out)


if __name__ == '__main__':
    main()
