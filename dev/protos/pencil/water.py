"""DEV ONLY. Where does the koi water's tone move: the table, or the picture? Builds Pencil (no save) on the koi clip,
then every 4 frames for 2 s writes six water cells' mean relative luminance (20 x 20 px, linear light), in the
input and in the output: TD_ARGS='clip=b4_koi' dev/td.sh dev/protos/pencil/water.py; dev/td.sh --pull dev/out/pencil/water.txt.done"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
builder = os.path.join(_ROOT, 'effects', 'pencil', 'build_pencil.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']
opts = dict(clip='b4_koi', beat='none')
for w in [w for w in TDLIB_ARGS if w.split('=')[0] in opts]:
    k, v = w.split('=', 1)
    opts[k] = v
clip, beat = testbed(host, opts)
wire(fx, clip, beat)
OUT = os.path.join(_ROOT, 'dev', 'out', 'pencil', 'water.txt')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').close()
if os.path.exists(OUT + '.done'):
    os.remove(OUT + '.done')
CELLS = []


def lin(a):
    a = a[..., :3]
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return (a * np.array([0.2126, 0.7152, 0.0722])).sum(-1)


def look(i):
    global np
    import numpy as np
    src = lin(clip.numpyArray()[::-1])
    out = lin(fx.op('out_top').numpyArray()[::-1])
    cin = src.reshape(36, 20, 64, 20).mean((1, 3))
    cout = out.reshape(36, 20, 64, 20).mean((1, 3))
    if not CELLS:
        ys, xs = np.nonzero(cin < 0.01)
        CELLS.extend(list(zip(ys, xs))[::max(1, len(ys) // 6)][:6])
    with open(OUT, 'a') as f:
        f.write('{:3d} '.format(i) + '  '.join('{:2d},{:2d} in {:.4f} out {:.3f}'.format(y, x, cin[y, x], cout[y, x])
                                               for y, x in CELLS) + '\n')
    if i < 30:
        run('args[0](args[1])', look, i + 1, delayFrames=4)
    else:
        open(OUT + '.done', 'w').close()


run('args[0](args[1])', look, 0, delayFrames=60)
