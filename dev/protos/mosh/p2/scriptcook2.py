"""DEV ONLY (datamosh pass 2): after a Script CHOP has cooked once, do its inputs keep cooking? Bare live COMPs:
In CHOP > Audio Filter > Analyze > Script CHOP, cooked 10 frames then left: s1 lib/audio_callbacks.py as is;
s2 the same with absTime.seconds replaced by a constant; s3 a minimal WHEN_USED callbacks. Writes p2_scriptcook2.txt."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_scriptcook2.txt')
CB = open(os.path.join(_ROOT, 'lib', 'audio_callbacks.py')).read()
MIN = ('def onSetupParameters(scriptOp):\n    return\n\ndef onPulse(par):\n    return\n\n'
       'def onGetCookLevel(scriptOp):\n    return CookLevel.WHEN_USED\n\n'
       'def onCook(scriptOp):\n    scriptOp.clear()\n    scriptOp.numSamples = 1\n    scriptOp.appendChan("x")[0] = 1\n')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
cases = []
for name, text in (('s1_lib', CB), ('s2_no_abstime', CB.replace('absTime.seconds', '1.0')), ('s3_minimal', MIN)):
    b = host.create(baseCOMP, name)
    i = b.create(inCHOP, 'in2_audio')
    f = b.create(audiofilterCHOP, 'audio_low')
    f.inputConnectors[0].connect(i)
    a = b.create(analyzeCHOP, 'audio_rms')
    a.inputConnectors[0].connect(f)
    a.par.function = 'rmspower'
    s = b.create(scriptCHOP, 'audio')
    s.inputConnectors[0].connect(i)
    s.inputConnectors[1].connect(a)
    [d for d in s.docked if d.isDAT and d.name.endswith('_callbacks')][0].text = text
    cases.append(b)
F0 = {}


def done():
    lines = ['{}: cooked {}'.format(c.name, [o.name for o in c.findChildren() if o.cookAbsFrame > F0['f']] or 'none')
             for c in cases]
    open(OUTF, 'w').write('\n'.join(lines) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    for c in cases:
        c.allowCooking = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=3)


def pull(n):
    if n < 10:
        for c in cases:
            c.op('audio').cook()
        run('args[0](args[1])', pull, n + 1, delayFrames=1)
        return
    F0['f'] = absTime.frame + 1
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0](args[1])', pull, 0, delayFrames=5)
print('probing script cooks')
