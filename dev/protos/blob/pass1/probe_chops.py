# DEV ONLY probe (blob pass 1): do a Slope CHOP (Time Slice on) and a Lag-difference turn
# audio_in()'s counts into one-frame steps? Hold CHOP parameter names.
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
host = op(TDLIB_PARENT)
box = host.op('probe_chops')
if box:
    box.destroy()
box = host.create(baseCOMP, 'probe_chops')
mk(box, inCHOP, 'in2_audio', -800, -350)
lfo = mk(box, lfoCHOP, 'lfo', -1200, -350, wavetype='square', frequency=2, offset=0.5, amp=0.5)
cnt = mk(box, countCHOP, 'cnt', -1100, -350, [lfo])
ren = mk(box, renameCHOP, 'ren', -1000, -350, [cnt], renamefrom='*', renameto='beat_count')
box.op('in2_audio').inputConnectors[0].connect(ren)
audio = audio_in(box, _ROOT)
counts = mk(box, selectCHOP, 'counts', 0, -350, [audio], channames='beat_count bar_count')
slope = mk(box, slopeCHOP, 'slope', 200, -350, [counts], timeslice=True)
lag = mk(box, lagCHOP, 'lag', 200, -500, [counts], lag1=0.05, lag2=0.05)
diff = mk(box, mathCHOP, 'diff', 400, -500, [counts, lag], chopop='sub')
trig = mk(box, triggerCHOP, 'trig', 400, -350, [slope], attack=0, peak=1, decay=0.4, sustain=0, release=0)
trig2 = mk(box, triggerCHOP, 'trig2', 600, -500, [diff], threshup=0.5, attack=0, peak=1, decay=0.4, sustain=0, release=0)
hold = box.create(holdCHOP, 'hold')
print('hold pars', [(p.name, p.eval(), p.menuNames if p.isMenu else '', p.page.name) for p in hold.pars() if p.page and p.page.name not in ('Common',)][:12])
print('slope ts', slope.isTimeSlice, 'audio ts', audio.isTimeSlice, 'trig ts', trig.isTimeSlice)
OUT = os.path.join(_ROOT, 'dev', 'out', 'blob_track', 'probe_chops.txt')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
rows = []
def tick(n):
    trig.cook(); trig2.cook()
    rows.append('{:4d} cnt {:.0f} bar {:.0f} slope {:.1f} trig {:.2f} diff {:.2f} trig2 {:.2f}'.format(
        n, counts['beat_count'].eval(), counts['bar_count'].eval(), slope['beat_count'].eval(),
        trig['beat_count'].eval(), diff['beat_count'].eval(), trig2['beat_count'].eval()))
    if n < 100:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
    else:
        open(OUT, 'w').write('\n'.join(rows) + '\n')
        box.destroy()
tick(0)
