"""DEV ONLY. Build Slit-Scan from effects/slit_scan/build_slit_scan.py without saving it (no checks, no .tox), feed
it a test clip and a beat, and capture its output and insides; also write the frames table (how many input frames the
history holds, how far back it reaches, the first ages) at each capture time to frames.txt:

    TD_ARGS='clip=b1_dancer beat=none out=r1 Map=slit' dev/td.sh dev/protos/slit_scan/look.py
    dev/td.sh --pull dev/out/slit_scan/r1/done

Words: clip=<name> (private/assets/ready/<name>.mp4; clip=sample leaves input 1 unwired), beat=stress|music|none,
out=<folder under dev/out/slit_scan>, at=1,2,4 (capture times), tops=out,scan (what to capture: out, input, or any
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
builder = os.path.join(_ROOT, 'effects', 'slit_scan', 'build_slit_scan.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']

opts = dict(clip='b1_dancer', beat='none', out='r1', at='1,2,4', tops='out')
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

out = os.path.join(_ROOT, 'dev', 'out', 'slit_scan', opts['out'])
os.makedirs(out, exist_ok=True)
tops = {}
for name in opts['tops'].split(','):
    tops[name] = fx.op('out_top') if name == 'out' else (clip if name == 'input' else fx.op(name))
at = [float(t) for t in opts['at'].split(',')]
log = []


def table(i):
    f = fx.op('frames')
    row = [f.sample(x=j, y=0) for j in range(min(f.width, 12))]
    cut = [round(f.sample(x=j, y=1)[0]) for j in range(min(f.width, 12))]
    st = fx.op('stamp').sample(x=0, y=0)
    log.append('t={} count={} reach={:.3f} slots={} stamp={} | first (slot, age): {} | cuts {} | gpu MB pics {:.1f} '
               'flows {:.1f} stamps {:.3f} frames {:.3f}'.format(
                   at[i], row[0][2], row[0][3], f.width, [round(v, 3) for v in st],
                   [(int(r[0]), round(r[1], 3)) for r in row], cut,
                   fx.op('pics').gpuMemory / 1e6, fx.op('flows').gpuMemory / 1e6, fx.op('stamps').gpuMemory / 1e6,
                   f.gpuMemory / 1e6))
    with open(os.path.join(out, 'frames.txt'), 'w') as fh:
        fh.write('\n'.join(log) + '\n')


for i, t in enumerate(at):
    run('args[0](args[1])', table, i, delayMilliSeconds=int(t * 1000) - 30)
capture(tops, out, at=at, keep_cooking=True)
