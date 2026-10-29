"""DEV ONLY. Relight as it is dragged in (board #4677): load the built .tox with nothing wired, let it cook a few
seconds, and save its output at two moments, to check the sample picture under the lights.

    dev/td.sh dev/probes/relight_unwired.py && dev/td.sh --pull dev/out/relight/unwired/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'relight', 'unwired')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'relight', 'relight.tox'))
view = mk(host, nullTOP, 'view', [fx.outputConnectors[0]], comment='Pulls the output every frame.', at=(400, 0))
view.viewer = True


def save(k, last):
    fx.op('out_top').save(os.path.join(OUT, 'unwired_{}.png'.format(k)))
    if last:
        open(os.path.join(OUT, 'done'), 'w').write('saved\n')


run('args[0](0, False)', save, delayMilliSeconds=2000)
run('args[0](1, True)', save, delayMilliSeconds=6000)
print('saving the unwired output at 2 and 6 s')
