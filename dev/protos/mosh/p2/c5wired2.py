"""DEV ONLY (datamosh pass 2): what makes in2_audio cook with input 2 wired to a time-driven CHOP (dev/testbed.py's
stress beat), nothing pulling. Never pulled, 1 s: datamosh as is; datamosh with in2_audio's consumers removed; the
other effects; a bare COMP with an In CHOP. Writes dev/out/datamosh/p2_c5wired2.txt; removes everything after."""
import glob, os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_c5wired2.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, {'clip': 'b1_dancer', 'beat': 'stress'})
cases = []
for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox'))):
    c = host.loadTox(p)
    c.viewer = False
    c.inputConnectors[0].connect(clip)
    if len(c.inputConnectors) > 1:
        c.inputConnectors[1].connect(beat)
    cases.append(c)
c = host.loadTox(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox'))
c.name = 'datamosh_no_consumers'
c.viewer = False
for n in ('audio', 'audio_low', 'audio_rms'):
    c.op(n).destroy()
c.inputConnectors[1].connect(beat)
cases.append(c)
b = host.create(baseCOMP, 'bare')
b.create(inCHOP, 'in2_audio')
b.inputConnectors[0].connect(beat)
cases.append(b)
F0 = {}


def done():
    lines = ['{}: cooked {}'.format(c.name, [o.name for o in c.findChildren() if o.cookAbsFrame > F0['f']] or 'none')
             for c in cases]
    open(OUTF, 'w').write('\n'.join(lines) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    for c in cases:
        c.allowCooking = False
    clip.par.play = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=3)


def start():
    F0['f'] = absTime.frame
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0]()', start, delayFrames=10)
print('C5 wired bisect')
