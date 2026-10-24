"""DEV ONLY (datamosh pass 2): with input 2 wired, is the Script CHOP what keeps in2_audio cooking? Copies wired to
the dancer and stress beat: w1 never pulled; w2 pulled 10 frames then left; w3 as w2, then its audio Script CHOP
destroyed. 1 s. Writes dev/out/datamosh/p2_c5wired.txt; removes everything after."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_c5wired.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, {'clip': 'b1_dancer', 'beat': 'stress'})
TOX = os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox')
cases = []
for name in ('w1_never_pulled', 'w2_pulled_then_left', 'w3_pulled_no_script'):
    c = host.loadTox(TOX)
    c.name = name
    c.viewer = False
    c.inputConnectors[0].connect(clip)
    c.inputConnectors[1].connect(beat)
    cases.append(c)
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


def pull(n):
    if n < 10:
        for c in cases[1:]:
            c.op('out_top').cook()
        run('args[0](args[1])', pull, n + 1, delayFrames=1)
        return
    cases[2].op('audio').destroy()
    F0['f'] = absTime.frame + 1
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0](args[1])', pull, 0, delayFrames=5)
print('C5 wired check')
