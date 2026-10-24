"""DEV ONLY. Record a RealSense camera (on the Linux box) as test footage for the depth effects:

    uv run --python 3.11 --with pyrealsense2 --with numpy dev/realsense_record.py r1_room --seconds 8
    uv run --python 3.11 --with pyrealsense2 --with numpy dev/realsense_record.py --check   # one frame, no files

Writes, in private/assets/ (then run dev/assets.py, and dev/td.sh copies them to the Mac):
  <id>.mp4          the color picture, 1280 x 720 at 30 fps
  <id>_depth.mp4    the depth lined up with it, the library's way: brighter nearer, 0 m to --max-depth
                    over 1 to 0, and black where the camera got no reading
  <id>_rsdepth.mp4  the same depth as TouchDesigner's RealSense TOP gives it on Windows: darker nearer
                    (0 m is 0, Max Depth and beyond 1), and black (0 m) where there is no reading, so an
                    effect's Darker Is Nearer setting meets real sensor holes and noise
Depth is aligned to the color camera (rs.align), so the two line up pixel for pixel. 8-bit video
quantizes depth to 1/255 of --max-depth (2 cm at 5 m), enough for finding people.
"""

import argparse
import os
import subprocess

import numpy as np
import pyrealsense2 as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1280, 720, 30


def writer(path, pix_fmt):
    return subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', pix_fmt, '-s', '{}x{}'.format(W, H),
                             '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                             '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path], stdin=subprocess.PIPE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('id', nargs='?', default='r1_room')
    ap.add_argument('--seconds', type=float, default=8.0)
    ap.add_argument('--max-depth', type=float, default=5.0, help='meters that map to the far end')
    ap.add_argument('--check', action='store_true', help='open the camera, read one frame, report, write nothing')
    a = ap.parse_args()

    pipe = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, W, H, rs.format.rgb8, FPS)
    cfg.enable_stream(rs.stream.depth, W, H, rs.format.z16, FPS)
    profile = pipe.start(cfg)
    scale = profile.get_device().first_depth_sensor().get_depth_scale()   # meters per z16 unit
    align = rs.align(rs.stream.color)
    try:
        for _ in range(30):                     # let auto exposure settle
            pipe.wait_for_frames()
        if a.check:
            f = align.process(pipe.wait_for_frames())
            d = np.asanyarray(f.get_depth_frame().get_data()) * scale
            name = profile.get_device().get_info(rs.camera_info.name)
            print('{}: depth scale {} m; valid {:.0%}; median {:.2f} m; color {}'.format(
                name, scale, (d > 0).mean(), np.median(d[d > 0]) if (d > 0).any() else 0,
                np.asanyarray(f.get_color_frame().get_data()).shape))
            return
        base = os.path.join(ROOT, 'private', 'assets', a.id)
        out = {k: writer(base + suffix, fmt) for k, suffix, fmt in
               (('color', '.mp4', 'rgb24'), ('depth', '_depth.mp4', 'gray'), ('rs', '_rsdepth.mp4', 'gray'))}
        n = int(a.seconds * FPS)
        for _ in range(n):
            f = align.process(pipe.wait_for_frames())
            color = np.asanyarray(f.get_color_frame().get_data())
            meters = np.asanyarray(f.get_depth_frame().get_data()).astype(np.float32) * scale
            far = np.clip(meters / a.max_depth, 0.0, 1.0)
            valid = meters > 0
            ours = np.where(valid, 1.0 - far, 0.0)
            out['color'].stdin.write(color.tobytes())
            out['depth'].stdin.write((ours * 255 + 0.5).astype(np.uint8).tobytes())
            out['rs'].stdin.write((np.where(valid, far, 0.0) * 255 + 0.5).astype(np.uint8).tobytes())
        for p in out.values():
            p.stdin.close()
            p.wait()
        print('wrote {} frames ({:g} s at {} fps): {}.mp4, {}_depth.mp4, {}_rsdepth.mp4'.format(
            n, a.seconds, FPS, base, base, base))
    finally:
        pipe.stop()


if __name__ == '__main__':
    main()
