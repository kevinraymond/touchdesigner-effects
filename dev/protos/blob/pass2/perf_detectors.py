"""DEV ONLY. blob_track pass 2: dev/perf.py's measurement (same sampling, same testbed) for the
two detectors one after the other, twice each, so their costs compare under the same conditions.
    TD_PARENT=/tdlib_dev_blob dev/td.sh dev/protos/blob/pass2/perf_detectors.py
    dev/td.sh --pull dev/out/blob_track/perf/done
Destroys everything it made when done.
"""
import os
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'blob_track', 'perf')
SETTLE, SECONDS = 3.0, 8.0
ARGS = list(globals().get('TDLIB_ARGS') or [])
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))


def pct(values, p):
    v = sorted(values)
    return v[min(int(len(v) * p), len(v) - 1)] if v else 0.0


host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
_, opts = test_args(ARGS)
clip, beat = testbed(host, opts)
view = mk(host, nullTOP, 'view', 400, 0, comment='x')
runs = []
for k, det in enumerate(('blobtrack', 'grid', 'blobtrack', 'grid')):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'blob_track', 'blob_track.tox'))
    fx.name = 'p{}_{}'.format(k, det)
    fx.par.Detector = det
    fx.inputConnectors[0].connect(clip)
    if beat is not None:
        fx.inputConnectors[1].connect(beat)
    fx.allowCooking = False
    runs.append(fx)
lines = ['Per frame at 1280 x 720, {} clip, {} build {}; {:g} s each after {:g} s.'.format(
    opts['clip'], app.product, app.build, SECONDS, SETTLE)]
state = {'i': -1}


def begin(i):
    state.update(i=i, start=absTime.seconds + SETTLE, cpu=[], gpu=[], frame=[], ops={}, prev=time.time())
    for fx in runs:
        fx.allowCooking = fx is runs[i]
    view.inputConnectors[0].connect(runs[i].outputConnectors[0])


def tick():
    fx = runs[state['i']]
    view.cook()
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
    top = sorted(state['ops'].items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:6]
    fps = 1000 / (sum(state['frame']) / max(len(state['frame']), 1))
    lines.append('{}: CPU {:.2f} ms (95% {:.2f}), GPU {:.2f} ms (95% {:.2f}); {:.0f} fps; most: {}'.format(
        fx.name, sum(state['cpu']) / n, pct(state['cpu'], 0.95), sum(state['gpu']) / n, pct(state['gpu'], 0.95), fps,
        ', '.join('{} {:.2f}/{:.2f}'.format(k, c / n, g / n) for k, (c, g) in top)))
    if state['i'] + 1 < len(runs):
        begin(state['i'] + 1)
        run('args[0]()', tick, delayFrames=1)
        return
    with open(os.path.join(OUT, 'report.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')
    clip.par.play = False
    for o in list(host.children):
        if o.isCOMP:
            o.allowCooking = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=2)


begin(0)
run('args[0]()', tick, delayFrames=1)
print('measuring', [fx.name for fx in runs])
