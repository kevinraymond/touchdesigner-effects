"""DEV ONLY (datamosh pass 2): does audio_in()'s Script CHOP (WHEN_USED) make its inputs cook every frame with
nothing pulling it? Bare COMPs: In CHOP > Audio Filter > Analyze > Script CHOP (lib/audio_callbacks.py), with and
without a downstream Select, unwired and on an LFO. 1 s. Writes dev/out/datamosh/p2_scriptcook.txt."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_scriptcook.txt')
CB = open(os.path.join(_ROOT, 'lib', 'audio_callbacks.py')).read()
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
lfo = host.create(lfoCHOP, 'lfo')
cases = []
for kind in ('none', 'lfo'):
    for downstream in (False, True):
        b = host.create(baseCOMP, 'b_{}_{}'.format(kind, 'sel' if downstream else 'nosel'))
        i = b.create(inCHOP, 'in2_audio')
        f = b.create(audiofilterCHOP, 'audio_low')
        f.inputConnectors[0].connect(i)
        a = b.create(analyzeCHOP, 'audio_rms')
        a.inputConnectors[0].connect(f)
        a.par.function = 'rmspower'
        s = b.create(scriptCHOP, 'audio')
        s.inputConnectors[0].connect(i)
        s.inputConnectors[1].connect(a)
        [d for d in s.docked if d.isDAT and d.name.endswith('_callbacks')][0].text = CB
        if downstream:
            sel = b.create(selectCHOP, 'counts')
            sel.inputConnectors[0].connect(s)
        if kind == 'lfo':
            b.inputConnectors[0].connect(lfo)
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


def start():
    F0['f'] = absTime.frame
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0]()', start, delayFrames=20)
print('probing the Script CHOP')
