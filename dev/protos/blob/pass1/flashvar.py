"""DEV ONLY (blob_track pass 1): dev/flash.py's recording, but for variants of blob_track's
parameters, to find what makes it flash. Settings in flashvar_settings.py beside this file:
  TAG       output folder dev/out/blob_track/flashvar/<TAG>/ (count with dev/flashcount.py)
  ARGS      testbed options, e.g. ['clip=b2_plaza', 'beat=none']
  VARIANTS  {name: {par: value}}; each recorded as <name>_<Flashing>.npz (Flashing in the dict,
            default off), after the clip alone (clip_source.npz)
Run: TD_PARENT=/tdlib_dev_blob dev/td.sh dev/protos/blob/pass1/flashvar.py
Everything it makes is stopped and destroyed when it is done.
"""
import os

import numpy as np

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flashvar_settings.py')).read(),
             'flashvar_settings.py', 'exec'), globals())
# The meter, exactly as dev/flash.py has it.
_flash_src = open(os.path.join(_ROOT, 'dev', 'flash.py')).read()
METER = _flash_src.split('METER = """', 1)[1].split('"""', 1)[0]
SETTLE, SECONDS = globals().get('SETTLE', 2.0), globals().get('SECONDS', 10.0)

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
_, opts = test_args(ARGS)
out = os.path.join(_ROOT, 'dev', 'out', 'blob_track', 'flashvar', TAG)
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    os.remove(os.path.join(out, f))
clip, beat = testbed(host, opts)
view = mk(host, nullTOP, 'view', 400, 0, comment='x')
meter = glsl(host, 'meter', 600, 0, [view], METER, 'x', res=(64, 36), fmt='rgba32float')
runs = [('clip_source', None)]
for i, (name, pars) in enumerate(VARIANTS.items()):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'blob_track', 'blob_track.tox'))
    fx.name = 'v_' + name
    fx.nodeX, fx.nodeY = 0, 300 * (i + 1)
    fx.inputConnectors[0].connect(clip)
    if beat is not None:
        fx.inputConnectors[1].connect(beat)
    pars = dict(pars)
    pars.setdefault('Flashing', 'off')
    for k, v in pars.items():
        setattr(fx.par, k, v)
    fx.allowCooking = False
    runs.append(('{}_{}'.format(name, pars['Flashing']), fx))
state = {'i': -1, 'frames': [], 'start': 0.0}


def begin(i):
    state['i'], state['frames'] = i, []
    name, fx = runs[i]
    for o in host.findChildren(type=COMP, depth=1):
        o.allowCooking = o is fx
    view.inputConnectors[0].connect(clip if fx is None else fx.outputConnectors[0])
    state['start'] = absTime.seconds + SETTLE


def tick():
    now = absTime.seconds
    if now >= state['start']:
        a = meter.numpyArray()
        state['frames'].append((now, a[:, :, 0].copy(), a[:, :, 1].copy()))
    if now < state['start'] + SECONDS:
        run('args[0]()', tick, delayFrames=1)
        return
    name, _ = runs[state['i']]
    t, lum, red = zip(*state['frames'])
    np.savez_compressed(os.path.join(out, name + '.npz'), t=np.array(t), lum=np.array(lum, dtype=np.float32),
                        red=np.array(red, dtype=np.float32))
    if state['i'] + 1 < len(runs):
        begin(state['i'] + 1)
        run('args[0]()', tick, delayFrames=1)
        return
    with open(os.path.join(out, 'done'), 'w') as f:
        f.write('\n'.join(n for n, _ in runs) + '\n')
    for o in list(host.children):
        o.allowCooking = False
    clip.par.play = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=2)


begin(0)
run('args[0]()', tick, delayFrames=1)
print('flashvar {}: {} runs of {:g} s: {}'.format(TAG, len(runs), SECONDS + SETTLE, [n for n, _ in runs]))
