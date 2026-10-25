"""DEV ONLY. Pixel sort looks, offline, on the test clips (private/assets/ready), before any TouchDesigner: which
spans read well (Brightness between two thresholds, Edges, Depth or a mask, Whole lines cut at random), what to sort
by, how lines at an angle look as digital lines (each pixel in exactly one line, no resampling), and how much the
spans flicker from one input frame to the next, with and without hysteresis.

    uv run --with opencv-python-headless --with numpy dev/protos/pixel_sort/proto.py dev/out/pixel_sort_proto/r1

Writes one PNG per clip and look at a moment, a contact sheet per clip, and flicker.txt: for each look, how often a
pixel's brightness swings by 0.1 or more and back, per second at the clip's 16 fps (the input's own rate beside it).
"""
import math
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ASSETS = os.path.join(ROOT, 'private', 'assets', 'ready')
W, H = 640, 360
FPS_IN = 16.0
LUMA = np.array([0.0722, 0.7152, 0.2126], np.float32)  # BGR


def load(name, n=None):
    cap = cv2.VideoCapture(os.path.join(ASSETS, name + '.mp4'))
    frames = []
    while n is None or len(frames) < n:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    return np.stack(frames)


def lines(angle):
    """Each pixel's line and its position along it, for sorting toward angle (degrees counterclockwise from the right,
    y up). Digital lines: within 45 degrees of horizontal a line has one pixel per column (line = y - round(x tan)),
    else one per row. The position grows in the sort's direction."""
    yy, xx = np.mgrid[0:H, 0:W]
    y = H - 1 - yy  # y up, as TouchDesigner has it
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    if abs(c) >= abs(s):
        line = y - np.round(xx * (s / c)).astype(int)
        pos = xx if c > 0 else W - 1 - xx
    else:
        line = xx - np.round(y * (c / s)).astype(int)
        pos = y if s > 0 else H - 1 - y
    return line, pos


def hsv(img):
    h = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)  # float: H 0-360, S 0-1, V 0-1
    return h[..., 0] / 360.0, h[..., 1], h[..., 2]


def value(img, by):
    if by == 'brightness':
        return img @ LUMA
    hh, ss, vv = hsv(img)
    return {'hue': hh, 'saturation': ss}[by]


def hash01(x, y, seed=0):
    """lowbias32 (Chris Wellons, hash-prospector, public domain) of the pixel, 0-1."""
    v = (x.astype(np.uint64) * 1973 + y.astype(np.uint64) * 9277 + seed * 26699) & 0xFFFFFFFF
    v ^= v >> 16
    v = (v * 0x7feb352d) & 0xFFFFFFFF
    v ^= v >> 15
    v = (v * 0x846ca68b) & 0xFFFFFFFF
    v ^= v >> 16
    return v.astype(np.float64) / 4294967296.0


YY, XX = np.mgrid[0:H, 0:W]


def spans(img, kind, lo, hi, depth=None, prev=None, hyst=0.0, edge=0.25, length=0):
    """Which pixels sort (in a span) and where lines are cut. Brightness: luma between lo and hi. Edges: away from the
    picture's edges (gradient above edge). Depth: depth between lo and hi. Whole: everything. Hysteresis: a pixel in
    a span last frame stays in until it leaves the range by hyst; one outside joins only once hyst inside it."""
    lum = cv2.GaussianBlur(img @ LUMA, (3, 3), 0)
    if kind == 'brightness' or kind == 'depth':
        v = lum if kind == 'brightness' else depth
        if prev is None or hyst == 0:
            m = (v >= lo) & (v <= hi)
        else:
            m_in = (v >= lo - hyst) & (v <= hi + hyst)
            m_out = (v >= lo + hyst) & (v <= hi - hyst)
            m = np.where(prev, m_in, m_out)
    elif kind == 'edges':
        gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3) / 4
        gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3) / 4
        g = np.hypot(gx, gy)
        if prev is None or hyst == 0:
            m = g < edge
        else:
            m = np.where(prev, g < edge + hyst, g < edge - hyst)
    else:
        m = np.ones((H, W), bool)
    cut = hash01(XX, YY) < (1.0 / length) if length else np.zeros((H, W), bool)
    return m, cut


def sort(img, m, cut, angle, by, amount=1.0):
    line, pos = lines(angle)
    v = value(img, by)
    q = np.clip(np.round(v * 1023), 0, 1023).astype(np.int64)
    L, P = line.ravel(), pos.ravel()
    order = np.lexsort((P, L))  # pixels in line order
    Lo, Po, Mo, Co = L[order], P[order], m.ravel()[order], cut.ravel()[order]
    first = np.ones_like(Mo)
    first[1:] = Lo[1:] != Lo[:-1]
    prev_m = np.zeros_like(Mo)
    prev_m[1:] = Mo[:-1]
    brk = first | ~Mo | (Mo & ~prev_m) | Co
    idx = np.arange(len(order))
    start = np.maximum.accumulate(np.where(brk, idx, 0))
    key_sorted = np.lexsort((idx, q.ravel()[order], start))  # within each span by value, stable
    src = order[key_sorted]
    out = img.reshape(-1, 3).copy()
    if amount >= 1:
        out[order] = img.reshape(-1, 3)[src]
    else:
        # Amount: each pixel reads from part of the way to where its sorted color came from, along its line.
        come = np.empty_like(idx)
        come[idx] = key_sorted  # line-order index each slot's color comes from
        mid = np.round(idx + (come - idx) * amount).astype(int)
        out[order] = img.reshape(-1, 3)[order[mid]]
    return out.reshape(H, W, 3)


def flicker(seq):
    """Swings of 0.1 or more in brightness that come back (a flash's two halves), per pixel per second, averaged."""
    lum = np.stack([f @ LUMA for f in seq])
    d = np.diff(lum, axis=0)
    big = np.abs(d) >= 0.1
    s = np.sign(d) * big
    # a reversal: a big swing one way followed (at the next big swing) by one the other way
    count = np.zeros(lum.shape[1:])
    last = np.zeros(lum.shape[1:])
    for k in range(len(d)):
        rev = (s[k] != 0) & (last != 0) & (s[k] != last)
        count += rev
        last = np.where(s[k] != 0, s[k], last)
    return float(count.mean() * FPS_IN / len(d))


LOOKS = [
    # name, spans, lo, hi, angle, by, extra
    ('bright_down', 'brightness', 0.25, 0.8, 270, 'brightness', {}),
    ('bright_right', 'brightness', 0.25, 0.8, 0, 'brightness', {}),
    ('bright_30', 'brightness', 0.25, 0.8, 30, 'brightness', {}),
    ('edges_down', 'edges', 0, 0, 270, 'brightness', {'edge': 0.08}),
    ('whole_cut_right', 'whole', 0, 0, 0, 'brightness', {'length': 120}),
    ('bright_hue_down', 'brightness', 0.25, 0.8, 270, 'hue', {}),
    ('depth_up', 'depth', 0.5, 1.0, 90, 'brightness', {}),
    ('bright_down_len80', 'brightness', 0.25, 0.8, 270, 'brightness', {'length': 80}),
    ('bright_down_amt05', 'brightness', 0.25, 0.8, 270, 'brightness', {'amount': 0.5}),
]
CLIPS = ['b1_dancer', 'b2_plaza', 'd3b_flowers', 'b4_koi', 'b3_headlights', 'd5_silk', 'd1_skyline']
DEPTH = {'b1_dancer': 'b1_dancer_depth', 'a2_silhouette': 'a2_silhouette_depth', 'd2_walker': 'd2_walker_depth'}


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rep = []
    for clip in CLIPS:
        frames = load(clip, 48)
        depth = load(DEPTH[clip], 48)[..., 0] if clip in DEPTH else None
        if depth is None:
            depth = np.stack([cv2.GaussianBlur(f @ LUMA, (9, 9), 0) for f in frames])
        tiles = []
        rep.append('{}: input {:.3f}'.format(clip, flicker(frames)))
        for name, kind, lo, hi, angle, by, extra in LOOKS:
            seq, prev = [], None
            seqh, prevh = [], None
            for i, f in enumerate(frames):
                m, cut = spans(f, kind, lo, hi, depth[i], None, 0, extra.get('edge', 0.25), extra.get('length', 0))
                seq.append(sort(f, m, cut, angle, by, extra.get('amount', 1.0)))
                mh, cut = spans(f, kind, lo, hi, depth[i], prevh, 0.04, extra.get('edge', 0.25), extra.get('length', 0))
                prevh = mh
                seqh.append(sort(f, mh, cut, angle, by, extra.get('amount', 1.0)))
            rep.append('  {:20s} flicker {:.3f}, with hysteresis 0.04 {:.3f}'.format(name, flicker(seq), flicker(seqh)))
            im8 = (np.clip(seq[24], 0, 1) * 255).astype(np.uint8)
            cv2.putText(im8, name, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imwrite(os.path.join(out_dir, '{}_{}.png'.format(clip, name)), im8)
            tiles.append(cv2.resize(im8, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
        live = (np.clip(frames[24], 0, 1) * 255).astype(np.uint8)
        tiles.insert(0, cv2.resize(live, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
        while len(tiles) % 5:
            tiles.append(np.zeros_like(tiles[0]))
        sheet = np.vstack([np.hstack(tiles[i:i + 5]) for i in range(0, len(tiles), 5)])
        cv2.imwrite(os.path.join(out_dir, '{}_sheet.png'.format(clip)), sheet)
        print('\n'.join(rep[-len(LOOKS) - 1:]), flush=True)
    open(os.path.join(out_dir, 'flicker.txt'), 'w').write('\n'.join(rep) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
