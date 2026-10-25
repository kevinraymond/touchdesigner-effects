"""DEV ONLY. Read-only: save Particles' buffers (TDLIB_PARENT/particles: sim, sim_life, sim_color,
sim_shove, and air, subject, subject_blur, subject_wide, emit_stats) as .npy files under dev/out/particles/<out>/, a few seconds from now, for looking at where
particles are offline. Run it right after dev/protos/particles/look.py, which leaves the effect cooking.

    TD_ARGS='out=flow_dump at=3' dev/td.sh dev/probes/sim_dump.py
    dev/td.sh --pull dev/out/particles/flow_dump/done
"""
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
opts = dict(out='dump', at='3')
for w in TDLIB_ARGS:
    k, v = w.split('=', 1)
    opts[k] = v
fx = op(TDLIB_PARENT).op('particles')
out_dir = os.path.join(_ROOT, 'dev', 'out', 'particles', opts['out'])
os.makedirs(out_dir, exist_ok=True)


def dump():
    names = ('sim', 'sim_life', 'sim_color', 'sim_shove', 'air', 'subject', 'subject_blur', 'subject_wide', 'emit_stats')
    for name in names:
        np.save(os.path.join(out_dir, name + '.npy'), fx.op(name).numpyArray())
    with open(os.path.join(out_dir, 'done'), 'w') as f:
        f.write('\n'.join(n + '.npy' for n in names) + '\n')


run('args[0]()', dump, delayMilliSeconds=int(float(opts['at']) * 1000))
print('dumping', fx.path, 'Behavior', fx.par.Behavior.eval(), 'in', opts['at'], 's into', out_dir)
