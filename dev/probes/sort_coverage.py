"""DEV ONLY probe: does Pixel Sort's compute shader write every pixel exactly as it should at every angle? With nothing
in a span (Low 1, High 1) the output must equal the input; with Whole Lines, every line must hold the same pixels as
before, only reordered, and none may be left unwritten (stale or black). Steps through angles a frame or two apart and
writes dev/out/probe_cover/result.txt, then done:

    dev/td.sh dev/probes/sort_coverage.py && dev/td.sh --pull dev/out/probe_cover/done"""
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
host = op(TDLIB_PARENT)
out_dir = os.path.join(_ROOT, 'dev', 'out', 'probe_cover')
os.makedirs(out_dir, exist_ok=True)
for f in ('done', 'result.txt'):
    if os.path.exists(os.path.join(out_dir, f)):
        os.remove(os.path.join(out_dir, f))
for o in list(host.children):
    if o.valid:
        o.destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'pixel_sort', 'pixel_sort.tox'))
noise = host.create(noiseTOP, 'cover_noise')
noise.par.outputresolution = 'custom'
noise.par.resolutionw, noise.par.resolutionh = 1280, 720
noise.par.mono = False
noise.par.period = 0.3
fx.inputConnectors[0].connect(noise)
fx.par.Flips = 'off'
fx.par.Kick = 0
view = host.create(nullTOP, 'cover_view')
view.inputConnectors[0].connect(fx.outputConnectors[0])
ANGLES = [0, 0.3, 1, 7.3, 22.5, 30, 44.9, 45, 45.1, 60, 89.7, 90, 133, 180, 200.5, 225, 270, 300, 359.6]
CASES = [('none', dict(Spans='brightness', Low=1.0, High=1.0)), ('whole', dict(Spans='whole', Cutevery=0))]
jobs = [(c, a) for c in CASES for a in ANGLES]
lines = []
state = {'i': 0, 'f': 0}


def tick():
    (name, pars), angle = jobs[state['i']]
    if state['f'] == 0:
        for k, v in pars.items():
            setattr(fx.par, k, v)
        fx.par.Angle = angle
    view.cook()
    state['f'] += 1
    if state['f'] >= 4:  # the key pass's hysteresis settles in a frame or two
        a = view.numpyArray()
        src = noise.numpyArray()
        if name == 'none':
            bad = np.abs(a - src).max(axis=2) > 1e-3
            lines.append('{:5s} angle {:6.1f}: {} pixels differ from the input'.format(name, angle, int(bad.sum())))
        else:
            black = int((a[..., :3].sum(axis=2) < 1e-4).sum())
            # every pixel's color must be one the input has: the multiset of each channel is kept overall
            same = np.allclose(np.sort(a[..., 0].ravel()), np.sort(src[..., 0].ravel()), atol=1e-3)
            lines.append('{:5s} angle {:6.1f}: black {}, same colors overall {}, changed {:.2f}'.format(
                name, angle, black, same, float((np.abs(a - src).max(axis=2) > 1e-3).mean())))
        state['i'] += 1
        state['f'] = 0
    if state['i'] < len(jobs):
        run('args[0]()', tick, delayFrames=1)
        return
    open(os.path.join(out_dir, 'result.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(out_dir, 'done'), 'w').write('result.txt\n')
    print('\n'.join(lines))


run('args[0]()', tick, delayFrames=1)
print('probe_cover running')
