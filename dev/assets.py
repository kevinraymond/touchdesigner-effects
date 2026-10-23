"""DEV ONLY. Get test footage and audio ready for TouchDesigner, from private/assets/ (see
PROMPTS.md there for what each clip is for):

    uv run --with pillow dev/assets.py            # normalize new files, then report
    uv run --with pillow dev/assets.py --force    # redo everything

Each video becomes private/assets/ready/<name>.mp4: 1280 x 720 (scaled to cover, then
center-cropped, so any aspect works), a constant frame rate (the source's if it is 24, 25, 30,
50 or 60, else 30), H.264, no sound. Each audio file becomes ready/<name>.wav, 48 kHz 16-bit.
Clips whose names start d3a and d3b are also joined into ready/d3_cut.mp4, a hard cut. A contact
sheet of every ready clip (start, middle, end) goes to ready/sheet.png, and the report lists the
PROMPTS.md IDs that have no clip yet. dev/td.sh copies private/ to the Mac with everything else,
so a ready clip is at ~/tdlib/private/assets/ready/ there.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = ('.mp4', '.mov', '.webm', '.mkv', '.m4v', '.avi')
AUDIO = ('.wav', '.mp3', '.flac', '.aif', '.aiff', '.ogg', '.m4a')
RATES = (24, 25, 30, 50, 60)


def run(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def video_info(path):
    info = probe(path)
    v = next(s for s in info['streams'] if s['codec_type'] == 'video')
    num, den = (int(x) for x in v.get('avg_frame_rate', '30/1').split('/'))
    return int(v['width']), int(v['height']), (num / den if den else 30.0), float(info['format'].get('duration', 0))


def fresh(src, dst):
    return os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src)


def normalize_video(src, dst):
    w, h, fps, _ = video_info(src)
    rate = min(RATES, key=lambda r: abs(r - fps)) if any(abs(r - fps) < 0.6 for r in RATES) else 30
    run('ffmpeg', '-y', '-v', 'error', '-i', src, '-an', '-map_metadata', '-1',
        '-vf', 'scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1',
        '-r', str(rate), '-fps_mode', 'cfr', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst)
    return '{}x{} {:.2f} fps -> 1280x720 {} fps'.format(w, h, fps, rate)


def normalize_audio(src, dst):
    run('ffmpeg', '-y', '-v', 'error', '-i', src, '-vn', '-map_metadata', '-1', '-ar', '48000',
        '-c:a', 'pcm_s16le', dst)
    return '-> 48 kHz 16-bit WAV'


def join(parts, dst):
    """Parts one after another, a hard cut between them, all at the first part's frame rate (the
    concat filter resamples each part, so parts at different rates keep their durations)."""
    rate = round(video_info(parts[0])[2])
    inputs = [x for p in parts for x in ('-i', p)]
    chains = ''.join('[{}:v]fps={},setpts=PTS-STARTPTS[v{}];'.format(i, rate, i) for i in range(len(parts)))
    joined = ''.join('[v{}]'.format(i) for i in range(len(parts))) + 'concat=n={}:v=1:a=0[out]'.format(len(parts))
    run('ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', chains + joined, '-map', '[out]',
        '-r', str(rate), '-fps_mode', 'cfr', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst)


def sheet(clips, dst):
    from PIL import Image, ImageDraw
    w, h, pad, label = 320, 180, 6, 18
    out = Image.new('RGB', (3 * (w + pad) + pad, len(clips) * (h + label + pad) + pad), (24, 24, 24))
    draw = ImageDraw.Draw(out)
    with tempfile.TemporaryDirectory() as tmp:
        for r, clip in enumerate(clips):
            _, _, fps, dur = video_info(clip)
            y = pad + r * (h + label + pad)
            draw.text((pad, y + 3), '{}  {:.1f} s, {:.0f} fps'.format(os.path.basename(clip), dur, fps),
                      fill=(235, 235, 235))
            for c, t in enumerate((0.0, dur / 2, max(dur - 0.1, 0.0))):
                png = os.path.join(tmp, '{}_{}.png'.format(r, c))
                run('ffmpeg', '-y', '-v', 'error', '-ss', '{:.2f}'.format(t), '-i', clip, '-frames:v', '1',
                    '-vf', 'scale={}:{}'.format(w, h), png)
                out.paste(Image.open(png).convert('RGB'), (pad + c * (w + pad), y + label))
    out.save(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default=os.path.join(ROOT, 'private', 'assets'))
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    ready = os.path.join(a.dir, 'ready')
    os.makedirs(ready, exist_ok=True)

    names = set()
    for src in sorted(glob.glob(os.path.join(a.dir, '*'))):
        stem, ext = os.path.splitext(os.path.basename(src))
        ext = ext.lower()
        if ext in VIDEO:
            dst = os.path.join(ready, stem + '.mp4')
            names.add(stem)
            if a.force or not fresh(src, dst):
                print('video', stem, normalize_video(src, dst))
        elif ext in AUDIO:
            dst = os.path.join(ready, stem + '.wav')
            names.add(stem)
            if a.force or not fresh(src, dst):
                print('audio', stem, normalize_audio(src, dst))

    parts = [sorted(glob.glob(os.path.join(ready, p + '*.mp4'))) for p in ('d3a', 'd3b')]
    if all(parts):
        dst = os.path.join(ready, 'd3_cut.mp4')
        if a.force or not all(fresh(p[0], dst) for p in parts):
            join([parts[0][0], parts[1][0]], dst)
            print('joined', os.path.basename(parts[0][0]), '+', os.path.basename(parts[1][0]), '-> d3_cut.mp4')

    clips = sorted(glob.glob(os.path.join(ready, '*.mp4')))
    if clips:
        sheet(clips, os.path.join(ready, 'sheet.png'))
        print('sheet', os.path.join(ready, 'sheet.png'), len(clips), 'clips')

    prompts = os.path.join(a.dir, 'PROMPTS.md')
    if os.path.exists(prompts):
        wanted = re.findall(r'^\*\*([A-Z]\d+[a-z]?) ', open(prompts).read(), re.M)
        have = {n.split('_')[0].upper() for n in names}
        missing = [i for i in wanted if i.upper() not in have]
        print('PROMPTS.md: {} of {} clips in; missing {}'.format(len(wanted) - len(missing), len(wanted),
                                                                  ' '.join(missing) or 'none'))


if __name__ == '__main__':
    main()
