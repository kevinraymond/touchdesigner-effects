"""DEV ONLY. Build Fluid from effects/fluid/build_fluid.py without saving it (no checks, no .tox), feed it a
test clip, its depth clip on input 3 and a beat, and capture its output and insides, with numbers:

    TD_ARGS='clip=b1_dancer beat=none out=r1 Look=fire' dev/td.sh dev/protos/fluid/look.py
    dev/td.sh --pull dev/out/fluid/r1/done

Words: clip=<name> (private/assets/ready/<name>.mp4 and <name>_depth.mp4; depth=none leaves input 3
unwired; clip=sample leaves input 1 unwired too), beat=stress|music|none, out=<folder under dev/out/fluid>,
at=1,2,4 (capture times), and <Par>=<value> for the effect's parameters. stats.txt beside the frames gives
the motion's speed and confidence, the emit mask, the velocity and the dye at each capture time.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
builder = os.path.join(_ROOT, 'effects', 'fluid', 'build_fluid.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']

words = [w for w in TDLIB_ARGS if '=' in w]
opts = dict(clip='b1_dancer', beat='none', depth='clip', out='r1', at='1,2,4')
pars = {}
for w in words:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
if opts['clip'] != 'sample':
    clip, beat = testbed(host, dict(clip=opts['clip'], beat=opts['beat']))
    if opts['depth'] == 'none':
        for name in ('clip_depth', 'clip_depth_at'):
            if host.op(name):
                host.op(name).destroy()
    wire(fx, clip, beat)
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = type(p.default)(float(v)) if isinstance(p.default, (int, float)) and not isinstance(p.default, bool) else v
print('clip', opts['clip'], 'beat', opts['beat'], 'pars', pars, 'errors:', fx.errors(recurse=True), 'warnings:', fx.warnings(recurse=True))

out = os.path.join(_ROOT, 'dev', 'out', 'fluid', opts['out'])
at = [float(t) for t in opts['at'].split(',')]
lines = []


def stats(i):
    import numpy as np
    m = fx.op('motion').numpyArray()
    sp = np.hypot(m[..., 0], m[..., 1]) / m.shape[0]      # frame heights per second
    e = fx.op('emit').numpyArray()[..., 0]
    v = fx.op('velocity').numpyArray()
    vs = np.hypot(v[..., 0], v[..., 1]) / v.shape[0]
    d = fx.op('dye').numpyArray()[..., 3]
    pc = lambda a: ' '.join('{:.3g}'.format(x) for x in np.percentile(a, (50, 90, 99, 100)))
    lines.append('t{} motion fh/s p50/90/99/max {} | conf {} | emit mean {:.3f} >0.5 {:.3f} | velocity fh/s {} | '
                 'dye mean {:.3f} >0.1 {:.3f} | pace {}'.format(
                     i, pc(sp), pc(m[..., 2]), e.mean(), (e > 0.5).mean(), pc(vs), d.mean(), (d > 0.1).mean(),
                     [round(x, 4) for x in fx.op('pace').numpyArray()[0, 0]]))
    if i == len(at) - 1:
        open(os.path.join(out, 'stats.txt'), 'w').write('\n'.join(lines) + '\n')


os.makedirs(out, exist_ok=True)
for i, s in enumerate(at):
    run('args[0](args[1])', stats, i, delayMilliSeconds=max(0, int(s * 1000) - 30))
capture({'out': fx.op('out_top'), 'emit': fx.op('emit')}, out, at=at, keep_cooking=True)
