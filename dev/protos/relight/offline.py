"""DEV ONLY. Relight's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4677): the
picture lit again by colored lights that move over it, its shape from the depth map on input 3 (the picture's own
brightness, smoothed, without one).

    uv run --with numpy --with opencv-python-headless dev/protos/relight/offline.py b1_dancer \\
        stage:look=0 studio:look=1 --song m1x_ease_from_drop --seconds 10 --out dev/out/relight/offline_r1

The surface is a height field: the depth (brighter nearer) times Relief, smoothed finely for its detail and broadly
for roundness, so a figure cut out of a flat depth map bulges like a relief instead of standing as a slab. Its normals
come from the height's slope. The picture is the surface's color, its own shading flattened by Flatten (divided by
its blurred brightness). Each light is a point over the picture, on a slow Lissajous path: Lambert's diffuse and a
GGX specular (Schlick's Fresnel, F0 0.04), falling off with distance; its shadow found by marching the height field
from each pixel toward the light (a soft penumbra from how far under the ray the field rises, relative to the
distance). Ambient occlusion from the height field, after Luft, Colditz and Deussen's unsharp masking of the depth
buffer (2006): what lies below its blurred surroundings is darker. Skin (found by color, YCrCb) scatters the light
under it, the diffuse light blurred wider in red than green and blue, as Jimenez et al.'s separable subsurface
scattering does with a diffusion profile (2015), here as three Gaussians.

This prototype predates the patent check (private/patents/relight.md). The effect itself finds no skin or any other
region (Canon US 11,948,282 and 11,106,938), multiplies its shadow samples' light rather than taking a minimum (Adobe
US 8,379,021), and adds no two Gaussian blurs (NVIDIA US 8,064,726); see effects/relight/build_relight.py.

Variants are named on the command line as name:key=value,...; keys are DEFAULTS'. Writes a sheet (a row a moment, the
clip then each variant), an MP4 with the song, and flash counts per variant against the clip (dev/flashcount.py's
measure on 64 x 36 cells of linear luminance, as dev/protos/caustics/offline.py does).
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
SIZE = (640, 360)
FPS = 30


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


chladni = load('chladni', os.path.join(ROOT, 'dev', 'protos', 'chladni', 'offline.py'))
chladni.SIZE, chladni.FPS = SIZE, FPS
flashcount = load('flashcount', os.path.join(ROOT, 'dev', 'flashcount.py'))
caustics = load('caustics', os.path.join(ROOT, 'dev', 'protos', 'caustics', 'offline.py'))

DEFAULTS = dict(look=0, relief=0.25, round=8.0, fine=1.5, flatten=0.5, flatblur=24.0, lift=1.0, ambient=0.03, exposure=1.0, rough=0.4,
                spec=1.0, shadow=1.0, soft=0.15, ao=0.5, sss=1.0, glow=1.0, thick=1.0, speed=1.0, kick=0.5, radius=0.9, nodepth=0, bumps=0.5,
                steps=32, reach=0.35)

# The looks: each a list of lights (color in linear RGB, intensity, path: center x, y as shares of the frame, sway
# x, y, periods x, y in seconds, phase, height as a share of the frame's height).
LOOKS = {
    0: ('Stage', [((0.55, 0.15, 1.0), 2.2, (0.3, 0.3, 0.25, 0.2, 9.0, 7.0, 0.0, 0.35)),
                  ((0.05, 0.85, 0.75), 2.0, (0.7, 0.35, 0.25, 0.2, 11.0, 8.0, 2.0, 0.35)),
                  ((1.0, 0.55, 0.05), 1.6, (0.5, 0.8, 0.35, 0.1, 13.0, 10.0, 4.0, 0.3))]),
    1: ('Studio', [((1.0, 0.85, 0.7), 2.6, (0.25, 0.25, 0.08, 0.06, 17.0, 13.0, 0.0, 0.6)),
                   ((0.6, 0.75, 1.0), 0.6, (0.8, 0.45, 0.05, 0.05, 19.0, 15.0, 1.0, 0.5)),
                   ((1.0, 1.0, 1.0), 1.6, (0.55, -0.05, 0.3, 0.02, 23.0, 11.0, 3.0, 0.08))]),
    2: ('Sun', [((1.0, 0.8, 0.55), 1.6, (1.2, -2.4, 0, 0, 30.0, 0, 0.0, -25.0)),
                ((0.35, 0.5, 0.9), 0.0, (0.5, 0.5, 0, 0, 1.0, 1.0, 0.0, 2.0))]),
    3: ('Two Tone', [((1.0, 0.5, 0.1), 3.0, (0.0, 0.4, 0.05, 0.2, 13.0, 9.0, 0.0, 0.25)),
                     ((0.1, 0.4, 1.0), 3.0, (1.0, 0.4, 0.05, 0.2, 11.0, 10.0, 1.5, 0.25))]),
}


def blur(img, sigma):
    if sigma <= 0:
        return img
    return cv2.GaussianBlur(img, (0, 0), sigma, borderType=cv2.BORDER_REPLICATE)


def lum(c):
    return 0.0722 * c[..., 0] + 0.7152 * c[..., 1] + 0.2126 * c[..., 2]


def red_guard(lin):
    """lib/glsl/red_guard.glsl on BGR arrays in linear light."""
    knee, top = 0.73, 0.775
    b, g, r = lin[..., 0], lin[..., 1], lin[..., 2]
    total = r + g + b
    share = r / np.maximum(total, 1e-6)
    t = knee + (top - knee) * (1 - np.exp(-(share - knee) / (top - knee)))
    gb = g + b
    e = 0.01 * r
    add = (r * (1 / t - 1) - gb) / (gb + 2 * e)
    out = lin.copy()
    m = share > knee
    out[..., 0] = np.where(m, b + add * (b + e), b)
    out[..., 1] = np.where(m, g + add * (g + e), g)
    return out


def ggx(n_h, n_l, n_v, v_h, rough):
    a = rough * rough
    a2 = a * a
    d = a2 / (math.pi * (n_h * n_h * (a2 - 1) + 1) ** 2)
    k = a / 2
    g = (n_l / (n_l * (1 - k) + k)) * (n_v / (n_v * (1 - k) + k))
    f = 0.04 + 0.96 * (1 - v_h) ** 5
    return d * g * f / np.maximum(4 * n_l * n_v, 1e-4)


class Relight:
    def __init__(self, v):
        self.v = v
        self.t = 0.0
        self.boost = 0.0
        W, H = SIZE
        self.y, self.x = np.mgrid[0:H, 0:W].astype(np.float32)

    def step(self, beat):
        """A frame's time: a beat pushes the lights along their paths (an eased burst of speed)."""
        if beat:
            self.boost += self.v['kick'] * 4.0
        self.t += (self.v['speed'] + self.boost) / FPS
        self.boost *= math.exp(-1 / FPS / 0.25)

    def lights(self):
        W, H = SIZE
        out = []
        for col, inten, (cx, cy, sx, sy, px, py, ph, z) in LOOKS[int(self.v['look'])][1]:
            if z < 0:   # a sun: cx the azimuth's sway (radians) about cy, px its period; -z its elevation (degrees)
                az = cy + cx * math.sin(2 * math.pi * self.t / px + ph)
                el = math.radians(-z)
                out.append((np.array(col, np.float32)[::-1], inten, math.cos(el) * math.cos(az),
                            math.cos(el) * math.sin(az), math.sin(el), None))
                continue
            lx = (cx + sx * math.sin(2 * math.pi * self.t / px + ph)) * W
            ly = (cy + sy * math.sin(2 * math.pi * self.t / py + ph * 1.3)) * H
            out.append((np.array(col, np.float32)[::-1], inten, lx, ly, z * H, 1))   # BGR
        return out

    def render(self, srgb, depth):
        v = self.v
        W, H = SIZE
        pic = caustics.lin(np.clip(srgb, 0, 1)).astype(np.float32)   # light adds up in linear light
        L = lum(pic)
        if depth is None or v['nodepth']:
            # The weak stand-in: only the picture's fine detail as bumps on a flat plane (its brightness as a whole made the
            # sky the nearest thing in a landscape), so the lights pool on it and glance off its texture.
            g = np.sqrt(np.maximum(L, 0))
            d = 0.5 + v['bumps'] * (blur(g, 1.0) - blur(g, 6.0))
        else:
            d = depth.astype(np.float32) / 255
        scale = v['relief'] * H
        h = scale * (0.5 * blur(d, v['fine']) + 0.5 * blur(d, v['round']))
        gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
        gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
        gx[:, 0] = gx[:, -1] = 0
        gy[0, :] = gy[-1, :] = 0
        nl = np.sqrt(gx * gx + gy * gy + 1)
        nx, ny, nz = -gx / nl, -gy / nl, 1 / nl
        # The picture's own light, flattened: divided by its blurred brightness, toward the frame's mean.
        # Lifting the darks is held to LIFT times, since a video's darks are mostly noise and blocks.
        shade = blur(L, v['flatblur'])
        gain = np.clip(float(L.mean() + 0.05) / np.maximum(shade, 1e-3), 1 / 4, v['lift']) ** v['flatten']
        albedo = np.clip(pic * gain[..., None], 0, 1)
        # Ambient occlusion: what lies below its blurred surroundings (Luft et al. 2006), at two radii.
        hs = blur(d, 1.0) * scale
        # A neighbor much higher is something in front, not a wall around this pixel, so it doesn't occlude (SSAO's range
        # check): its rise counts fully up to a radius, then fades out by twice it.
        occ = np.zeros_like(hs)
        taps = 0
        for r in (3.0, 8.0, 16.0):
            for k in range(8):
                a = 2 * math.pi * (k + 0.5 * (r == 8.0)) / 8
                hn = cv2.remap(hs, self.x + r * math.cos(a), self.y + r * math.sin(a), cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_REPLICATE)
                rise = hn - hs
                occ += np.clip(rise / r, 0, 1) * np.clip(2 - rise / r, 0, 1)
                taps += 1
        ao = np.clip(1 - v['ao'] * occ / taps * 2, 0, 1)
        diffuse = np.zeros_like(pic)
        spec = np.zeros_like(pic)
        back = np.zeros_like(pic)
        for col, inten, lx, ly, lz, point in self.lights():
            if point:
                dx, dy, dz = lx - self.x, ly - self.y, lz - h
                dist = np.sqrt(dx * dx + dy * dy + dz * dz)
                ux, uy, uz = dx / dist, dy / dist, dz / dist
                fall = 1 / (1 + (dist / (v['radius'] * H)) ** 2)
            else:
                ux, uy, uz, fall = lx, ly, lz, 1.0
            n_l = np.maximum(nx * ux + ny * uy + nz * uz, 0)
            back += (inten * fall * np.maximum(0.3 - (nx * ux + ny * uy + nz * uz), 0))[..., None] * \
                np.array(col if point else col, np.float32)
            # The view is straight down the z axis.
            hx, hy, hz = ux, uy, uz + 1
            hl = np.sqrt(hx * hx + hy * hy + hz * hz)
            n_h = np.maximum((nx * hx + ny * hy + nz * hz) / hl, 0)
            v_h = np.maximum(hz / hl, 0)
            s = ggx(n_h, np.maximum(n_l, 1e-3), np.maximum(nz, 1e-3), v_h, v['rough']) * n_l
            sh = (self.shadow(h, lx, ly, lz) if point else self.sun_shadow(h, lx, ly, lz)) if v['shadow'] > 0 else 1.0
            sh = 1 - v['shadow'] * (1 - sh)
            k = (inten * fall * sh)[..., None] * col
            diffuse += k * n_l[..., None]
            spec += k * s[..., None] * v['spec']
        # Skin scatters the light under it: the diffuse light blurred, red widest (three Gaussians for the profile).
        if v['sss'] > 0:
            ycc = cv2.cvtColor(np.clip(srgb, 0, 1).astype(np.float32), cv2.COLOR_BGR2YCrCb)
            cr, cb = ycc[..., 1] * 255, ycc[..., 2] * 255
            skin = np.clip((cr - 133) / 8, 0, 1) * np.clip((173 - cr) / 8, 0, 1) * \
                np.clip((cb - 77) / 8, 0, 1) * np.clip((127 - cb) / 8, 0, 1) * np.clip(ycc[..., 0] * 8, 0, 1)
            skin = blur(skin, 2.0)
            wide = np.stack([blur(diffuse[..., 0], 1.0), blur(diffuse[..., 1], 2.0), blur(diffuse[..., 2], 5.0)], -1)
            diffuse = diffuse + (wide - diffuse) * (skin * v['sss'])[..., None]
            # Light through thin skin (Jimenez et al. 2010's transmittance): how much skin lies around a pixel stands in
            # for its thickness, and the light from behind its side (0.3 + n.-L) comes through red first.
            thick = blur(skin, 12.0) * v['thick']
            tr = np.stack([np.exp(-thick * thick / 0.04), np.exp(-thick * thick / 0.15), np.exp(-thick * thick / 0.6)], -1)
            diffuse += back[..., :] * tr * (skin * v['glow'])[..., None]
        light = v['ambient'] * ao[..., None] + diffuse * ao[..., None]
        out = (albedo * light + spec) * v['exposure']
        # A soft shoulder above 0.8, so bright lights roll off instead of clipping.
        k = 0.8
        out = np.where(out > k, k + (1 - k) * (1 - np.exp(-(out - k) / (1 - k))), out)
        out = red_guard(out)
        return (np.where(out <= 0.0031308, out * 12.92, 1.055 * np.maximum(out, 0) ** (1 / 2.4) - 0.055)).astype(np.float32)

    def shadow(self, h, lx, ly, lz):
        """March the height field from each pixel toward the light: lit 1, shadowed 0, a penumbra between from how far
        the field rises above the ray, over the distance (like a cone's)."""
        v = self.v
        W, H = SIZE
        dx, dy = lx - self.x, ly - self.y
        dxy = np.maximum(np.sqrt(dx * dx + dy * dy), 1e-3)
        ex, ey = dx / dxy, dy / dxy
        slope = (lz - h) / dxy
        reach = np.minimum(dxy, v['reach'] * W)
        lit = np.ones_like(h)
        n = int(v['steps'])
        for i in range(1, n + 1):
            t = reach * (i / n) ** 1.5
            hs = cv2.remap(h, self.x + ex * t, self.y + ey * t, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            above = hs - (h + slope * t) - 0.5
            lit = np.minimum(lit, np.clip(1 - above / np.maximum(t * v['soft'], 0.5), 0, 1))
        return lit


def _sun_shadow(self, h, ux, uy, uz):
    """The same march toward a sun: one direction everywhere, the ray rising at the sun's slope."""
    v = self.v
    W, H = SIZE
    exy = max(math.hypot(ux, uy), 1e-4)
    ex, ey, slope = ux / exy, uy / exy, uz / exy
    lit = np.ones_like(h)
    n = int(v['steps'])
    for i in range(1, n + 1):
        t = v['reach'] * W * (i / n) ** 1.5
        hs = cv2.remap(h, self.x + ex * t, self.y + ey * t, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        above = hs - (h + slope * t) - 0.5
        lit = np.minimum(lit, np.clip(1 - above / max(t * v['soft'], 0.5), 0, 1))
    return lit


Relight.sun_shadow = _sun_shadow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('variants', nargs='*', help='name:key=value,...')
    ap.add_argument('--song', default='m1x_ease_from_drop')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--out', default='dev/out/relight/offline')
    ap.add_argument('--no-video', action='store_true')
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
    depths = [None if d is None else (d * 255).astype(np.uint8) for d in depths]
    variants = []
    for spec in a.variants or ['defaults:']:
        name, _, kv = spec.partition(':')
        v = dict(DEFAULTS)
        v.update({k: float(x) for k, x in (p.split('=') for p in kv.split(',') if p)})
        variants.append((name, Relight(v)))
    outs = {name: [] for name, _ in variants}
    for f in range(n):
        for name, r in variants:
            r.step(f in beats)
            outs[name].append(r.render(pics[f], depths[f]))
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
    times = [int(s * FPS) for s in (1.0, 3.5, 6.0, 8.5) if s * FPS < n]
    sheet = [np.hstack([cv2.resize(np.clip(im, 0, 1), (w // 2, hgt // 2), interpolation=cv2.INTER_AREA)
                        for im in [pics[k]] + [outs[nm][k] for nm in names]]) for k in times]
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.jpg'), (np.vstack(sheet) * 255).astype(np.uint8))
    k = times[1]
    cv2.imwrite(os.path.join(a.out, a.clip + '_full.jpg'),
                (np.vstack([np.hstack([pics[k], outs[names[0]][k]])] +
                           [np.hstack([outs[names[i]][k], outs[names[i + 1]][k] if i + 1 < len(names) else
                                       np.zeros_like(pics[k])]) for i in range(1, len(names), 2)]) * 255).astype(np.uint8))
    if a.no_video:
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
