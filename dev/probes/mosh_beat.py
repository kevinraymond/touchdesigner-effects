"""DEV ONLY. Inside TouchDesigner: Datamosh hearing a song as raw audio for a few seconds: its beat
envelope, the uniforms mosh reads for a beat's surge, and any problems; it saves mosh's picture on
the frame before the 4th beat and 0, 2, 4, 8, 12 and 20 frames after (beat4_<k>.png). Reads only.

    dev/td.sh dev/probes/mosh_beat.py && dev/td.sh --pull dev/out/mosh_beat/done && cat dev/out/mosh_beat/report.txt
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, 'dev', 'out', 'mosh_beat')
os.makedirs(OUT, exist_ok=True)
for f in ('report.txt', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
track = host.create(audiofileinCHOP, 'track')
track.par.file = os.path.join(_ROOT, 'private', 'assets', 'ready', 'm1x_ease_from_drop.wav')
track.par.repeat = 'on'
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox'))
fx.inputConnectors[1].connect(track)
clip = host.create(moviefileinTOP, 'clip')
clip.par.file = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')
fx.inputConnectors[0].connect(clip)
shots = {}
mosh = fx.op('mosh')
lines = []
names = [mosh.par['vec{}name'.format(i)].eval() for i in range(mosh.seq.vec.numBlocks)]
lines.append('uniforms: ' + ' '.join(names))


def tick(n):
    fx.op('out_top').cook()
    vals = {}
    for i, name in enumerate(names):
        if name in ('uBeat', 'uPush', 'uAud'):
            vals[name] = tuple(round(mosh.par['vec{}value{}'.format(i, a)].eval(), 3) for a in 'xyzw')
    a = fx.op('audio')
    beats = a['beat_count'].eval()
    if beats == 3:
        mosh.save(os.path.join(OUT, 'beat4_before.png'))
    if beats >= 4 and 'at' not in shots:
        shots['at'] = n
    if 'at' in shots and n - shots['at'] in (0, 2, 4, 8, 12, 20):
        mosh.save(os.path.join(OUT, 'beat4_{}.png'.format(n - shots['at'])))
    lines.append('{:3d} beats {:.0f} env {:.2f} {}'.format(n, a['beat_count'].eval(), fx.op('beat_env')[0].eval(), vals))
    if n < 180:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
        return
    lines.append('problems: {}'.format(fx.errors(recurse=True) + fx.warnings(recurse=True) or 'none'))
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')
    for o in list(host.children):
        o.destroy()


tick(0)
