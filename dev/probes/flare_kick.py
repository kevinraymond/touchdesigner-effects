"""DEV ONLY. Does Lens Flare's Beat Kick show? On a clip with a dance-tempo beat (dev/testbed.py beat=music), read
each frame the kick envelope and the eased flare's mean brightness, and print them over 2 s.

    TD_ARGS='clip=b5_night_field Kick=1' dev/td.sh dev/probes/flare_kick.py && dev/td.sh --pull dev/out/probes/flare_kick/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'probes', 'flare_kick')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
names, opts = test_args(TDLIB_ARGS)
clip, beat = testbed(host, dict(opts, beat=opts.get('beat', 'music')))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'lens_flare', 'lens_flare.tox'))
fx.inputConnectors[0].connect(clip)
fx.inputConnectors[1].connect(beat)
for k, v in opts.items():
    if k[:1].isupper():
        p = getattr(fx.par, k)
        p.val = v if p.isMenu else float(v)
view = mk(host, nullTOP, 'view', [fx.outputConnectors[0]], comment='Pulls the output every frame.', at=(400, 0))
rows = []


def tick(i):
    view.cook(force=True)
    if i >= 60:
        render = fx.op('render').numpyArray(delayed=False)[..., :3].mean()
        flare = fx.op('flare').numpyArray(delayed=False)[..., :3].mean()
        rows.append('{:3d} kick {:.2f} render {:.4f} flare {:.4f}'.format(i, fx.op('kick')[0].eval(), render, flare))
    if i < 180:
        run('args[0](args[1])', tick, i + 1, delayFrames=1)
    else:
        open(os.path.join(OUT, 'done'), 'w').write('\n'.join(rows) + '\n')


tick(0)
