"""DEV ONLY. Build Pixel Sort from effects/pixel_sort/build_pixel_sort.py without saving it (no checks, no .tox), feed it
a test clip and a beat, and capture its output (and the input, or any operator inside) at a few moments:

    TD_ARGS='clip=b1_dancer beat=none out=r1 Angle=0' dev/td.sh dev/protos/pixel_sort/look.py
    dev/td.sh --pull dev/out/pixel_sort/r1/done

Words: clip=<name> (private/assets/ready/<name>.mp4; clip=sample leaves input 1 unwired), beat=stress|music|none,
out=<folder under dev/out/pixel_sort>, at=1,2,4 (capture times), tops=out,input (what to capture: out, input, or any
operator inside), and <Par>=<value> for the effect's parameters.
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
builder = os.path.join(_ROOT, 'effects', 'pixel_sort', 'build_pixel_sort.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']

opts = dict(clip='b1_dancer', beat='none', out='r1', at='1,2,4', tops='out,input')
pars = {}
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
clip = None
if opts['clip'] != 'sample':
    clip, beat = testbed(host, dict(clip=opts['clip'], beat=opts['beat']))
    wire(fx, clip, beat)
for k, v in pars.items():
    p = getattr(fx.par, k)
    if p.isMenu:
        p.val = v
    elif isinstance(p.default, bool):
        p.val = v not in ('0', 'off', 'False')
    elif isinstance(p.default, (int, float)):
        p.val = type(p.default)(float(v))
    else:
        p.val = v
print('clip', opts['clip'], 'beat', opts['beat'], 'pars', pars)
print('errors:', fx.errors(recurse=True), 'warnings:', fx.warnings(recurse=True))
for o in fx.findChildren(type=glslTOP):
    print(o.name, o.width, o.height, o.par.format.eval(), (o.warnings() or o.errors() or 'ok')[:400])

out = os.path.join(_ROOT, 'dev', 'out', 'pixel_sort', opts['out'])
os.makedirs(out, exist_ok=True)
tops = {}
for name in opts['tops'].split(','):
    tops[name] = fx.op('out_top') if name == 'out' else (fx.op('source') if name == 'input' else fx.op(name))
capture(tops, out, at=[float(t) for t in opts['at'].split(',')], keep_cooking=True)
