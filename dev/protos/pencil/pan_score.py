"""DEV ONLY. Score dev/protos/pencil/pan.py's takes: the horizontal shift that best lines up the output's two moments
(the mean squared difference over the middle of the frame, for shifts around 0 and around the pan's own), for the
output and for the input. If the strokes travel with the picture, the output lines up at the pan's shift as well as
the input does; if they stay on the screen, the best match at the pan's shift is worse.
    uv run --with numpy --with pillow dev/protos/pencil/pan_score.py dev/out/pencil/p1 [dev/out/pencil/p2 ...]"""
import os
import sys

import numpy as np
from PIL import Image


def gray(p):
    return np.asarray(Image.open(p).convert('L'), dtype=np.float32) / 255


for d in sys.argv[1:]:
    pan = [float(open(os.path.join(d, 'tx_{}.txt'.format(i))).read()) for i in (0, 1)]
    # The capture's own frames may land a frame or two from the stamps: search around the stamped shift.
    want = pan[1] - pan[0]
    for name in ('input', 'out'):
        a, b = gray(os.path.join(d, name + '_0.png')), gray(os.path.join(d, name + '_1.png'))
        h, w = a.shape
        y0, y1, x0, x1 = h // 4, 3 * h // 4, w // 4, 3 * w // 4
        # TouchDesigner's +x is to the right, and PNG rows run top down: a pan right moves content to larger x.
        errs = {s: float(np.mean((a[y0:y1, x0:x1] - b[y0:y1, x0 + s:x1 + s]) ** 2))
                for s in range(-20, int(want) + 20)}
        best = min(errs, key=errs.get)
        print('{:<28} {:<6} pan {:6.1f} px  best shift {:4d} (error {:.5f}), at 0 {:.5f}, at the pan {:.5f}'.format(
            d, name, want, best, errs[best], errs[0], errs[int(round(want))]))
