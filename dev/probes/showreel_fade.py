"""DEV ONLY. Cycle's fade in the Showreel (TDLIB_PARENT/showreel as dev/td.sh built it): with nothing
wired (the dancer) and Every 1, Cycle moves every 2 s. Every frame for 6 s it notes view's index and
which effects cooked, and saves the output 8 times a second across the first move after 2 s, to
dev/out/showreel_fade/ (report.txt, out_<i>.png), then done.

    dev/td.sh dev/probes/showreel_fade.py && dev/td.sh --pull dev/out/showreel_fade/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, 'dev', 'out', 'showreel_fade')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
reel = op(TDLIB_PARENT).op('showreel')
reel.par.View, reel.par.Every = 'cycle', 1
fxs = [c for c in reel.findChildren(type=COMP, depth=1) if c.op('out_top') is not None and c.name != 'window']
view, out = reel.op('view'), reel.op('out_top')
state = {'start': absTime.seconds, 'lines': [], 'shots': 0, 'last_step': None}


def tick():
    out.cook(force=True)
    t = absTime.seconds - state['start']
    cooked = [f.name for f in fxs if f.op('out_top').cookAbsFrame >= absTime.frame - 1]
    idx = view.par.index.eval()
    state['lines'].append('{:5.2f} index {:5.2f} cooked {}'.format(t, idx, cooked))
    if t > 2.0 and state['shots'] < 16 and abs(idx - round(idx)) > 1e-3 or 0 < state['shots'] < 16:
        out.save(os.path.join(OUT, 'out_{}.png'.format(state['shots'])))
        state['shots'] += 1
    if t < 6.0:
        run('args[0]()', tick, delayFrames=1)
        return
    with open(os.path.join(OUT, 'report.txt'), 'w') as f:
        f.write('\n'.join(state['lines']) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('ok\n')


tick()
print('watching', [f.name for f in fxs])
