"""DEV ONLY. Capture the ASCII round-1 variants (build_round1.py first): one column per test
input, then a stats file (indicative cook times, beat-chain values) and stop cooking.

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/shoot_round1.py
    TD_PARENT=/tdlib_dev_ascii dev/td.sh --pull dev/out/ascii/round1/done
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())

r = op(TDLIB_PARENT + '/r1')
r.allowCooking = True
OUT = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'round1')
DEBUG = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'debug')
os.makedirs(DEBUG, exist_ok=True)
TOPS = {'a_atlas': 'a_render', 'b_edges': 'b_render', 'c_color': 'c_render', 'd_rain': 'd_glow', 'e_beat': 'e_render', 'e_beat_peak': 'e_peak'}
AT = (1.5, 3.5, 5.5, 7.5, 9.5)
log = []


def pick(i):
    r.op('pick').par.index = i


t0 = absTime.seconds
PREFIXES = ('a_', 'b_', 'c_', 'd_', 'e_', 'f_')
cook = {p: [0.0, 0.0, 0] for p in PREFIXES}


def sample():
    vals = ['{}={:.3f}'.format(n, r.op(n)[0].eval()) for n in ('e_rms', 'e_ratio', 'e_trig', 'e_count')
            if r.op(n) is not None and r.op(n).numChans]
    log.append('{:.2f} {}'.format(absTime.seconds, ' '.join(vals)))
    for prefix in PREFIXES:
        ops = [o for o in r.children if o.name.startswith(prefix) and (o.isTOP or o.isCHOP)
               and o.OPType not in ('textTOP',) and o.name != 'e_peak']
        if absTime.seconds - t0 < 2.0:
            return
        cook[prefix][0] += sum(o.cpuCookTime for o in ops)
        cook[prefix][1] += sum(o.gpuCookTime for o in ops)
        cook[prefix][2] += 1


def stats():
    lines = ['cook ms per frame, cpu / gpu, mean of {} samples; indicative only: other sessions share this '
             'TouchDesigner. f_ is the cell pass C, D and E share.'.format(cook['a_'][2])]
    for prefix, (cpu, gpu, n) in cook.items():
        lines.append('{} cpu {:.3f} gpu {:.3f}'.format(prefix, cpu / max(n, 1), gpu / max(n, 1)))
    o = r.op('a_render')
    lines.append('a_render attrs: cookTime {} cpuCookTime {} gpuCookTime {}'.format(
        o.cookTime, o.cpuCookTime, o.gpuCookTime))
    with open(os.path.join(OUT, 'stats.txt'), 'w') as f:
        f.write('\n'.join(lines + log) + '\n')
    r.op('a_atlas').save(os.path.join(DEBUG, 'a_atlas.png'))
    r.op('b_edge').save(os.path.join(DEBUG, 'b_edge.png'))


for i, t in enumerate(AT):
    run('args[0](args[1])', pick, i, delayMilliSeconds=int(max(0.0, t - 1.2) * 1000))
for k in range(int(AT[-1] * 4) - 2):
    run('args[0]()', sample, delayMilliSeconds=250 * k + 400)
capture({name: r.op(top) for name, top in TOPS.items()}, OUT, at=AT)
run('args[0]()', stats, delayMilliSeconds=int((AT[-1] - 0.3) * 1000))
run('args[0].allowCooking = False', r, delayMilliSeconds=int((AT[-1] + 1.0) * 1000))
