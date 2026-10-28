"""DEV ONLY probe for Words (board #4673): Lines on the dancer for 2 s, then its state: words, field, region."""
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
host = op(TDLIB_PARENT)
_d = os.path.join(_ROOT, 'dev', 'out', 'words', 'dbg', 'done')
if os.path.exists(_d):
    os.remove(_d)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, dict(clip='b1_dancer', beat='none'))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'words', 'words.tox'))
wire(fx, clip, beat)
fx.par.Layout = 'lines'
for k, v in [w.split('=', 1) for w in TDLIB_ARGS]:
    p = getattr(fx.par, k)
    p.val = v if p.isMenu or p.isString else float(v)
view = mk(host, nullTOP, 'view', comment='pulls', at=(400, 0))
view.inputConnectors[0].connect(fx.outputConnectors[0])
t0 = absTime.seconds


def tick():
    view.cook()
    if absTime.seconds - t0 < 2.0:
        run('args[0]()', tick, delayFrames=1)
        return
    lines = []
    print = lambda *a: lines.append(' '.join(str(x) for x in a))
    lay = fx.op('layout').numpyArray(delayed=False)
    f = fx.op('field').numpyArray(delayed=False)
    r = fx.op('region').numpyArray(delayed=False)
    print('inputs', [c.connections[0].owner.name if c.connections else None for c in fx.inputConnectors])
    print('states', np.unique(lay[1, :, 3], return_counts=True))
    print('field r', np.percentile(f[..., 0], (0, 50, 100)).round(2), 'g', np.percentile(f[..., 1], (0, 50, 100)).round(2),
          'nan', int(np.isnan(f).sum()))
    print('region inside', int((r[..., 0] > 0.5).sum()))
    print('glob', lay[3, 0])
    print('layout warnings', fx.op('layout').warnings(), fx.op('field').warnings())
    out = os.path.join(_ROOT, 'dev', 'out', 'words', 'dbg')
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'dbg.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(out, 'done'), 'w').write('dbg.txt\n')


run('args[0]()', tick, delayFrames=1)
