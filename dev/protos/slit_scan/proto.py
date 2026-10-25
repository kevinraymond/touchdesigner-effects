"""DEV ONLY. Slit-scan looks, offline, on the test clips (private/assets/ready), before any TouchDesigner:
which time maps read well, and how much filling in between the input's frames matters (Steps: the frame that
was showing; Blend: a cross-fade of the two either side; Flow: the two warped along the motion between them).

    uv run --with opencv-python-headless --with numpy dev/protos/slit_scan/proto.py dev/out/slit_proto/r1

The clips run at 16 fps, as TouchDesigner sees them at 60: each input frame shows for 3.75 TouchDesigner
frames. Writes one PNG per clip, map and fill at a few moments, and a contact sheet per clip."""
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ASSETS = os.path.join(ROOT, 'private', 'assets', 'ready')
W, H = 640, 360
FPS_IN = 16.0


def load(name):
    cap = cv2.VideoCapture(os.path.join(ASSETS, name + '.mp4'))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    return np.stack(frames)


def flows(frames):
    """flow[i]: for each pixel of frame i, where it was in frame i - 1 (pixels), Farneback on gray."""
    gray = [cv2.cvtColor((f * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY) for f in frames]
    out = [np.zeros((H, W, 2), np.float32)]
    for i in range(1, len(gray)):
        out.append(cv2.calcOpticalFlowFarneback(gray[i], gray[i - 1], None, 0.5, 4, 21, 3, 5, 1.1, 0))
    return np.stack(out)


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def warp(img, dx, dy):
    return cv2.remap(img, XX + dx, YY + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def gather(frames, fl, t_in, fill):
    """The picture at input time t_in (in input frames, a float per pixel), filled by fill. The clip is held at
    its first frame before it starts, as a history that has just started would."""
    t_in = np.clip(t_in, 0, len(frames) - 1)
    i0 = np.floor(t_in).astype(int)
    i1 = np.minimum(i0 + 1, len(frames) - 1)
    f = (t_in - i0)[..., None]
    out = np.zeros((H, W, 3), np.float32)
    if fill == 'steps':
        for i in np.unique(i0):
            m = i0 == i
            out[m] = frames[i][m]
        return out
    for i in np.unique(i0):
        m = i0 == i
        j = min(i + 1, len(frames) - 1)
        if fill == 'blend':
            a, b = frames[i], frames[j]
        else:
            # flow[j] at p: where p of frame j was in frame i. At fraction f between them a point at p came from
            # p + f * d in frame i... approximately: sample i at p + f*d and j at p - (1-f)*d, d = flow[j] at p.
            ff = f[m][:, 0]
            fi = np.full((H, W), 0.0, np.float32)
            fi[m] = ff
            d = fl[j]
            a = warp(frames[i], fi * d[..., 0], fi * d[..., 1])
            b = warp(frames[j], -(1 - fi) * d[..., 0], -(1 - fi) * d[..., 1])
        out[m] = (a * (1 - f) + b * f)[m]
    return out


def noise_field(t, scale=3.0):
    """Smooth value noise in 0-1, drifting with t (seconds)."""
    rng = np.random.default_rng(7)
    g = rng.random((8, 8, 8)).astype(np.float32)
    x = XX / W * scale + 0.13 * t
    y = YY / H * scale * H / W + 0.07 * t
    z = np.full_like(x, 0.25 * t)
    out = np.zeros_like(x)
    xi, yi, zi = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int)
    fx, fy, fz = [v - np.floor(v) for v in (x, y, z)]
    fx, fy, fz = [v * v * (3 - 2 * v) for v in (fx, fy, fz)]
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                out += w * g[(xi + dx) % 8, (yi + dy) % 8, (zi + dz) % 8]
    return out


def delay_map(kind, t, depth=None):
    """0 (now) to 1 (the most delay)."""
    if kind == 'sweep_down':
        return YY / (H - 1)
    if kind == 'sweep_right':
        return XX / (W - 1)
    if kind == 'rings':
        r = np.hypot((XX - W / 2) / (H / 2), (YY - H / 2) / (H / 2))
        return np.clip(r / np.hypot(W / H, 1), 0, 1)
    if kind == 'depth_far_old':
        return 1 - depth
    if kind == 'depth_near_old':
        return depth
    if kind == 'noise':
        return np.clip((noise_field(t) - 0.2) / 0.6, 0, 1)
    if kind == 'bands8':
        return np.floor(YY / H * 8) / 7
    raise ValueError(kind)


def slit(frames, fl, n_in, speed_px_s, fill, x_slit=None):
    """Strip photography: the column at x_slit, each moment of it laid down as the film runs left at speed_px_s:
    column x shows the slit as it was (x_slit - x) / speed seconds ago; right of the slit, the live picture."""
    x_slit = W - 1 if x_slit is None else x_slit
    age = np.clip((x_slit - XX) / speed_px_s, 0, None)
    t_in = n_in - age * FPS_IN
    pic = np.zeros((H, W, 3), np.float32)
    # Each column's moment comes from the slit's column, so gather the whole picture at that time and take the
    # slit's column from it, column by column: a picture per distinct column time is too slow, so bin the times.
    cols = np.arange(W)
    times = t_in[0]
    for c in cols:
        if c >= x_slit:
            pic[:, c] = frames[int(n_in)][:, c]
            continue
        tt = np.full((H, W), times[c], np.float32)
        img = gather(frames, fl, tt, fill) if fill != 'steps' else frames[int(np.clip(np.floor(times[c]), 0, len(frames) - 1))]
        pic[:, c] = img[:, x_slit]
    return pic


def main2(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    clips = sys.argv[2].split(',')
    for clip in clips:
        frames = load(clip)
        fl = flows(frames)
        t_out = 4.5
        n_in = t_out * FPS_IN
        outs = []
        for kind in ('sweep_down', 'sweep_right', 'rings'):
            d = delay_map(kind, t_out)
            outs.append(('{} 2.5s flow'.format(kind), gather(frames, fl, n_in - d * 2.5 * FPS_IN, 'flow')))
        for fill in ('steps', 'flow'):
            outs.append(('slit 200px/s {}'.format(fill), slit(frames, fl, n_in, 200.0, fill, x_slit=W // 2)))
        for lab, img in outs:
            im8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
            cv2.putText(im8, lab, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imwrite(os.path.join(out_dir, '{}_{}.png'.format(clip, lab.replace(' ', '_').replace('/', ''))), im8)
        live = (frames[int(n_in)] * 255).astype(np.uint8)
        cv2.imwrite(os.path.join(out_dir, '{}_input.png'.format(clip)), live)
        print(clip, 'done')


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    clips = sys.argv[2].split(',') if len(sys.argv) > 2 else ['b1_dancer', 'd2_walker', 'b2_plaza', 'a3_hands']
    kinds = ['sweep_down', 'sweep_right', 'rings', 'noise', 'depth_far_old', 'depth_near_old', 'bands8']
    fills = ['steps', 'blend', 'flow']
    delay_s = 1.0
    for clip in clips:
        frames = load(clip)
        fl = flows(frames)
        depth = None
        dpath = os.path.join(ASSETS, clip + '_depth.mp4')
        if os.path.exists(dpath):
            dframes = load(clip + '_depth')
        sheet_rows = []
        for t_out in (3.0, 4.2):
            n_in = t_out * FPS_IN
            row = []
            for kind in kinds:
                if kind.startswith('depth'):
                    if not os.path.exists(dpath):
                        continue
                    depth = dframes[min(int(n_in), len(dframes) - 1)].mean(axis=2)
                d = delay_map(kind, t_out, depth)
                for fill in fills if kind in ('sweep_right', 'rings') else ['flow']:
                    img = gather(frames, fl, n_in - d * delay_s * FPS_IN, fill)
                    lab = '{} {} t{:.1f}'.format(kind, fill, t_out)
                    im8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
                    cv2.putText(im8, lab, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.imwrite(os.path.join(out_dir, '{}_{}_{}_{:.1f}.png'.format(clip, kind, fill, t_out)), im8)
                    row.append(im8)
            live = (frames[int(n_in)] * 255).astype(np.uint8).copy()
            cv2.putText(live, 'input t{:.1f}'.format(t_out), (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            row.insert(0, live)
            sheet_rows.append(row)
        print(clip, 'done')


if __name__ == '__main__':
    (main2 if os.environ.get('ROUND') == '2' else main)(sys.argv[1])
