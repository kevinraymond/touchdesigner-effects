"""DEV ONLY. Inside TouchDesigner: what each effect costs per frame at 1280 x 720, for the
performance note on its docs page (docs/TD_IDIOMS.md C7):

    TD_ARGS='ascii' dev/td.sh dev/perf.py     # those effects (none named: every one)
    TD_ARGS='datamosh Mode=blocks' dev/td.sh dev/perf.py   # a parameter other than its default
    dev/td.sh --pull dev/out/perf/b1_dancer/done           # clip=<name> in TD_ARGS: another clip
    cat dev/out/perf/b1_dancer/report.txt

Each effect is loaded from effects/<n>/<n>.tox (a bundle when named) into TDLIB_PARENT with its
default parameters and dev/testbed.py's input (the test clip, a busy Fosfora-shaped beat), with
nothing else of ours cooking. After SETTLE seconds it samples SECONDS seconds: every frame, the CPU
and GPU cook time of everything inside the effect that cooked, and the frame's wall-clock length.
The report gives the mean and the 95th percentile, the operators that cost the most, and the frame
rate TouchDesigner held meanwhile (capped by the project's cook rate). Measure with the Mac
otherwise idle: other sessions' work lands in the frame times, though not in the effect's own cook
times.
"""

import glob
import os
import time

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_HERE, 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
OUT = os.path.join(_HERE, 'out', 'perf')
SETTLE, SECONDS = 3.0, 10.0


def pct(values, p):
    v = sorted(values)
    return v[min(int(len(v) * p), len(v) - 1)] if v else 0.0


def main():
    host = op(TDLIB_PARENT)
    for o in list(host.children):
        if o.valid:  # destroying an operator also destroys the DATs docked to it
            o.destroy()
    names, opts = test_args(globals().get('TDLIB_ARGS') or [])
    out = os.path.join(OUT, '_'.join([opts['clip']] + ([] if opts['beat'] == 'stress' else ['no_beat']) +
                                     ['{}-{}'.format(k, v) for k, v in opts.items() if k[:1].isupper()]))
    os.makedirs(out, exist_ok=True)
    for f in ('report.txt', 'done'):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    paths = [p for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox')))
             if not names or os.path.splitext(os.path.basename(p))[0] in names]
    paths += [p for p in sorted(glob.glob(os.path.join(_ROOT, 'bundles', '*', '*.tox')))
              if os.path.splitext(os.path.basename(p))[0] in names]  # bundles by name only
    clip, beat = testbed(host, opts)
    overrides = {k: v for k, v in opts.items() if k[:1].isupper()}
    view = mk(host, nullTOP, 'view', 400, 0, comment='Pulls the effect every frame.')
    effects = []
    for path in paths:
        fx = host.loadTox(path)
        fx.nodeX, fx.nodeY = 0, 300 * len(effects)
        fx.inputConnectors[0].connect(clip)
        if beat is not None and len(fx.inputConnectors) > 1:
            fx.inputConnectors[1].connect(beat)
        for k, v in overrides.items():  # Mode=blocks and the like: measure a setting other than the default
            if hasattr(fx.par, k):
                setattr(fx.par, k, v)
        fx.allowCooking = False
        effects.append(fx)
    lines = ['Per frame at {} x {}, {}, {} build {}; {:g} s each after {:g} s.'.format(
        WINDOW_W, WINDOW_H, ', '.join('{}={}'.format(k, v) for k, v in overrides.items()) or 'defaults',
        app.product, app.build, SECONDS, SETTLE)]
    state = {'i': -1}

    def begin(i):
        state.update(i=i, start=absTime.seconds + SETTLE, cpu=[], gpu=[], frame=[], ops={}, prev=time.time())
        for fx in effects:
            fx.allowCooking = fx is effects[i]
        view.inputConnectors[0].connect(effects[i].outputConnectors[0])

    def tick():
        fx = effects[state['i']]
        view.cook()  # nothing views it: pull the effect every frame
        now, wall = absTime.seconds, time.time()
        if now >= state['start']:
            cpu = gpu = 0.0
            for o in fx.findChildren():
                if o.cookAbsFrame >= absTime.frame - 1:
                    c, g = o.cpuCookTime or 0.0, getattr(o, 'gpuCookTime', 0.0) or 0.0
                    cpu, gpu = cpu + c, gpu + g
                    tot = state['ops'].setdefault(o.name, [0.0, 0.0])
                    tot[0], tot[1] = tot[0] + c, tot[1] + g
            state['cpu'].append(cpu)
            state['gpu'].append(gpu)
            state['frame'].append((wall - state['prev']) * 1000)
        state['prev'] = wall
        if now < state['start'] + SECONDS:
            run('args[0]()', tick, delayFrames=1)
            return
        n = max(len(state['cpu']), 1)
        top = sorted(state['ops'].items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:5]
        fps = 1000 / (sum(state['frame']) / max(len(state['frame']), 1))
        lines.append('{}: CPU {:.2f} ms (95% {:.2f}), GPU {:.2f} ms (95% {:.2f}); TouchDesigner held '
                     '{:.0f} fps (cook rate {:g}); most: {}'.format(
                         fx.name, sum(state['cpu']) / n, pct(state['cpu'], 0.95), sum(state['gpu']) / n,
                         pct(state['gpu'], 0.95), fps, project.cookRate,
                         ', '.join('{} {:.2f}'.format(k, (c + g) / n) for k, (c, g) in top)))
        if state['i'] + 1 < len(effects):
            begin(state['i'] + 1)
            run('args[0]()', tick, delayFrames=1)
            return
        with open(os.path.join(out, 'report.txt'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        open(os.path.join(out, 'done'), 'w').write('report.txt\n')
        for o in list(host.children):
            o.allowCooking = False
        run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=2)

    if not effects:
        print('no effects to measure')
        return
    begin(0)
    run('args[0]()', tick, delayFrames=1)
    print('measuring {} for {:g} s each after {:g} s'.format(', '.join(fx.name for fx in effects), SECONDS, SETTLE))


main()
