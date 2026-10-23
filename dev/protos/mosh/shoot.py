"""DEV ONLY. Play a cut sequence through the datamosh prototypes and save frames over ~8 s.

    TD_PARENT=/tdlib_dev_mosh dev/td.sh dev/protos/mosh/shoot.py
    dev/td.sh --pull dev/out/mosh/round1/done

Wrappers set MOSH_SEQ (sources before and after the cut), MOSH_OUT, MOSH_PREFIX ... before exec()ing this file.
Timeline (wall clock): 0 s clean on A with a keyframe held; 1 s keyframe released; 2 s cut to B
(the effect drops that keyframe); 2.4 s Hold on (bloom); 6 s keyframe (fade / sweep), Hold off;
7 s keyframe released. Cooking stops itself 0.5 s after the last frame.
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())

SEQ = globals().get('MOSH_SEQ', (0, 1))
OUT = globals().get('MOSH_OUT', os.path.join(_ROOT, 'dev', 'out', 'mosh', 'round1'))
AT = globals().get('MOSH_AT', (1.9, 2.3, 2.8, 3.5, 4.5, 5.9, 6.2, 6.5, 7.4))
ROWS = globals().get('MOSH_ROWS', ('a_smear', 'b_bloom', 'c_blocks', 'd_audio', 'e_chroma'))
PREFIX = globals().get('MOSH_PREFIX', '')
host = op(TDLIB_PARENT)
src = host.op('src')
for c in host.children:
    c.allowCooking = True
src.par.Source, src.par.Kf, src.par.Hold, src.par.Kft = SEQ[0], 1, 0, -100
for fb in host.findChildren(type=feedbackTOP):
    fb.par.resetpulse.pulse()


def at(seconds, **values):
    def go(values):
        s = op(TDLIB_PARENT + '/src')
        for k, v in values.items():
            setattr(s.par, k, absTime.seconds if v == 'now' else v)
    run('args[0](args[1])', go, values, delayMilliSeconds=int(seconds * 1000))


def stop():
    for c in op(TDLIB_PARENT).children:
        c.allowCooking = False


# Scheduled first, so cooking stops even if something below fails.
run('args[0]()', stop, delayMilliSeconds=int((max(AT) + 0.5) * 1000))
at(1.0, Kf=0)
at(2.0, Source=SEQ[1])
at(2.4, Hold=1)
at(6.0, Kf=1, Kft='now', Hold=0)
at(7.0, Kf=0)
tops = {PREFIX + '0_input': src.op('out')}
tops.update({PREFIX + r: host.op(r).op('out') for r in ROWS})
for extra in globals().get('MOSH_EXTRA', ()):
    tops[extra[0]] = op(TDLIB_PARENT + '/' + extra[1])
capture(tops, OUT, at=AT)

# Cook times (indicative: other sessions share this GPU) and the audio chain, sampled over frames.
STATS = []


def sample(i):
    h = op(TDLIB_PARENT)
    row = {c.name: (round(c.childrenCPUCookTime, 3), round(c.childrenGPUCookTime, 3)) for c in h.children}
    a = h.op('d_audio')
    row['audio'] = tuple(round(float(a.op(n)[0]), 4) for n in ('rms', 'slowg', 'onset', 'beat'))
    STATS.append(row)
    if i == 59:
        keys = [c.name for c in h.children]
        with open(os.path.join(OUT, 'stats_{}.txt'.format(SEQ[1])), 'w') as f:
            f.write('per COMP children cook ms (cpu, gpu), mean over {} frames:\n'.format(len(STATS)))
            for k in keys:
                f.write('  {} cpu {:.3f} gpu {:.3f}\n'.format(k, sum(r[k][0] for r in STATS) / len(STATS),
                                                             sum(r[k][1] for r in STATS) / len(STATS)))
            f.write('audio rms, slow*1.35+0.002, onset, beat per frame:\n')
            for r in STATS:
                f.write('  {}\n'.format(r['audio']))


for i in range(60):
    run('args[0](args[1])', sample, i, delayFrames=180 + 2 * i)

# Mean luminance of every output each frame (wall-clock stamped), for a rough flash check.
LUM = []
NAMES = ['src', 'a_smear', 'b_bloom', 'c_blocks', 'd_audio', 'e_chroma']
T_START = absTime.seconds


def meter(i):
    m = op(TDLIB_PARENT + '/meter')
    LUM.append([absTime.seconds - T_START] + [float(m.op('lum_' + n).numpyArray()[0, 0, 0]) for n in NAMES])
    if i == NFRAMES - 1:
        with open(os.path.join(OUT, 'lum_{}.csv'.format(PREFIX.strip('_') or 'x')), 'w') as f:
            f.write('t,' + ','.join(NAMES) + '\n')
            for r in LUM:
                f.write(','.join('{:.4f}'.format(v) for v in r) + '\n')


NFRAMES = int(max(AT) * 60)
for i in range(NFRAMES):
    run('args[0](args[1])', meter, i, delayFrames=i + 1)
