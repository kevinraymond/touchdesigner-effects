"""DEV ONLY probe: does Fluid's Reset clear it? Loads the built fluid.tox with the test clip, lets the fluid fill
for 2 s, pulses Reset, and writes the dye's and the velocity's mean before and on the next frames to
dev/out/fluid_reset.txt. dev/td.sh dev/probes/fluid_reset.py; dev/td.sh --pull"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')     # testbed.py's own is relative to this file
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'fluid', 'fluid.tox'))
clip, beat = testbed(host, dict(clip='b1_dancer', beat='none'))
wire(fx, clip, beat)
view = host.create(nullTOP, 'view')
view.inputConnectors[0].connect(fx.outputConnectors[0])
log = []
state = dict(n=0, reset_at=None)


def means():
    import numpy as np
    d = fx.op('dye').numpyArray()[..., 3].mean()
    v = np.abs(fx.op('velocity').numpyArray()[..., :2]).mean()
    return round(float(d), 4), round(float(v), 3)


def tick():
    view.cook(force=True)
    state['n'] += 1
    if state['n'] == 120:
        log.append('before Reset: dye, |velocity| {}'.format(means()))
        fx.par.Reset.pulse()
        state['reset_at'] = state['n']
    elif state['reset_at'] and state['n'] - state['reset_at'] in (1, 2, 3, 30):
        log.append('{} frames after: {}'.format(state['n'] - state['reset_at'], means()))
    if state['n'] < 160:
        run('args[0]()', tick, delayFrames=1)
    else:
        open(os.path.join(_ROOT, 'dev', 'out', 'fluid_reset.txt'), 'w').write('\n'.join(log) + '\n')


tick()
print('running 160 frames')
