"""DEV ONLY. Temporal Resonator's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4717):
each pixel a plucked string over time, after Karplus and Strong (CMJ 1983) with Jaffe and Smith's extensions (CMJ
1983): a delay line one beat long whose output is averaged and fed back, so whatever moves comes round again on the next
beat, fainter and softer each time, as a string's tone repeats every period and loses its highs first.

    uv run --with numpy --with opencv-python-headless dev/protos/temporal_resonator/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/resonator/offline

The song goes through lib/audio_callbacks.py as raw audio, a cook at a time, for the beats; the beat length is the
median gap between them. The delay line holds the string's state s at FPS; the loop reads it one beat back (a
fractional delay, linear between frames), averages that with the frame before (Karplus-Strong's two-point average,
weighted by Jaffe and Smith's decay stretch S) and blurs it a little across the picture (each echo softer), times the
loop gain g.

Variants (columns of the sheet), round 4 (board #4717 has rounds 1 to 3):
  ema_pluck  the string carries what differs from the background, a running average over 2 s; plucked for the beat
             after each beat (rising over a tenth of it, gone by the next); the echoes added to the live picture,
             behind what differs from the background now
  med_pluck  the same over an approximate median (McFarlane and Schofield: each pixel steps toward the picture by at
             most 0.6 a second), which someone walking through leaves no trace in; what the effect does
  med_bow    the median, plucked all the time
  med_odd    the median, the loop's gain negative: the echoes alternate in sign
Set aside in earlier rounds: the textbook comb over the whole picture shown as (1 - g) y (the live subject dims to
1 - g), and Schroeder's allpass over the difference, mixed half and half with it dry (it barely showed).
Also writes a strip of the dancer's middle over two beats.
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

_spec = importlib.util.spec_from_file_location('chladni', os.path.join(ROOT, 'dev', 'protos', 'chladni', 'offline.py'))
chladni = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chladni)
chladni.SIZE, chladni.FPS = SIZE, FPS


class Line:
    """A delay line of whole frames, read a fractional number of frames back."""

    def __init__(self, n):
        self.buf = [np.zeros((SIZE[1], SIZE[0], 3), np.float32) for _ in range(n)]
        self.i = 0

    def push(self, v):
        self.i = (self.i + 1) % len(self.buf)
        self.buf[self.i] = v

    def back(self, d):
        """The state d frames before the newest (d >= 1)."""
        k = int(np.floor(d))
        u = d - k
        a = self.buf[(self.i - k + 1) % len(self.buf)]
        b = self.buf[(self.i - k) % len(self.buf)]
        return a * (1 - u) + b * u


def loop(line, n, stretch, soft):
    """What comes back round the loop: one beat back, Karplus-Strong's average with the frame before, softened."""
    y = (1 - stretch) * line.back(n) + stretch * line.back(n + 1)
    return cv2.GaussianBlur(y, (0, 0), soft) if soft > 0 else y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--gain', type=float, default=0.7)
    ap.add_argument('--stretch', type=float, default=0.5, help="Jaffe and Smith's S: 0.5 is Karplus-Strong's average")
    ap.add_argument('--soft', type=float, default=1.0, help='px of blur per trip round the loop')
    ap.add_argument('--beats', type=float, default=1.0, help='the delay in beats')
    ap.add_argument('--out', default='dev/out/resonator/offline')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    n_frames = int(a.seconds * FPS)
    rows = chladni.song_channels(a.song, a.seconds)
    counts = [r['beat_count'] for r in rows]
    beat_at = [i for i in range(1, len(counts)) if counts[i] > counts[i - 1]]
    period = float(np.median(np.diff(beat_at))) if len(beat_at) > 2 else FPS / 2
    n = period * a.beats
    print('beats', len(beat_at), 'period', period / FPS, 's =', period, 'frames; delay', n, 'frames')
    pics = chladni.frames(a.clip, n_frames)

    g, S, soft = a.gain, a.stretch, a.soft
    size = int(n) + 3
    # name: (background: 'ema' or 'median', excite on beats only, loop gain, blur a trip (px), echo strength)
    variants = {'ema_pluck': ('ema', True, 0.85, 1.5, 1.5), 'med_pluck': ('median', True, 0.85, 1.5, 1.5),
                'med_bow': ('median', False, 0.85, 1.5, 1.5), 'med_odd': ('median', True, -0.85, 1.5, 1.5)}
    lines = {k: Line(size) for k in variants}
    ema = pics[0].copy()
    med = pics[0].copy()
    since_beat = 1e9
    outs = {k: [] for k in variants}
    for f in range(n_frames):
        x = pics[f]
        if f in beat_at:
            since_beat = 0
        else:
            since_beat += 1
        ema += (x - ema) * (1 / (2.0 * FPS))         # the picture over the last 2 s
        med += np.clip(x - med, -0.6 / FPS, 0.6 / FPS)   # approximate median (McFarlane and Schofield): at most 0.6 a second
        ph = since_beat / n
        pluck = min(ph / 0.1, 1.0) * (1 - ph) if ph < 1 else 0.0   # a pluck: rises over a tenth of a beat, fades by the next
        for k, (bgk, on_beats, gk, sk, amp) in variants.items():
            e = x - (ema if bgk == 'ema' else med)
            mag = np.abs(e).max(-1, keepdims=True)
            live = np.clip(mag / 0.15, 0, 1)             # where the subject is now
            core = np.clip((mag - 0.04) / 0.08, 0, 1)    # faint drift (smoke, noise) doesn't ring
            L = lines[k]
            r = gk * loop(L, n, S, sk)
            L.push((pluck if on_beats else 1.0) * core * e + r)
            outs[k].append(x + amp * r * (1 - live))

    names = list(outs)
    w, h = SIZE
    # A sheet: one row a moment, the clip then each variant.
    times = [int(t * FPS) for t in (2.0, 3.3, 4.6, 6.0, 7.4, 8.8) if t * FPS < n_frames]
    sheet = []
    for t in times:
        row = [pics[t]] + [outs[k][t] for k in names]
        row = [np.clip(im, 0, 1) for im in row]
        sheet.append(np.hstack([cv2.resize(im, (w // 2, h // 2), interpolation=cv2.INTER_AREA) for im in row]))
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.jpg'), (np.vstack(sheet) * 255).astype(np.uint8))
    print('columns: clip', ' '.join(names))
    # A strip: the dancer's middle, every other frame over two beats from the first beat after 4 s.
    t0 = next(b for b in beat_at if b > 4 * FPS)
    x0 = int(0.40 * w)
    strip = []
    for k in ['clip'] + names:
        src = pics if k == 'clip' else outs[k]
        strip.append(np.hstack([np.clip(src[t][:, x0:x0 + int(0.28 * w)], 0, 1)
                                for t in range(t0, min(t0 + int(2 * n) + 1, n_frames), 2)]))
    cv2.imwrite(os.path.join(a.out, a.clip + '_strip.jpg'), (np.vstack(strip) * 255).astype(np.uint8))

    raw = os.path.join(a.out, a.clip + '_raw.mp4')
    vw = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (w // 2 * 3, h))
    for f in range(n_frames):
        ims = [pics[f]] + [outs[k][f] for k in names] + [np.zeros_like(pics[f])] * 5
        top, bot = ims[:3], ims[3:6]
        frame = np.vstack([np.hstack([cv2.resize(np.clip(im, 0, 1), (w // 2, h // 2)) for im in r]) for r in (top, bot)])
        vw.write((frame * 255).astype(np.uint8))
    vw.release()
    out = os.path.join(a.out, a.clip + '.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-i', os.path.join(READY, a.song + '.wav'),
                    '-shortest', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', out], check=True)
    os.remove(raw)
    print('wrote', out)


if __name__ == '__main__':
    main()
