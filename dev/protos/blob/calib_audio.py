# DEV ONLY: sample the beat chain (rms, onset, trigger, count) for 8 s to choose the threshold.
import os
host = op(TDLIB_PARENT)
inp = host.op('inputs')
d = host.op('d_beat')
d.allowCooking = True
OUT = os.path.expanduser('~/tdlib/dev/out/blob/calib_audio.txt')
rows = []
def sample():
    rows.append((absTime.seconds, inp.op('rms')[0].eval(), inp.op('onset')[0].eval(), inp.op('beat')[0].eval(),
                 inp.op('count')[0].eval()))
def report():
    d.allowCooking = False
    with open(OUT, 'w') as f:
        for r in rows:
            f.write('{:.3f} {:.4f} {:.4f} {:.3f} {:.0f}\n'.format(*r))
for k in range(200):
    run('args[0]()', sample, delayFrames=30 + k * 2)
run('args[0]()', report, delayFrames=30 + 200 * 2 + 5)
print('trigger pars', {n: inp.op('beat').par[n].eval() for n in ('threshup', 'retrigger', 'attack', 'peak', 'decay', 'sustain', 'release')})
print('count pars', [(p.name, p.eval()) for p in inp.op('count').pars() if p.page and p.page.name == 'Count'][:12])
print('math chopop', inp.op('onset').par.chopop.eval(), 'lowpass', inp.op('lowpass').par.cutofffrequency.eval(), inp.op('lowpass').par.units.eval())
