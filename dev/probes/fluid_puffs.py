"""DEV ONLY probe: do Fluid's beat puffs fire? Loads the built fluid.tox with the test clip and a beat
(beat=music by default: 140 BPM), then logs over 3 s, every frame, the beat count, the flash gate's
output, puff_env and the puff's expansion uniform on divergence, and prints a summary.
TD_ARGS='beat=music' dev/td.sh dev/probes/fluid_puffs.py, then dev/td.sh --pull dev/out/fluid_puffs.txt"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')     # testbed.py's own is relative to this file
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
opts = dict(clip='b1_dancer', beat='music')
opts.update(w.split('=', 1) for w in TDLIB_ARGS if '=' in w)
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'fluid', 'fluid.tox'))
clip, beat = testbed(host, opts)
wire(fx, clip, beat)
view = host.create(nullTOP, 'view')
view.inputConnectors[0].connect(fx.outputConnectors[0])
rows = []
end = absTime.seconds + 3


def tick():
    view.cook(force=True)
    a, f, p = fx.op('audio'), fx.op('flash'), fx.op('puff_env')
    rows.append((absTime.seconds, a['beat_count'].eval(), [round(c.eval(), 2) for c in f.chans()],
                 round(p[0].eval(), 3), round(fx.op('divergence').par.vec0valuex.eval(), 3),
                 [c.name for c in fx.op('ask').chans()]))
    if absTime.seconds < end:
        run('args[0]()', tick, delayFrames=1)
    else:
        out = os.path.join(_ROOT, 'dev', 'out', 'fluid_puffs.txt')
        peaks = sum(1 for i in range(1, len(rows)) if rows[i][3] > 0.9 and rows[i - 1][3] <= 0.9)
        with open(out, 'w') as fh:
            fh.write('frames {} beats {} -> {} puffs that reached 1: {} ask chans {}\n'.format(
                len(rows), rows[0][1], rows[-1][1], peaks, rows[-1][5]))
            fh.write('\n'.join(str(r[:5]) for r in rows[:200]) + '\n')


tick()
print('logging 3 s')
