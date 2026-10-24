"""DEV ONLY. Inside TouchDesigner: an effect hearing a song file, frame by frame: the beats its audio
input detects and, if it has them, the bursts it fires (burst_count). TD_ARGS: effect name, then
audio=<file in private/assets/ready> (default m1x_ease_from_drop.wav) and seconds=<n> (default 8).

    TD_ARGS='glitch' dev/td.sh dev/probes/effect_beats.py && dev/td.sh --pull dev/out/effect_beats/done
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_ROOT, 'dev', 'out', 'effect_beats')
os.makedirs(OUT, exist_ok=True)
for f in ('report.txt', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
args = globals().get('TDLIB_ARGS') or ['glitch']
opts = dict(a.split('=', 1) for a in args if '=' in a)
name = [a for a in args if '=' not in a][0]
seconds = float(opts.get('seconds', 8))
host = op(TDLIB_PARENT) or op('/').create(baseCOMP, TDLIB_PARENT.strip('/'))
for o in list(host.children):
    if o.valid:
        o.destroy()
track = host.create(audiofileinCHOP, 'track')
track.par.file = os.path.join(_ROOT, 'private', 'assets', 'ready', opts.get('audio', 'm1x_ease_from_drop.wav'))
fx = host.loadTox(os.path.join(_ROOT, 'effects', name, name + '.tox'))
fx.inputConnectors[1].connect(track)
track.par.cuepulse.pulse()
st = dict(start=absTime.seconds, beats=[], bursts=[], last=(None, None))


def tick():
    fx.op('out_top').cook()
    t = round(absTime.seconds - st['start'], 2)
    b = fx.op('audio')['beat_count'].eval()
    n = fx.op('burst_count')[0].eval() if fx.op('burst_count') is not None else None
    if st['last'][0] is not None and b > st['last'][0]:
        st['beats'].append(t)
    if st['last'][1] is not None and n is not None and n > st['last'][1]:
        st['bursts'].append(t)
    st['last'] = (b, n)
    if t < seconds:
        run('args[0]()', tick, delayFrames=1)
        return
    lines = ['{} hearing {} for {:g} s, Flashing {}'.format(name, os.path.basename(track.par.file.eval()), seconds,
                                                          fx.par.Flashing.eval() if hasattr(fx.par, 'Flashing') else '-'),
             'beats ({}): {}'.format(len(st['beats']), st['beats']),
             'bursts ({}): {}'.format(len(st['bursts']), st['bursts'])]
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('ok\n')
    for o in list(host.children):
        if o.valid:
            o.destroy()


tick()
print('listening for {:g} s'.format(seconds))
