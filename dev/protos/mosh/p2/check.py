"""DEV ONLY (datamosh pass 2), in TDLIB_PARENT, about 20 s, then removes everything it made:
A. under dev/testbed.py's stress beat, how many skips and keyframes pass the gate at each Flashing setting;
B. Blocks' cost per frame, measured as dev/perf.py does;
C. C5: loaded with nothing downstream and no viewer, which children still cook.
Writes dev/out/datamosh/p2_check.txt (+ .done)."""
import os
import time
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_check.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, {'clip': 'b1_dancer', 'beat': 'stress'})
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox'))
fx.inputConnectors[0].connect(clip)
fx.inputConnectors[1].connect(beat)
view = mk(host, nullTOP, 'view', 400, 0, comment='pulls')
view.inputConnectors[0].connect(fx.outputConnectors[0])
L = []
S = {'phase': 'A', 'i': 0, 'n': 0, 'prev': {}, 'cnt': {}, 'cpu': [], 'gpu': []}
SETTINGS = ('off', 'calm', 'wcag')
A_SECONDS, B_SETTLE, B_SECONDS, C_SECONDS = 3.0, 2.0, 6.0, 1.5


def stop_all():
    for o in list(op(TDLIB_PARENT).children):
        if o.isCOMP:
            o.allowCooking = False
    c = op(TDLIB_PARENT + '/clip')
    if c is not None:
        c.par.play = False


def finish():
    open(OUTF, 'w').write('\n'.join(L) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    stop_all()
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=5)


def tick():
    try:
        step()
    except Exception as e:
        L.append('error {!r}'.format(e))
        finish()


def step():
    now = absTime.seconds
    if S['phase'] == 'A':
        if S['n'] == 0:
            fx.par.Flashing = SETTINGS[S['i']]
            S.update(t0=now, cnt={'skip': 0, 'key': 0, 'skip_env>0': 0, 'key_env>0': 0}, prev={'skip': 0, 'key': 0})
        view.cook()
        g = fx.op('flash')
        for ch in ('skip', 'key'):
            v = g[ch][0]
            if v > 0.5 and S['prev'][ch] <= 0.5:
                S['cnt'][ch] += 1
            S['prev'][ch] = v
        S['cnt']['skip_env>0'] += fx.op('skip_env')['skip'][0] > 0.01
        S['cnt']['key_env>0'] += fx.op('key_env')['key'][0] > 0.01
        S['n'] += 1
        if now - S['t0'] >= A_SECONDS:
            a = fx.op('audio')
            L.append('A Flashing {}: in {:.1f} s, gate passed {} skips and {} keyframes; frames with skip_env {} / key_env {} '
                     '(of {}); audio source {:.0f}, bars {:.0f}, drops {:.0f}, sections {:.0f}'.format(
                         SETTINGS[S['i']], now - S['t0'], S['cnt']['skip'], S['cnt']['key'], S['cnt']['skip_env>0'],
                         S['cnt']['key_env>0'], S['n'], a['source'][0], a['bar_count'][0], a['drop_count'][0],
                         a['section_count'][0]))
            S['i'] += 1
            S['n'] = 0
            if S['i'] == len(SETTINGS):
                fx.par.Flashing = 'calm'
                fx.par.Mode = 'blocks'
                S.update(phase='B', t0=now, prev_wall=time.time(), frame=[])
    elif S['phase'] == 'B':
        view.cook()
        wall = time.time()
        if now - S['t0'] >= B_SETTLE:
            cpu = gpu = 0.0
            for o in fx.findChildren():
                if o.cookAbsFrame >= absTime.frame - 1:
                    cpu += o.cpuCookTime or 0.0
                    gpu += getattr(o, 'gpuCookTime', 0.0) or 0.0
            S['cpu'].append(cpu)
            S['gpu'].append(gpu)
            S['frame'].append((wall - S['prev_wall']) * 1000)
        S['prev_wall'] = wall
        if now - S['t0'] >= B_SETTLE + B_SECONDS:
            n = max(len(S['cpu']), 1)
            p95 = lambda v: sorted(v)[min(int(len(v) * 0.95), len(v) - 1)]
            L.append('B Blocks, stress beat, 1280x720: CPU {:.2f} ms (95% {:.2f}), GPU {:.2f} ms (95% {:.2f}) over {} frames; '
                     'TD {:.0f} fps'.format(sum(S['cpu']) / n, p95(S['cpu']), sum(S['gpu']) / n, p95(S['gpu']), n,
                                            1000 / (sum(S['frame']) / max(len(S['frame']), 1))))
            fx.par.Mode = 'smear'
            view.inputConnectors[0].disconnect()
            fx.viewer = False
            S.update(phase='C', t0=now, f0=absTime.frame, before={o.path: o.cookAbsFrame for o in fx.findChildren()})
    else:
        if now - S['t0'] >= C_SECONDS:
            cooked = [o.name for o in fx.findChildren() if o.cookAbsFrame > S['f0']]
            L.append('C nothing downstream, viewer off, allowCooking on, clip playing: {} frames later, children that '
                     'cooked: {}'.format(absTime.frame - S['f0'], cooked or 'none'))
            finish()
            return
    run('args[0]()', tick, delayFrames=1)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0]()', tick, delayFrames=2)
print('checking; about', len(SETTINGS) * A_SECONDS + B_SETTLE + B_SECONDS + C_SECONDS, 's')
