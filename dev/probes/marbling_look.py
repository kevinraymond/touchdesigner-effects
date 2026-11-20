"""DEV ONLY. Marbling's look (board #4848): load the built .tox once per variant on one clip, set each variant's
parameters, and save every variant's output (and the clip) at a few moments; also write what the first variant's field,
surface and look measure to state.txt at the last moment:

    TD_ARGS='clip=b1_dancer at=3,6 beat=song default Inks=ebru' dev/td.sh dev/probes/marbling_look.py
    dev/td.sh --pull dev/out/marbling/look/done

out=<dir> writes under dev/out/marbling/<dir> instead of look. Each word with '=' that isn't clip=, at=, beat=, song=
or out= is a variant: comma-separated parameter=value pairs (none: the defaults, 'default'). nodepth=1 leaves input 3
unwired; clip=none leaves every input unwired, as a drag-in does. inner=tools,ink also saves those operators of the first variant (as i_<name>_<i>.png, scaled to show).
Writes clip_<i>.png, v<k>_<i>.png and state.txt; tile them with dev/sheet.py.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')   # testbed.py's own is from this file's __file__
_OUTNAME = next((w.split('=', 1)[1] for w in TDLIB_ARGS if w.startswith('out=')), 'look')
OUT = os.path.join(_ROOT, 'dev', 'out', 'marbling', _OUTNAME)
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
opts = dict(clip='b1_dancer', at='3,6', beat='none', nodepth='0', inner='')
variants = []
for w in TDLIB_ARGS:
    key = w.split('=', 1)[0]
    if key == 'out':
        continue
    if key in ('clip', 'at', 'beat', 'song', 'nodepth', 'inner'):
        opts[key] = w.split('=', 1)[1]
    else:
        variants.append({} if w == 'default' else dict(kv.split('=', 1) for kv in w.split(',')))
variants = variants or [{}]
nodepth = opts.pop('nodepth') == '1'
inner = [n for n in opts.pop('inner').split(',') if n]
unwired = opts['clip'] == 'none'
clip, beat = (None, None) if unwired else testbed(host, dict(opts))
tops = {} if unwired else {'clip': clip}
fxs = []
for k, v in enumerate(variants):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'marbling', 'marbling.tox'))
    fx.name = 'v{}'.format(k)
    fx.nodeX, fx.nodeY = 300 + 250 * k, 0
    if not unwired:
        wire(fx, clip, beat)
    if nodepth and not unwired:
        fx.inputConnectors[2].disconnect()
    for name, value in v.items():
        p = getattr(fx.par, name)
        p.val = value if p.isMenu or p.isString else float(value)
    tops['v{}'.format(k)] = fx.op('out_top')
    fxs.append(fx)
for name in inner:
    # Each inner operator's first channels scaled to show: the field's r and drive, the height around gray.
    # A wire can't cross into the effect: a Select TOP reads the operator by path.
    pick = mk(host, selectTOP, 'p_' + name, at=(100, -300 - 200 * len(tops)), top=fxs[0].op(name).path)
    show = mk(host, levelTOP, 'i_' + name, [pick], at=(300, -300 - 200 * len(tops)))
    tops['i_' + name] = show
at = tuple(float(x) for x in opts['at'].split(','))
capture(tops, OUT, at=at, keep_cooking=True)


def dump():
    fx = fxs[0]
    lines = []
    tray = fx.op('tray')
    kinds = tray['kind'].vals
    lines.append('tray tools {} (drops {}, combs {}, waves {})'.format(sum(1 for k in kinds if k > 0),
                 sum(1 for k in kinds if k == 1), sum(1 for k in kinds if k == 2), sum(1 for k in kinds if k == 3)))
    ink = fx.op('ink').numpyArray()
    lines.append('ink ' + ' '.join('({:.2f},{:.2f},{:.2f},{:.0f})'.format(*ink[0, j]) for j in range(8)))
    lines.append('audio ' + ' '.join('{}={:.3f}'.format(c.name, c.eval()) for c in fx.op('audio').chans()))
    m = fx.op('marble')
    lines.append('marble uK {} {}  find mean r {:.3f}'.format(m.par.vec1valuex.eval(), m.par.vec1valuey.eval(), float(fx.op('find').numpyArray()[..., 0].mean())))
    lines.append('errors ' + repr(fx.errors(recurse=True)) + ' warnings ' + repr(fx.warnings(recurse=True)))
    with open(os.path.join(OUT, 'state.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')


run('args[0]()', dump, delayMilliSeconds=int(max(at) * 1000) + 200)
print('variants', variants, 'clip', opts['clip'], 'at', at)
