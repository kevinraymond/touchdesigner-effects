"""DEV ONLY. What each point cloud prototype costs (look.py builds them in TDLIB_PARENT; run it
first): pulls one variant at a time for SECONDS after SETTLE, adding up the CPU and GPU cook times
of its operators each frame, as dev/perf.py does for an effect. Camera at a side angle.

    dev/td.sh dev/protos/point_cloud/cost.py
    dev/td.sh --pull dev/out/point_cloud/cost/done; cat dev/out/point_cloud/cost/report.txt
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
OUT = os.path.join(_ROOT, 'dev', 'out', 'point_cloud', 'cost')
os.makedirs(OUT, exist_ok=True)
for f in ('done', 'report.txt'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
SETTLE, SECONDS = 1.0, 3.0
host = op(TDLIB_PARENT)
names = sorted(o.name[len('pos_'):] for o in host.findChildren(name='pos_*', depth=1, type=TOP))
ends = {n: host.op('norm_' + n) or host.op('render_' + n) for n in names}
cam = host.op('cam')
cam.par.tx, cam.par.ty = 1.0, 0.3
state = {'i': -1, 'lines': ['{} {} ({} s each after {} s)'.format(app.product, app.build, SECONDS, SETTLE)]}


def parts(n):
    return [o for o in (host.op(p + n) for p in ('pos_', 'render_', 'pass_', 'norm_', 'geo_')) if o]


def begin(i):
    state.update(i=i, start=absTime.seconds + SETTLE, cpu=[], gpu=[])


def tick():
    n = names[state['i']]
    ends[n].cook(force=True)
    if absTime.seconds >= state['start']:
        cpu = gpu = 0.0
        for o in parts(n):
            if o.cookAbsFrame >= absTime.frame - 1:
                cpu += o.cpuCookTime or 0.0
                gpu += getattr(o, 'gpuCookTime', 0.0) or 0.0
        state['cpu'].append(cpu)
        state['gpu'].append(gpu)
    if absTime.seconds < state['start'] + SECONDS:
        run('args[0]()', tick, delayFrames=1)
        return
    k = max(len(state['gpu']), 1)
    state['lines'].append('{}: CPU {:.2f} ms, GPU {:.2f} ms (max {:.2f}), {} frames'.format(
        n, sum(state['cpu']) / k, sum(state['gpu']) / k, max(state['gpu'] or [0]), len(state['gpu'])))
    if state['i'] + 1 < len(names):
        begin(state['i'] + 1)
        run('args[0]()', tick, delayFrames=1)
        return
    with open(os.path.join(OUT, 'report.txt'), 'w') as f:
        f.write('\n'.join(state['lines']) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('ok\n')


begin(0)
tick()
print('measuring', names)
