"""DEV ONLY. Build Pixel Art from effects/pixel_art/build_pixel_art.py without saving it (no checks, no .tox), feed it a
test clip and a beat, and capture its output (and the input, or any operator inside) at a few moments:

    TD_ARGS='clip=b1_dancer beat=none out=r1 Colors=8' dev/td.sh dev/protos/pixel_art/look.py
    dev/td.sh --pull dev/out/pixel_art/r1/done

Words: clip=<name> (private/assets/ready/<name>.mp4; clip=sample leaves input 1 unwired), beat=stress|music|none,
out=<folder under dev/out/pixel_art>, at=1,2,4 (capture times), tops=out,input (what to capture: out, input, or any
operator inside), and <Par>=<value> for the effect's parameters. Also writes times.txt (each shader's GPU time) and
state.txt (the palette's state and colors).
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
builder = os.path.join(_ROOT, 'effects', 'pixel_art', 'build_pixel_art.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']

opts = dict(clip='b1_dancer', beat='none', out='r1', at='1,2,4', tops='out,input', sample='', trace='', grid='')
pars = {}
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
if opts['sample']:
    fx.op('sample').par.file.expr = "app.samplesFolder + '/Map/{}'".format(opts['sample'])
if opts['clip'] != 'sample':
    clip, beat = testbed(host, dict(clip=opts['clip'], beat=opts['beat']))
    wire(fx, clip, beat)
elif opts['beat'] != 'none':
    _, beat = testbed(host, dict(clip='b1_dancer', beat=opts['beat']))
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

out = os.path.join(_ROOT, 'dev', 'out', 'pixel_art', opts['out'])
os.makedirs(out, exist_ok=True)
for f in ('times.txt', 'state.txt'):
    if os.path.exists(os.path.join(out, f)):
        os.remove(os.path.join(out, f))
tops = {}
for name in opts['tops'].split(','):
    tops[name] = fx.op('out_top') if name == 'out' else (fx.op('source') if name == 'input' else fx.op(name))
at = [float(t) for t in opts['at'].split(',')]
capture(tops, out, at=at, keep_cooking=True)


def _times():
    rows = ['{:<12} gpu {:6.2f} ms  cpu {:5.2f} ms  cooked {} frames ago'.format(
        o.name, getattr(o, 'gpuCookTime', 0) or 0, o.cpuCookTime or 0, absTime.frame - o.cookAbsFrame)
        for o in fx.findChildren(type=glslTOP)]
    with open(os.path.join(out, 'times.txt'), 'a') as f:
        f.write('@ frame {}\n'.format(absTime.frame))
        f.write('\n'.join(rows) + '\n')


def _state():
    pal = fx.op('palette').numpyArray(delayed=False)
    st = pal[2, 0]
    with open(os.path.join(out, 'state.txt'), 'a') as f:
        f.write('@ {:.2f} s  T {:.3f} phase {:.0f} at {:.0f} colors {:.0f}\n'.format(
            absTime.seconds, st[0], st[1], st[2], st[3]))
        for k in range(32):
            c = pal[3, k]
            if c[3] > 0:
                f.write('  color {:2d} Lab {:6.1f} {:6.1f} {:6.1f} share {:.4f}\n'.format(k, c[0], c[1], c[2], c[3]))
        f.write('  entries: ' + ' '.join('{}:{:.3f}'.format(e, pal[0, e][3]) for e in range(64) if pal[0, e][3] > 0)
                + '\n')


for _k in range(6):
    run('args[0]()', _times, delayMilliSeconds=int(1000 * max(at) - 300 - 70 * _k))
for t in [0.05, 0.2, 0.5, 1.0] + at:
    run('args[0]()', _state, delayMilliSeconds=int(1000 * t))


# With trace=<seconds>: the palette every frame for that long (trace.txt): its colors and shares, for finding what
# changes it (a color revived, one drifting).
if 'trace' in [w.split('=')[0] for w in TDLIB_ARGS]:
    _span = float([w for w in TDLIB_ARGS if w.startswith('trace=')][0].split('=')[1])
    _trace = {'end': absTime.seconds + 1.0 + _span, 'start': absTime.seconds + 1.0, 'rows': []}

    def _tick():
        if absTime.seconds >= _trace['start']:
            pal = fx.op('palette').numpyArray(delayed=False)
            _trace['rows'].append((absTime.seconds, pal[2, 0].copy(), pal[3, :32].copy()))
        if absTime.seconds < _trace['end']:
            run('args[0]()', _tick, delayFrames=1)
        else:
            import numpy as np
            np.savez(os.path.join(out, 'trace.npz'), t=[r[0] for r in _trace['rows']],
                     state=[r[1] for r in _trace['rows']], colors=[r[2] for r in _trace['rows']])
            open(os.path.join(out, 'trace_done'), 'w').write('ok\n')

    _tick()


# With grid=<seconds>: every art pixel's color choice and superpixel color each frame for that long (grid.npz).
if 'grid' in [w.split('=')[0] for w in TDLIB_ARGS]:
    _gspan = float([w for w in TDLIB_ARGS if w.startswith('grid=')][0].split('=')[1])
    _g = {'end': absTime.seconds + 2.0 + _gspan, 'start': absTime.seconds + 2.0, 'idx': [], 'x': [], 't': []}

    def _gtick():
        if absTime.seconds >= _g['start']:
            _g['idx'].append(fx.op('index').numpyArray(delayed=False)[:96, :, 3].copy())
            _g['x'].append(fx.op('colors').numpyArray(delayed=False)[:96, :, :3].copy())
            _g['t'].append(absTime.seconds)
        if absTime.seconds < _g['end']:
            run('args[0]()', _gtick, delayFrames=1)
        else:
            import numpy as np
            np.savez_compressed(os.path.join(out, 'grid.npz'), t=_g['t'], idx=np.array(_g['idx'], np.float32),
                                x=np.array(_g['x'], np.float16))
            open(os.path.join(out, 'grid_done'), 'w').write('ok\n')

    _gtick()
