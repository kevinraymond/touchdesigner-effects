"""DEV ONLY (datamosh pass 2): which of audio_in()'s operators cook every frame with nothing pulling the effect,
by what is on input 2. Bare chains (In CHOP > Audio Filter > Analyze) and the datamosh .tox, 1 s per case.
Writes dev/out/datamosh/p2_audiocook.txt; removes everything after."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_audiocook.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
const = host.create(constantCHOP, 'const')
const.par.const0name, const.par.const0value = 'energy', 0.5
lfo = host.create(lfoCHOP, 'lfo')
mp3 = host.create(audiofileinCHOP, 'mp3')
mp3.par.file = app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'
mp3.par.repeat = 'on'
sources = {'none': None, 'const': const, 'lfo': lfo, 'mp3': mp3}
cases = []
for kind, src in sources.items():
    b = host.create(baseCOMP, 'bare_' + kind)
    i = b.create(inCHOP, 'in2_audio')
    f = b.create(audiofilterCHOP, 'audio_low')
    f.inputConnectors[0].connect(i)
    f.par.filter, f.par.cutofffrequency = 'lowpass', 150
    a = b.create(analyzeCHOP, 'audio_rms')
    a.inputConnectors[0].connect(f)
    a.par.function = 'rmspower'
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox'))
    fx.name = 'fx_' + kind
    fx.viewer = False
    if src is not None:
        b.inputConnectors[0].connect(src)
        fx.inputConnectors[1].connect(src)
    cases += [b, fx]
F0 = {}


def done():
    lines = ['{}: cooked {}'.format(c.name, [o.name for o in c.findChildren() if o.cookAbsFrame > F0['f']] or 'none')
             for c in cases]
    lines.append('outside: {}'.format([o.name for o in (const, lfo, mp3) if o.cookAbsFrame > F0['f']] or 'none'))
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
print('probing audio cooks')
