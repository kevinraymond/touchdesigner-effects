"""DEV ONLY. Relight's passes on one frame (board #4677): load the built .tox on a clip with its depth, wait, and save
each pass's pixels as .npy (surface, shadows, irradiance, sss_v, shape, show, lights, and the clip), for looking at
what makes what outside TouchDesigner:

    TD_ARGS='clip=a3_hands at=4 Look=studio' dev/td.sh dev/probes/relight_passes.py
    dev/td.sh --pull dev/out/relight/passes/done
"""
import os
import numpy

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'relight', 'passes')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
names, opts = test_args(TDLIB_ARGS)
opts.setdefault('at', '4')
clip, beat = testbed(host, dict(opts, beat='none'))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'relight', 'relight.tox'))
wire(fx, clip, None)
for k, v in opts.items():
    if k[:1].isupper():
        p = getattr(fx.par, k)
        p.val = v if p.isMenu else float(v)
view = mk(host, nullTOP, 'view', [fx.outputConnectors[0]], comment='Pulls the output every frame.', at=(400, 0))
view.viewer = True


def save():
    for name in ('surface', 'shadows', 'irradiance', 'sss_v', 'shape', 'show', 'lights'):
        numpy.save(os.path.join(OUT, name + '.npy'), fx.op(name).numpyArray())
    numpy.save(os.path.join(OUT, 'clip.npy'), clip.numpyArray())
    open(os.path.join(OUT, 'done'), 'w').write('saved\n')


run('args[0]()', save, delayMilliSeconds=int(float(opts['at']) * 1000))
print('saving passes at', opts['at'])
