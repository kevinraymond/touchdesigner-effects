"""DEV ONLY. Feed Particles (TDLIB_PARENT/particles as dev/td.sh built it, else loaded
from its .tox) a test clip, its depth clip on input 3 and the stress beat, and capture its output
and insides:

    TD_ARGS='clip=b1_dancer beat=stress out=r1 Rate=8000' dev/td.sh dev/protos/particles/look.py
    dev/td.sh --pull dev/out/particles/r1/done

Words: clip=<name> (private/assets/ready/<name>.mp4 and <name>_depth.mp4; depth=none leaves input 3
unwired; dfile=<path on the Mac> another depth file), beat=stress|none, out=<folder under dev/out/particles>, at=1,2,4 (capture times), and
<Par>=<value> to set the effect's parameters for the run (they are put back on the next run).
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')     # testbed.py's own is relative to this file

host = op(TDLIB_PARENT)
fx = host.op('particles') or host.loadTox(os.path.join(_ROOT, 'effects', 'particles', 'particles.tox'))
words = [w for w in TDLIB_ARGS if '=' in w]
opts = dict(clip='b1_dancer', beat='stress', depth='clip', out='r1', at='1,2,4', dfile='')
pars = {}
for w in words:
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
wire(fx, clip, beat)
if opts['dfile']:                   # another depth file on input 3 (a path on the Mac, ~ allowed)
    host.op('clip_depth').par.file = os.path.expanduser(opts['dfile'])
for p in fx.customPars:
    if not p.readOnly and p.style not in ('Pulse', 'Momentary', 'Header'):
        p.val = p.default
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = type(p.default)(float(v)) if isinstance(p.default, (int, float)) and not isinstance(p.default, bool) else v
print('wired:', [[o.owner.name for o in c.connections] for c in fx.inputConnectors], 'clip file', clip.par.file.eval())
print('clip', opts['clip'], 'beat', opts['beat'], 'depth', opts['depth'], 'pars', pars)
at = [float(t) for t in opts['at'].split(',')]
capture({'out': fx.op('out_top'), 'subject': fx.op('subject'), 'render': fx.op('render')},
        os.path.join(_ROOT, 'dev', 'out', 'particles', opts['out']), at=at, keep_cooking=True)
