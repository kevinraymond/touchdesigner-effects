"""DEV ONLY. Count flashes the way WCAG 2.3.1 defines them, in recordings dev/flash.py makes
inside TouchDesigner, and say whether each effect keeps its Flashing promise:

    uv run --with numpy dev/flashcount.py dev/out/flash      # report on every recording there
    uv run --with numpy dev/flashcount.py --selftest         # check the counting on made-up input
    uv run --with numpy --with pillow dev/flashcount.py dev/out/flash --where   # and maps

A recording is <name>.npz: t (seconds, one per frame) and two grids per frame, GRID_H x GRID_W
cells of the output averaged in linear light: lum, its relative luminance (0..1), and red, the
saturated-red measure WCAG uses ((R - G - B) x 320 where R / (R + G + B) >= 0.8, else 0).

The definitions (WCAG 2.2, Understanding SC 2.3.1, "general flash and red flash thresholds"):
- a transition is a change in relative luminance of at least 0.1 where the darker side is below
  0.8 (red: a change of more than 20 in the red measure); turning points are found with that much
  hysteresis, so small wobble never counts;
- a flash is a pair of opposing transitions, so flashes in a second = transitions / 2;
- it only matters over an area: flashing that covers at least a quarter of any 10-degree field
  of view, which WCAG puts at 341 x 256 px on a 1024 x 768 screen: a third of the screen's width
  and height. So a second fails when, inside some window a third of the screen wide and high, a
  quarter of the cells flash more than 3 times.

Per recording it reports the worst second for the whole picture (the most intuitive number), for
WCAG's area rule (the one that decides), for red, and for the single worst cell (informative: a
small area may flash faster and still pass). The checks, over the area rule (luminance or red,
whichever is worse): every recording at most 3 a second, WCAG's limit; and each Flashing setting
keeps its promise on top of what the clip does by itself (clip_source.npz, the baseline): Off
adds nothing, Calm at most 1 a second. Pass --where to also save <name>_where.png beside each
recording: each cell's worst second, from dark (none) to orange (6 or more a second).
"""

import argparse
import glob
import os
import sys

import numpy as np

GRID_W, GRID_H = 64, 36   # cells of the output (20 x 20 px each at 1280 x 720)
LUM_STEP, DARKER_MAX = 0.1, 0.8
RED_STEP = 20.0
LIMIT = 3.0               # WCAG: no more than three flashes in any one second
AREA = 0.25               # of a window a third of the screen wide and high
PROMISE = {'off': 0.0, 'calm': 1.0, 'wcag': 3.0}   # flashes a second the effect may add to its input
SLACK = 0.5                # measuring noise allowed on top of the baseline


def transitions(t, v, step, darker_max=None):
    """Times of the transitions in one cell's series v (sampled at times t): the swings between
    turning points found with `step` of hysteresis, each at least `step`, timed where the swing
    crosses its midpoint (when the change happens, wherever the extremes sit). With darker_max, a
    swing whose darker end is at or above it is dropped."""
    v = np.asarray(v, dtype=np.float64)
    points = []                     # (index, value) of confirmed turning points
    lo = hi = v[0]
    lo_i = hi_i = 0
    direction = 0
    for i, x in enumerate(v):
        if direction == 0:
            if x < lo:
                lo, lo_i = x, i
            if x > hi:
                hi, hi_i = x, i
            if x - lo >= step:
                points.append((lo_i, lo))
                direction, hi, hi_i = 1, x, i
            elif hi - x >= step:
                points.append((hi_i, hi))
                direction, lo, lo_i = -1, x, i
        elif direction == 1:
            if x > hi:
                hi, hi_i = x, i
            elif hi - x >= step:
                points.append((hi_i, hi))
                direction, lo, lo_i = -1, x, i
        else:
            if x < lo:
                lo, lo_i = x, i
            elif x - lo >= step:
                points.append((lo_i, lo))
                direction, hi, hi_i = 1, x, i
    # The swing in progress at the end counts once it has gone far enough.
    if direction == 1 and hi - points[-1][1] >= step:
        points.append((hi_i, hi))
    elif direction == -1 and points[-1][1] - lo >= step:
        points.append((lo_i, lo))
    out = []
    for (ia, a), (ib, b) in zip(points, points[1:]):
        if darker_max is not None and min(a, b) >= darker_max:
            continue
        seg = v[ia:ib + 1]
        crossed = np.nonzero(seg >= (a + b) / 2 if b > a else seg <= (a + b) / 2)[0]
        out.append(t[ia + crossed[0]])
    return np.array(out)


def per_second(times_per_cell, starts):
    """counts[c, w]: transitions of cell c in the second starting at starts[w]."""
    counts = np.zeros((len(times_per_cell), len(starts)), dtype=np.int32)
    for c, times in enumerate(times_per_cell):
        if len(times):
            counts[c] = np.searchsorted(times, starts + 1.0) - np.searchsorted(times, starts)
    return counts


def area_rate(counts):
    """The most transitions a second reached by at least AREA of the cells in some window a third
    of the screen wide and high, over every second: the number WCAG's area rule judges."""
    win_h, win_w = max(GRID_H // 3, 1), max(GRID_W // 3, 1)
    need = AREA * win_h * win_w
    best = 0
    grids = counts.T.reshape(-1, GRID_H, GRID_W)
    for k in range(1, int(counts.max()) + 1 if counts.size else 1):
        hit = (grids >= k).astype(np.int32)
        s = np.pad(hit.cumsum(1).cumsum(2), ((0, 0), (1, 0), (1, 0)))
        rect = s[:, win_h:, win_w:] - s[:, :-win_h, win_w:] - s[:, win_h:, :-win_w] + s[:, :-win_h, :-win_w]
        if (rect >= need).any():
            best = k
        else:
            break
    return best


def measure(t, lum, red):
    """Worst flashes per second in one recording: whole picture, area rule, red (area rule), worst cell."""
    t = np.asarray(t, dtype=np.float64)
    lum = np.asarray(lum, dtype=np.float64).reshape(len(t), -1)
    red = np.asarray(red, dtype=np.float64).reshape(len(t), -1)
    starts = t[t <= t[-1] - 1.0] if t[-1] - t[0] >= 1.0 else t[:1]
    whole = per_second([transitions(t, lum.mean(1), LUM_STEP, DARKER_MAX)], starts).max()
    cells = per_second([transitions(t, lum[:, c], LUM_STEP, DARKER_MAX) for c in range(lum.shape[1])], starts)
    reds = per_second([transitions(t, red[:, c], RED_STEP) for c in range(red.shape[1])], starts)
    return {'whole': whole / 2, 'area': area_rate(cells) / 2, 'red': area_rate(reds) / 2,
            'cell': cells.max() / 2, 'seconds': t[-1] - t[0]}


def where(path, t, lum):
    """Save a map of each cell's worst second (flashes a second), dark none to orange 6 or more."""
    from PIL import Image
    t, lum = np.asarray(t, dtype=np.float64), np.asarray(lum, dtype=np.float64).reshape(len(t), -1)
    starts = t[t <= t[-1] - 1.0]
    cells = per_second([transitions(t, lum[:, c], LUM_STEP, DARKER_MAX) for c in range(lum.shape[1])], starts)
    # Rows come from TouchDesigner's numpyArray(), bottom row first: flip to look like the picture.
    worst = np.clip(cells.max(1).reshape(GRID_H, GRID_W)[::-1] / 2 / 6.0, 0, 1)
    rgb = np.stack([worst, worst * 0.55, (1 - worst) * 0.3], -1)
    Image.fromarray((rgb * 255).astype(np.uint8)).resize((GRID_W * 8, GRID_H * 8), Image.NEAREST).save(path)


def report(folder, maps=False):
    results = {}
    for path in sorted(glob.glob(os.path.join(folder, '*.npz'))):
        data = np.load(path)
        name = os.path.splitext(os.path.basename(path))[0]
        results[name] = measure(data['t'], data['lum'], data['red'])
        if maps:
            where(os.path.join(folder, name + '_where.png'), data['t'], data['lum'])
    base = results.get('clip_source')
    baseline = max(base['area'], base['red']) if base else 0.0
    lines = ['{:<28} {:>6} {:>6} {:>6} {:>6}  {}'.format('recording (flashes/s, worst second)', 'whole',
                                                        'area', 'red', 'cell', 'verdict')]
    ok_all = True
    for name, m in results.items():
        setting = name.rsplit('_', 1)[-1]
        worst = max(m['area'], m['red'])
        limit = LIMIT
        why = 'WCAG'
        if setting in PROMISE and name != 'clip_source':
            promised = baseline + PROMISE[setting] + (SLACK if setting != 'wcag' else 0.0)
            if promised < limit:
                limit, why = promised, 'clip {:g} + {} adds at most {:g}'.format(baseline, setting, PROMISE[setting])
        ok = worst <= limit
        ok_all &= ok
        lines.append('{:<28} {:>6.1f} {:>6.1f} {:>6.1f} {:>6.1f}  {} (at most {:g}: {})  [{:.0f} s]'.format(
            name, m['whole'], m['area'], m['red'], m['cell'], 'ok' if ok else 'FAIL', limit, why, m['seconds']))
    text = '\n'.join(lines) + '\n'
    with open(os.path.join(folder, 'report.txt'), 'w') as f:
        f.write(text)
    print(text, end='')
    return ok_all


def selftest():
    """Made-up recordings with known answers: each line must come out as stated."""
    fps, seconds = 60, 4
    t = np.arange(fps * seconds) / fps
    flat = np.full((len(t), GRID_H, GRID_W), 0.2)

    def square(hz, lo=0.1, hi=0.9):
        return np.where((t * hz * 2).astype(int) % 2 == 0, lo, hi)[:, None, None]

    def case(lum, red=None):
        return measure(t, lum, np.zeros_like(lum) if red is None else red)

    checks = []
    m = case(flat + 0 * square(1))
    checks.append(('steady picture: no flashes', m['area'] == 0 and m['whole'] == 0))
    m = case(flat * 0 + square(2))
    checks.append(('whole screen at 2 Hz: 2 a second, passes', m['area'] == 2 and m['whole'] == 2))
    m = case(flat * 0 + square(5))
    checks.append(('whole screen at 5 Hz: 5 a second, fails', m['area'] == 5))
    m = case(flat * 0 + square(5, 0.85, 0.98))
    checks.append(('5 Hz but the darker side above 0.8: no flashes', m['area'] == 0))
    m = case(flat * 0 + square(5, 0.4, 0.45))
    checks.append(('5 Hz swing of 0.05: under the 0.1 step, no flashes', m['area'] == 0))
    small = flat.copy()
    small[:, :4, :6] = square(10)[:, :, :1]    # 24 of 2304 cells: about 1 percent of the screen
    m = case(small)
    checks.append(('10 Hz in 1 percent of the screen: passes the area rule', m['area'] == 0 and m['cell'] == 10))
    big = flat.copy()
    big[:, :12, :21] = square(10)[:, :, :1]    # a whole third-by-third window
    m = case(big)
    checks.append(('10 Hz over a third-by-third window: fails', m['area'] == 10 and m['whole'] < 10))
    red = np.zeros_like(flat) + np.where((t * 10).astype(int) % 2 == 0, 0.0, 300.0)[:, None, None]
    m = case(flat, red)
    checks.append(('saturated red at 5 Hz: red fails', m['red'] == 5 and m['area'] == 0))
    m = case(flat * 0 + square(1) + 0.03 * np.sin(t * 2 * np.pi * 20)[:, None, None])
    checks.append(('1 Hz with a small 20 Hz ripple on top: 1 a second', m['area'] == 1))
    for label, ok in checks:
        print('{} {}'.format('ok   ' if ok else 'MISS ', label))
    print('ALL OK' if all(ok for _, ok in checks) else 'FAILED')
    return all(ok for _, ok in checks)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', nargs='?')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--where', action='store_true', help='also save a map of where each recording flashes')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.folder:
        ap.error('give a folder of recordings, or --selftest')
    sys.exit(0 if report(a.folder, a.where) else 1)
