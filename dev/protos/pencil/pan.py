"""DEV ONLY. Do Pencil's strokes travel with the picture (Follow Movement)? Builds Pencil (no save) on a still picture
panning sideways at a steady speed (a Transform TOP of a paused frame of the flower clip, repeated), and saves the output
at two moments (at=, default 0.1 s apart in the middle of an offset's life), at speed= picture widths a second, the pan's shift between them written beside them:
    TD_ARGS='out=p1 Style=hatching Follow=1' dev/td.sh dev/protos/pencil/pan.py
    dev/td.sh --pull dev/out/pencil/p1/done
dev/protos/pencil/pan_score.py then finds the shift that best lines the two up."""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
SPEED = 0.05   # picture widths a second

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
builder = os.path.join(_ROOT, 'effects', 'pencil', 'build_pencil.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']
# A paused frame of the flower clip: textured all over, so the optical flow is sure of it everywhere (the banana
# sample's flat middle gave the flow no confidence, and no motion).
pic = mk(host, moviefileinTOP, 'pan_pic', comment='DEV: the still picture.', at=(-600, 0),
         file=os.path.join(_ROOT, 'private', 'assets', 'ready', 'd3b_flowers.mp4'), speed=0)
fit = mk(host, fitTOP, 'pan_fit', [pic], 'DEV: 1280 x 720.', at=(-400, 0), outputresolution='custom',
         resolutionw=1280, resolutionh=720)
pan = mk(host, transformTOP, 'pan', [fit], 'DEV: the picture sliding left to right.', at=(-200, 0),
         extend='repeat', tx=Expr('absTime.seconds * {} % 1'.format(SPEED)))
fx.inputConnectors[0].connect(pan)
opts = dict(out='p1', at='2.45,2.55', speed=str(SPEED))
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    if k in opts:
        opts[k] = v
        continue
    p = getattr(fx.par, k)
    p.val = v if p.isMenu else type(p.default)(float(v))
out = os.path.join(_ROOT, 'dev', 'out', 'pencil', opts['out'])
os.makedirs(out, exist_ok=True)


def stamp(i):
    with open(os.path.join(out, 'tx_{}.txt'.format(i)), 'w') as f:
        f.write('{:.6f}\n'.format(pan.par.tx.eval() * 1280))


pan.par.tx.expr = 'absTime.seconds * {} % 1'.format(float(opts['speed']))
times = [float(t) for t in opts['at'].split(',')]
for i, t in enumerate(times):
    run('args[0](args[1])', stamp, i, delayMilliSeconds=int(t * 1000))
capture({'out': fx.op('out_top'), 'input': pan}, out, at=times, keep_cooking=True)
print('panning at', opts['speed'], 'widths a second; pars', {k: getattr(fx.par, k).eval() for k in ('Style', 'Follow')})


def offsets(i):
    """The offsets drift.glsl carries (median over the middle, in pixels) beside what the pan predicts."""
    import numpy as np
    d = fx.op('drift').numpyArray()
    m = fx.op('motion').numpyArray()
    h, w = d.shape[:2]
    mid = (slice(h // 4, 3 * h // 4), slice(w // 4, 3 * w // 4))
    age = absTime.seconds % 16384 / ns['DRIFT'] % 1
    with open(os.path.join(out, 'offsets.txt'), 'a') as f:
        f.write('age {:.2f}  offset a {:7.1f} px (pan says {:6.1f})  offset b {:7.1f} px (pan says {:6.1f})  '
                'motion {:6.1f} px/s (pan {:6.1f}), confidence {:.5f}\n'.format(
                    age, np.median(d[mid][..., 0]) * 1280, age * float(opts['speed']) * 1280 * ns['DRIFT'],
                    np.median(d[mid][..., 2]) * 1280, ((age + 0.5) % 1) * float(opts['speed']) * 1280 * ns['DRIFT'],
                    np.median(m[mid][..., 0]) * 4, float(opts['speed']) * 1280, np.median(m[mid][..., 2])))


for k in range(6):
    run('args[0](args[1])', offsets, k, delayMilliSeconds=1500 + 170 * k)
