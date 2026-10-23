"""DEV ONLY: capture the blob round 1 variants on one input, note rough cook times, then stop
them cooking. Settings come from dev/protos/blob/cap_settings.py (rewritten before each run):
INPUT (0 Movie.4, 1 Movie.2, 2 synthetic), TAG (suffix for the frame names), VARIANTS, AT, EXTRA
(name -> path of extra TOPs to save, e.g. a tracker's own drawn bounds).
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
exec(compile(open(os.path.join(_HERE, 'cap_settings.py')).read(), 'cap_settings.py', 'exec'), globals())

host = op(TDLIB_PARENT)
OUT = os.path.join(_ROOT, 'dev', 'out', 'blob', 'round1')
inp = host.op('inputs')
inp.allowCooking = True
inp.op('sel').par.index = INPUT
comps = [host.op(v) for v in VARIANTS]
for c in comps:
    c.allowCooking = True
tops = {'{}_{}'.format(c.name, TAG): c.op('out') for c in comps}
for name, path in EXTRA.items():
    tops[name] = op(path)
capture(tops, OUT, at=AT)


SAMPLES = {}


def sample():
    for c in comps:
        for o in c.findChildren():
            if (o.isTOP or o.isCHOP or o.isDAT or o.isSOP) and o.name != 'keep':
                SAMPLES.setdefault((c.name, o.name), []).append(
                    (o.cookTime, getattr(o, 'gpuCookTime', 0) or 0, o.cookAbsFrame))


def med(v):
    v = sorted(v)
    return v[len(v) // 2] if v else 0


def costs():
    lines = ['median of {} samples over the capture (ms; cpu/gpu); indicative only, TD is shared'.format(
        len(next(iter(SAMPLES.values()), [])))]
    for c in comps:
        rows = [(name, med([x[0] for x in v]), med([x[1] for x in v]), len(set(x[2] for x in v)))
                for (cn, name), v in SAMPLES.items() if cn == c.name]
        cpu = sum(r[1] for r in rows)
        gpu = sum(r[2] for r in rows)
        top = sorted(rows, key=lambda r: -(r[1] + r[2]))[:5]
        lines.append('{} {}: cpu {:.2f} gpu {:.2f} | {}'.format(c.name, TAG, cpu, gpu, ', '.join(
            '{} {:.2f}/{:.2f} ({} cooks seen)'.format(*r) for r in top)))
        if c.op('info') and c.op('info').isCHOP and c.op('info')['num_blobs'] is not None:
            lines.append('   num_blobs {}'.format(c.op('info')['num_blobs'].eval()))
    with open(os.path.join(OUT, 'costs_{}.txt'.format(TAG)), 'w') as f:
        f.write('\n'.join(lines) + '\n')


for k in range(9):
    run('args[0]()', sample, delayMilliSeconds=int((AT[0] + (AT[-1] - AT[0]) * k / 8.0) * 1000) - 150)


# DEV ONLY: for d_beat, also save one frame just after the first beat (the sample WAV hits about
# every 2.7 s, so the timed frames rarely land on a flash).
watch = None
if host.op('d_beat') in comps:
    if host.op('beatshot'):
        host.op('beatshot').destroy()
    watch = host.create(chopexecuteDAT, 'beatshot')
    watch.par.chop = inp.op('count').path
    watch.par.valuechange = True
    watch.par.offtoon = False
    watch.par.ontooff = False
    watch.text = ('import os\n'
                  'def onValueChange(channel, sampleIndex, val, prev):\n'
                  '    if me.fetch("shot", False):\n'
                  '        return\n'
                  '    me.store("shot", True)\n'
                  '    run("op(args[0]).save(args[1])", {!r}, {!r}, delayFrames=3)\n').format(
        host.op('d_beat/out').path, os.path.join(OUT, 'd_beatflash_{}_0.png'.format(TAG)))


def stop():
    for c in comps:
        c.allowCooking = False
    if watch is not None and watch.valid:
        watch.destroy()


run('args[0]()', costs, delayMilliSeconds=int(AT[-1] * 1000) + 200)
run('args[0]()', stop, delayMilliSeconds=int(AT[-1] * 1000) + 1500)
