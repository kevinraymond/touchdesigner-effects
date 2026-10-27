"""DEV ONLY. Detail's method outside TouchDesigner, in numpy: the fast local Laplacian filter (Aubry, Paris, Hasinoff,
Kautz and Durand, TOG 2014, after Paris, Hasinoff and Kautz, SIGGRAPH 2011) on a few frames of the clips, with the
library's own pyramid (lib/glsl pyramid_down.glsl's binomial [1 5 10 10 5 1] / 32, pyramid.glsl's cubic B-spline
expand()), to choose how many remapped copies the GPU needs and to look at the settings side by side:

    uv run --with numpy --with scipy --with opencv-python-headless dev/protos/detail/offline.py \\
        --clips b1_dancer,d3b_flowers --at 2 --out dev/out/detail/offline

The picture's luma (sRGB-encoded, Rec. 709 weights) is remapped around K values spread over 0 to 1, each copy's
Laplacian pyramid is built, and each output coefficient is taken between the two copies whose value brackets the
luma's Gaussian pyramid there; the coarsest level is the luma's own. While detail boosts, a band's change is cored by
its own coefficient c, c^2 / (c^2 + noise^2). The output adds the luma's change to each channel.
--error compares K copies against 64 (as good as exact for 8 bits) and prints the PSNR. A look of retinex=<amount>
is the multiscale Retinex that was tried as a mode and set aside (board #4720): each channel in linear light divided
by its blur at three of the pyramid's sizes, raised to the amount.
"""

import argparse
import os

import cv2
import numpy as np
from scipy import sparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE = (1280, 720)


def frame(clip, at):
    cap = cv2.VideoCapture(os.path.join(READY, clip + '.mp4'))
    cap.set(cv2.CAP_PROP_POS_MSEC, at * 1000)
    ok, f = cap.read()
    assert ok, clip
    f = cv2.resize(f, SIZE, interpolation=cv2.INTER_AREA)
    return f[..., ::-1].astype(np.float32) / 255   # RGB


def down_matrix(n_in):
    """pyramid_down.glsl along one axis: n_in -> half, taps 2x-2 ... 2x+3 weighted 1 5 10 10 5 1 (/32), edges held."""
    n_out = max(1, (n_in + 1) // 2)
    w = np.array([1, 5, 10, 10, 5, 1], np.float32) / 32
    rows, cols, vals = [], [], []
    for x in range(n_out):
        for k in range(6):
            rows.append(x)
            cols.append(min(max(2 * x - 2 + k, 0), n_in - 1))
            vals.append(w[k])
    return sparse.csr_matrix((vals, (rows, cols)), shape=(n_out, n_in))


def expand_matrix(n_lvl, n_out):
    """pyramid.glsl's expand() along one axis: a level of n_lvl read at each of n_out pixels by the cubic B-spline."""
    rows, cols, vals = [], [], []
    for X in range(n_out):
        p = (X + 0.5) / n_out * n_lvl - 0.5
        i = int(np.floor(p))
        f = p - i
        ws = ((1 - f) ** 3 / 6, (4 - 6 * f * f + 3 * f ** 3) / 6, (1 + 3 * f + 3 * f * f - 3 * f ** 3) / 6, f ** 3 / 6)
        for k, wk in enumerate(ws):
            rows.append(X)
            cols.append(min(max(i - 1 + k, 0), n_lvl - 1))
            vals.append(wk)
    return sparse.csr_matrix((vals, (rows, cols)), shape=(n_out, n_lvl))


class Pyr:
    """The down and expand matrices for every level of a picture of size (h, w)."""

    def __init__(self, h, w, levels):
        self.shapes = [(h, w)]
        self.dy, self.dx, self.ey, self.ex = [], [], [], []
        for _ in range(levels):
            h0, w0 = self.shapes[-1]
            self.dy.append(down_matrix(h0))
            self.dx.append(down_matrix(w0))
            h1, w1 = self.dy[-1].shape[0], self.dx[-1].shape[0]
            self.ey.append(expand_matrix(h1, h0))
            self.ex.append(expand_matrix(w1, w0))
            self.shapes.append((h1, w1))

    @staticmethod
    def _apply(my, mx, a):
        if a.ndim == 2:
            return (my @ (mx @ a.T).T).astype(np.float32)
        return np.stack([Pyr._apply(my, mx, a[..., c]) for c in range(a.shape[2])], -1)

    def gauss(self, a):
        out = [a]
        for k in range(len(self.dy)):
            out.append(self._apply(self.dy[k], self.dx[k], out[-1]))
        return out

    def expand(self, k, a):
        """Level k + 1 read at level k's pixels."""
        return self._apply(self.ey[k], self.ex[k], a)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def remap(i, g, detail, tone, edge):
    """The pointwise remapping around the reference g, in Aubry et al.'s smooth (Gaussian) form: near g (closer than
    about edge) a difference is multiplied by 1 + detail, far from it by tone."""
    d = i - g
    e = np.exp(-d * d / (2 * edge * edge))
    return g + d * (tone + (1 - tone) * e + detail * e)


def llf(lum, pyr, k, detail, tone, edge, noise, levels):
    gam = np.linspace(0, 1, k).astype(np.float32)
    G = pyr.gauss(lum)
    copies = np.stack([remap(lum, g, detail, tone, edge) for g in gam], -1)
    C = pyr.gauss(copies)
    out = G[levels]
    for l in reversed(range(levels)):
        lap = C[l] - pyr.expand(l, C[l + 1])                      # every copy's band at level l
        g = np.clip(G[l], 0, 1) * (k - 1)
        j = np.minimum(np.floor(g).astype(int), k - 2)
        a = g - j
        lo = np.take_along_axis(lap, j[..., None], -1)[..., 0]
        hi = np.take_along_axis(lap, (j + 1)[..., None], -1)[..., 0]
        own = G[l] - pyr.expand(l, G[l + 1])
        keep = own * own / (own * own + (noise * noise if detail > 0 else 0) + 1e-12)   # coring (collapse.glsl)
        out = own + keep * ((1 - a) * lo + a * hi - own) + pyr.expand(l, out)
    return out


def luma(rgb):
    return (rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)).astype(np.float32)


def label(img, text):
    img = np.ascontiguousarray(img)
    cv2.putText(img, text, (12, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 5, cv2.LINE_AA)
    cv2.putText(img, text, (12, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clips', default='b1_dancer,d3b_flowers,b4_koi,a1_portrait')
    ap.add_argument('--at', type=float, default=2.0)
    ap.add_argument('--k', type=int, default=8)
    ap.add_argument('--levels', type=int, default=7)
    ap.add_argument('--noise', type=float, default=0.01)
    ap.add_argument('--looks', default='in;detail=1.5,tone=1,edge=0.15;detail=-1,tone=1,edge=0.15;'
                                       'detail=0.5,tone=0.5,edge=0.15;detail=3,tone=0.5,edge=0.2')
    ap.add_argument('--error', action='store_true')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'detail', 'offline'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pyr = Pyr(SIZE[1], SIZE[0], a.levels)
    for clip in a.clips.split(','):
        rgb = frame(clip, a.at)
        y = luma(rgb)
        tiles = []
        for look in a.looks.split(';'):
            if look == 'in':
                tiles.append(label((rgb * 255).astype(np.uint8), 'input'))
                continue
            if look.startswith('retinex'):
                amt = float(look.split('=')[1])
                G = pyr.gauss(rgb)
                blur = []
                for top in (4, 5, 6):                            # MSR's three surrounds, from the pyramid
                    b = G[top]
                    for l in reversed(range(top)):
                        b = pyr.expand(l, b)
                    blur.append(b)
                lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
                enc = lambda c: np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - 0.055)
                eps = 0.004
                logr = sum(np.log(lin(rgb) + eps) - np.log(lin(b) + eps) for b in blur) / 3
                mean = np.mean(lin(G[6]), (0, 1))
                out = np.clip(enc(lin(rgb) * np.exp(-amt * (np.log(lin(rgb) + eps) - logr - np.log(mean + eps)))), 0, 1)
                tiles.append(label((out * 255).astype(np.uint8), look))
                continue
            p = dict(kv.split('=') for kv in look.split(','))
            p = {k: float(v) for k, v in p.items()}
            o = llf(y, pyr, a.k, p['detail'], p['tone'], p['edge'], a.noise, a.levels)
            if a.error:
                ref = llf(y, pyr, 64, p['detail'], p['tone'], p['edge'], a.noise, a.levels)
                mse = float(np.mean((np.clip(o, 0, 1) - np.clip(ref, 0, 1)) ** 2))
                print('{} {} K={}: PSNR {:.1f} dB against K=64, max diff {:.3f}'.format(
                    clip, look, a.k, 10 * np.log10(1 / max(mse, 1e-12)), float(np.abs(o - ref).max())))
            out = np.clip(rgb + (o - y)[..., None], 0, 1)
            tiles.append(label((out * 255).astype(np.uint8), look))
        small = [cv2.resize(t, (640, 360), interpolation=cv2.INTER_AREA) for t in tiles]
        while len(small) % 3:
            small.append(np.zeros_like(small[0]))
        rows = [np.concatenate(small[i:i + 3], 1) for i in range(0, len(small), 3)]
        cv2.imwrite(os.path.join(a.out, clip + '.png'), np.concatenate(rows, 0)[..., ::-1])
        print('wrote', os.path.join(a.out, clip + '.png'))


if __name__ == '__main__':
    main()
