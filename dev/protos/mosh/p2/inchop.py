"""DEV ONLY (datamosh pass 2): does an In CHOP cook every frame with nothing pulling it? A bare COMP with an In
CHOP and an In TOP; each effects/*/*.tox loaded unwired with its viewer off. 1 s, then removes it all.
Writes dev/out/datamosh/p2_inchop.txt."""
import glob, os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_inchop.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
bare = host.create(baseCOMP, 'bare')
bare.create(inCHOP, 'in1')
bare.create(inTOP, 'in2')
bare2 = host.create(baseCOMP, 'bare_chop_only')
bare2.create(inCHOP, 'in1')
comps = [bare, bare2]
for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox'))):
    c = host.loadTox(p)
    c.viewer = False
    comps.append(c)
F0 = {}


def done():
    lines = []
    for c in comps:
        cooked = [o.name for o in c.findChildren() if o.cookAbsFrame > F0['f']]
        lines.append('{}: {} frames, cooked: {}'.format(c.name, absTime.frame - F0['f'], cooked or 'none'))
    open(OUTF, 'w').write('\n'.join(lines) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    for c in comps:
        c.allowCooking = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=3)


def start():
    F0['f'] = absTime.frame
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0]()', start, delayFrames=10)
print('probing In CHOPs')
