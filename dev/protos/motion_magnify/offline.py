"""DEV ONLY. Motion Magnify's method outside TouchDesigner, in numpy and OpenCV, as it was first tried: run it on a
clip and write the input beside the output at a few frames, and a row of both over time (a time slice, time running
down), to see what grows:

    uv run --with numpy --with opencv-python-headless dev/protos/motion_magnify/offline.py b5_night_field \\
        --amount 3 --timing 1 --row 430 --out dev/out/motion_magnify/offline

Each frame, at a quarter of 1280 x 720 as the effect works: the optical flow from the last frame (Farneback here, the
effect's is Lucas-Kanade), the displacement taken from where the content was and this frame's motion added
(semi-Lagrangian), leaked toward 0 (corner at Timing / 2) and eased (corner at 2 x Timing), spread (sigma 3 px at a
quarter, 12 at 720), made Amount times larger, held back where it would fold the picture (stretch over 0.6 px a pixel,
counted 3 px around), and the full-size frame taken from that far back.
"""

import argparse
import math
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
SIZE, QUARTER = (1280, 720), (320, 180)
FOLD, REACH, SPREAD = 0.6, 3.0, 3.0


def frames(path):
    cap = cv2.VideoCapture(path)
    fps, out = cap.get(cv2.CAP_PROP_FPS), []
    while True:
        ok, f = cap.read()
        if not ok:
            return out, fps
        out.append(cv2.resize(f, SIZE, interpolation=cv2.INTER_AREA))


def sample(img, x, y):
    return cv2.remap(img, x, y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def guard(a):
    """a scaled down wherever its change from pixel to pixel would fold the warp (guard.glsl)."""
    g = np.zeros(a.shape[:2], np.float32)
    for c in range(2):
        for dx, dy in ((1, 0), (0, 1)):
            g = np.maximum(g, np.abs(cv2.Sobel(a[..., c], cv2.CV_32F, dx, dy, ksize=3) / 8))
    g = cv2.GaussianBlur(cv2.dilate(g, np.ones((9, 9), np.uint8)), (0, 0), REACH / 2)
    return a * np.minimum(1.0, FOLD / np.maximum(g, 1e-6))[..., None]


def magnify(fr, fps, amount, timing):
    w, h = QUARTER
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    big_x, big_y = np.meshgrid(np.arange(SIZE[0], dtype=np.float32), np.arange(SIZE[1], dtype=np.float32))
    dt, leak, ease = 1 / fps, 1 / (2 * math.pi * timing / 2), 1 / (2 * math.pi * timing * 2)
    d = np.zeros((h, w, 2), np.float32)
    s = np.zeros_like(d)
    small = lambda f: cv2.cvtColor(cv2.resize(f, QUARTER, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    prev, out = small(fr[0]), [fr[0]]
    for f in fr[1:]:
        cur = small(f)
        back = cv2.calcOpticalFlowFarneback(cur, prev, None, 0.5, 3, 13, 3, 5, 1.1, 0)   # here -> where it was
        x, y = gx + back[..., 0], gy + back[..., 1]
        d = (sample(d, x, y) - back) * math.exp(-dt / leak)
        s = sample(s, x, y)
        s += (d - s) * (1 - math.exp(-dt / ease))
        a = guard(amount * cv2.GaussianBlur(s, (0, 0), SPREAD))
        a = cv2.resize(a, SIZE, interpolation=cv2.INTER_LINEAR) * (SIZE[0] / w)
        out.append(sample(f, big_x - a[..., 0], big_y - a[..., 1]))
        prev = cur
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip', help='private/assets/ready/<clip>.mp4')
    ap.add_argument('--amount', type=float, default=3.0)
    ap.add_argument('--timing', type=float, default=1.0, help='Hz')
    ap.add_argument('--row', type=int, default=360, help='the row of the time slice, at 720 high')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'motion_magnify', 'offline'))
    a = ap.parse_args()
    fr, fps = frames(os.path.join(READY, a.clip + '.mp4'))
    mag = magnify(fr, fps, a.amount, a.timing)
    os.makedirs(a.out, exist_ok=True)
    picks = [len(fr) * k // 4 for k in (1, 2, 3)]
    pairs = [np.hstack([cv2.resize(fr[i], (640, 360)), cv2.resize(mag[i], (640, 360))]) for i in picks]
    cv2.imwrite(os.path.join(a.out, a.clip + '_frames.jpg'), np.vstack(pairs))
    rows = [cv2.resize(np.stack([f[a.row] for f in v]), (640, 240)) for v in (fr, mag)]
    cv2.imwrite(os.path.join(a.out, a.clip + '_rows.jpg'), np.vstack([rows[0], np.full((6, 640, 3), 255, np.uint8),
                                                                       rows[1]]))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
