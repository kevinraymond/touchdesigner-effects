"""DEV ONLY. Build Motion Magnify without saving it, feed it the clip and a beat, and log the music's channels and the
displacement's amount every 50 ms for 3 s after a 3 s settle, to see that beats push and Follow Tempo follows:

    TD_ARGS='beat=music Tempo=1' dev/td.sh dev/protos/motion_magnify/kick.py
    dev/td.sh --pull dev/out/motion_magnify/kick/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
builder = os.path.join(_ROOT, 'effects', 'motion_magnify', 'build_motion_magnify.py')
ns = dict(globals(), __file__=builder)
exec(compile(open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n'), builder, 'exec'), ns)
fx = ns['comp']
opts = dict(clip='b1_dancer', beat='music')
pars = {}
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
clip, beat = testbed(host, opts)
wire(fx, clip, beat)
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = v if p.isMenu else (v not in ('0', 'off') if isinstance(p.default, bool) else float(v))
out = os.path.join(_ROOT, 'dev', 'out', 'motion_magnify', 'kick')
os.makedirs(out, exist_ok=True)
log = os.path.join(out, 'log.txt')
open(log, 'w').write('pars {} opts {}\n'.format(pars, opts))
if os.path.exists(os.path.join(out, 'done')):
    os.remove(os.path.join(out, 'done'))
st, mv = fx.op('stretch'), fx.op('move')


def sample(i):
    fx.op('out_top').cook(force=True)
    row = 't {:6.2f} beat_count {:5.0f} flash {:.2f} kick_env {:.2f} beat_rate {:.2f} level {:.2f} times {:.2f} leak {:.3f} ease {:.3f}'.format(
        absTime.seconds % 1000, fx.op('audio')['beat_count'].eval(), fx.op('flash')[0].eval(), fx.op('kick_env')[0].eval(),
        fx.op('beat_rate')[0].eval(), fx.op('level_smooth')[0].eval(), st.par.vec0valuex.eval(),
        mv.par.vec0valuey.eval(), mv.par.vec0valuez.eval())
    open(log, 'a').write(row + '\n')
    if i == 59:
        open(os.path.join(out, 'done'), 'w').write('log.txt\n')


for i in range(60):
    run('args[0](args[1])', sample, i, delayMilliSeconds=3000 + 50 * i)
