"""DEV ONLY probe: Slit-Scan's GPU memory, measured (TOP.gpuMemory), for its docs page: each History Size at 1280 x 720
and 1280 x 1280, at History 1, 2 (the default) and 8 s. A Noise TOP that changes every frame stands in for the input,
and each setting cooks for a second before the reading, so the rings are allocated and written.

    dev/td.sh dev/probes/slit_memory.py && TD_WAIT=200 dev/td.sh --pull dev/out/probe_slit_mem/done
    cat dev/out/probe_slit_mem/result.txt"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
out_dir = os.path.join(_ROOT, 'dev', 'out', 'probe_slit_mem')
os.makedirs(out_dir, exist_ok=True)
for f in ('done', 'result.txt'):
    if os.path.exists(os.path.join(out_dir, f)):
        os.remove(os.path.join(out_dir, f))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'slit_scan', 'slit_scan.tox'))
noise = host.create(noiseTOP, 'mem_input')
noise.par.outputresolution = 'custom'
noise.par.tz.expr = 'absTime.seconds'
fx.inputConnectors[0].connect(noise)
view = host.create(nullTOP, 'mem_view')
view.inputConnectors[0].connect(fx.outputConnectors[0])
view.viewer = True
configs = [(w, h, hist, size) for (w, h) in ((1280, 720), (1280, 1280)) for hist in (1.0, 2.0, 8.0)
           for size in ('full', 'half', 'quarter')]
lines = ['w x h, History, History Size: slots, MB (pics, flows, stamps, frames, every operator inside)']


def setup(i):
    w, h, hist, size = configs[i]
    noise.par.resolutionw, noise.par.resolutionh = w, h
    fx.par.History, fx.par.Histsize = hist, size
    state['until'] = absTime.seconds + 1.0
    run('args[0](args[1])', tick, i, delayFrames=1)


def tick(i):
    try:
        _tick(i)
    except Exception as e:
        with open(os.path.join(out_dir, 'result.txt'), 'w') as f:
            f.write('\n'.join(lines + ['ERROR {!r}'.format(e)]) + '\n')
        open(os.path.join(out_dir, 'done'), 'w').close()


def _tick(i):
    view.cook(force=True)
    if absTime.seconds < state['until']:
        run('args[0](args[1])', tick, i, delayFrames=1)
        return
    w, h, hist, size = configs[i]
    mem = [fx.op(n).gpuMemory / 1e6 for n in ('pics', 'flows', 'stamps', 'frames')]
    lines.append('{} x {}, {:g} s, {}: {} slots, {:.1f} {:.2f} {:.3f} {:.3f} | all {:.1f}'.format(
        w, h, hist, size, fx.op('pics').par.cachesize.eval(), *mem, fx.childrenGPUMemory() / 1e6))
    if i + 1 < len(configs):
        setup(i + 1)
    else:
        fx.par.History.val = fx.par.History.default
        fx.par.Histsize.val = fx.par.Histsize.default
        with open(os.path.join(out_dir, 'result.txt'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        open(os.path.join(out_dir, 'done'), 'w').close()


state = {}
setup(0)
print('measuring {} settings, about {} s'.format(len(configs), len(configs) * 1.2))
