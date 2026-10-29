"""DEV ONLY. Frost's Dew style outside TouchDesigner (board #4846): breath figures, the droplets that bead a cold pane,
simulated as droplets that nucleate, grow, touch and merge, as Beysens and Knobler watched them form ("Growth of breath
figures", PRL 57, 1986) and Fritter, Knobler and Beysens simulated them (PRA 43, 1991): each droplet grows (the pane
condenses water at a steady rate a unit area, so a droplet's radius grows at a steady rate), two that touch become one
with their volume at their center of volume, and the pane they free beads again with new small droplets between the big
ones. The droplets live on grids of cells, one droplet a cell, a level a size: level k's cells are C0 2^k pixels and
its droplets up to half that across, so a droplet can only touch those in the 3 x 3 cells around it on its own level
(and bigger ones above). A GPU can step that in one atlas of all the levels, a few passes a frame.

    uv run --with numpy --with opencv-python-headless dev/protos/frost/dew.py --out dev/out/frost/dew

This first version runs on a blank pane (no picture) to see the pattern form, then over a clip.
"""
import argparse
import os

import cv2
import numpy as np

C0 = 2.0          # level 0's cell, in pixels
LEVELS = 4


class Droplets:
    def __init__(self, W, H, seed=5):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.lv = []
        for k in range(LEVELS):
            c = C0 * 2 ** k
            w, h = int(np.ceil(W / c)), int(np.ceil(H / c))
            self.lv.append(dict(c=c, x=np.zeros((h, w), np.float32), y=np.zeros((h, w), np.float32),
                                r=np.zeros((h, w), np.float32)))

    @staticmethod
    def shifts(a, dy, dx, fill=0.0):
        out = np.full_like(a, fill)
        h, w = a.shape
        ys0, ys1 = max(0, dy), min(h, h + dy)
        xs0, xs1 = max(0, dx), min(w, w + dx)
        out[ys0:ys1, xs0:xs1] = a[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        return out

    def merge_level(self, L):
        """Droplets on one level that touch: each goes into the biggest one it touches that is bigger than it (ties by
        place), which takes the volumes of all that chose it, at their center of volume."""
        x, y, r = L['x'], L['y'], L['r']
        h, w = r.shape
        idx = np.arange(h * w, dtype=np.float32).reshape(h, w)
        best_r = np.zeros_like(r)
        best_d = np.zeros((h, w, 2), np.int32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                nx, ny, nr = self.shifts(x, dy, dx), self.shifts(y, dy, dx), self.shifts(r, dy, dx)
                ni = self.shifts(idx, dy, dx, -1)
                touch = (r > 0) & (nr > 0) & (np.hypot(nx - x, ny - y) < r + nr)
                bigger = (nr > r) | ((nr == r) & (ni < idx))
                pick = touch & bigger & (nr > best_r)
                best_r = np.where(pick, nr, best_r)
                best_d[pick] = (dy, dx)
        goes = best_r > 0
        # gather: each droplet that stays takes the ones whose choice points at it
        vol = np.where(goes, 0, r ** 3)
        mx, my = x * vol, y * vol
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                # a neighbor at offset (dy, dx) from me chose me if its choice is (-dy, -dx)
                ng = self.shifts(goes, dy, dx, False)
                nd = np.stack([self.shifts(best_d[..., 0].astype(np.float32), dy, dx),
                               self.shifts(best_d[..., 1].astype(np.float32), dy, dx)], -1)
                chose = ng & (nd[..., 0] == -dy) & (nd[..., 1] == -dx) & ~goes
                nv = self.shifts(r ** 3, dy, dx)
                vol = vol + np.where(chose, nv, 0)
                mx = mx + np.where(chose, self.shifts(x, dy, dx) * nv, 0)
                my = my + np.where(chose, self.shifts(y, dy, dx) * nv, 0)
        keep = vol > 0
        L['x'] = np.where(keep, mx / np.maximum(vol, 1e-12), 0).astype(np.float32)
        L['y'] = np.where(keep, my / np.maximum(vol, 1e-12), 0).astype(np.float32)
        L['r'] = np.where(keep, np.cbrt(vol), 0).astype(np.float32)

    def promote(self, k):
        """Droplets too big for level k's cells move up to level k + 1, merging with what is in the cell there."""
        A, B = self.lv[k], self.lv[k + 1]
        big = A['r'] >= A['c'] * 0.5
        if not big.any():
            return
        ys, xs = np.nonzero(big)
        for yy, xx in zip(ys, xs):
            px, py, pr = A['x'][yy, xx], A['y'][yy, xx], A['r'][yy, xx]
            by, bx = min(int(py // B['c']), B['r'].shape[0] - 1), min(int(px // B['c']), B['r'].shape[1] - 1)
            v0, v1 = B['r'][by, bx] ** 3, pr ** 3
            v = v0 + v1
            B['x'][by, bx] = (B['x'][by, bx] * v0 + px * v1) / v
            B['y'][by, bx] = (B['y'][by, bx] * v0 + py * v1) / v
            B['r'][by, bx] = np.cbrt(v)
        A['r'][big] = 0

    def covered_by_bigger(self, k):
        """Droplets on level k that a droplet on a level above touches go into it (it takes their volume)."""
        A = self.lv[k]
        ys, xs = np.nonzero(A['r'] > 0)
        if len(ys) == 0:
            return
        px, py, pr = A['x'][ys, xs], A['y'][ys, xs], A['r'][ys, xs]
        dead = np.zeros(len(ys), bool)
        for j in range(k + 1, LEVELS):
            B = self.lv[j]
            cy, cx = (py // B['c']).astype(int), (px // B['c']).astype(int)
            h, w = B['r'].shape
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = np.clip(cy + dy, 0, h - 1), np.clip(cx + dx, 0, w - 1)
                    br = B['r'][yy, xx]
                    hit = (br > 0) & ~dead & (np.hypot(B['x'][yy, xx] - px, B['y'][yy, xx] - py) < br + pr)
                    if hit.any():
                        # the big one takes the volume (its center stays)
                        np.add.at(B['r'], (yy[hit], xx[hit]), 0)  # keep shape
                        for i in np.nonzero(hit)[0]:
                            B['r'][yy[i], xx[i]] = np.cbrt(B['r'][yy[i], xx[i]] ** 3 + pr[i] ** 3)
                        dead |= hit
        A['r'][ys[dead], xs[dead]] = 0

    def coverage(self):
        """1 where a droplet covers the pixel, at the picture's size; and each pixel's droplet (x, y, r)."""
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32) + 0.5
        best = np.zeros((self.H, self.W, 3), np.float32)
        for L in self.lv:
            c = L['c']
            cy, cx = (yy // c).astype(int), (xx // c).astype(int)
            h, w = L['r'].shape
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    y2, x2 = np.clip(cy + dy, 0, h - 1), np.clip(cx + dx, 0, w - 1)
                    r = L['r'][y2, x2]
                    ox, oy = L['x'][y2, x2], L['y'][y2, x2]
                    inside = (r > 0) & ((xx - ox) ** 2 + (yy - oy) ** 2 < r * r) & (r > best[..., 2])
                    best[inside] = np.stack([ox, oy, r], -1)[inside]
        return best

    def step(self, dt, grow, cold, warm, nucleate, rmax=8.0):
        """grow: radius px/s where coldest; cold and warm: maps at level 0's size; nucleate: chance a free level-0
        cell starts a droplet each second, where coldest."""
        for k, L in enumerate(self.lv):
            c = L['c']
            h, w = L['r'].shape
            cl = cv2.resize(cold, (w, h), interpolation=cv2.INTER_AREA)
            wm = cv2.resize(warm, (w, h), interpolation=cv2.INTER_AREA)
            on = L['r'] > 0
            r = L['r'] + dt * (grow * cl * (1 - wm) * np.clip(1 - L['r'] / rmax, 0, 1)
                               - 3 * grow * wm * (1 + 4 / np.maximum(L['r'], 0.5)))
            L['r'] = np.where(on, np.clip(r, 0, min(rmax, c * 0.499) if k == LEVELS - 1 else rmax), 0)
        for k in range(LEVELS):
            self.merge_level(self.lv[k])
            if k + 1 < LEVELS:
                self.promote(k)
        for k in range(LEVELS - 1):
            self.covered_by_bigger(k)
        # new droplets where the pane is free
        L = self.lv[0]
        h, w = L['r'].shape
        cov = self.coverage()[..., 2] > 0
        free = cv2.resize(cov.astype(np.float32), (w, h), interpolation=cv2.INTER_AREA) < 0.01
        cl = cv2.resize(cold, (w, h), interpolation=cv2.INTER_AREA)
        wm = cv2.resize(warm, (w, h), interpolation=cv2.INTER_AREA)
        new = free & (L['r'] == 0) & (self.rng.random((h, w)) < nucleate * dt * cl * (1 - wm))
        ys, xs = np.nonzero(new)
        L['x'][ys, xs] = (xs + self.rng.random(len(xs))) * L['c']
        L['y'][ys, xs] = (ys + self.rng.random(len(ys))) * L['c']
        L['r'][ys, xs] = 0.3


def render(d, pic):
    """Each droplet a small lens over the picture: the picture seen through it shrunk and turned over, bright where the
    light behind comes through its middle, dark at its rim (light there is bent away), with a glint; free pane clear."""
    best = d.coverage()
    H, W = pic.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    ox, oy, r = best[..., 0], best[..., 1], best[..., 2]
    on = r > 0
    rr = np.maximum(r, 1e-3)
    u, v = (xx - ox) / rr, (yy - oy) / rr
    q = np.clip(u * u + v * v, 0, 1)
    z = np.sqrt(1 - q)
    # a lens: the picture behind seen through a cap, flipped about the droplet's center and spread over a wider area
    spread = 4.0
    sx, sy = ox - u * rr * spread, oy - v * rr * spread
    seen = cv2.remap(cv2.GaussianBlur(pic, (0, 0), 2), sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    rim = np.clip((q - 0.55) / 0.45, 0, 1) ** 1.5
    glint = np.clip(1 - np.hypot(u + 0.35, v + 0.4) / 0.25, 0, 1) ** 2
    small = np.clip((2.5 - r) / 2.0, 0, 1)          # droplets too small to see as lenses: a milky haze
    hazed = cv2.GaussianBlur(pic, (0, 0), 3) * 0.8 + 0.12
    drop = seen * (1 - 0.75 * rim)[..., None] + (glint * 0.6)[..., None]
    drop = drop * (1 - small[..., None]) + hazed * small[..., None]
    a = on.astype(np.float32)[..., None]
    return np.clip(pic * (1 - a) + drop * a, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='dev/out/frost/dew')
    ap.add_argument('--seconds', type=float, default=8)
    ap.add_argument('--grow', type=float, default=3.0)
    ap.add_argument('--nuc', type=float, default=3.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    W, H = 640, 360
    d = Droplets(W, H)
    cold = np.ones((int(H / C0), int(W / C0)), np.float32)
    warm = np.zeros_like(cold)
    yy, xx = np.mgrid[0:cold.shape[0], 0:cold.shape[1]]
    pic = np.zeros((H, W, 3), np.float32)
    pic[:] = np.linspace(0.15, 0.6, W)[None, :, None]
    pic[:, :, 2] *= 1.3
    pic[100:260, 200:440] = (0.2, 0.5, 0.9)
    fps = 30
    tiles = []
    for f in range(int(a.seconds * fps)):
        t = f / fps
        warm = np.where((xx - 160) ** 2 + (yy - 90) ** 2 < (30 if 3 < t < 5 else 0) ** 2, 1.0, 0.0).astype(np.float32)
        d.step(1 / fps, a.grow, cold, warm, a.nuc)
        if f % (fps * 2) == fps * 2 - 1:
            n = [int((L['r'] > 0).sum()) for L in d.lv]
            print('t', round(t, 1), 'droplets per level', n, flush=True)
            tiles.append(render(d, pic))
    sheet = np.vstack([np.hstack(tiles[i:i + 2]) for i in range(0, len(tiles), 2)])
    cv2.imwrite(os.path.join(a.out, 'blank_sheet.jpg'), (sheet * 255).astype(np.uint8))


if __name__ == '__main__':
    main()
