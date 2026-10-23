"""DEV ONLY. Per-operator GPU/CPU cook times inside the datamosh prototypes over ~1 s of frames
(indicative only: other sessions share this GPU). Writes dev/out/mosh/profile.txt, then stops."""
import os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'mosh', 'profile.txt')
host = op(TDLIB_PARENT)
for c in host.children:
    c.allowCooking = True
host.op('src').par.Source = 3
ACC = {}
FPS = [0.0]
T0 = [0.0]


def sample(i):
    h = op(TDLIB_PARENT)
    if i == 0:
        T0[0] = (absTime.seconds, absTime.frame)
    if i == 39:
        FPS[0] = (absTime.frame - T0[0][1]) / max(absTime.seconds - T0[0][0], 1e-6)
    for o in h.findChildren(type=TOP):
        if o.cookAbsFrame != absTime.frame:
            continue
        a = ACC.setdefault(o.path, [0.0, 0.0, 0])
        a[0] += o.cpuCookTime; a[1] += o.gpuCookTime; a[2] += 1
    if i == 39:
        for c in h.children:
            c.allowCooking = False
        rows = sorted(ACC.items(), key=lambda kv: -kv[1][1])
        with open(OUTF, 'w') as f:
            f.write('mean ms over {} frames: gpu, cpu (TD fps over the window {:.1f})\n'.format(max(v[2] for v in ACC.values()), FPS[0]))
            for p, (c, g, n) in rows[:30]:
                f.write('  {:50s} gpu {:7.3f} cpu {:6.3f}\n'.format(p, g / n, c / n))
        open(OUTF + '.done', 'w').write('ok')


for i in range(40):
    run('args[0](args[1])', sample, i, delayFrames=30 + i)
print('profiling')
