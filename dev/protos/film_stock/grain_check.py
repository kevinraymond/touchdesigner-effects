"""DEV ONLY. Checks Film Stock's grain simulation against the Boolean model it simulates, in numpy (board #4622):

    uv run --with numpy dev/protos/film_stock/grain_check.py

The model (Newson, Delon and Galerne 2017): developed grains are opaque disks whose centers fall as a Poisson process of
density lambda = ln(1 / (1 - u)) / (pi r^2), so a point is covered with probability u, the pixel's exposure. The ground
truth here rasterizes the disks on an 8 x 8 subgrid per pixel and averages (the pixel's coverage). The effect can't
afford that, so it simulates the same model two ways and this prints how far each strays, in the mean and in the
standard deviation of a pixel's coverage, over a field of constant u:
  fine    r below SWITCH px: per pixel, the number of grains N from Poisson(lambda), coverage 1 - (1 - pi r^2)^N (the
          grains' places inside the pixel marginalized; grains straddling the pixel's edge ignored)
  coarse  r at or above SWITCH: cells of 2 r_max; per cell N from Poisson(lambda c^2); each grain's place and radius
          drawn; the pixel taken as a disk of the same area (radius 0.5642) and its coverage by a grain the area of the
          two disks' lens, so the mean stays exactly u (the Boolean model's generating functional); the union as
          1 - prod(1 - cov_i), the grains' places inside the pixel taken as independent
"""
import numpy as np

SWITCH = 0.25
rng = np.random.default_rng(1)


def truth(u, r, n=96, ss=8):
    lam = np.log(1 / (1 - u)) / (np.pi * r * r)
    N = rng.poisson(lam * n * n)
    cx, cy = rng.uniform(0, n, N), rng.uniform(0, n, N)
    ys, xs = np.mgrid[0:n * ss, 0:n * ss]
    xs = (xs + 0.5) / ss; ys = (ys + 0.5) / ss
    cov = np.zeros((n * ss, n * ss), bool)
    rr = r * r
    for x, y in zip(cx, cy):
        x0, x1 = max(0, int((x - r) * ss) - 1), min(n * ss, int((x + r) * ss) + 2)
        y0, y1 = max(0, int((y - r) * ss) - 1), min(n * ss, int((y + r) * ss) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        sub = (xs[y0:y1, x0:x1] - x) ** 2 + (ys[y0:y1, x0:x1] - y) ** 2 <= rr
        cov[y0:y1, x0:x1] |= sub
    return cov.reshape(n, ss, n, ss).mean(axis=(1, 3))


def fine(u, r, n=96):
    lam = np.log(1 / (1 - u)) / (np.pi * r * r)
    N = rng.poisson(lam, (n, n))
    return 1 - (1 - np.pi * r * r) ** N


R = 0.5641896   # a disk of the pixel's area


def lens(d, r):
    """Area of the lens where a disk of radius r at distance d meets the pixel's disk (radius R, area 1)."""
    d = np.maximum(d, 1e-6)
    full = np.where(r >= R, 1.0, np.pi * r * r)              # one inside the other
    inside = d <= abs(r - R)
    apart = d >= r + R
    x1 = np.clip((d * d + r * r - R * R) / (2 * d * r), -1, 1)
    x2 = np.clip((d * d + R * R - r * r) / (2 * d * R), -1, 1)
    k = np.maximum((-d + r + R) * (d + r - R) * (d - r + R) * (d + r + R), 0)
    a = r * r * np.arccos(x1) + R * R * np.arccos(x2) - 0.5 * np.sqrt(k)
    return np.where(apart, 0.0, np.where(inside, full, a))


def coarse(u, r, n=96):
    c = 2 * r
    lam = np.log(1 / (1 - u)) / (np.pi * r * r)
    m = int(np.ceil(n / c)) + 2
    out = np.ones((n, n))
    ys, xs = np.mgrid[0:n, 0:n]
    xs = xs + 0.5; ys = ys + 0.5
    for i in range(-1, m):
        for j in range(-1, m):
            N = rng.poisson(lam * c * c)
            for _ in range(N):
                x, y = (i + rng.uniform()) * c, (j + rng.uniform()) * c
                if x < -r - 1 or x > n + r + 1 or y < -r - 1 or y > n + r + 1:
                    continue
                d = np.sqrt((xs - x) ** 2 + (ys - y) ** 2)
                out *= 1 - lens(d, r)
    return 1 - out


print('   u     r   | truth mean  sd  | fine mean  sd  | coarse mean  sd')
for u in (0.3, 0.6, 0.9):
    for r in (0.05, 0.1, 0.2, 0.25, 0.35, 0.5, 1.0, 2.0):
        t = truth(u, r)
        f = fine(u, r) if r < 0.6 else None
        c = coarse(u, r) if r >= 0.2 else None
        fs = '{:.3f} {:.3f}'.format(f.mean(), f.std()) if f is not None else '    -      -'
        cs = '{:.3f} {:.3f}'.format(c.mean(), c.std()) if c is not None else '    -      -'
        print('{:4.1f} {:5.2f}  | {:.3f} {:.3f} | {} | {}'.format(u, r, t.mean(), t.std(), fs, cs))
