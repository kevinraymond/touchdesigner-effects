"""DEV ONLY. Build Reaction-Diffusion (no save) on the test clip and print the state's size and range over a few
frames: TD_ARGS='<Par>=<value> ...' dev/td.sh dev/protos/reaction_diffusion/probe.py"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
builder = os.path.join(_ROOT, 'effects', 'reaction_diffusion', 'build_reaction_diffusion.py')
text = open(builder).read().replace('\nsave_effect(comp, _HERE, _ROOT)', '\n')
ns = dict(globals(), __file__=builder)
exec(compile(text, builder, 'exec'), ns)
fx = ns['comp']
clip, beat = testbed(host, dict(clip='b1_dancer', beat='none'))
wire(fx, clip, beat)
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    p = getattr(fx.par, k)
    p.val = v if p.isMenu else type(p.default)(float(v))
OUT = os.path.join(_ROOT, 'dev', 'out', 'reaction_diffusion', 'probe.txt')
open(OUT, 'w').close()


def look(i):
    rows = []
    for name in ('state_fb', 'seed', 'react', 'where', 'flow'):
        o = fx.op(name)
        a = o.numpyArray()
        rows.append('{} {}x{} npasses {} | '.format(name, o.width, o.height, getattr(o.par, 'npasses', None) and o.par.npasses.eval())
                    + ' '.join('ch{} {:.4f}/{:.4f}/{:.4f}'.format(c, a[..., c].min(), a[..., c].mean(), a[..., c].max())
                               for c in range(4)))
    fx.op('out_top').cook(force=True)
    with open(OUT, 'a') as f:
        f.write('@{} frame {}\n'.format(i, absTime.frame) + '\n'.join(rows) + '\n')
    if i < 4:
        run('args[0](args[1])', look, i + 1, delayFrames=30)
    else:
        open(OUT + '.done', 'w').close()


run('args[0](0)', look, delayFrames=5)
print('probing')
