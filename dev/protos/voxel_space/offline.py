"""DEV ONLY. Voxel Space's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4716):
the picture as Comanche's terrain (NovaLogic, 1992), its depth (or brightness) the height map and its colors the color
map, drawn a screen column at a time front to back with a y-buffer while a camera flies over it.

    uv run --with numpy --with opencv-python-headless dev/protos/voxel_space/offline.py b1_dancer \\
        --song m1x_ease_from_drop --seconds 10 --out dev/out/voxel/offline

The song goes through lib/audio_callbacks.py as raw audio (dev/protos/chladni/offline.py's song_channels()). Each
screen column steps out from the camera along its ray, each step longer than the last; a step's height, projected by
its distance, draws the column from there up to the highest point drawn so far (the y-buffer), so nearer terrain hides
what is behind it. Above the last point drawn is sky; far terrain fades into it.

Flights (columns of the sheet):
  fly     forward over the picture mirrored at its edges, weaving and banking into the turns, keeping clear of the
          ground ahead, as Comanche's helicopter flew
  orbit   circling the picture, one island in a flat sea, looking down at its middle
  hover   standing off the picture's bottom edge and looking across it, swaying, so it reads as a landscape
"""

import argparse
import importlib.util
import math
import os
import subprocess

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE = (640, 360)      # the maps
OUT = (640, 360)       # the view
FPS = 30
WORLD = 1024.0         # the picture's width in world units, whatever its size
GATE = 1.0

_spec = importlib.util.spec_from_file_location('chladni', os.path.join(ROOT, 'dev', 'protos', 'chladni', 'offline.py'))
chladni = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chladni)
chladni.SIZE, chladni.FPS = SIZE, FPS


def bilinear(img, x, y):
    """img sampled at pixel coordinates x, y (1-D arrays), clamped."""
    h, w = img.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = x - x0, y - y0
    if img.ndim == 3:
        fx, fy = fx[:, None], fy[:, None]
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def shade(height, scale, sun=(-0.5, -0.6, 0.62), ambient=0.35):
    """Lambert light from the upper left on the height map (heights in world units), as Comanche's maps had it baked
    in: the terrain's shape reads where its colors are flat."""
    h, w = height.shape
    unit = WORLD / w
    gx = cv2.Sobel(height * scale, cv2.CV_32F, 1, 0, ksize=3) / (8 * unit)
    gy = cv2.Sobel(height * scale, cv2.CV_32F, 0, 1, ksize=3) / (8 * unit)
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    s = np.array(sun, np.float32)
    s /= np.linalg.norm(s)
    lam = np.clip(n @ s, 0, 1)
    return ambient + (1 - ambient) * lam / max(float(s[2]), 1e-3)


def render(color, height, cam, mode, scale, fog_color, sky_top, zfar=2200.0, fov=1.6):
    """One view. cam: x, y (world units; y down the picture), alt, heading (radians; 0 looks up the picture), horizon
    (screen rows from the top), roll (radians). Heights are height x scale world units."""
    hm, wm = height.shape
    W, H = OUT
    aspect = hm / wm
    x, y, alt, heading, horizon, roll = cam
    fwd = np.array([math.sin(heading), -math.cos(heading)])
    right = np.array([-fwd[1], fwd[0]])
    t = math.tan(fov / 2)
    focal = (W / 2) / t
    s = (np.arange(W) + 0.5) / W * 2 - 1
    dirs = fwd[None, :] + (s * t)[:, None] * right[None, :]
    tilt = (np.arange(W) - W / 2) * math.tan(roll)
    zs = [1.0]
    while zs[-1] < zfar:
        zs.append(zs[-1] + 0.6 + 0.012 * zs[-1])
    z = np.array(zs, np.float32)[:, None]                       # K steps x W columns, all at once
    px = x + dirs[None, :, 0] * z
    py = y + dirs[None, :, 1] * z
    u = px / WORLD
    v = py / (WORLD * aspect)
    if mode == 'orbit':
        inside = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    else:
        u = 1 - np.abs(np.mod(u, 2) - 1)
        v = 1 - np.abs(np.mod(v, 2) - 1)
        inside = np.ones(u.shape, bool)
    mx, my = (u * (wm - 1)).ravel(), (v * (hm - 1)).ravel()
    hh = np.where(inside, bilinear(height, mx, my).reshape(u.shape) * scale, 0.0)
    col = bilinear(color, mx, my).reshape(u.shape + (3,))
    if mode == 'orbit':
        col = np.where(inside[..., None], col, (fog_color * 0.35)[None, None, :])
    ys = horizon + (alt - hh) / z * focal + tilt[None, :]
    fog = np.clip((z - zfar * 0.45) / (zfar * 0.55), 0, 1) ** 1.5
    col = col * (1 - fog[..., None]) + fog_color[None, None, :] * fog[..., None]
    # The y-buffer front to back: a row is drawn by the first step whose top reaches it, the first k where the
    # running minimum of the steps' tops is at or above the row.
    top = np.minimum.accumulate(ys, axis=0)
    rows = np.arange(H, dtype=np.float32) + 0.5
    K = len(zs)
    img = np.empty((H, W, 3), np.float32)
    skyk = np.clip((horizon + tilt[None, :] - rows[:, None]) / H, 0, 1)[:, :, None]
    sky = fog_color[None, None, :] * (1 - skyk) + sky_top[None, None, :] * skyk
    for c in range(W):
        k = np.searchsorted(-top[:, c], -rows, side='left')
        hit = k < K
        img[:, c] = np.where(hit[:, None], col[np.minimum(k, K - 1), c], sky[:, c])
    return img


def ground(height, scale, x, y, mode):
    hm, wm = height.shape
    u, v = x / WORLD, y / (WORLD * hm / wm)
    if mode == 'orbit' and not (0 <= u <= 1 and 0 <= v <= 1):
        return 0.0
    u = 1 - abs((u % 2) - 1)
    v = 1 - abs((v % 2) - 1)
    return float(bilinear(height, np.array([u * (wm - 1)]), np.array([v * (hm - 1)]))[0]) * scale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'voxel', 'offline'))
    ap.add_argument('--modes', default='fly,orbit,hover')
    ap.add_argument('--height', type=float, default=320.0)
    ap.add_argument('--sun', type=float, default=1.0)
    ap.add_argument('--every', type=int, default=1)
    ap.add_argument('--relief', type=int, default=1)
    ap.add_argument('--nodepth', action='store_true')
    ap.add_argument('--smooth', type=float, default=0.006)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    pics = chladni.frames(a.clip, n)
    dpath = os.path.join(READY, a.clip + '_depth.mp4')
    deps = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in chladni.frames(a.clip + '_depth', n)] if os.path.exists(dpath) and not a.nodepth \
        else [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in pics]
    chans = chladni.song_channels(a.song, a.seconds + 1) if a.song else [{} for _ in range(n)]
    modes = a.modes.split(',')
    writers = {m: cv2.VideoWriter(os.path.join(a.out, m + '.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), FPS / a.every, OUT)
               for m in modes}
    dt = 1 / FPS
    eased = None
    bass_now = bass_usual = 0.0
    last_count, last_strike, strike_t = 0, -9.0, -9.0
    beats_t = []
    speed = 1.0
    state = {m: {'x': WORLD * 0.5, 'y': WORLD * 0.5625 * 1.15, 'alt': None, 'dist': 0.0, 'theta': math.pi / 2}
             for m in modes}
    hm, wm = deps[0].shape
    aspect = hm / wm
    for f in range(n):
        tsec = f * dt
        c = chans[f] if f < len(chans) else {}
        dep = cv2.GaussianBlur(deps[f], (0, 0), 1.2)
        if a.relief:
            # Nearness above the row's far baseline: a floor is about as near all along a row, so it goes flat, and
            # whatever stands in front of its surroundings stands up.
            base = np.percentile(dep, 12, axis=1).astype(np.float32)
            base = cv2.GaussianBlur(base[:, None], (0, 0), dep.shape[0] * 0.03)[:, 0]
            dep = np.maximum(dep - base[:, None], 0)
        if a.smooth:
            dep = cv2.GaussianBlur(dep, (0, 0), dep.shape[1] * a.smooth)
        if 'orbit' in a.modes:      # the island's shore: heights taper to the sea over its outer 4%
            hh, ww = dep.shape
            ty = np.clip(np.minimum(np.arange(hh), hh - 1 - np.arange(hh)) / (0.04 * hh), 0, 1)
            tx = np.clip(np.minimum(np.arange(ww), ww - 1 - np.arange(ww)) / (0.04 * hh), 0, 1)
            dep = (dep * np.minimum(ty[:, None], tx[None, :]) ** 0.5).astype(np.float32)
        eased = dep.copy() if eased is None else eased + (dep - eased) * (1 - math.exp(-dt / 0.2))
        bass = 0.5 * (c.get('sub_bass', 0) + c.get('bass', 0))
        bass_now += (bass - bass_now) * (1 - math.exp(-dt / 1.0))
        bass_usual += (bass_now - bass_usual) * (1 - math.exp(-dt / 4.0))
        lift = 1 + 0.6 * min(bass_now * 0.5 + max(bass_now - bass_usual, 0) * 1.5, 1)
        count = int(c.get('beat_count', 0))
        if count > last_count:
            beats_t.append(tsec)
            if tsec - last_strike >= GATE:
                last_strike = strike_t = tsec
        last_count = count
        recent = [b for b in beats_t if tsec - b < 6]
        tempo = (len(recent) - 1) / (recent[-1] - recent[0]) * 60 if len(recent) > 3 else 120.0
        speed += (min(max(tempo / 120, 0.6), 1.6) - speed) * (1 - math.exp(-dt / 2.0))
        bump = 0.0
        if tsec - strike_t < 0.6:
            q = (tsec - strike_t) / 0.6
            bump = math.sin(math.pi * q) * (1 - q) ** 0.5
        scale = a.height * lift
        sh = shade(eased, scale)
        sh = 1 + (sh - 1) * a.sun
        color = pics[f][:, :, ::-1] * sh[:, :, None]
        mean = pics[f].reshape(-1, 3).mean(0)[::-1]
        fog_color = np.clip(mean * 1.6 + 0.08, 0, 1).astype(np.float32)
        sky_top = (fog_color * 0.35).astype(np.float32)
        if f % a.every:
            continue
        for m in modes:
            st = state[m]
            if m == 'fly':
                heading = 0.5 * math.sin(tsec * 0.21) + 0.25 * math.sin(tsec * 0.53 + 1)
                turn = 0.5 * 0.21 * math.cos(tsec * 0.21) + 0.25 * 0.53 * math.cos(tsec * 0.53 + 1)
                st['x'] += math.sin(heading) * 90 * speed * dt
                st['y'] -= math.cos(heading) * 90 * speed * dt
                ahead = max(ground(eased, scale, st['x'] + math.sin(heading) * d, st['y'] - math.cos(heading) * d, m)
                            for d in (0, 40, 90, 160))
                want = ahead + 70
                st['alt'] = want if st['alt'] is None else st['alt'] + (want - st['alt']) * (1 - math.exp(-dt / 0.6))
                cam = (st['x'], st['y'], st['alt'] - 25 * bump, heading, OUT[1] * 0.38, -turn * 0.5)
            elif m == 'orbit':
                st['theta'] += 0.12 * speed * dt
                r = WORLD * 0.62
                cx, cy = WORLD * 0.5, WORLD * aspect * 0.5
                x, y = cx + r * math.cos(st['theta']), cy + r * math.sin(st['theta'])
                heading = math.atan2(cx - x, -(cy - y))
                alt = scale * 0.5 + 240 - 30 * bump
                horizon = OUT[1] * 0.5 - alt / r * (OUT[0] / 2) / math.tan(0.8)
                cam = (x, y, alt, heading, horizon, 0.0)
            else:
                x = WORLD * (0.5 + 0.12 * math.sin(tsec * 0.3))
                y = WORLD * aspect * 1.3
                heading = -0.18 * math.sin(tsec * 0.3)
                alt = scale * 0.5 + 140 - 25 * bump
                cam = (x, y, alt, heading, OUT[1] * 0.5 - alt / (WORLD * aspect * 0.8) * (OUT[0] / 2) / math.tan(0.8),
                       0.05 * math.sin(tsec * 0.3))
            img = render(color, eased, cam, m, scale, fog_color, sky_top)
            out = (np.clip(img[:, :, ::-1], 0, 1) * 255).astype(np.uint8)
            writers[m].write(out)
            if f % (FPS * 2) == FPS:
                cv2.imwrite(os.path.join(a.out, '{}_{:03d}.png'.format(m, f)), out)
        if f % 30 == 0:
            print('frame', f, 'tempo %.0f' % tempo, 'lift %.2f' % lift, flush=True)
    for w in writers.values():
        w.release()
    sheet = []
    for m in modes:
        shots = sorted(p for p in os.listdir(a.out) if p.startswith(m + '_') and p.endswith('.png'))
        row = [cv2.imread(os.path.join(a.out, p)) for p in shots[:4]]
        sheet.append(np.concatenate(row, 1))
    cv2.imwrite(os.path.join(a.out, 'sheet.png'), np.concatenate(sheet, 0))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
