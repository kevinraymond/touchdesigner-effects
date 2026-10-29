"""DEV ONLY. What a Gaussian Blur TOP costs on the GPU by its size (board #4677: Relight's size-6 blurs measured about
1 ms at 640 x 360, its size-24 and 36 ones 0.03): a noise TOP at 640 x 360 in 16-bit float, a Blur TOP a size, each
pulled every frame for 2 s, then each one's mean GPU cook time.

    dev/td.sh dev/probes/blur_cost.py && dev/td.sh --pull dev/out/probes/blur_cost/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'probes', 'blur_cost')
os.makedirs(OUT, exist_ok=True)
if os.path.exists(os.path.join(OUT, 'done')):
    os.remove(os.path.join(OUT, 'done'))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
SIZES = (36, 24, 16, 12, 9, 8, 7, 6, 5, 4, 3, 2)
noise = mk(host, noiseTOP, 'noise', comment='A changing picture.', at=(0, 0), outputresolution='custom',
           resolutionw=640, resolutionh=360, format='rgba16float', tz=Expr('absTime.seconds'))
blurs = [mk(host, blurTOP, 'blur{}'.format(s), [noise], comment='size {}'.format(s), at=(200, -120 * k),
            type='gaussian', size=s) for k, s in enumerate(SIZES)]
samples = {b.name: [] for b in blurs}


def tick(i):
    for b in blurs:
        b.cook(force=True)
    if i > 20:
        for b in blurs:
            samples[b.name].append(b.gpuCookTime)
    if i < 140:
        run('args[0](args[1])', tick, i + 1, delayFrames=1)
        return
    lines = ['{:<8} gpu {:.3f} ms'.format(b.name, sum(samples[b.name]) / len(samples[b.name])) for b in blurs]
    lines.append('pars: ' + ', '.join('{}={}'.format(p.name, p.eval()) for p in blurs[0].pars()
                                      if p.page is not None and p.page.name == 'Blur'))
    open(os.path.join(OUT, 'done'), 'w').write('\n'.join(lines) + '\n')


tick(0)
