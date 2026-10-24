"""DEV ONLY (datamosh pass 2): bisect, round 3: does audio_in()'s loaded Script CHOP stop pulling its inputs once
it has cooked? Loaded copies, unwired: x1 never cooked; x2 out_top cooked once; x3 only 'audio' cooked once;
x4 out_top pulled for 10 frames then left. Then 1 s. Writes dev/out/datamosh/p2_bisect3.txt."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_bisect3.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
TOX = os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox')
cases = []
for n in ('x1_never', 'x2_out_once', 'x3_script_once', 'x4_viewed_then_left'):
    c = host.loadTox(TOX)
    c.name = n
    c.viewer = False
    cases.append(c)
cases[1].op('out_top').cook(force=True)
cases[2].op('audio').cook(force=True)
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
        cases[3].op('out_top').cook()
        run('args[0](args[1])', pull, n + 1, delayFrames=1)
        return
    F0['f'] = absTime.frame + 1
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0](args[1])', pull, 0, delayFrames=10)
print('bisecting 3')
