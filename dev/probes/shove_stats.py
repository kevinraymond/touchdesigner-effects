"""DEV ONLY. Read-only: how Particles in TDLIB_PARENT is moving its particles, once a frame for the next
seconds (run it right after dev/protos/particles/look.py, which leaves the effect cooking): how many are
alive, how many were shoved lately (sim_shove above 0.2) and how fast the living move, mean and 95th
percentile, in frame heights per second. Writes dev/out/particles/<out>/shove.txt and done.

    TD_ARGS='out=push1 seconds=3' dev/td.sh dev/probes/shove_stats.py
    dev/td.sh --pull dev/out/particles/push1/done
"""
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
opts = dict(out='shove', seconds='3')
for w in TDLIB_ARGS:
    k, v = w.split('=', 1)
    opts[k] = v
fx = op(TDLIB_PARENT).op('particles')
out_dir = os.path.join(_ROOT, 'dev', 'out', 'particles', opts['out'])
os.makedirs(out_dir, exist_ok=True)
rows = []
end = absTime.seconds + float(opts['seconds'])


def tick():
    for name in ('sim', 'sim_life', 'sim_shove'):
        fx.op(name).cook(force=True)
    pos = fx.op('sim').numpyArray()
    life = fx.op('sim_life').numpyArray()
    shove = fx.op('sim_shove').numpyArray()
    alive = life[..., 3] > 0.5
    speed = np.hypot(pos[..., 2], pos[..., 3])[alive]
    rows.append('{:.2f} alive {} shoved {} speed mean {:.3f} p95 {:.3f} max {:.3f} | shove mean {:.3f}'.format(
        absTime.seconds, int(alive.sum()), int((shove[..., 0][alive] > 0.2).sum()),
        float(speed.mean()) if speed.size else 0, float(np.percentile(speed, 95)) if speed.size else 0,
        float(speed.max()) if speed.size else 0, float(shove[..., 0][alive].mean()) if speed.size else 0))
    if absTime.seconds < end:
        run('args[0]()', tick, delayFrames=6)
    else:
        with open(os.path.join(out_dir, 'shove.txt'), 'w') as f:
            f.write('\n'.join(rows) + '\n')
        with open(os.path.join(out_dir, 'done'), 'w') as f:
            f.write('shove.txt\n')


tick()
print('sampling', fx.path, 'Behavior', fx.par.Behavior.eval(), 'for', opts['seconds'], 's into', out_dir)
