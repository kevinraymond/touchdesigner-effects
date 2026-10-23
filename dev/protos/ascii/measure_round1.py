"""DEV ONLY. Indicative cook times of the ASCII round-1 variants (fixed 1280 x 720 movie input,
medians after a warm-up; other sessions share this TouchDesigner) and the beat count the E
chain gives on the sample MP3 with the Calm re-trigger delay. Writes dev/out/ascii/measure/cook.txt.

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/measure_round1.py
    TD_PARENT=/tdlib_dev_ascii dev/td.sh --pull dev/out/ascii/measure/done
"""
import os
import statistics

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
OUT = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'measure')
os.makedirs(OUT, exist_ok=True)
if os.path.exists(os.path.join(OUT, 'done')):
    os.remove(os.path.join(OUT, 'done'))
r = op(TDLIB_PARENT + '/r1')
r.op('pick').par.index = 0
r.op('e_audio').par.file.expr = "app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'"
r.allowCooking = True
GROUPS = {'A atlas': ('a_',), 'B edges': ('b_',), 'C color': ('c_',), 'D rain': ('d_',), 'E beat': ('e_',),
          'shared cells + auto levels': ('f_',)}
samples = {k: ([], []) for k in GROUPS}
beats = []


def sample():
    for k, prefixes in GROUPS.items():
        ops = [o for o in r.children if o.name.startswith(prefixes) and (o.isTOP or o.isCHOP)
               and o.OPType != 'textTOP' and o.name != 'e_peak']
        samples[k][0].append(sum(o.cpuCookTime for o in ops))
        samples[k][1].append(sum(o.gpuCookTime for o in ops))
    beats.append((absTime.seconds, r.op('e_count')[0].eval()))


def report():
    lines = ['median cook ms per frame over {} samples, fixed input Movie.3 1280 x 720; indicative only '
             '(other sessions share this TouchDesigner)'.format(len(beats))]
    for k, (cpu, gpu) in samples.items():
        lines.append('{:28s} cpu {:.3f}  gpu {:.3f}'.format(k, statistics.median(cpu), statistics.median(gpu)))
    (t0, c0), (t1, c1) = beats[0], beats[-1]
    lines.append('MP3 beats counted with re-trigger delay {} s: {:.0f} in {:.1f} s'.format(
        r.op('e_trig').par.retrigger.eval(), c1 - c0, t1 - t0))
    lines.append('per-sample counts: ' + ' '.join('{:.0f}'.format(c) for _, c in beats))
    with open(os.path.join(OUT, 'cook.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    r.op('e_audio').par.file.expr = "app.samplesFolder + '/Audio/SonarBlackie666.wav'"
    r.allowCooking = False
    open(os.path.join(OUT, 'done'), 'w').write('cook.txt\n')


for k in range(32):
    run('args[0]()', sample, delayMilliSeconds=3000 + 250 * k)
run('args[0]()', report, delayMilliSeconds=3000 + 250 * 32 + 100)
print('measuring for 11 s')
