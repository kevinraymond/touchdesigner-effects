"""DEV ONLY. Inside TouchDesigner: when the showreel's Cycle moves on. Loads bundles/showreel/showreel.tox
fresh with View Cycle and Every 1, pulls its picture every frame for SECONDS, first with nothing on
input 2, then with dev/testbed.py's stress beat (2 bars a second), and writes the times the view
changed to dev/out/showreel_cycle/report.txt (expected: never closer than 2 s).

    dev/td.sh dev/probes/showreel_cycle.py && dev/td.sh --pull dev/out/showreel_cycle/done
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'showreel_cycle')
SECONDS = 9.0
os.makedirs(OUT, exist_ok=True)
for f in ('report.txt', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT) or op('/').create(baseCOMP, TDLIB_PARENT.strip('/'))
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, dict(clip='b1_dancer', beat='stress'))
reel = host.loadTox(os.path.join(_ROOT, 'bundles', 'showreel', 'showreel.tox'))
reel.inputConnectors[0].connect(clip)
reel.par.View, reel.par.Every = 'cycle', 1
lines = []
runs = [('nothing on input 2', None), ('stress beat', beat)]


def begin(r):
    name, src = runs[r]
    if src is None:
        reel.inputConnectors[1].disconnect()
    else:
        reel.inputConnectors[1].connect(src)
    st = dict(start=absTime.seconds, last=None, changes=[])
    run('args[0](args[1], args[2])', tick, r, st, delayFrames=1)


def tick(r, st):
    reel.op('out_top').cook()
    t = absTime.seconds - st['start']
    i = reel.op('view').par.index.eval()
    if st['last'] is not None and i != st['last']:
        st['changes'].append(round(t, 2))
    st['last'] = i
    if t < SECONDS:
        run('args[0](args[1], args[2])', tick, r, st, delayFrames=1)
        return
    gaps = [round(b - a, 2) for a, b in zip(st['changes'], st['changes'][1:])]
    lines.append('{}: view changed at {} s; gaps {}'.format(runs[r][0], st['changes'], gaps))
    if r + 1 < len(runs):
        begin(r + 1)
        return
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('ok\n')
    for o in list(host.children):
        if o.valid:
            o.destroy()


begin(0)
print('watching Cycle for 2 x {:g} s'.format(SECONDS))
