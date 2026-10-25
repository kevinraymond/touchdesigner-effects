"""DEV ONLY. Inside TouchDesigner: record every channel of /tdlib_demo's Fosfora signal, every
frame, for SECONDS (TD_ARGS='seconds=<n>', default 60), while music plays where Fosfora listens: what
each level channel (energy, drums, bass, kick_strength...) does from beat to beat. Every copy of the
signal on the port gets the same stream while it cooks; signal=<path of an out_signal> reads another.
A copy that isn't cooking (the demo bypassed) holds its last values, online = 1 included, so this
refuses one that isn't live: dev/probes/find_signal.py's test (cooking, a heartbeat under 1.5 s old).

    TD_ARGS='seconds=60' dev/td.sh dev/probes/fosfora_levels.py
    TD_ARGS='seconds=60 signal=/project1/fosfora_examples/fosfora_signal/out_signal tag=drop' dev/td.sh dev/probes/fosfora_levels.py
    TD_WAIT=90 dev/td.sh --pull dev/out/fosfora_levels/done

Writes dev/out/fosfora_levels/signal.npz (signal_<tag>.npz with tag=<word>: t and one array per
channel), then done. Changes nothing.
"""
import os

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(_HERE, 'find_signal.py')).read().split('\n\nfor o in ')[0], 'find_signal.py', 'exec'),
     globals())

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, 'dev', 'out', 'fosfora_levels')
opts = dict(a.split('=', 1) for a in (globals().get('TDLIB_ARGS') or []) if '=' in a)
SECONDS = float(opts.get('seconds', 60))
os.makedirs(OUT, exist_ok=True)
if os.path.exists(os.path.join(OUT, 'done')):
    os.remove(os.path.join(OUT, 'done'))
signal = op(opts.get('signal', '/tdlib_demo/fosfora_signal/out_signal'))
FILE = 'signal{}.npz'.format('_' + opts['tag'] if 'tag' in opts else '')
cooking, age = live(signal.parent())
if not (cooking and age is not None and age < 1.5):
    raise RuntimeError('{} is not live (cooking {}, heartbeat {}): its values are stale'.format(
        signal.path, cooking, 'none' if age is None else '{:.1f} s ago'.format(age)))
names = [c.name for c in signal.chans()]
rows = []
start = absTime.seconds


def tick():
    t = absTime.seconds - start
    rows.append([t] + [signal[n].eval() for n in names])
    if t < SECONDS:
        run('args[0]()', tick, delayFrames=1)
        return
    a = np.array(rows, dtype=np.float64)
    np.savez_compressed(os.path.join(OUT, FILE), t=a[:, 0], **{n: a[:, i + 1] for i, n in enumerate(names)})
    open(os.path.join(OUT, 'done'), 'w').write(FILE + '\n')


tick()
print('recording {} channels of {} for {:g} s'.format(len(names), signal.path, SECONDS))
