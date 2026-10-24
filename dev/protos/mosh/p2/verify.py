"""DEV ONLY (datamosh pass 2): after the rebuild. C5 on copies pulled 10 frames then left (unwired; wired to
dev/testbed.py's clip + stress beat), then Blocks through the dancer's loop cut captured (dev/out/datamosh/p2_blocks).
Writes dev/out/datamosh/p2_verify.txt; stops and removes everything after."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_verify.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
TOX = os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox')
clip, beat = testbed(host, {'clip': 'b1_dancer', 'beat': 'stress'})
clip.par.cuepoint, clip.par.cuepointunit = 8.4, 'seconds'
a = host.loadTox(TOX); a.name = 'c5_unwired'; a.viewer = False
b = host.loadTox(TOX); b.name = 'c5_wired'; b.viewer = False
b.inputConnectors[0].connect(clip)
b.inputConnectors[1].connect(beat)
L = []
F0 = {}


def stop():
    for c in op(TDLIB_PARENT).children:
        if c.isCOMP:
            c.allowCooking = False
    c = op(TDLIB_PARENT + '/clip')
    if c is not None:
        c.par.play = False


def blocks():
    L.extend('{} (pulled 10 frames, then left 1 s): cooked {}'.format(
        c.name, [o.name for o in c.findChildren() if o.cookAbsFrame > F0['f']] or 'none') for c in (a, b))
    L.append('outside: {}'.format([o.name for o in (clip, beat) if o.cookAbsFrame > F0['f']] or 'none'))
    a.allowCooking = b.allowCooking = False
    v = host.loadTox(TOX)
    v.name = 'blk'
    v.par.Mode = 'blocks'
    v.par.Skipon = 'off'
    v.inputConnectors[0].connect(clip)
    clip.par.cuepulse.pulse()
    capture({'0_input': clip, 'blocks': v.op('out_top')}, os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_blocks'),
            at=(1.5, 1.9, 2.3, 2.8, 3.5), keep_cooking=True)
    run('args[0]()', finish, delayMilliSeconds=4500)


def finish():
    open(OUTF, 'w').write('\n'.join(L) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    stop()
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=30)


def pull(n):
    if n < 10:
        a.op('out_top').cook()
        b.op('out_top').cook()
        run('args[0](args[1])', pull, n + 1, delayFrames=1)
        return
    F0['f'] = absTime.frame + 1
    run('args[0]()', blocks, delayMilliSeconds=1000)


for f in (OUTF + '.done', os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_blocks', 'done')):
    if os.path.exists(f):
        os.remove(f)
run('args[0](args[1])', pull, 0, delayFrames=5)
print('verifying')
