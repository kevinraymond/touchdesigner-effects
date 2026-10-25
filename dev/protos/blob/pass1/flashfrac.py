"""DEV ONLY (blob_track pass 1): a finer reading of recordings like dev/flash.py's than the area
rule's 0.5 steps: for k = 2, 3, 4 transitions in a second, the largest fraction of a window a third
of the screen wide and high whose cells reach k (WCAG's area rule fails at 25%).
    uv run --with numpy dev/protos/blob/pass1/flashfrac.py <folder>
"""
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
import flashcount as fc  # noqa: E402

for path in sorted(glob.glob(os.path.join(sys.argv[1], '*.npz'))):
    d = np.load(path)
    t = d['t'].astype(np.float64)
    lum = d['lum'].astype(np.float64).reshape(len(t), -1)
    starts = t[t <= t[-1] - 1.0]
    cells = fc.per_second([fc.transitions(t, lum[:, c], fc.LUM_STEP, fc.DARKER_MAX) for c in range(lum.shape[1])],
                          starts)
    win_h, win_w = fc.GRID_H // 3, fc.GRID_W // 3
    grids = cells.T.reshape(-1, fc.GRID_H, fc.GRID_W)
    out = []
    for k in (2, 3, 4):
        hit = (grids >= k).astype(np.int32)
        s = np.pad(hit.cumsum(1).cumsum(2), ((0, 0), (1, 0), (1, 0)))
        rect = s[:, win_h:, win_w:] - s[:, :-win_h, win_w:] - s[:, win_h:, :-win_w] + s[:, :-win_h, :-win_w]
        out.append(rect.max() / float(win_h * win_w))
    print('{:<24} k>=2 {:5.1%}  k>=3 {:5.1%}  k>=4 {:5.1%}'.format(os.path.basename(path)[:-4], *out))
