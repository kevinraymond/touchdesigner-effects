"""DEV ONLY. Caustics' look (board #4671): load the built .tox once per variant on one clip, set each
variant's parameters, and save every variant's output (and the clip) at a few moments; also write what the first
variant's surface and light measure (heights, slopes, the caustics' range) to state.txt at the last moment:

    TD_ARGS='clip=b1_dancer at=3,4.5 beat=song default Caustics=1' dev/td.sh dev/probes/caustics_look.py
    dev/td.sh --pull dev/out/caustics/look/done

out=<dir> writes under dev/out/caustics/<dir> instead of look. Each word with '=' that isn't clip=, at=, beat=, song=
or out= is a variant: comma-separated parameter=value pairs (none: the defaults, 'default'). Writes clip_<i>.png,
v<k>_<i>.png and state.txt; tile them with dev/sheet.py.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')   # testbed.py's own is from this file's __file__
_OUTNAME = next((w.split('=', 1)[1] for w in TDLIB_ARGS if w.startswith('out=')), 'look')
OUT = os.path.join(_ROOT, 'dev', 'out', 'caustics', _OUTNAME)
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
opts = dict(clip='b1_dancer', at='3,4.5', beat='none')
variants = []
for w in TDLIB_ARGS:
    key = w.split('=', 1)[0]
    if key == 'out':
        continue
    if key in ('clip', 'at', 'beat', 'song'):
        opts[key] = w.split('=', 1)[1]
    else:
        variants.append({} if w == 'default' else dict(kv.split('=', 1) for kv in w.split(',')))
variants = variants or [{}]
clip, beat = testbed(host, dict(opts))
tops = {'clip': clip}
fxs = []
for k, v in enumerate(variants):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'caustics', 'caustics.tox'))
    fx.name = 'v{}'.format(k)
    fx.nodeX, fx.nodeY = 300 + 250 * k, 0
    wire(fx, clip, beat)
    for name, value in v.items():
        p = getattr(fx.par, name)
        p.val = value if p.isMenu or p.isString else float(value)
    tops['v{}'.format(k)] = fx.op('out_top')
    fxs.append(fx)
at = tuple(float(x) for x in opts['at'].split(','))
capture(tops, OUT, at=at, keep_cooking=True)


def dump():
    fx = fxs[0]
    lines = []
    for name in ('surface', 'caustics', 'water'):
        a = fx.op(name).numpyArray()
        lines.append('{} {}x{}: '.format(name, a.shape[1], a.shape[0]) + ', '.join(
            'ch{} min {:.3f} mean {:.3f} max {:.3f}'.format(c, a[..., c].min(), a[..., c].mean(), a[..., c].max())
            for c in range(4)))
    for name in ('drop_env', 'drops', 'level_smooth', 'wind'):
        lines.append('{} {}'.format(name, ' '.join('{}={:.4f}'.format(c.name, c.eval()) for c in fx.op(name).chans())))
    lines.append('audio ' + ' '.join('{}={:.3f}'.format(c.name, c.eval()) for c in fx.op('audio').chans()))
    with open(os.path.join(OUT, 'state.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')


run('args[0]()', dump, delayMilliSeconds=int(max(at) * 1000) + 200)
print('variants', variants, 'clip', opts['clip'], 'at', at)
