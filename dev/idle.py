"""DEV ONLY. Inside TouchDesigner: check that an effect does nothing while its output is unused
(docs/TD_IDIOMS.md C5), the way the review asks for it:

    TD_ARGS='ascii datamosh' dev/td.sh dev/idle.py      # those effects (none named: every one)
    dev/td.sh --pull dev/out/idle/done
    cat dev/out/idle/report.txt

Each effect is loaded from effects/<n>/<n>.tox into TDLIB_PARENT with its node viewer off and
nothing downstream, first with nothing wired, then with dev/testbed.py's clip and stress beat on
its inputs (a beat that changes every frame, as Fosfora's signal does). Each time it waits
SETTLE frames, then counts the operators inside whose cookAbsFrame moves over WATCH frames: the
answer should be 0. As a control it then pulls out_top every frame for a few frames, which must
make operators cook, or the check proves nothing.
"""

import glob
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_HERE, 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
OUT = os.path.join(_HERE, 'out', 'idle')
SETTLE, WATCH, CONTROL = 30, 60, 10


def main():
    host = op(TDLIB_PARENT)
    for o in list(host.children):
        if o.valid:  # destroying an operator also destroys the DATs docked to it
            o.destroy()
    os.makedirs(OUT, exist_ok=True)
    for f in ('report.txt', 'done'):
        if os.path.exists(os.path.join(OUT, f)):
            os.remove(os.path.join(OUT, f))
    names, opts = test_args(globals().get('TDLIB_ARGS') or [])
    paths = [p for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox')))
             if not names or os.path.splitext(os.path.basename(p))[0] in names]
    clip, beat = testbed(host, dict(opts, beat='stress'))
    runs = []
    for path in paths:
        for wired in (False, True):
            runs.append((path, wired))
    lines = []
    state = {}

    def begin(i):
        for o in list(host.children):
            if o.valid and o.isCOMP:
                o.destroy()
        path, wired = runs[i]
        fx = host.loadTox(path)
        fx.viewer = False
        if wired:
            fx.inputConnectors[0].connect(clip)
            if len(fx.inputConnectors) > 1:
                fx.inputConnectors[1].connect(beat)
        state.update(i=i, fx=fx, n=0, before=None)
        run('args[0]()', tick, delayFrames=1)

    def frames(fx):
        return {o.path: o.cookAbsFrame for o in fx.findChildren()}

    def tick():
        fx, n = state['fx'], state['n']
        state['n'] = n + 1
        if n == SETTLE:
            state['before'] = frames(fx)
        elif n == SETTLE + WATCH:
            after = frames(fx)
            state['idle'] = sorted(p.rsplit('/', 1)[-1] for p, f in after.items() if f != state['before'][p])
            state['before'] = after
        elif SETTLE + WATCH < n <= SETTLE + WATCH + CONTROL:
            fx.op('out_top').cook(force=True)  # the control: pulling the output must make things cook
        elif n > SETTLE + WATCH + CONTROL:
            after = frames(fx)
            control = sum(1 for p, f in after.items() if f != state['before'][p])
            path, wired = runs[state['i']]
            lines.append('{} {}: {} of {} operators cooked over {} frames unused{}; control {} cooked'.format(
                os.path.splitext(os.path.basename(path))[0], 'wired' if wired else 'unwired',
                len(state['idle']), len(after), WATCH,
                ' ({})'.format(', '.join(state['idle'][:8])) if state['idle'] else '', control))
            if state['i'] + 1 < len(runs):
                begin(state['i'] + 1)
            else:
                with open(os.path.join(OUT, 'report.txt'), 'w') as f:
                    f.write('\n'.join(lines) + '\n')
                open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')
                for o in list(host.children):
                    if o.valid:
                        o.allowCooking = False
                run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=2)
            return
        run('args[0]()', tick, delayFrames=1)

    if not runs:
        print('no effects to check')
        return
    begin(0)
    print('checking {} runs of {} frames each'.format(len(runs), SETTLE + WATCH + CONTROL))


main()
