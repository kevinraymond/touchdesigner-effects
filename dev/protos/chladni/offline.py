"""DEV ONLY. Chladni Sand's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4715):
the picture moved like sand on a vibrating plate, toward the nodal lines of plate modes the music's bands set.

    uv run --with numpy --with opencv-python-headless dev/protos/chladni/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/chladni/offline

The song goes through lib/audio_callbacks.py as raw audio, a cook at a time (as dev/beat_bench.py does), for the
seven bands, the level and the beats. Each band sets one mode of a square plate, after Chladni (1787) and the usual
approximation of its figures, phi_nm = cos(n pi x) cos(m pi y) - cos(m pi x) cos(n pi y) (the lowest band the fewest
lines); the plate's shape u is their sum, weighted by how far each band is above its usual level, and a beat strikes the
plate (its amplitude jumps and rings down). Sand on a plate drifts away from where it shakes most and settles where it
doesn't, so the flow is -grad(u^2), which is 0 on the nodal lines and points at them from both sides.

Two ways to show it, written side by side with the clip:
  warp  the picture moved: a displacement carried with the content (as Motion Magnify's), leaking back to rest, so the
        picture is drawn in toward the lines and stretched between them, and settles back between hits;
  sand  the picture's light as the sand: carried along the flow with its mass kept, so light piles up on the lines and
        drains from between them, and relaxes back to the live picture between hits.
Also writes the plate's lines alone (plate) and an MP4 of the four with the song.
"""

import argparse
import math
import os
import subprocess
import types
import wave

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE = (640, 360)
FPS = 30
BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')
# One mode per band, lowest band the fewest lines.
MODES = ((1, 3), (2, 4), (2, 5), (3, 6), (3, 7), (4, 8), (5, 8))
GATE = 1.0           # s between strikes, as Flashing at Calm allows
FOLD, REACH = 0.6, 3.0   # Motion Magnify's fold guard: at most 0.6 px of stretch a pixel, counted 3 px around


def song_channels(name, seconds):
    """lib/audio_callbacks.py cooked FPS times a second on the song as raw audio: each channel, per frame."""
    with wave.open(os.path.join(READY, name + '.wav')) as w:
        rate, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        n = min(n, int(seconds * rate))
        x = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, ch).T.astype(np.float32) / 32768
    clock = types.SimpleNamespace(seconds=0.0)
    ns = {'absTime': clock, 'CookLevel': types.SimpleNamespace(WHEN_USED=1)}
    path = os.path.join(ROOT, 'lib', 'audio_callbacks.py')
    exec(compile(open(path).read(), path, 'exec'), ns)
    chans = {}

    class Chan:
        def __init__(self, name):
            self.name, self.v = name, 0.0

        def __setitem__(self, i, v):
            self.v = v

    class Inp:
        numChans = x.shape[0]
        rate = 0

        def numpyArray(self):
            return self.slice

        def chans(self):
            return [Chan('chan1'), Chan('chan2')]

    inp = Inp()
    inp.rate = rate

    class Op:
        id = 1
        inputs = [inp]
        numSamples = 1

        def clear(self):
            chans.clear()

        def appendChan(self, name):
            chans[name] = Chan(name)
            return chans[name]

    op = Op()
    per = rate / FPS
    rows = []
    for f in range(int(x.shape[1] / per)):
        clock.seconds = (f + 1) / FPS
        inp.slice = x[:, int(f * per):int((f + 1) * per)]
        ns['onCook'](op)
        rows.append({k: c.v for k, c in chans.items()})
    return rows


def frames(clip, n):
    """n frames at FPS, the clip looping."""
    cap = cv2.VideoCapture(os.path.join(READY, clip + '.mp4'))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    src = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        src.append(cv2.resize(f, SIZE, interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    return [src[int(k / FPS * src_fps) % len(src)] for k in range(n)]


def plate_modes():
    """Each band's mode over the frame: the plate is square, as tall as the frame, centered; the picture's sides run
    on past its edges, where the cosines carry on."""
    w, h = SIZE
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    px = (x - w / 2) / h + 0.5
    py = y / h
    return np.stack([np.cos(n * np.pi * px) * np.cos(m * np.pi * py) - np.cos(m * np.pi * px) * np.cos(n * np.pi * py)
                     for n, m in MODES], -1)


def sample(img, x, y):
    return cv2.remap(img, x, y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--speed', type=float, default=160.0, help='px/s at 360 high where the plate shakes hardest')
    ap.add_argument('--leak', type=float, default=0.6, help='s: the warp settling back to rest')
    ap.add_argument('--relax', type=float, default=0.8, help='s: the sand relaxing back to the picture')
    ap.add_argument('--kick', type=float, default=1.5, help="a beat's strike: the plate's amplitude jumps by this")
    ap.add_argument('--ring', type=float, default=0.35, help='s: how long a strike rings')
    ap.add_argument('--swell', type=float, default=0.5, help='how hard the bands rising above their usual level shake it')
    ap.add_argument('--strip', default='4.0,2.0', help='start,seconds: a strip of the sand every 0.1 s')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'chladni', 'offline'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    rows = song_channels(a.song, a.seconds)
    n = len(rows)
    fr = frames(a.clip, n)
    n = min(n, len(fr))
    modes = plate_modes()
    w, h = SIZE
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    dt = 1 / FPS
    bands = np.array([[r.get(b, 0.0) for b in BANDS] for r in rows[:n]], np.float32)
    # Each band against its usual level (its average over the last 4 s), as Video Vocoder judges them, smoothed over
    # 0.25 s so the plate's shape turns rather than jumps.
    usual = np.zeros(7, np.float32)
    now = np.zeros(7, np.float32)
    strike, last_count, last_strike = 0.0, rows[0].get('beat_count', 0), -GATE
    d = np.zeros((h, w, 2), np.float32)          # warp: how far the content at each pixel is from its rest
    color = fr[0].copy()                         # sand: the colors it carries
    mass = np.ones((h, w), np.float32)           # sand: how much of it there is, 1 at rest
    out_w, out_s, out_p, energies = [], [], [], []
    for f in range(n):
        b = bands[f]
        usual += (b - usual) * (1 - math.exp(-dt / 4.0))
        now += (b - now) * (1 - math.exp(-dt / 0.25))
        count = rows[f].get('beat_count', 0)
        if count > last_count and f * dt - last_strike >= GATE:
            strike, last_strike = 1.0, f * dt
        last_count = count
        strike *= math.exp(-dt / a.ring)
        above = np.clip(now - usual, 0, None)
        shape = modes @ (above + 0.15 * now)                   # the figure: the bands rising most, a little of each
        u = shape / (np.abs(shape).max() + 1e-6)
        energy = min(a.swell * float(above.max()) + a.kick * strike, 1.5)   # how hard it shakes: the swell and the strike
        energies.append(energy)
        gyy, gxx = np.gradient(u * u)
        g = np.stack([gxx, gyy], -1)
        g /= np.abs(g).max() + 1e-6
        v = -a.speed * (h / 360) * energy * g                  # px/s toward the nodal lines
        step = v * dt
        pic = fr[f]
        # warp: carry the displacement with the content, add this frame's step, leak toward rest, fold guard
        d = (sample(d, gx - step[..., 0], gy - step[..., 1]) + step) * math.exp(-dt / a.leak)
        st = np.zeros((h, w), np.float32)
        for c in range(2):
            for dx, dy in ((1, 0), (0, 1)):
                st = np.maximum(st, np.abs(cv2.Sobel(d[..., c], cv2.CV_32F, dx, dy, ksize=3) / 8))
        st = cv2.GaussianBlur(cv2.dilate(st, np.ones((5, 5), np.uint8)), (0, 0), REACH)
        dg = d * np.minimum(1.0, FOLD / np.maximum(st, 1e-6))[..., None]
        out_w.append(sample(pic, gx - dg[..., 0], gy - dg[..., 1]))
        # sand: carry the colors along the flow and the mass with it (kept: it gathers where the flow converges),
        # both relaxing back to the live picture; the light shown is the colors times the mass, eased past 1
        div = np.gradient(v[..., 0], axis=1) + np.gradient(v[..., 1], axis=0)
        color = sample(color, gx - step[..., 0], gy - step[..., 1])
        mass = sample(mass, gx - step[..., 0], gy - step[..., 1]) * np.exp(np.clip(-div * dt, -0.5, 0.5))
        k = 1 - math.exp(-dt / a.relax)
        color += (pic - color) * k
        mass += (1 - mass) * k
        mass = np.clip(mass, 0, 8)
        out_s.append(np.clip(color * (2 * mass / (1 + mass))[..., None], 0, 1))
        line = np.exp(-(u / 0.06) ** 2)
        out_p.append(np.repeat((line * min(energy, 1.0))[..., None], 3, -1).astype(np.float32))

    # the flash test's recordings (dev/flash.py's grid, dev/flashcount.py counts them)
    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    for name, seq in (('clip_source', fr[:n]), ('chladni_warp', out_w), ('chladni_sand', out_s)):
        lum, red = [], []
        for img in seq:
            c = lin(np.clip(img[..., ::-1], 0, 1))
            sm = c.sum(-1)
            rm = np.where((sm > 0) & (c[..., 0] >= 0.8 * sm), np.maximum((c[..., 0] - c[..., 1] - c[..., 2]) * 320, 0), 0)
            y = c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            lum.append(cv2.resize(y.astype(np.float32), (64, 36), interpolation=cv2.INTER_AREA)[::-1])
            red.append(cv2.resize(rm.astype(np.float32), (64, 36), interpolation=cv2.INTER_AREA)[::-1])
        os.makedirs(os.path.join(a.out, 'flash_' + a.clip), exist_ok=True)
        np.savez_compressed(os.path.join(a.out, 'flash_' + a.clip, name + '.npz'), t=np.arange(n) * dt,
                            lum=np.array(lum, np.float32), red=np.array(red, np.float32))

    picks = [int(n * k / 6) for k in range(1, 6)]
    sheet = []
    for i in picks:
        row = [fr[i], out_w[i], out_s[i], out_p[i]]
        row = [(np.clip(r, 0, 1) * 255).astype(np.uint8) for r in row]
        for r, label in zip(row, ('input', 'warp', 'sand', 'plate')):
            cv2.putText(r, '{} {:.1f}s'.format(label, i / FPS), (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255),
                        2, cv2.LINE_AA)
        sheet.append(np.hstack(row))
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.jpg'), np.vstack(sheet))
    t0, span = (float(x) for x in a.strip.split(','))
    strip = []
    for k in range(int(span / 0.1)):
        i = min(int((t0 + 0.1 * k) * FPS), n - 1)
        img = (np.clip(cv2.resize(out_s[i], (320, 180)), 0, 1) * 255).astype(np.uint8)
        cv2.putText(img, '{:.1f}s e{:.2f}'.format(i / FPS, energies[i]), (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (255, 255, 255), 1, cv2.LINE_AA)
        strip.append(img)
    while len(strip) % 5:
        strip.append(np.zeros_like(strip[0]))
    cv2.imwrite(os.path.join(a.out, a.clip + '_strip.jpg'),
                np.vstack([np.hstack(strip[i:i + 5]) for i in range(0, len(strip), 5)]))
    raw = os.path.join(a.out, a.clip + '.raw.mp4')
    vw = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (w * 2, h * 2))
    for f in range(n):
        top = np.hstack([fr[f], out_w[f]])
        bot = np.hstack([out_s[f], out_p[f]])
        vw.write((np.clip(np.vstack([top, bot]), 0, 1) * 255).astype(np.uint8))
    vw.release()
    final = os.path.join(a.out, a.clip + '.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-i', os.path.join(READY, a.song + '.wav'),
                    '-t', str(n / FPS), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-c:a', 'aac',
                    '-shortest', final], check=True)
    os.remove(raw)
    print('wrote', final, 'and', a.clip + '_sheet.jpg;', 'beats', last_count, 'energy p50/p90',
          np.round(np.percentile(energies, [50, 90]), 2))


if __name__ == '__main__':
    main()
