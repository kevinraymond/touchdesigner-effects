"""DEV ONLY. Which of Lens Flare's operators cook every frame, and their GPU time: load it on a clip, pull its output
for 2 s, then print each TOP's cooks and last GPU cook time, and the render's per frame (the viewer pulls it). The starburst lane should cook once.

    TD_ARGS='clip=b5_night_field' dev/td.sh dev/probes/flare_cooks.py && dev/td.sh --pull dev/out/probes/flare_cooks/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'probes', 'flare_cooks')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
names, opts = test_args(TDLIB_ARGS)
clip, beat = testbed(host, dict(opts, beat='none'))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'lens_flare', 'lens_flare.tox'))
fx.inputConnectors[0].connect(clip)
for k, v in opts.items():
    if k[:1].isupper():
        p = getattr(fx.par, k)
        p.val = v if p.isMenu else float(v)
view = mk(host, nullTOP, 'view', [fx.outputConnectors[0]], comment='Pulls the output every frame.', at=(400, 0))
view.viewer = True
start = {}
samples = []


def tick(i):
    view.cook(force=True)
    if i > 30:
        samples.append(fx.op('render').gpuCookTime)
    if i == 30:
        for o in fx.findChildren(type=TOP, depth=1):
            start[o.name] = o.totalCooks
    if i < 150:
        run('args[0](args[1])', tick, i + 1, delayFrames=1)
    else:
        lines = ['{:<12} cooks {:4d} in 120 frames, gpu {:.3f} ms, cpu {:.3f} ms'.format(
            o.name, o.totalCooks - start.get(o.name, 0), o.gpuCookTime, o.cpuCookTime)
            for o in sorted(fx.findChildren(type=TOP, depth=1), key=lambda o: -o.gpuCookTime)]
        samples.sort()
        lines.append('render gpu per frame: mean {:.3f} median {:.3f} min {:.3f} max {:.3f}'.format(
            sum(samples) / len(samples), samples[len(samples) // 2], samples[0], samples[-1]))
        open(os.path.join(OUT, 'done'), 'w').write('\n'.join(lines) + '\n')


tick(0)
