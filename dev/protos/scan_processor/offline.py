"""DEV ONLY. Scan Processor's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4714):
the picture re-scanned as a raster of lines whose deflection the music drives, as the scan processors of 1969-73 bent
a television's raster (Paik and Abe's Wobbulator, Harrison's Scanimate).

    uv run --with numpy --with opencv-python-headless dev/protos/scan_processor/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/scan/offline

The song goes through lib/audio_callbacks.py as raw audio, a cook at a time, for the bands and the beats; the waveform
comes from the song's samples directly. The beam draws each line of the raster where the deflection puts it, a
Gaussian spot wide, carrying the picture's row it was scanned from; where lines bunch up or the beam slows along a line
the light piles up, as on a CRT, since the beam's energy per line is fixed.

Signals laid along the raster (u, 0 at the top, 1 at the bottom, the time the beam takes over one field):
  wave  the song's own waveform over one field (1/60 s), held still like an oscilloscope's trace (triggered on a
        rising zero crossing of its low end), over its running peak, eased per line
  osc   one oscillator per band, each a band's level (eased) times a sine of its own number of cycles down the frame,
        its phase drifting slowly, as Paik's signal generators drove the yokes

Variants (columns of the sheet, and a flash recording each):
  wob_wave, wob_osc  Wobbulator: each line pushed sideways by the signal, and up or down by it a quarter field later
  scanimate          each line's own twist (a ribbon about the middle), bend and shift, from the bands' envelopes
  fm                 the beam's speed along each line frequency-modulated (Chowning), pleats that glow where it slows
  colorize, shape    the Wobbulator (osc) through a colorizer of luma bands, or a Chebyshev waveshaper of the luma
"""

import argparse
import importlib.util
import math
import os
import subprocess
import wave

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE = (640, 360)
FPS = 30
BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')
CYCLES = (0.5, 1, 2, 3, 5, 8, 13)          # each band's oscillator: cycles down the frame, the lowest a bow
DRIFT = (0.0, 0.07, -0.09, 0.11, -0.13, 0.15, -0.17)   # its phase, cycles a second (a tone off the field rate scrolls)
GATE = 1.0

_spec = importlib.util.spec_from_file_location('chladni', os.path.join(ROOT, 'dev', 'protos', 'chladni', 'offline.py'))
chladni = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chladni)
chladni.SIZE, chladni.FPS = SIZE, FPS


def song_samples(name, seconds):
    with wave.open(os.path.join(READY, name + '.wav')) as w:
        rate, ch = w.getframerate(), w.getnchannels()
        n = min(w.getnframes(), int(seconds * rate))
        x = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, ch).astype(np.float32) / 32768
    return rate, x.mean(1)


def lowpass(x, rate, hz):
    a = 1 - math.exp(-2 * math.pi * hz / rate)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(0, len(x), 4096):   # one pole, run in blocks through cumulative filtering
        seg = x[i:i + 4096]
        out = np.empty_like(seg)
        for j, v in enumerate(seg):
            acc += a * (v - acc)
            out[j] = acc
        y[i:i + 4096] = out
    return y


class Wave:
    """The song's waveform over one field, triggered and eased per line, over its running peak."""

    def __init__(self, rate, mono, n, ease):
        self.rate, self.x, self.n, self.ease = rate, mono, n, ease
        self.lo = lowpass(mono, rate, 120.0)
        self.win = int(rate / 60)
        self.peak = 1e-3
        self.s = np.zeros(n, np.float32)

    def at(self, t, dt):
        end = int(t * self.rate)
        start = max(end - self.win, 0)
        # the latest rising zero crossing of the low end at most 25 ms before the window would start
        lo = self.lo[max(start - int(0.025 * self.rate), 0):start + 1]
        up = np.nonzero((lo[:-1] < 0) & (lo[1:] >= 0))[0]
        if len(up):
            start = max(start - int(0.025 * self.rate), 0) + int(up[-1])
        seg = self.x[start:start + self.win]
        if len(seg) < self.win:
            seg = np.pad(seg, (0, self.win - len(seg)))
        self.peak = max(float(np.abs(seg).max()), self.peak * 0.5 ** (dt / 2.0), 1e-3)
        now = np.interp(np.linspace(0, self.win - 1, self.n), np.arange(self.win), seg) / self.peak
        self.s += (now - self.s) * (1 - math.exp(-dt / self.ease))
        return self.s.copy()


def colorize(img, shift):
    """Sandin and Scanimate's colorizer: luma bands, each a color, the luminance kept (only hue follows the band),
    orange and blue apart; shift slides the bands through the tones."""
    y = img @ np.array([0.299, 0.587, 0.114], np.float32)
    pal = np.array([(0.10, 0.20, 0.85), (0.10, 0.65, 0.85), (0.55, 0.55, 0.60), (0.95, 0.55, 0.10),
                    (0.95, 0.80, 0.30), (0.95, 0.95, 0.90)], np.float32)   # RGB, dark to light
    k = (y * len(pal) * 0.999 + shift * len(pal)) % len(pal)
    i = k.astype(int)
    f = np.clip((k - i - 0.85) / 0.15, 0, 1)[..., None]                 # soft edge into the next band
    c = pal[i] * (1 - f) + pal[(i + 1) % len(pal)] * f
    cy = c @ np.array([0.299, 0.587, 0.114], np.float32)
    return np.clip(c * (y / np.maximum(cy, 1e-3))[..., None], 0, 1)[..., ::-1]   # BGR


def waveshape(img, h):
    """Chebyshev waveshaping of the luma (Le Brun 1979): T_n(2y - 1) = cos(n acos(2y - 1)), weighted by h (h[0] is
    T_1, the picture as it is); the color kept by scaling it with the luma."""
    y = img @ np.array([0.114, 0.587, 0.299], np.float32)
    th = np.arccos(np.clip(2 * y - 1, -1, 1))
    out = sum(w * np.cos((n + 1) * th) for n, w in enumerate(h)) / max(sum(abs(w) for w in h), 1e-6)
    y2 = (out + 1) / 2
    return np.clip(img * (y2 / np.maximum(y, 0.02))[..., None], 0, 1)


def draw(rows, xs, yd, gain, lines, size, width):
    """The beam: line i, carrying rows[i] sampled at xs[i] (source x for each output column), drawn centered on
    yd[i] (each output column) with gain[i], a Gaussian spot width x the spacing wide (sigma = width x spacing / 2)."""
    w, h = size
    sp = h / lines
    sig = max(width * sp / 2, 0.35)
    reach = int(math.ceil(3 * sig))
    cols = np.arange(w)
    out = np.zeros((h * w, 3), np.float32)
    valid = (xs >= 0) & (xs <= w - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, w - 2)
    fx = np.clip(xs - x0, 0, 1)[..., None]
    li = np.arange(lines)[:, None]
    color = rows[li, x0] * (1 - fx) + rows[li, x0 + 1] * fx                 # (lines, w, 3)
    color *= (gain * valid)[..., None]
    for k in range(-reach, reach + 1):
        yy = np.floor(yd).astype(int) + k
        wgt = np.exp(-0.5 * ((yy + 0.5 - yd) / sig) ** 2) * sp / (sig * math.sqrt(2 * math.pi))
        ok = (yy >= 0) & (yy < h)
        idx = (yy * w + cols[None, :])[ok]
        for c in range(3):
            out[:, c] += np.bincount(idx, (color[..., c] * wgt)[ok], minlength=h * w)
    out = out.reshape(h, w, 3)
    return out / (1 + np.maximum(out - 1, 0))        # soft knee past white: the CRT blooms rather than clips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--lines', type=int, default=120, help='raster lines over 360 px')
    ap.add_argument('--width', type=float, default=0.7, help='beam spot / line spacing')
    ap.add_argument('--amount', type=float, default=0.05, help='deflection: share of the width at full signal')
    ap.add_argument('--vert', type=float, default=0.03, help='vertical yoke: share of the height')
    ap.add_argument('--ease', type=float, default=0.25, help='s: the waveform eased per line')
    ap.add_argument('--kick', type=float, default=0.06, help="a gated beat's bow, share of the width")
    ap.add_argument('--only', default='', help='comma list of variants')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'scan', 'offline'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    rows = chladni.song_channels(a.song, a.seconds)
    n = len(rows)
    fr = chladni.frames(a.clip, n)
    n = min(n, len(fr))
    rate, mono = song_samples(a.song, a.seconds)
    w, h = SIZE
    L = a.lines
    dt = 1 / FPS
    N = 512
    wav = Wave(rate, mono, N, a.ease)
    bands = np.array([[r.get(b, 0.0) for b in BANDS] for r in rows[:n]], np.float32)
    usual = np.zeros(7, np.float32)
    slow = np.zeros(7, np.float32)
    phase = np.random.default_rng(1).random(7)
    strike, sign, last_count, last_strike = 0.0, 1.0, rows[0].get('beat_count', 0), -GATE
    yi = (np.arange(L) + 0.5) * h / L
    yoke_at = np.array([w / 2, h / 2], np.float64)
    xo = np.arange(w, dtype=np.float32)
    names = ['wob_wave', 'wob_osc', 'yoke', 'scanimate', 'fm', 'colorize', 'shape']
    if a.only:
        names = a.only.split(',')
    outs = {k: [] for k in names}
    sig_log = []
    for f in range(n):
        t = (f + 1) * dt
        b = bands[f]
        usual += (b - usual) * (1 - math.exp(-dt / 4.0))
        slow += (b - slow) * (1 - math.exp(-dt / 1.0))       # a level follows its band smoothed over a second
        phase += np.array(DRIFT) * dt
        count = rows[f].get('beat_count', 0)
        if count > last_count and t - last_strike >= GATE:
            strike, last_strike, sign = 1.0, t, -sign
        last_count = count
        strike *= math.exp(-dt / 0.35)
        pic = fr[f]
        # the motion's centroid (frame difference at 1/8), eased over half a second: where the extra yoke sits
        if f:
            dm = cv2.resize(np.abs(pic - fr[f - 1]).sum(-1), (w // 8, h // 8), interpolation=cv2.INTER_AREA)
            dm = np.maximum(dm - 0.03, 0)
            if dm.sum() > 1e-3:
                gy8, gx8 = np.mgrid[0:h // 8, 0:w // 8]
                cen = np.array([(dm * gx8).sum() / dm.sum() * 8, (dm * gy8).sum() / dm.sum() * 8])
                yoke_at[:] += (cen - yoke_at) * (1 - math.exp(-dt / 0.5))
        rp = cv2.resize(pic, (w, L), interpolation=cv2.INTER_AREA)       # each line's row, averaged over its band
        u_line = (np.arange(L)[:, None] + xo[None, :] / w) / L             # raster time along each line
        bow = np.sin(np.pi * u_line)

        def osc(u):
            return sum(slow[k] * np.sin(2 * np.pi * (CYCLES[k] * u + phase[k])) for k in range(7)) / 2.0

        def signal(kind, u):
            if kind == 'wave':
                return np.interp(u % 1, np.linspace(0, 1, N), wv)
            return osc(u)

        wv = wav.at(t, dt) if 'wob_wave' in names else None
        sig_log.append(float(np.abs(osc(np.linspace(0, 1, 64))).max()))
        for name in names:
            if name in ('wob_wave', 'wob_osc', 'colorize', 'shape'):
                kind = 'wave' if name == 'wob_wave' else 'osc'
                sh = a.amount * w * signal(kind, u_line) + a.kick * w * sign * strike * bow
                xs = xo[None, :] - sh
                xs = np.abs(xs) % (2 * (w - 1))
                xs = np.where(xs > w - 1, 2 * (w - 1) - xs, xs)                # mirrored past the raster's edges
                yd = yi[:, None] + a.vert * h * signal(kind, u_line + 0.25)
                img = draw(rp, xs, yd, np.ones_like(xs), L, SIZE, a.width)
                if name == 'colorize':
                    img = colorize(img[..., ::-1], 0.15 * float(slow[:3].mean()) + 0.05 * t)
                elif name == 'shape':
                    hh = [1.0, 0, 0.8 * float(slow[:2].mean()), 0, 0.6 * float(slow[2:5].mean()), 0,
                          0.4 * float(slow[5:].mean())]
                    img = waveshape(img, hh)
            elif name == 'yoke':
                # the Wobbulator with an extra yoke beside the moving subject: a field that pushes the picture out
                # from it and back with the low bands (and a gated beat), fading with distance
                sh = 0.5 * a.amount * w * osc(u_line)
                px, py = xo[None, :] - yoke_at[0], yi[:, None] - yoke_at[1]
                r2 = (px ** 2 + py ** 2) / (0.35 * h) ** 2
                push = (0.25 * float(slow[:2].mean()) * math.sin(2 * np.pi * 0.4 * t) + 0.35 * strike * sign)
                fall = np.exp(-r2) * push
                xs = xo[None, :] - sh - px * fall
                xs = np.clip(xs, 0, w - 1)
                yd = yi[:, None] + py * fall + a.vert * h * osc(u_line + 0.25)
                img = draw(rp, xs, yd, np.ones_like(xs), L, SIZE, a.width)
            elif name == 'scanimate':
                low = float(np.clip((slow[:2] - usual[:2]).mean() * 3 + 0.35 * slow[:2].mean(), 0, 1))
                mid = float(np.clip(slow[2:5].mean(), 0, 1))
                high = float(np.clip(slow[5:].mean(), 0, 1))
                theta = np.pi / 2 * (0.6 * low + 0.4 * strike * sign) * (yi / h - 0.5) * 2 + 0.2 * math.sin(0.4 * t)
                k = np.cos(theta)[:, None]
                shift = 0.04 * w * high * np.sin(2 * np.pi * (6 * yi / h + 0.1 * t))[:, None]
                c = w / 2
                xs = c + (xo[None, :] - c - shift) / np.where(np.abs(k) < 1e-3, 1e-3, k)
                gain = np.minimum(1 / np.maximum(np.abs(k), 1e-3), 2.0) * np.where(k < 0, 0.75, 1.0)
                yd = yi[:, None] + 0.12 * h * mid * ((xo[None, :] - c) / c) ** 2 * math.sin(0.3 * t + 1)
                img = draw(rp, xs, yd, np.broadcast_to(gain, xs.shape), L, SIZE, a.width)
            elif name == 'fm':
                beta = min(0.25 + 0.6 * float(slow.mean()), 0.85)       # fold guard: the beam never runs backward
                m = 7.0
                phi = 2 * np.pi * 0.08 * t + np.pi * osc(yi / h)[:, None] * 1.5
                xs = np.broadcast_to(xo[None, :], (L, w)).copy()
                for _ in range(4):        # Newton: the source x whose beam lands at this column
                    arg = 2 * np.pi * m * xs / w + phi
                    fx = xs + beta * w / (2 * np.pi * m) * np.sin(arg) - xo[None, :]
                    xs = xs - fx / (1 + beta * np.cos(arg))
                gain = 1 / (1 + beta * np.cos(2 * np.pi * m * xs / w + phi))
                img = draw(rp, xs, np.broadcast_to(yi[:, None], xs.shape), gain, L, SIZE, a.width)
            outs[name].append(img)

    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    fdir = os.path.join(a.out, 'flash_' + a.clip)
    os.makedirs(fdir, exist_ok=True)
    for name, seq in [('clip_source', fr[:n])] + list(outs.items()):
        lum, red = [], []
        for img in seq:
            c = lin(np.clip(img[..., ::-1], 0, 1))
            sm = c.sum(-1)
            rm = np.where((sm > 0) & (c[..., 0] >= 0.8 * sm), np.maximum((c[..., 0] - c[..., 1] - c[..., 2]) * 320, 0), 0)
            y = c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            lum.append(cv2.resize(y.astype(np.float32), (64, 36), interpolation=cv2.INTER_AREA)[::-1])
            red.append(cv2.resize(rm.astype(np.float32), (64, 36), interpolation=cv2.INTER_AREA)[::-1])
        np.savez_compressed(os.path.join(fdir, name + '.npz'), t=np.arange(n) * dt,
                            lum=np.array(lum, np.float32), red=np.array(red, np.float32))

    picks = [int(n * k / 5) for k in range(1, 5)]
    sheet = []
    for i in picks:
        row = [fr[i]] + [outs[k][i] for k in names]
        row = [(np.clip(r, 0, 1) * 255).astype(np.uint8) for r in row]
        for r, label in zip(row, ['input'] + names):
            cv2.putText(r, '{} {:.1f}s'.format(label, i / FPS), (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (255, 255, 255), 2, cv2.LINE_AA)
        sheet.append(np.hstack(row))
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.jpg'), np.vstack(sheet))
    for k in names:
        cv2.imwrite(os.path.join(a.out, '{}_{}.png'.format(a.clip, k)),
                    (np.clip(outs[k][picks[1]], 0, 1) * 255).astype(np.uint8))
    raw = os.path.join(a.out, a.clip + '.raw.mp4')
    cols = 3
    tiles = [fr[:n]] + [outs[k] for k in names]
    while len(tiles) % cols:
        tiles.append([np.zeros_like(fr[0])] * n)
    vw = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (w * cols, h * (len(tiles) // cols)))
    for f in range(n):
        grid = [np.hstack([tiles[r * cols + c][f] for c in range(cols)]) for r in range(len(tiles) // cols)]
        vw.write((np.clip(np.vstack(grid), 0, 1) * 255).astype(np.uint8))
    vw.release()
    final = os.path.join(a.out, a.clip + '.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-i', os.path.join(READY, a.song + '.wav'),
                    '-t', str(n / FPS), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-c:a', 'aac',
                    '-shortest', final], check=True)
    os.remove(raw)
    print('wrote', final, 'osc peak p50/p90', np.round(np.percentile(sig_log, [50, 90]), 2))


if __name__ == '__main__':
    main()
