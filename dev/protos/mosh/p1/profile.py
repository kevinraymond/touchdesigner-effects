"""DEV ONLY (datamosh pass 1): per-operator cook times of a copy of the effect on the dancer clip, 40 frames
per mode (indicative: other sessions share this GPU). Writes dev/out/datamosh/profile.txt; stops everything."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'profile.txt')
host = op(TDLIB_PARENT)
for c in list(host.children):
    if c.name.startswith('v_') or c.name == 'prof':
        c.destroy()
v = host.copy(host.op('datamosh'), name='prof')
v.allowCooking = True
clip = host.op('clip')
clip.par.play = True
v.inputConnectors[0].connect(clip)
ACC, WALL = {}, {}
LINES = []


def stop():
    for c in op(TDLIB_PARENT).findChildren(type=COMP, depth=1):
        c.allowCooking = False
    op(TDLIB_PARENT + '/clip').par.play = False


def sample(i):
    try:
        step(i)
    except Exception as e:
        open(OUTF, 'w').write('error at {}: {!r}\n'.format(i, e))
        open(OUTF + '.done', 'w').write('err\n')
        stop()
        return
    if i < 99:
        run('args[0](args[1])', sample, i + 1, delayFrames=1)


def step(i):
    mode = 'smear' if i < 50 else 'blocks'
    v.par.Mode = mode
    out = v.op('out_top')
    out.cook()
    if i % 50 < 10:
        return
    if i % 50 == 10:
        WALL[mode] = [absTime.seconds, absTime.frame]
    a = ACC.setdefault(mode, {})
    for o in v.findChildren():
        if (o.isTOP or o.isCHOP) and o.cookAbsFrame == absTime.frame:
            r = a.setdefault(o.name, [0.0, 0.0, 0])
            r[0] += o.gpuCookTime if o.isTOP else 0.0
            r[1] += o.cpuCookTime
            r[2] += 1
    if i % 50 == 49:
        fps = (absTime.frame - WALL[mode][1]) / max(absTime.seconds - WALL[mode][0], 1e-6)
        rows = sorted(a.items(), key=lambda kv: -kv[1][0])
        LINES.append('{}: TD {:.1f} fps over the window; total gpu {:.2f} ms, cpu {:.2f} ms per frame (39 frames)'.format(
            mode, fps, sum(r[0] for r in a.values()) / 39, sum(r[1] for r in a.values()) / 39))
        for name, (g, c, n) in rows[:14]:
            LINES.append('  {:16s} gpu {:6.3f} cpu {:6.3f} (cooked {} of 39 frames)'.format(name, g / 39, c / 39, n))
    if i == 99:
        open(OUTF, 'w').write('\n'.join(LINES) + '\n')
        open(OUTF + '.done', 'w').write('ok\n')
        stop()


run('args[0](args[1])', sample, 0, delayFrames=1)
print('profiling')
