"""DEV ONLY. Turn dev/record.py's Motion JPEG recordings into shareable files:

    uv run dev/clips.py dev/out/record                 # each .mov -> .mp4 (H.264, AAC)
    uv run dev/clips.py dev/out/record --preview       # also a silent animated .webp preview
    uv run dev/clips.py dev/out/record --preview --start 2 --crop   # from 2 s in, the middle at 1:1

The MP4 keeps the recording's size, rate and sound (for the README, a demo reel, sharing). The
preview is what a docs page shows inline: 640 px wide, 20 fps, PREVIEW_SECONDS from --start (0: the
first), looping, no sound (GitHub shows an animated WebP in Markdown; it can't play a video kept in
the repo). --crop takes the middle 640 x 360 pixels instead of scaling the whole picture down, so
small text in the picture stays readable.
"""

import argparse
import glob
import os
import subprocess

PREVIEW_SECONDS = 6


def run(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--start', type=float, default=0.0, help='seconds into the recording the preview starts')
    ap.add_argument('--crop', action='store_true', help='the middle 640 x 360 pixels, not the whole picture')
    ap.add_argument('--quality', type=int, default=80, help="the WebP's quality, 0-100 (lower for busy pictures)")
    a = ap.parse_args()
    for mov in sorted(glob.glob(os.path.join(a.folder, '*.mov'))):
        stem = os.path.splitext(mov)[0]
        run('ffmpeg', '-y', '-v', 'error', '-i', mov, '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', stem + '.mp4')
        made = [stem + '.mp4']
        if a.preview:
            size = 'crop=640:360' if a.crop else 'scale=640:-2:flags=lanczos'
            run('ffmpeg', '-y', '-v', 'error', '-ss', str(a.start), '-t', str(PREVIEW_SECONDS), '-i', mov,
                '-an', '-vf', 'fps=20,' + size, '-c:v', 'libwebp_anim', '-quality', str(a.quality), '-loop', '0',
                stem + '.webp')
            made.append(stem + '.webp')
        print(', '.join('{} ({:.1f} MB)'.format(os.path.basename(m), os.path.getsize(m) / 1e6) for m in made))


if __name__ == '__main__':
    main()
