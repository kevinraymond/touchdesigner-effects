"""DEV ONLY. Lens Flare's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4674): the
picture's bright spots throwing the ghosts a real lens would, after Lee and Eisemann, 'Practical Real-Time Lens-Flare
Rendering' (EGSR 2013).

    uv run --with numpy --with opencv-python-headless dev/protos/lens_flare/offline.py b3_headlights \\
        --at 2.0 --out dev/out/lens_flare/offline

The optics are the effect's own (effects/lens_flare/src/optics.py, lenses.py). Here:
  lights    the picture's light above a threshold, summed in tiles: each tile a point light at its centroid, with its
            energy and color (a flare is linear in the light, so the tiles of one big light add up to its flare); the
            K brightest tiles, the K+1th's energy taken off every one so a tile leaving the top K fades out;
  ghosts    for each light and ghost, the iris's polygon at c p, radius rho, per color channel, cut by the front
            element's circle, as bright as energy x R_i R_j x the area ratio;
  starburst the iris's far-field diffraction (its Fourier transform, squared), summed over wavelengths, at each light.
Writes a sheet of lens x f-number x coating on one frame, and the flare alone.
"""

import argparse
import math
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
sys.path.insert(0, os.path.join(ROOT, 'effects', 'lens_flare', 'src'))
import lenses  # noqa: E402
import optics  # noqa: E402

SIZE = (640, 360)


def frame(clip, at):
    cap = cv2.VideoCapture(os.path.join(READY, clip + '.mp4'))
    cap.set(cv2.CAP_PROP_POS_MSEC, at * 1000)
    ok, f = cap.read()
    f = cv2.resize(f, SIZE, interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32) / 255


def to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def find_lights(img, threshold=0.85, tile=16, k=8, merge=0.1):
    """(position in picture units from the middle, energy in picture units^2, color, spread) of up to K lights: the
    brightest tile, with every tile within merge of it, then the next, ...; the K+1th's energy taken off each."""
    h, w, _ = img.shape
    half = math.hypot(w, h) / 2
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    excess = np.clip((lum - threshold) / (1 - threshold), 0, None)
    lin = to_linear(img)
    ty, tx = h // tile, w // tile
    ex = excess[:ty * tile, :tx * tile].reshape(ty, tile, tx, tile)
    ys, xs = np.mgrid[0:ty * tile, 0:tx * tile].astype(np.float32) + 0.5
    px = ((xs - w / 2) / half).reshape(ty, tile, tx, tile)
    py = ((ys - h / 2) / half).reshape(ty, tile, tx, tile)
    m = np.stack([ex.sum(axis=(1, 3)), (ex * px).sum(axis=(1, 3)), (ex * py).sum(axis=(1, 3)),
                  (ex * (px ** 2 + py ** 2)).sum(axis=(1, 3))], -1).reshape(-1, 4)
    col = (ex[..., None] * lin[:ty * tile, :tx * tile].reshape(ty, tile, tx, tile, 3)).sum(axis=(1, 3)).reshape(-1, 3)
    cen = m[:, 1:3] / np.maximum(m[:, :1], 1e-9)
    free = m[:, 0] > 0
    lights = []
    for _ in range(k + 1):
        if not free.any():
            break
        best = np.argmax(np.where(free, m[:, 0], -1))
        near = free & (np.hypot(*(cen - cen[best]).T) < merge)
        tot = m[near].sum(axis=0)
        c = tot[1:3] / tot[0]
        spread = math.sqrt(max(tot[3] / tot[0] - c @ c, 0))
        rgb = col[near].sum(axis=0)
        lights.append([c, tot[0] / half ** 2, rgb / max(rgb.max(), 1e-9), spread])
        free &= ~near
    if len(lights) > k:
        floor = lights.pop()[1]
        for l in lights:
            l[1] -= floor
    return [tuple(l) for l in lights if l[1] > 0]


def polygon(px, py, blades, rot=0.0, soft=0.02):
    """Coverage of a regular polygon with circumradius 1 (a circle for blades < 3), soft edge."""
    r = np.hypot(px, py)
    if blades < 3:
        d = r - 1
    else:
        a = np.arctan2(py, px) - rot
        seg = 2 * math.pi / blades
        a = (a + seg / 2) % seg - seg / 2
        d = r * np.cos(a) - math.cos(math.pi / blades)
    return np.clip(0.5 - d / soft, 0, 1)


COATINGS = {
    'bare': lambda k: None,
    'single': lambda k: 550.0,
    'multi': lambda k: (430.0, 600.0, 500.0, 650.0, 470.0, 560.0)[k % 6],
}


def render_ghosts(shape, lights, table, coating, blades, gain, rot=0.0):
    h, w = shape
    half = math.hypot(w, h) / 2
    out = np.zeros((h, w, 3), np.float32)
    gain = gain / optics.power(table, coating)
    area = math.pi if blades < 3 else 0.5 * blades * math.sin(2 * math.pi / blades)
    for p, energy, col, spread in lights:
        for g in table:
            for ch in range(3):
                # The ghost is the iris's image (radius rho) blurred by the light's own size, scaled by c: wider than
                # itself, it becomes a blob that wide, its energy kept.
                blur = 1.5 / half + abs(g['c'][ch]) * spread
                rho0 = g['rho'][ch]
                rho = max(rho0, blur)
                bright = g['bright'][ch] * (rho0 / rho) ** 2 * g['refl'][coating][ch]
                val = gain * energy * col[ch] * bright / area
                if val < 1e-4:
                    continue
                q = g['c'][ch] * p
                reach = rho + blur
                x0, x1 = int((q[0] - reach) * half + w / 2) - 1, int((q[0] + reach) * half + w / 2) + 2
                y0, y1 = int((q[1] - reach) * half + h / 2) - 1, int((q[1] + reach) * half + h / 2) + 2
                x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w), min(y1, h)
                if x0 >= x1 or y0 >= y1:
                    continue
                ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
                ax = ((xs - w / 2) / half - q[0]) / rho
                ay = ((ys - h / 2) / half - q[1]) / rho
                cov = polygon(ax, ay, blades, rot, soft=2 * blur / rho)
                cc = g['clip_c'][ch] * p
                inside = np.clip(0.5 - (np.hypot(ax - cc[0], ay - cc[1]) - g['clip_r'][ch]) * rho * half / 2.0, 0, 1)
                out[y0:y1, x0:x1, ch] += val * cov * inside
    return out


def starburst(blades, size=256, rot=0.0):
    """The iris's far-field diffraction, summed over 24 wavelengths with rough sRGB weights: size x size x 3."""
    n = 1024
    ys, xs = (np.mgrid[0:n, 0:n] - n / 2) / (n / 8)
    ap = polygon(xs, ys, blades, rot, soft=0.01)
    rng = np.random.default_rng(1)
    dust = rng.random((n // 16, n // 16)) > 0.98
    ap = ap * (1 - 0.6 * cv2.resize(dust.astype(np.float32), (n, n), interpolation=cv2.INTER_NEAREST))
    f = np.abs(np.fft.fftshift(np.fft.fft2(ap))) ** 2
    f /= f.max()
    f = f ** 0.25          # a real light is far brighter than its clipped pixels: show the spikes
    out = np.zeros((size, size, 3), np.float32)
    lams = np.linspace(420, 680, 24)
    for lam in lams:
        # Far field scales with the wavelength: sample the transform at (x / lam) around its middle.
        k = 0.5 * 550.0 / lam
        m = np.float32([[k, 0, n / 2 - k * size / 2], [0, k, n / 2 - k * size / 2]])
        sub = cv2.warpAffine(f, m, (size, size), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        rgb = np.array([math.exp(-((lam - 610) / 40) ** 2), math.exp(-((lam - 545) / 40) ** 2),
                        math.exp(-((lam - 450) / 35) ** 2)], np.float32)
        out += sub[..., None] * rgb
    return out / out.max()


def add_starbursts(img_lin, lights, burst, gain, radius):
    h, w, _ = img_lin.shape
    half = math.hypot(w, h) / 2
    s = burst.shape[0]
    for p, energy, col, spread in lights:
        cx, cy = p[0] * half + w / 2, p[1] * half + h / 2
        r = radius * half
        m = np.float32([[2 * r / s, 0, cx - r], [0, 2 * r / s, cy - r]])
        warped = cv2.warpAffine(burst, m, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        img_lin += gain * energy * warped * col
    return img_lin


def label(img, text):
    cv2.putText(img, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--at', type=float, default=2.0)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'lens_flare', 'offline'))
    ap.add_argument('--gain', type=float, default=40.0)
    ap.add_argument('--burst', type=float, default=40.0)
    ap.add_argument('--blades', type=int, default=6)
    ap.add_argument('--threshold', type=float, default=0.85)
    ap.add_argument('--fnumbers', default='8')
    ap.add_argument('--coatings', default='bare,single,multi')
    ap.add_argument('--lenses', default='heliar,sonnar,topogon,phone')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    img = frame(a.clip, a.at)
    lights = find_lights(img, a.threshold)
    print(len(lights), 'lights; energy', sum(l[1] for l in lights), [(round(l[1], 5), round(l[3], 3)) for l in lights])
    burst = starburst(a.blades)
    cv2.imwrite(os.path.join(a.out, 'burst.png'), (to_srgb(burst) * 255).astype(np.uint8)[..., ::-1])
    rows = []
    for lens in a.lenses.split(','):
        for coat in a.coatings.split(','):
            row = []
            for fn in [float(x) for x in a.fnumbers.split(',')]:
                table = optics.ghosts(lenses.LENSES[lens], fn)
                lin = to_linear(img)
                fl = render_ghosts(img.shape[:2], lights, table, coat, a.blades, a.gain)
                lin = add_starbursts(lin + fl, lights, burst, a.burst, 0.25)
                out = (to_srgb(lin) * 255).clip(0, 255).astype(np.uint8)[..., ::-1].copy()
                row.append(label(out, '%s %s f/%g' % (lens, coat, fn)))
            rows.append(np.hstack(row))
    sheet = np.vstack(rows)
    path = os.path.join(a.out, '%s_%g.jpg' % (a.clip, a.at))
    cv2.imwrite(path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(path, sheet.shape)


if __name__ == '__main__':
    main()
