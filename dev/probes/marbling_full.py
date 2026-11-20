"""DEV ONLY. Marbling's cost with a full tray (board #4848): loads the built .tox on the dancer with the song on
input 2 and Hold at 16 bars (TD_ARGS='Hold=4' for another), lets the tray fill for FILL seconds, then reads marble's GPU cook time and the effect's
over SAMPLE frames, with how many tools are on the tray. Writes dev/out/marbling/full.txt.

    dev/td.sh dev/probes/marbling_full.py; sleep 50; dev/td.sh --pull dev/out/marbling/full.txt
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'marbling', 'full.txt')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
FILL, SAMPLE = 40.0, 120
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, {'clip': 'b1_dancer', 'beat': 'song'})
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'marbling', 'marbling.tox'))
fx.nodeX = 300
wire(fx, clip, beat)
HOLD = float(next((w.split('=', 1)[1] for w in TDLIB_ARGS if w.startswith('Hold=')), 16))
fx.par.Hold = HOLD
null = mk(host, nullTOP, 'pull', at=(500, 0))
null.inputConnectors[0].connect(fx.outputConnectors[0])
null.viewer = True
samples = {'marble': [], 'all': [], 'tools': []}


START = absTime.seconds


def tick(n):
    null.cook()   # nothing views it: pull the effect every frame, as dev/perf.py does
    if absTime.seconds - START < FILL:
        run('args[0](args[1])', tick, 0, delayFrames=1)
        return
    m = fx.op('marble')
    samples['marble'].append(m.gpuCookTime)
    samples['all'].append(sum(o.gpuCookTime for o in fx.findChildren(type=TOP) if o.cookAbsFrame >= absTime.frame - 1))
    samples['tools'].append(sum(1 for k in fx.op('tray')['kind'].vals if k > 0))
    if n < SAMPLE:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
    else:
        s = sorted(samples['marble'])
        a = sorted(samples['all'])
        with open(OUT, 'w') as f:
            f.write('Hold {:g}: tools'.format(HOLD) + '  {}-{}; marble GPU median {:.2f} ms (95% {:.2f}); effect TOPs GPU median {:.2f} ms\n'.format(
                min(samples['tools']), max(samples['tools']), s[len(s) // 2], s[int(len(s) * 0.95)], a[len(a) // 2]))


run('args[0](0)', tick, delayFrames=1)
print('filling for', FILL, 's')
