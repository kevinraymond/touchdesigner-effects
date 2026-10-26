"""DEV ONLY. Feed Point Cloud (TDLIB_PARENT/point_cloud as dev/td.sh built it, else loaded from
its .tox) a test clip, its depth clip on input 3 and the stress beat, and capture its output:

    TD_ARGS='clip=b1_dancer beat=stress out=fx1 Look=glow' dev/td.sh dev/protos/point_cloud/fx.py
    dev/td.sh --pull dev/out/point_cloud/fx1/done

Words: clip=<name> (private/assets/ready/<name>.mp4 and <name>_depth.mp4; clip=sample leaves input 1
unwired; depth=none leaves input 3 unwired, depth=black wires all black; dfile=<path on the Mac>
another depth file), beat=stress|none, out=<folder under
dev/out/point_cloud>, at=1,3,5,7 (capture times), and <Par>=<value> for the effect's parameters
(the rest go back to their defaults).
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')     # testbed.py's own is relative to this file

host = op(TDLIB_PARENT)
fx = host.op('point_cloud') or host.loadTox(os.path.join(_ROOT, 'effects', 'point_cloud', 'point_cloud.tox'))
opts = dict(clip='b1_dancer', beat='stress', depth='clip', out='fx1', at='1,3,5,7', dfile='')
pars = {}
for w in TDLIB_ARGS:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v

# Wires can't cross network levels: the test inputs sit beside the effect, as dev/perf.py's do.
for name in ('clip', 'stress', 'clip_depth', 'clip_depth_at'):
    if host.op(name):
        host.op(name).destroy()
clip, beat = testbed(host, dict(clip=opts['clip'], beat=opts['beat']))
for c in fx.inputConnectors:
    c.disconnect()
if opts['depth'] == 'none':
    for name in ('clip_depth', 'clip_depth_at'):
        if host.op(name):
            host.op(name).destroy()
if opts['clip'] != 'sample':
    wire(fx, clip, beat)
elif beat is not None:
    fx.inputConnectors[1].connect(beat)
if opts['depth'] == 'black':          # wired but carrying nothing, as a camera unplugged
    black = host.op('black') or mk(host, constantTOP, 'black', comment='All black: no depth.',
                                   colorr=0, colorg=0, colorb=0, alpha=1, at=(-600, -450))
    fx.inputConnectors[2].connect(black)
if opts['dfile']:
    host.op('clip_depth').par.file = os.path.expanduser(opts['dfile'])
for p in fx.customPars:
    if not p.readOnly and p.style not in ('Pulse', 'Momentary', 'Header'):
        p.val = p.default
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = type(p.default)(float(v)) if isinstance(p.default, (int, float)) and not isinstance(p.default, bool) else v
print('wired:', [[o.owner.name for o in c.connections] for c in fx.inputConnectors], 'clip', opts['clip'], 'pars', pars)
print('errors', fx.errors(recurse=True), 'warnings', fx.warnings(recurse=True))
capture({'out': fx.op('out_top')}, os.path.join(_ROOT, 'dev', 'out', 'point_cloud', opts['out']),
        at=[float(t) for t in opts['at'].split(',')], keep_cooking=True)
