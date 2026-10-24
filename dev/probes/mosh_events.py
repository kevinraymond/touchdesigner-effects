"""DEV ONLY. Inside TouchDesigner: what /tdlib_demo/datamosh does over SECONDS, as it runs (it changes
nothing): skips and keyframes that passed the Flashing limit, cuts it found in the input, input 2's
bars and build, and the parameters set away from their defaults.

    dev/td.sh dev/probes/mosh_events.py && dev/td.sh --pull dev/out/mosh_events/done
    cat dev/out/mosh_events/report.txt
"""

import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
OUT = os.path.join(os.path.dirname(_HERE), 'out', 'mosh_events')
SECONDS = 10
os.makedirs(OUT, exist_ok=True)
for f in ('report.txt', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
fx = op('/tdlib_demo/datamosh')
state = dict(n=0, skips=[], keys=[], cuts=set(), builds=[], start=absTime.seconds,
             bars0=fx.op('audio')['bar_count'].eval())


def tick():
    t = absTime.seconds - state['start']
    if fx.op('skip_sel')['skip'].eval() > 0.5:
        state['skips'].append(round(t, 2))
    if fx.op('key_sel')['key'].eval() > 0.5:
        state['keys'].append(round(t, 2))
    if state['n'] % 15 == 0:
        state['cuts'].add(round(float(fx.op('clock').numpyArray()[0, 0, 3]), 2))
        state['builds'].append(round(fx.op('audio')['build'].eval(), 2))
    state['n'] += 1
    if t < SECONDS:
        run('args[0]()', tick, delayFrames=1)
        return
    a = fx.op('audio')
    pars = {p.label: p.eval() for p in fx.customPars if not p.isDefault and p.style not in ('Pulse',)}
    lines = [
        'over {:.1f} s ({} frames), Effect {}:'.format(t, state['n'], fx.parent().par.Effect.eval()),
        '  input 2 source {} (3 Fosfora, 1 raw audio), bars {:.0f}, build samples {}'.format(
            a['source'].eval(), a['bar_count'].eval() - state['bars0'], state['builds']),
        '  skips passed: {} at {}'.format(len(state['skips']), state['skips']),
        '  keyframes passed: {} at {}'.format(len(state['keys']), state['keys']),
        '  last-cut times seen (s on the clock): {}'.format(sorted(state['cuts'])),
        '  parameters away from default: {}'.format(pars or 'none'),
    ]
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')


tick()
print('watching datamosh for {} s'.format(SECONDS))
