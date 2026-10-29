"""DEV ONLY. Whether lib optical_flow()'s passes cook in a running effect: load each .tox named (a path from the repo
root), wire the clip, its depth and the stress beat in, pull its output every frame for 2 s, then list how many times
each of optical_flow()'s TOPs cooked, and every TOP inside that never did. Caustics and Temporal Resonator 0.1.0 read
only the luma and the clock, so their lk8, lk4 and lum8p should never cook (board #4797).

    TD_ARGS='dev/out/flow_cooks/old/caustics.tox effects/caustics/caustics.tox' dev/td.sh dev/probes/flow_cooks.py
    dev/td.sh --pull dev/out/probes/flow_cooks/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'probes', 'flow_cooks')
FLOW = ('lum8', 'lum8p', 'lum4', 'lum4p', 'lum2', 'lum2p', 'change', 'change_avg', 'clock', 'lk8', 'lk4')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
paths, opts = test_args(TDLIB_ARGS)
clip, beat = testbed(host, opts)
lines = []


def begin(i):
    for o in list(host.children):
        if o.valid and o.isCOMP:
            o.destroy()
    fx = host.loadTox(os.path.join(_ROOT, paths[i]))
    fx.viewer = False
    wire(fx, clip, beat)
    view = mk(host, nullTOP, 'view', [fx.outputConnectors[0]], comment='Pulls the output every frame.', at=(400, 0))
    run('args[0](args[1], args[2], args[3], 0, {})', tick, i, fx, view, delayFrames=1)


def tick(i, fx, view, n, start):
    view.cook(force=True)
    if n == 30:
        start.update((o.name, o.totalCooks) for o in fx.findChildren(type=TOP, depth=1))
    if n < 150:
        run('args[0](args[1], args[2], args[3], args[4], args[5])', tick, i, fx, view, n + 1, start, delayFrames=1)
        return
    tops = {o.name: o.totalCooks - start.get(o.name, 0) for o in fx.findChildren(type=TOP, depth=1)}
    lines.append('{} ({} TOPs, out_top cooked {} times in 120 frames)'.format(paths[i], len(tops), tops['out_top']))
    lines.append('  optical_flow: ' + ', '.join('{} {}'.format(k, tops[k]) for k in FLOW if k in tops))
    lines.append('  never cooked: ' + ', '.join(sorted(k for k, c in tops.items() if c == 0)))
    if i + 1 < len(paths):
        begin(i + 1)
        return
    open(os.path.join(OUT, 'done'), 'w').write('\n'.join(lines) + '\n')
    for o in list(host.children):
        if o.valid:
            o.allowCooking = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=2)


begin(0)
print('pulling {} effects for 150 frames each'.format(len(paths)))
