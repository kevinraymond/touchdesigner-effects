"""DEV ONLY. Pixel Art's look outside TouchDesigner, in numpy and OpenCV, before anything is built (board #4675):
the picture as pixel art with a small palette it picks itself, after Gerstner, DeCarlo, Alexa, Finkelstein, Gingold and
Nealen, 'Pixelated Image Abstraction' (NPAR 2012).

    uv run --with numpy --with opencv-python-headless dev/protos/pixel_art/offline.py b1_dancer \\
        --seconds 6 --out dev/out/pixel_art/offline

The paper's loop (its Algorithm 1), run on video one iteration a frame and never stopped, each frame starting from the
last one's superpixels and palette:
  superpixels  one per output pixel, on the output grid; each input pixel goes to the superpixel among its cell's 3 x 3
               neighbors that minimizes d = |lab - palette color of s| + m sqrt(N/M) |p - center of s| (m = 45: the
               color distance is to the superpixel's palette color, not its mean color); each center moves 40% of the
               way to the average of its 4 neighbors (Laplacian smoothing); the superpixels' mean colors go through a
               bilateral filter on the output grid;
  palette      mass-constrained deterministic annealing (Rose 1998): soft association P(c|s) ~ P(c) exp(-|m_s - c|^2/T),
               each color the weighted mean of the superpixels, starting from one color (two sub-clusters) at 1.1 Tc;
               when the palette settles, T falls by 0.7 and sub-clusters that have separated split, until K colors; then
               T settles at Tf;
  video        (ours) the palette and superpixels carry over from frame to frame; a color nobody uses any more takes half
               of the most spread-out one (its split along its principal axis); each superpixel keeps its palette color
               until another is clearly closer (hysteresis), so noise doesn't flip it.

Writes, side by side with the clip: ours, 'cubic' (area downsampling, the same palette machinery) and 'nearest' (a
bilateral filter, then the cell's middle pixel), as the paper compares; a sheet at a few moments, an MP4, and per frame
how many output pixels changed color.
"""

import argparse
import os
import subprocess

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE = (640, 360)
FPS = 30


def frames(clip, n):
    """n frames at FPS, the clip looping, RGB 0-1."""
    cap = cv2.VideoCapture(os.path.join(READY, clip + '.mp4'))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    src = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        f = cv2.resize(f, SIZE, interpolation=cv2.INTER_AREA)
        src.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32) / 255)
    return [src[int(k / FPS * src_fps) % len(src)] for k in range(n)]


def lab(rgb):
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)


def rgb(lab_img):
    return np.clip(cv2.cvtColor(lab_img.astype(np.float32), cv2.COLOR_Lab2RGB), 0, 1)


def principal(X, w):
    """Weighted mean, largest variance and its axis."""
    sw = w.sum() + 1e-12
    mu = (X * w[:, None]).sum(0) / sw
    D = X - mu
    cov = (D * w[:, None]).T @ D / sw
    vals, vecs = np.linalg.eigh(cov)
    return mu, vals[-1], vecs[:, -1]


class Palette:
    """MCDA (Rose 1998) as Gerstner et al. use it, one iteration a call, warm across calls."""

    def __init__(self, K, Tf=1.0, alpha=0.7, eps_palette=1.0, eps_cluster=0.25, delta=0.8, dead=0.002, max_at_t=8):
        self.K, self.Tf, self.alpha, self.max_at_t, self.at_t = K, Tf, alpha, max_at_t, 0
        self.eps_palette, self.eps_cluster, self.delta, self.dead = eps_palette, eps_cluster, delta, dead
        self.c = None      # entries (sub-clusters while splitting), Lab
        self.p = None      # P(c) of each entry
        self.pair = None   # which cluster each entry belongs to
        self.T = None
        self.paired = True

    def start(self, X, w):
        mu, lam, v = principal(X, w)
        self.T = 1.1 * 2 * lam
        self.c = np.stack([mu + self.delta * v, mu - self.delta * v])
        self.p = np.array([0.5, 0.5])
        self.pair = np.array([0, 0])
        self.paired = True

    def associate(self, X):
        d2 = ((X[:, None, :] - self.c[None]) ** 2).sum(-1)
        logit = np.log(self.p + 1e-12)[None] - d2 / self.T
        logit -= logit.max(1, keepdims=True)
        P = np.exp(logit)
        return P / P.sum(1, keepdims=True)

    def clusters(self):
        """Each cluster's color: the mean of its sub-clusters."""
        n = self.pair.max() + 1
        out = np.zeros((n, 3))
        for k in range(n):
            out[k] = self.c[self.pair == k].mean(0)
        return out

    def step(self, X, w):
        if self.c is None:
            self.start(X, w)
        w = w / w.sum()
        P = self.associate(X)
        Pw = P * w[:, None]
        pc = Pw.sum(0)
        new = (Pw.T @ X) / (pc[:, None] + 1e-12)
        change = np.abs(new - self.c).sum()
        self.c, self.p = new, pc
        n = self.pair.max() + 1
        self.at_t += 1
        # The paper lowers T once the palette has settled; on video it never quite settles, so also after max_at_t
        # iterations at one temperature (ours).
        if change < self.eps_palette or self.at_t >= self.max_at_t:
            self.at_t = 0
            self.T = max(self.T * self.alpha, self.Tf)
            if self.paired:
                self.expand(X, P, w)
        if not self.paired:
            self.revive(X, P, w)
        return n

    def expand(self, X, P, w):
        n = self.pair.max() + 1
        c, p, pair = [], [], []
        k_new = 0
        splits = [k for k in range(n) if np.linalg.norm(np.diff(self.c[self.pair == k], axis=0)) > self.eps_cluster]
        room = self.K - n
        for k in range(n):
            idx = np.where(self.pair == k)[0]
            if k in splits[:room]:
                for e in idx:   # each sub-cluster becomes a cluster with its own pair
                    mu, lam, v = principal(X, P[:, e] * w)
                    for s in (1, -1):
                        c.append(self.c[e] + s * self.delta * v)
                        p.append(self.p[e] / 2)
                        pair.append(k_new)
                    k_new += 1
            else:
                mu = self.c[idx].mean(0)
                _, lam, v = principal(X, P[:, idx].sum(1) * w)
                for s in (1, -1):
                    c.append(mu + s * self.delta * v)
                    p.append(self.p[idx].sum() / 2)
                    pair.append(k_new)
                k_new += 1
        self.c, self.p, self.pair = np.array(c), np.array(p), np.array(pair)
        if k_new >= self.K:   # palette full: drop the sub-clusters
            self.c, self.p = self.clusters(), np.array([self.p[self.pair == k].sum() for k in range(k_new)])
            self.pair = np.arange(k_new)
            self.paired = False

    def revive(self, X, P, w):
        """A color nobody uses takes half of the most spread-out one (ours, for video)."""
        for k in np.where(self.p < self.dead)[0]:
            spread = [self.p[j] * principal(X, P[:, j] * w)[1] if self.p[j] >= self.dead else -1 for j in range(len(self.c))]
            j = int(np.argmax(spread))
            mu, lam, v = principal(X, P[:, j] * w)
            s = np.sqrt(max(lam, 1e-6)) * 0.5
            self.c[k], self.c[j] = mu + s * v, mu - s * v
            self.p[k] = self.p[j] = self.p[j] / 2


class Superpixels:
    """Gerstner et al.'s modified SLIC on the output grid, one step a call."""

    def __init__(self, h, w, S, m=45.0, lap=0.4, sigma_r=10.0):
        self.S, self.m, self.lap, self.sigma_r = S, m, lap, sigma_r
        self.ho, self.wo = h // S, w // S
        gy, gx = np.mgrid[0:self.ho, 0:self.wo].astype(np.float32)
        self.home = np.stack([(gx + 0.5) * S, (gy + 0.5) * S], -1)
        self.cent = self.home.copy()
        py, px = np.mgrid[0:self.ho * S, 0:self.wo * S].astype(np.float32)
        self.px, self.py = px, py
        self.i0, self.j0 = (py // S).astype(int), (px // S).astype(int)

    def assign(self, L, color):
        """Each input pixel to the superpixel among its cell's 3 x 3 neighbors minimizing d."""
        best_d = np.full(L.shape[:2], np.inf, np.float32)
        best = np.zeros(L.shape[:2], int)
        wgt = self.m / self.S
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                ci = np.clip(self.i0 + di, 0, self.ho - 1)
                cj = np.clip(self.j0 + dj, 0, self.wo - 1)
                cen = self.cent[ci, cj]
                d = np.sqrt(((L - color[ci, cj]) ** 2).sum(-1)) + wgt * np.hypot(self.px - cen[..., 0], self.py - cen[..., 1])
                better = d < best_d
                best_d[better] = d[better]
                best[better] = (ci * self.wo + cj)[better]
        return best

    def update(self, L, label, importance=None):
        n = self.ho * self.wo
        lab_flat = label.ravel()
        cnt = np.bincount(lab_flat, minlength=n).astype(np.float32)
        safe = np.maximum(cnt, 1)
        cx = np.bincount(lab_flat, self.px.ravel(), n) / safe
        cy = np.bincount(lab_flat, self.py.ravel(), n) / safe
        mean = np.stack([np.bincount(lab_flat, L[..., c].ravel(), n) / safe for c in range(3)], -1)
        imp = np.bincount(lab_flat, importance.ravel(), n) / safe if importance is not None else np.ones(n)
        empty = cnt == 0
        if empty.any():   # a superpixel that lost every pixel keeps its place and takes the color under its center
            ci = np.clip(self.cent.reshape(-1, 2)[empty].astype(int), 0, [L.shape[1] - 1, L.shape[0] - 1])
            mean[empty] = L[ci[:, 1], ci[:, 0]]
        cent = np.stack([cx, cy], -1).reshape(self.ho, self.wo, 2)
        cent[empty.reshape(self.ho, self.wo)] = self.cent[empty.reshape(self.ho, self.wo)]
        # Laplacian smoothing toward the 4 neighbors; a missing neighbor counts as one cell further on.
        S = self.S
        up = np.concatenate([cent[:1] - [0, S], cent[:-1]], 0)
        dn = np.concatenate([cent[1:], cent[-1:] + [0, S]], 0)
        lf = np.concatenate([cent[:, :1] - [S, 0], cent[:, :-1]], 1)
        rt = np.concatenate([cent[:, 1:], cent[:, -1:] + [S, 0]], 1)
        cent = cent + self.lap * ((up + dn + lf + rt) / 4 - cent)
        self.cent = np.clip(cent, self.home - 0.5 * S, self.home + 0.5 * S)
        mean = mean.reshape(self.ho, self.wo, 3)
        return bilateral(mean, self.sigma_r), imp.reshape(self.ho, self.wo)


def bilateral(img, sigma_r, sigma_s=1.0):
    """3 x 3 bilateral filter on the output grid."""
    pad = np.pad(img, ((1, 1), (1, 1), (0, 0)), mode='edge')
    acc = np.zeros_like(img)
    ws = np.zeros(img.shape[:2], np.float32)
    h, w = img.shape[:2]
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            nb = pad[1 + di:1 + di + h, 1 + dj:1 + dj + w]
            wgt = np.exp(-(di * di + dj * dj) / (2 * sigma_s ** 2) - ((nb - img) ** 2).sum(-1) / (2 * sigma_r ** 2))
            acc += nb * wgt[..., None]
            ws += wgt
    return acc / ws[..., None]


class Art:
    """One way of making the art: superpixels (ours) or a plain downsampling, the same palette."""

    def __init__(self, kind, h, w, a):
        self.kind, self.a = kind, a
        self.sp = Superpixels(h, w, a.pixel, a.m, a.lap, a.sigma_r)
        self.pal = Palette(a.colors, a.tf, max_at_t=a.max_at_t)
        self.index = None
        self.ho, self.wo = self.sp.ho, self.sp.wo

    def colors_of(self, X):
        """Each superpixel's palette color now (the cluster it holds, with hysteresis)."""
        cl = self.pal.clusters()
        d = np.sqrt(((X[:, None, :] - cl[None]) ** 2).sum(-1))
        best = d.argmin(1)
        if self.index is not None and self.index.max() < len(cl) and len(cl) == self.ncl:
            keep = d[np.arange(len(X)), self.index] < d[np.arange(len(X)), best] + self.a.hold
            best = np.where(keep, self.index, best)
        self.index, self.ncl = best, len(cl)
        return cl[best], best

    def frame(self, img, importance=None):
        L = lab(img)[: self.ho * self.a.pixel, : self.wo * self.a.pixel]
        S = self.a.pixel
        if self.kind == 'ours':
            if self.index is None:
                color = np.broadcast_to(L.reshape(-1, 3).mean(0), (self.ho, self.wo, 3))
            else:
                color = self.pal.clusters()[self.index].reshape(self.ho, self.wo, 3)
            for _ in range(self.a.iters):
                label = self.sp.assign(L, color)
                X, imp = self.sp.update(L, label, importance)
        elif self.kind == 'cubic':
            X = cv2.resize(L, (self.wo, self.ho), interpolation=cv2.INTER_AREA)
            imp = np.ones((self.ho, self.wo))
        else:  # nearest: a bilateral filter, then the middle pixel of each cell
            b = cv2.bilateralFilter(L, 9, 20, 5)
            X = b[S // 2::S, S // 2::S][: self.ho, : self.wo]
            imp = np.ones((self.ho, self.wo))
        Xf = X.reshape(-1, 3).astype(np.float64)
        if self.a.ease > 0:   # each superpixel's color eased over time (ours), so noise doesn't flip its palette color
            if getattr(self, 'Xe', None) is None:
                self.Xe = Xf
            k = 1 - np.exp(-1 / FPS / self.a.ease)
            jump = np.sqrt(((Xf - self.Xe) ** 2).sum(-1, keepdims=True))
            k = k + (1 - k) * np.clip((jump - 5) / 15, 0, 1)   # a big change (a cut, a fast edge) passes at once
            self.Xe = self.Xe + (Xf - self.Xe) * k
            Xf = self.Xe
        for _ in range(self.a.piters):
            self.pal.step(Xf, imp.ravel() + 1e-6)
        col, idx = self.colors_of(Xf)
        if self.a.dither > 0:   # ordered dither between the two nearest colors, on the art's own grid
            cl = self.pal.clusters()
            d = np.sqrt(((Xf[:, None, :] - cl[None]) ** 2).sum(-1))
            d1 = d[np.arange(len(Xf)), idx]
            d_alt = d.copy()
            d_alt[np.arange(len(Xf)), idx] = np.inf
            j2 = d_alt.argmin(1)
            d2 = d_alt[np.arange(len(Xf)), j2]
            f = d1 / (d1 + d2 + 1e-6)
            D = self.a.dither
            f = np.clip((f - 0.5 * (1 - D)) / D, 0, 0.5)
            bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32
            gy, gx = np.mgrid[0:self.ho, 0:self.wo]
            t = bayer[gy % 4, gx % 4].ravel()
            col = np.where((t < f)[:, None], cl[j2], col)
        col = col.reshape(self.ho, self.wo, 3).copy()
        col[..., 1:] *= self.a.saturate
        small = rgb(col)
        big = cv2.resize(small, (self.wo * S, self.ho * S), interpolation=cv2.INTER_NEAREST)
        return big, small, idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--seconds', type=float, default=6)
    ap.add_argument('--pixel', type=int, default=4, help='input pixels per output pixel at 640 x 360 (8 at 1280 x 720)')
    ap.add_argument('--colors', type=int, default=12)
    ap.add_argument('--m', type=float, default=45.0)
    ap.add_argument('--lap', type=float, default=0.4)
    ap.add_argument('--sigma-r', type=float, default=10.0)
    ap.add_argument('--tf', type=float, default=1.0)
    ap.add_argument('--max-at-t', type=int, default=8)
    ap.add_argument('--hold', type=float, default=2.0, help='Lab: how much closer another color must be to take over')
    ap.add_argument('--iters', type=int, default=1, help='superpixel iterations a frame')
    ap.add_argument('--piters', type=int, default=4, help='palette iterations a frame')
    ap.add_argument('--saturate', type=float, default=1.1)
    ap.add_argument('--dither', type=float, default=0.0)
    ap.add_argument('--ease', type=float, default=0.0, help="s: each superpixel's color eased over time")
    ap.add_argument('--at', default='1,3,5', help='seconds for the sheet')
    ap.add_argument('--kinds', default='ours,cubic,nearest')
    ap.add_argument('--depth', action='store_true', help="the clip's depth map as the importance map")
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'pixel_art', 'offline'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    fr = frames(a.clip, n)
    dp = [f.mean(-1) for f in frames(a.clip + '_depth', n)] if a.depth else None
    h, w = SIZE[1], SIZE[0]
    kinds = a.kinds.split(',')
    arts = {k: Art(k, h, w, a) for k in kinds}
    at = [int(float(t) * FPS) for t in a.at.split(',')]
    sheet_rows, vid, prev, flips, full_at = [], [], {}, {k: [] for k in kinds}, {}
    hist = {k: [] for k in kinds}
    flipbacks = {k: [] for k in kinds}   # share of output pixels that left their color and came back within 4 frames   # the last few frames' art, for flips that come back
    for f in range(n):
        tiles = [fr[f][: arts[kinds[0]].ho * a.pixel, : arts[kinds[0]].wo * a.pixel]]
        for k in kinds:
            imp = dp[f][: arts[k].ho * a.pixel, : arts[k].wo * a.pixel] if dp else None
            big, small, idx = arts[k].frame(fr[f], imp)
            tiles.append(big)
            if k in prev:
                dE = np.abs(lab(small) - lab(prev[k])).sum(-1)
                flips[k].append(float((dE > 3).mean()))
            prev[k] = small
            hist[k] = (hist[k] + [lab(small)])[-5:]
            if len(hist[k]) == 5 and f >= 2 * FPS and f % FPS not in (0, 1, 2, 3, 4):
                h0, hn = hist[k][0], hist[k][-1]
                away = np.zeros(h0.shape[:2], bool)
                for mid in hist[k][1:-1]:
                    away |= np.abs(mid - h0).sum(-1) > 3
                back = away & (np.abs(hn - h0).sum(-1) <= 3)
                flipbacks[k].append(float(back.mean()))
            if k not in full_at and not arts[k].pal.paired:
                full_at[k] = f
        row = np.hstack(tiles)
        vid.append(row)
        if f in at:
            sheet_rows.append(row)
    cv2.imwrite(os.path.join(a.out, a.clip + '_sheet.png'),
                (cv2.cvtColor(np.vstack(sheet_rows), cv2.COLOR_RGB2BGR) * 255).astype(np.uint8))
    raw = os.path.join(a.out, a.clip + '_raw.mp4')
    vh, vw = vid[0].shape[:2]
    out = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (vw, vh))
    for v in vid:
        out.write((cv2.cvtColor(v, cv2.COLOR_RGB2BGR) * 255).astype(np.uint8))
    out.release()
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    os.path.join(a.out, a.clip + '.mp4')])
    os.remove(raw)
    for k in kinds:
        fl = np.array(flips[k])
        big = [(i + 1, round(v, 3)) for i, v in enumerate(fl) if v > 0.15]
        print(k, 'frames with >15% changed:', big[:20])
        settled = fl[int(2 * FPS):] if len(fl) > 2 * FPS else fl
        fb = np.array(flipbacks[k] or [0])
        print(f'{k:8s} palette full at frame {full_at.get(k)}  changed per frame after 2 s: '
              f'median {np.median(settled):.4f} mean {settled.mean():.4f} max {settled.max():.4f}  '
              f'flip-backs: mean {fb.mean():.4f} max {fb.max():.4f}')


if __name__ == '__main__':
    main()
