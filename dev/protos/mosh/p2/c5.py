"""DEV ONLY (datamosh pass 2): what keeps cooking with nothing downstream. Loads the .tox beside dev/testbed.py's
clip and stress beat, nothing pulling it, then for 1 s each: C1 as built; C2 with every expression that reads an
operator's .width/.height frozen to its value; C3 also with input 2 unwired. Writes dev/out/datamosh/p2_c5.txt."""
import os, re
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_c5.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, {'clip': 'b1_dancer', 'beat': 'stress'})
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox'))
fx.viewer = False
fx.inputConnectors[0].connect(clip)
fx.inputConnectors[1].connect(beat)
L = []
STEPS = ['C1 as built', 'C2 .width/.height expressions frozen', 'C3 and input 2 unwired']


def stage(i):
    if i > 0:
        cooked = [o.name for o in fx.findChildren() if o.cookAbsFrame > S['f0']]
        L.append('{}: {} frames, cooked: {}'.format(STEPS[i - 1], absTime.frame - S['f0'], cooked or 'none'))
    if i == 1:
        frozen = []
        for o in fx.findChildren():
            for p in o.pars():
                if p.mode == ParMode.EXPRESSION and re.search(r'\.(width|height)', p.expr):
                    v = p.eval()
                    p.val = v
                    frozen.append('{}.{}'.format(o.name, p.name))
        L.append('  froze ' + ', '.join(frozen))
    if i == 2:
        fx.inputConnectors[1].disconnect()
    if i == len(STEPS):
        open(OUTF, 'w').write('\n'.join(L) + '\n')
        open(OUTF + '.done', 'w').write('ok\n')
        clip.par.play = False
        fx.allowCooking = False
        run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=3)
        return
    S['f0'] = absTime.frame
    run('args[0](args[1])', stage, i + 1, delayMilliSeconds=1000)


S = {}
if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0](args[1])', stage, 0, delayFrames=10)
print('probing C5')
