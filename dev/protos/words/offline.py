"""DEV ONLY. Words' layouts outside TouchDesigner, in numpy, OpenCV and Pillow, before anything is built (board #4673).

    uv run --with numpy --with opencv-python-headless --with pillow dev/protos/words/offline.py b1_dancer \\
        --layout cloud --out dev/out/words/offline

The layout is Wordle's (Feinberg 2008; Viegas, Wattenberg and Feinberg, InfoVis 2009) on a grid of cells: words go in
one at a time, each taking the best free spot where its box fits, largest sizes first. A box fits where every cell it
covers is free and allowed: an occupancy grid with a summed-area table answers that for every spot at once.

  cloud     words only inside the subject (the depth map's near part, else a brightness key); among the spots where a
            word fits, the one deepest inside the subject's distance field (ShapeWordle, Wang et al. TVCG 2020, spirals
            out from the shape's deepest point along its distance field);
  portrait  the whole frame; a word of size s may cover only cells whose detail allows s (summed-area tests after Xu
            and Kaplan 2007), so big words take flat areas and small ones the features; each word colored by the
            picture under it.

Video (ours, after EdWordle, Wang et al. TVCG 2018, which re-places only the words that collide): words stay where they
are from frame to frame, carried by the optical flow; a word that leaves its region, collides or no longer fits the
detail fades out, and free space fills with new words a few at a time.
"""

import argparse
import os
import re
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
W, H = 1280, 720
CELL = 8
GW, GH = W // CELL, H // CELL
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

TEXT = """I sing the body electric, The armies of those I love engirth me and I engirth them, They will not let
me off till I go with them, respond to them, And discorrupt them, and charge them full with the charge of the soul.
Was it doubted that those who corrupt their own bodies conceal themselves? And if those who defile the living are as
bad as they who defile the dead? And if the body does not do fully as much as the soul? And if the body were not the
soul, what is the soul? The love of the body of man or woman balks account, the body itself balks account, That of the
male is perfect, and that of the female is perfect. The expression of the face balks account, But the expression of a
well-made man appears not only in his face, It is in his limbs and joints also, it is curiously in the joints of his
hips and wrists, It is in his walk, the carriage of his neck, the flex of his waist and knees, dress does not hide him,
The strong sweet quality he has strikes through the cotton and broadcloth, To see him pass conveys as much as the best
poem, perhaps more, You linger to see his back, and the back of his neck and shoulder-side. The sprawl and fulness of
babes, the bosoms and heads of women, the folds of their dress, their style as we pass in the street, the contour of
their shape downwards, The swimmer naked in the swimming-bath, seen as he swims through the transparent green-shine, or
lies with his face up and rolls silently to and from the heave of the water, The bending forward and backward of
rowers in row-boats, the horseman in his saddle, Girls, mothers, house-keepers, in all their performances"""

STOP = set('i the of those me and them they will not let off till go with to a an is it as if who are do does were what '
           'or that but in his he has be we their its also only up our on at by so this than'.split())


def words_from(text, stop=True):
    """Words by how often they appear (Wordle's sizes), ties by first appearance; stop words out."""
    toks = [t.strip(".,;:?!'\"").lower() for t in text.split()]
    toks = [t for t in toks if t and not (stop and t in STOP)]
    count, first = {}, {}
    for i, t in enumerate(toks):
        count[t] = count.get(t, 0) + 1
        first.setdefault(t, i)
    return sorted(count, key=lambda t: (-count[t], first[t])), toks


def frames(clip, n, fps=16):
    cap = cv2.VideoCapture(os.path.join(READY, clip + '.mp4'))
    src = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        src.append(cv2.cvtColor(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
                   .astype(np.float32) / 255)
    return [src[k % len(src)] for k in range(n)]


class Glyphs:
    """Each word's ink box at a reference size, in units of its height (the box the layout packs)."""

    def __init__(self, words, upper):
        self.ref = 200
        self.font = ImageFont.truetype(FONT, self.ref)
        self.upper = upper
        self.box = {}
        for w in words:
            s = w.upper() if upper else w
            l, t, r, b = self.font.getbbox(s)
            self.box[w] = (l, t, r, b)

    def aspect(self, w):
        l, t, r, b = self.box[w]
        return (r - l) / (b - t)

    def draw(self, img, w, x, y, h, color):
        """Draw word w with its ink box at (x, y), h pixels tall."""
        l, t, r, b = self.box[w]
        size = max(4, int(round(self.ref * h / (b - t))))
        f = ImageFont.truetype(FONT, size)
        k = size / self.ref
        ImageDraw.Draw(img).text((x - l * k, y - t * k), w.upper() if self.upper else w, font=f, fill=color)


def sat(a):
    s = np.zeros((a.shape[0] + 1, a.shape[1] + 1), np.int32)
    s[1:, 1:] = a.cumsum(0).cumsum(1)
    return s


def box_sum(s, bw, bh):
    """Sum over every bw x bh box, indexed by its top-left cell."""
    return s[bh:, bw:] - s[:-bh, bw:] - s[bh:, :-bw] + s[:-bh, :-bw]


def layout(region, score, allowed, glyphs, order, sizes, max_words, placed=None, per_frame=None):
    """Greedy: for each word in turn, the largest size that fits anywhere, at the best-scoring spot.

    region: GH x GW bool, cells words may cover. score: GH x GW float, higher is better (for a box, at its center).
    allowed: list per size of GH x GW bool (cells a word of that size may cover), or None.
    """
    occ = ~region.copy()
    out = [] if placed is None else list(placed)
    for p in out:
        x, y, bw, bh = p['cell']
        occ[y:y + bh, x:x + bw] = True
    i = 0 if placed is None else len(placed)
    added = 0
    misses = 0
    while len(out) < max_words and (per_frame is None or added < per_frame):
        w = order[i % len(order)]
        i += 1
        a = glyphs.aspect(w)
        best = None
        for si, h in enumerate(sizes):
            bh = max(1, int(round(h / CELL)))
            bw = max(1, int(np.ceil(h * a / CELL)))
            if bw >= GW or bh >= GH:
                continue
            block = occ if allowed is None else (occ | ~allowed[si])
            free = box_sum(sat(block.astype(np.int32)), bw, bh) == 0
            if not free.any():
                continue
            cy = np.arange(free.shape[0])[:, None] + bh // 2
            cx = np.arange(free.shape[1])[None, :] + bw // 2
            sc = np.where(free, score[cy, cx], -np.inf)
            k = np.argmax(sc)
            y, x = divmod(k, free.shape[1])
            best = (x, y, bw, bh, h)
            break
        if best is None:
            misses += 1
            if misses > len(order):
                break
            continue
        misses = 0
        x, y, bw, bh, h = best
        occ[y:y + bh, x:x + bw] = True
        out.append({'word': w, 'cell': (x, y, bw, bh), 'h': h})
        added += 1
    return out


def render(picture, placed, glyphs, backdrop=0.0, boost=1.4):
    """Words over a dark backdrop, each pixel of a word colored by the picture under it."""
    ink = Image.new('L', (W, H), 0)
    for p in placed:
        x, y, bw, bh = p['cell']
        # the word centered in its box (the box rounds the word up to whole cells)
        h = p['h']
        ww = h * glyphs.aspect(p['word'])
        glyphs.draw(ink, p['word'], x * CELL + (bw * CELL - ww) / 2, y * CELL + (bh * CELL - h) / 2, h, 255)
    m = np.asarray(ink, np.float32)[..., None] / 255
    col = np.clip(picture * boost, 0, 1)
    out = col * m + picture * backdrop * (1 - m)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def stand_out(d, far=0.16, by=0.1):
    """lib depth_find.glsl in numpy: nearer than far, and something at least by farther on both sides in its row
    (the farthest reading left and right, each the nearest of three side by side)."""
    m3 = np.maximum(np.maximum(np.roll(d, 1, 1), d), np.roll(d, -1, 1))
    left = np.minimum.accumulate(m3, axis=1)
    left = np.concatenate([np.full((d.shape[0], 1), 2.0), left[:, :-1]], 1)
    right = np.minimum.accumulate(m3[:, ::-1], axis=1)[:, ::-1]
    right = np.concatenate([right[:, 1:], np.full((d.shape[0], 1), 2.0)], 1)
    stand = np.where((left > 1.5) | (right > 1.5), 0, d - np.maximum(left, right))
    return (d > far) & (stand > by)


def subject_mask(clip, k, cells=True):
    """The subject: what stands out in the depth map when the clip has one, else a brightness key."""
    path = os.path.join(READY, clip + '_depth.mp4')
    if os.path.exists(path):
        d = frames(clip + '_depth', k + 1)[k].mean(2)
        d = cv2.resize(d, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        m = stand_out(d).astype(np.float32)
    else:
        d = cv2.GaussianBlur(frames(clip, k + 1)[k].mean(2), (0, 0), 6)
        m = (d > 0.5).astype(np.float32)
    if not cells:
        return m
    return cv2.resize(m, (GW, GH), interpolation=cv2.INTER_AREA) > 0.5


def detail_map(picture):
    """How much detail each cell holds: gradient magnitude of the luma, blurred a little, per cell."""
    luma = cv2.GaussianBlur(picture.mean(2), (0, 0), 1.5)
    gx = cv2.Sobel(luma, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(luma, cv2.CV_32F, 0, 1)
    g = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 4)
    return cv2.resize(g, (GW, GH), interpolation=cv2.INTER_AREA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--layout', default='cloud', choices=('cloud', 'portrait'))
    ap.add_argument('--frame', type=int, default=20)
    ap.add_argument('--upper', action='store_true')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dev', 'out', 'words', 'offline'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    order, toks = words_from(TEXT, stop=a.layout == 'cloud')
    glyphs = Glyphs(set(order) | set(toks), a.upper)
    pic = frames(a.clip, a.frame + 1)[a.frame]
    if a.layout == 'cloud':
        region = subject_mask(a.clip, a.frame)
        dist = cv2.distanceTransform(region.astype(np.uint8), cv2.DIST_L2, 5)
        sizes = [h for h in (160, 128, 104, 84, 68, 56, 46, 38, 32, 26, 21, 17) if h <= 2.2 * CELL * dist.max()]
        placed = layout(region, dist, None, glyphs, order, sizes, 900)
        img = render(pic, placed, glyphs, backdrop=0.15)
    else:
        region = np.ones((GH, GW), bool)
        det = detail_map(pic)
        sizes = (96, 72, 56, 44, 34, 26, 20, 16)
        q = np.quantile(det, (0.15, 0.25, 0.35, 0.45, 0.55, 0.7, 0.85, 1.0))
        allowed = [det <= q[i] for i in range(len(sizes))]
        allowed[-1][:] = True
        rng = np.random.default_rng(1)
        score = rng.random((GH, GW)) * 0.01 - np.abs(np.arange(GH)[:, None] - GH / 2) * 0.0
        placed = layout(region, -np.arange(GH)[:, None] * 0.001 + score, allowed, glyphs, toks, sizes, 4000)
        img = render(pic, placed, glyphs, backdrop=0.0)
    name = '{}_{}_{}{}'.format(a.clip, a.layout, a.frame, '_upper' if a.upper else '')
    Image.fromarray(img).save(os.path.join(a.out, name + '.png'))
    print(name, len(placed), 'words')


if __name__ == '__main__':
    main()
