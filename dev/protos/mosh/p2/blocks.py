"""DEV ONLY (datamosh pass 2): Blocks on the dancer with dev/testbed.py's stress beat: frames through the loop cut
(dev/out/datamosh/p2_blocks), then cost per frame as dev/perf.py measures it (2 s settle, 6 s).
Writes dev/out/datamosh/p2_blocks.txt; stops and removes everything after."""
import os, time
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')   # testbed.py finds it from __file__, which is this script
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_blocks.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, {'clip': 'b1_dancer', 'beat': 'stress'})
clip.par.cuepoint, clip.par.cuepointunit = 8.4, 'seconds'
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox'))
fx.par.Mode = 'blocks'
fx.inputConnectors[0].connect(clip)
fx.inputConnectors[1].connect(beat)
view = mk(host, nullTOP, 'view', 400, 0, comment='pulls')
view.inputConnectors[0].connect(fx.outputConnectors[0])
S = {'cpu': [], 'gpu': [], 'frame': [], 'ops': {}}
L = ['clip {}'.format(os.path.basename(clip.par.file.eval()))]


def measure():
    S.update(t0=absTime.seconds, prev=time.time())
    run('args[0]()', tick, delayFrames=1)


def tick():
    view.cook()
    now, wall = absTime.seconds, time.time()
    if now - S['t0'] >= 2.0:
        cpu = gpu = 0.0
        for o in fx.findChildren():
            if o.cookAbsFrame >= absTime.frame - 1:
                c, g = o.cpuCookTime or 0.0, getattr(o, 'gpuCookTime', 0.0) or 0.0
                cpu, gpu = cpu + c, gpu + g
                t = S['ops'].setdefault(o.name, [0.0, 0.0])
                t[0], t[1] = t[0] + c, t[1] + g
        S['cpu'].append(cpu)
        S['gpu'].append(gpu)
        S['frame'].append((wall - S['prev']) * 1000)
    S['prev'] = wall
    if now - S['t0'] < 8.0:
        run('args[0]()', tick, delayFrames=1)
        return
    n = max(len(S['cpu']), 1)
    p95 = lambda v: sorted(v)[min(int(len(v) * 0.95), len(v) - 1)]
    top = sorted(S['ops'].items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:6]
    L.append('Blocks, 1280x720, stress beat: CPU {:.2f} ms (95% {:.2f}), GPU {:.2f} ms (95% {:.2f}) over {} frames; TD {:.0f} fps; '
             'most: {}'.format(sum(S['cpu']) / n, p95(S['cpu']), sum(S['gpu']) / n, p95(S['gpu']), n,
                               1000 / (sum(S['frame']) / max(len(S['frame']), 1)),
                               ', '.join('{} {:.2f}'.format(k, (c + g) / n) for k, (c, g) in top)))
    open(OUTF, 'w').write('\n'.join(L) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    fx.allowCooking = False
    clip.par.play = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=30)


for f in (OUTF + '.done', os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_blocks', 'done')):
    if os.path.exists(f):
        os.remove(f)
run("args[0].par.cuepulse.pulse()", clip, delayFrames=1)
capture({'0_input': clip, 'blocks': fx.op('out_top')}, os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_blocks'),
        at=(1.5, 1.9, 2.3, 2.8, 3.5), keep_cooking=True)
run('args[0]()', measure, delayMilliSeconds=4000)
print('blocks: frames, then cost')
