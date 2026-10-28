"""DEV ONLY probe for Words (board #4673): the output every frame, at a quarter size, for a few seconds, with the
testbed's input (the stress beat unless beat=none), to see changes that alternate frame by frame, and the uniforms the
material gets. Writes dev/out/words/frames/frames.npz, then done:

    TD_ARGS='Layout=lines Color=white flashing=off from=5 seconds=2' dev/td.sh dev/probes/words_frames.py
    dev/td.sh --pull dev/out/words/frames/done
"""
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')   # testbed.py's own is from this file's __file__
OUT = os.path.join(_ROOT, 'dev', 'out', 'words', 'frames')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
opts = dict(clip='b1_dancer', beat='stress', seconds='2', **{'from': '5'})
pars = {}
for w in TDLIB_ARGS:
    k, v = w.split('=', 1)
    if k in ('clip', 'beat', 'seconds', 'from', 'flashing'):
        opts[k] = v
    else:
        pars[k] = v
clip, beat = testbed(host, dict(opts))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'words', 'words.tox'))
wire(fx, clip, beat)
for name, value in pars.items():
    p = getattr(fx.par, name)
    p.val = value if p.isMenu or p.isString else float(value)
if 'flashing' in opts:
    fx.par.Flashing = opts['flashing']
small = mk(host, resolutionTOP, 'small', comment='A quarter of the output.', at=(400, 0), outputresolution='quarter')
small.inputConnectors[0].connect(fx.outputConnectors[0])
frames, stats = [], []
state = {'t0': absTime.seconds}


def tick():
    now = absTime.seconds - state['t0']
    small.cook()
    if now >= float(opts['from']):
        a = small.numpyArray(delayed=False)
        frames.append((a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)).astype(np.float16))
        mat = fx.op('word_mat')
        stats.append([now, absTime.frame, float(mat.par.vec0valuez.eval()), float(mat.par.vec1valuez.eval())])
    if now < float(opts['from']) + float(opts['seconds']):
        run('args[0]()', tick, delayFrames=1)
        return
    np.savez(os.path.join(OUT, 'frames.npz'), frames=np.array(frames), stats=np.array(stats))
    open(os.path.join(OUT, 'done'), 'w').write('frames.npz\n')


run('args[0]()', tick, delayFrames=1)
print('frames running', pars, opts)
