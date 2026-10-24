"""DEV ONLY. ASCII pass 1: stills of the beat layer's moments on the dancer clip, made by pulsing the
envelopes directly (past the flash gate: stills only, never a flash measurement). Short; cleans up.

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/pass1_moments.py
    TD_PARENT=/tdlib_dev_ascii dev/td.sh --pull dev/out/ascii/moments/done
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_HERE, 'off.py')).read(), 'off.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'moments')
CLIP = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')

host = op(TDLIB_PARENT)
fx = host.op('ascii')
for o in list(host.children):
    if o.name != 'ascii':
        o.destroy()
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
clip = host.create(moviefileinTOP, 't_clip')
clip.par.file = CLIP
c = host.copy(fx, name='ascii_moments')
c.inputConnectors[0].connect(clip)
c.par.Beatglyphs = 1.0
c.allowCooking = True
top = c.op('out_top')
steps = [(30, 'save', 'calm'), (31, 'beat', None), (33, 'save', 'beat_swap'), (60, 'pop', None),
         (62, 'save', 'pop'), (100, 'drop', None), (102, 'save', 'drop')]


def tick(n):
    top.cook()
    for at, what, name in steps:
        if at != n:
            continue
        if what == 'save':
            top.save(os.path.join(OUT, name + '_0.png'))
        elif what == 'beat':
            c.op('beat_env').par.trigger.pulse()
        elif what == 'pop':
            c.op('pop_env').par.trigger.pulse()
        elif what == 'drop':
            c.op('pop_env').par.trigger.pulse()
            c.op('drop_env').par.trigger.pulse()
    if n < steps[-1][0]:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
    else:
        c.destroy()
        clip.destroy()
        off(host)
        open(os.path.join(OUT, 'done'), 'w').write('ok\n')


tick(0)
print('moments into', OUT)
