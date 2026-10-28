"""DEV ONLY. Words' look (board #4673): load the built .tox once per variant on one clip, set each variant's parameters,
and save every variant's output (and the clip) at a few moments:

    TD_ARGS='clip=b1_dancer at=2,4 Layout=cloud Layout=portrait' dev/td.sh dev/probes/words_look.py
    dev/td.sh --pull dev/out/words/look/done

Input 3 gets the clip's depth unless depth=off; out=<dir> writes under dev/out/words/<dir> instead of look. Each word with '=' that isn't clip=, at=, beat= or depth= is a variant: comma-separated parameter=value pairs (none: the defaults,
'default'). Writes clip_<i>.png, v<k>_<i>.png and lights.txt; tile them with dev/sheet.py.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')   # testbed.py's own is from this file's __file__
_OUTNAME = next((w.split('=', 1)[1] for w in TDLIB_ARGS if w.startswith('out=')), 'look')
OUT = os.path.join(_ROOT, 'dev', 'out', 'words', _OUTNAME)
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
words = list(TDLIB_ARGS)
opts = dict(clip='b1_dancer', at='2,4', beat='none', depth='on')
variants = []
for w in words:
    key = w.split('=', 1)[0]
    if key == 'out':
        continue
    if key in ('clip', 'at', 'beat', 'depth'):
        opts[key] = w.split('=', 1)[1]
    else:
        variants.append({} if w == 'default' else dict(kv.split('=', 1) for kv in w.split(',')))
variants = variants or [{}]
clip, beat = testbed(host, dict(opts))
tops = {'clip': clip}
fxs = []
for k, v in enumerate(variants):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'words', 'words.tox'))
    fx.name = 'v{}'.format(k)
    fx.nodeX, fx.nodeY = 300 + 250 * k, 0
    wire(fx, clip, beat)
    if opts['depth'] != 'on' and len(fx.inputConnectors) > 2:
        fx.inputConnectors[2].disconnect()
    for name, value in v.items():
        p = getattr(fx.par, name)
        p.val = value if p.isMenu or p.isString else float(value)
    tops['v{}'.format(k)] = fx.op('out_top')
    fxs.append(fx)
at = tuple(float(x) for x in opts['at'].split(','))
t0 = absTime.seconds
capture(tops, OUT, at=at, keep_cooking=True)
print('variants', variants, 'clip', opts['clip'], 'at', at)
