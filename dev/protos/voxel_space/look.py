"""DEV ONLY. Build Voxel Space from effects/voxel_space/build_voxel_space.py without saving it (no checks, no .tox), feed it
a test clip and a beat, and capture its output (and the input, or any operator inside) at a few moments:

    TD_ARGS='clip=b1_dancer beat=none out=r1 Flight=orbit' dev/td.sh dev/protos/voxel_space/look.py
    dev/td.sh --pull dev/out/voxel/r1/done

Words: clip=<name> (private/assets/ready/<name>.mp4; clip=sample leaves input 1 unwired), beat=stress|music|none,
out=<folder under dev/out/voxel>, at=1,2,4 (capture times), tops=out,input (what to capture: out, input, or any
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
builder = os.path.join(_ROOT, 'effects', 'voxel_space', 'build_voxel_space.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']

opts = dict(clip='b1_dancer', beat='none', out='r1', at='1,2,4', tops='out,input', sample='')
pars = {}
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
if opts['sample']:
    fx.op('sample').par.file.expr = "app.samplesFolder + '/Map/{}'".format(opts['sample'])
clip = None
if opts['clip'] != 'sample':
    clip, beat = testbed(host, dict(clip=opts['clip'], beat=opts['beat']))
    wire(fx, clip, beat)
elif opts['beat'] != 'none':
    _, beat = testbed(host, dict(clip='b1_dancer', beat=opts['beat']))   # the beat alone: input 1 stays the sample
    fx.inputConnectors[1].connect(beat)
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

out = os.path.join(_ROOT, 'dev', 'out', 'voxel', opts['out'])
os.makedirs(out, exist_ok=True)
tops = {}
for name in opts['tops'].split(','):
    tops[name] = fx.op('out_top') if name == 'out' else (fx.op('source') if name == 'input' else fx.op(name))
capture(tops, out, at=[float(t) for t in opts['at'].split(',')], keep_cooking=True)


def _times():
    rows = ['{:<12} gpu {:6.2f} ms  cpu {:5.2f} ms  cooked {} frames ago'.format(
        o.name, getattr(o, 'gpuCookTime', 0) or 0, o.cpuCookTime or 0, absTime.frame - o.cookAbsFrame)
        for o in fx.findChildren(type=glslTOP)]
    for name in ('drive', 'dip_env', 'tempo', 'pace'):
        o = fx.op(name)
        if o is not None:
            rows.append('{} {}'.format(name, [(c.name, round(c[0], 3)) for c in o.chans()]))
    with open(os.path.join(out, 'times.txt'), 'a') as f:
        f.write('@ frame {}\n'.format(absTime.frame))
        f.write('\n'.join(rows) + '\n')


# GPU cook times of every shader and the music's CHOPs, a little before the last capture and at a few moments before.
for _k in range(6):
    run('args[0]()', _times, delayMilliSeconds=int(1000 * max(float(t) for t in opts['at'].split(',')) - 300 - 70 * _k))
