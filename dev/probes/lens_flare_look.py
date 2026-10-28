"""DEV ONLY. Lens Flare's look: load the built .tox once per variant on one clip, set each variant's parameters, and
save every variant's output (and the clip) at a few moments, with the lights each found:

    TD_ARGS='clip=b1_dancer at=2,4 Lens=heliar Lens=sonnar,Coating=multi' dev/td.sh dev/probes/lens_flare_look.py
    dev/td.sh --pull dev/out/lens_flare/look/done

Input 3 stays unwired unless depth=on. Each word with '=' that isn't clip=, at=, beat= or depth= is a variant: comma-separated parameter=value pairs (none: the defaults,
'default'). Writes clip_<i>.png, v<k>_<i>.png and lights.txt; tile them with dev/sheet.py.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')   # testbed.py's own is from this file's __file__
OUT = os.path.join(_ROOT, 'dev', 'out', 'lens_flare', 'look')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
words = list(TDLIB_ARGS)
opts = dict(clip='b1_dancer', at='2,4', beat='none', depth='off')
variants = []
for w in words:
    key = w.split('=', 1)[0]
    if key in ('clip', 'at', 'beat', 'depth'):
        opts[key] = w.split('=', 1)[1]
    else:
        variants.append({} if w == 'default' else dict(kv.split('=', 1) for kv in w.split(',')))
variants = variants or [{}]
clip, beat = testbed(host, dict(opts))
tops = {'clip': clip}
fxs = []
for k, v in enumerate(variants):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'lens_flare', 'lens_flare.tox'))
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
log = []


def lights_now():
    for k, fx in enumerate(fxs):
        a = fx.op('lights').numpyArray(delayed=False)
        found = [(round(float(a[0, i, 0]), 3), round(float(a[0, i, 1]), 3), '{:.2e}'.format(a[0, i, 2]),
                  round(float(a[0, i, 3]), 3)) for i in range(a.shape[1]) if a[0, i, 2] > 0]
        log.append('t {:.2f} v{} {}: {}'.format(absTime.seconds - t0, k, variants[k], found))
    with open(os.path.join(OUT, 'lights.txt'), 'w') as f:
        f.write('\n'.join(log) + '\n')


t0 = absTime.seconds
for t in at:
    run('args[0]()', lights_now, delayMilliSeconds=int(t * 1000) + 50)
capture(tops, OUT, at=at, keep_cooking=True)
print('variants', variants, 'clip', opts['clip'], 'at', at)
