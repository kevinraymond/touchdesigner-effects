"""DEV ONLY. Temporal Resonator's GPU memory (board #4717): load the built .tox once per Length on the dancer clip at
1280 x 720, cook it for 2 s, and write each one's total TOP.gpuMemory and its delay line's (states, stamps) to
dev/out/resonator/memory.txt.

    dev/td.sh dev/probes/resonator_memory.py
    dev/td.sh --pull dev/out/resonator/memory.txt
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'resonator', 'memory.txt')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if os.path.exists(OUT):
    os.remove(OUT)

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, dict(clip='b1_dancer', beat='none'))
fxs = {}
for k, length in enumerate(('half', 'beat', 'two')):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'temporal_resonator', 'temporal_resonator.tox'))
    fx.name = 'mem_' + length
    fx.nodeX, fx.nodeY = 300 + 250 * k, 0
    wire(fx, clip, beat)
    fx.par.Length = length
    fxs[length] = fx


def tick(n):
    for fx in fxs.values():
        fx.op('out_top').cook()
    if n < 120:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
        return
    lines = ['cook rate {}, input {} x {}'.format(project.cookRate, clip.width, clip.height)]
    for length, fx in fxs.items():
        tops = [o for o in fx.findChildren(type=TOP)]
        total = sum(o.gpuMemory for o in tops)
        lines.append('{}: total {:.0f} MB, states {:.0f} MB ({} slots), stamps {:.3f} MB'.format(
            length, total / 1e6, fx.op('states').gpuMemory / 1e6, fx.op('states').depth, fx.op('stamps').gpuMemory / 1e6))
    open(OUT, 'w').write('\n'.join(lines) + '\n')


tick(0)
