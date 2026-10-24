"""DEV ONLY. Inside TouchDesigner: what /tdlib_demo/blob_track's boxes do over SECONDS, as it runs (it
changes nothing): boxes showing per frame, how many new boxes appear and how long boxes last, input
2, the clip, and the parameters set away from their defaults.

    dev/td.sh dev/probes/blob_events.py && dev/td.sh --pull dev/out/blob_events/done
    cat dev/out/blob_events/report.txt
"""

import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
OUT = os.path.join(os.path.dirname(_HERE), 'out', 'blob_events')
SECONDS = 10
HIDDEN = 0.001  # track.glsl: a held slot whose box isn't showing yet
os.makedirs(OUT, exist_ok=True)
for f in ('report.txt', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
fx = op('/tdlib_demo/blob_track')
state = dict(n=0, start=absTime.seconds, shown=[], seen={}, labels0=None, beats0=fx.op('audio')['beat_count'].eval())


def tick():
    t = absTime.seconds - state['start']
    a = fx.op('track').numpyArray()  # rows 0-2 of track.glsl's output, one column per slot
    labels = set()
    for s in range(a.shape[1]):
        if a[1, s, 1] > HIDDEN:
            labels.add(int(round(a[2, s, 0])))
    for lab in labels:
        first, _ = state['seen'].get(lab, (t, t))
        state['seen'][lab] = (first, t)
    state['shown'].append(len(labels))
    handed = a[2, 0, 1]
    if state['labels0'] is None:
        state['labels0'] = handed
    state['n'] += 1
    if t < SECONDS:
        run('args[0]()', tick, delayFrames=1)
        return
    lives = sorted(round(last - first, 1) for first, last in state['seen'].values())
    ended = [round(last - first, 1) for first, last in state['seen'].values() if last < t - 0.2 and first > 0.2]
    shown = state['shown']
    demo = fx.parent()
    pars = {p.label: p.eval() for p in fx.customPars if not p.isDefault and p.style not in ('Pulse',)}
    au = fx.op('audio')
    lines = [
        'over {:.1f} s ({} frames), Effect {}, clip {}:'.format(t, state['n'], demo.par.Effect.eval(),
                                                               os.path.basename(demo.op('clip').par.file.eval())),
        '  boxes showing: min {}, mean {:.1f}, max {}'.format(min(shown), sum(shown) / len(shown), max(shown)),
        '  new labels handed out: {:.0f} ({:.1f} a second)'.format(handed - state['labels0'], (handed - state['labels0']) / t),
        '  boxes seen: {}; lifetimes (s, cut at the window): {}'.format(len(lives), lives),
        '  boxes that came and went inside the window: {}, lasting {}'.format(len(ended), sorted(ended)),
        '  input 2 source {:.0f} (3 Fosfora, 1 raw audio, 0 none), beats {:.0f}, level {:.2f}'.format(
            au['source'].eval(), au['beat_count'].eval() - state['beats0'], au['level'].eval()),
        '  parameters away from default: {}'.format(pars or 'none'),
    ]
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')


tick()
print('watching blob_track for {} s'.format(SECONDS))
