"""DEV ONLY. ASCII pass 1: look at the built effect (TDLIB_PARENT/ascii, from build_ascii.py) on the
sample picture (unwired) and on the dancer clip, with parameter variants, plus debug views. Short,
and it cleans up after itself: the copies and the clip are destroyed and the effect stops cooking
once the frames are saved (the Mac is shared).

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/pass1_look.py
    TD_PARENT=/tdlib_dev_ascii dev/td.sh --pull dev/out/ascii/<OUT_NAME>/done
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
exec(compile(open(os.path.join(_HERE, 'off.py')).read(), 'off.py', 'exec'), globals())
OUT_NAME = 'pass1'
OUT = os.path.join(_ROOT, 'dev', 'out', 'ascii', OUT_NAME)
CLIP = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')
AT = (1.0, 2.5, 4.0)

# Row name: parameter overrides (None: the effect itself, unwired, on the sample picture); a 'Res'
# key feeds the clip through a Fit TOP of that size first.
VARIANTS = {
    'sample': None,
    'sample_bitmap': {'Sample': True, 'Font': 'bitmap'},
    'clip': {},
    'clip_source': {'Color': 'source'},
    'clip_mono': {'Color': 'mono'},
    'clip_bitmap': {'Font': 'bitmap'},
}

host = op(TDLIB_PARENT)
fx = host.op('ascii')
for o in list(host.children):
    if o.name != 'ascii':
        o.destroy()
fx.allowCooking = True
clip = host.create(moviefileinTOP, 't_clip')
clip.par.file = CLIP
clip.nodeX, clip.nodeY = -800, -600
tops = {}
made = [clip]
for i, (name, pars) in enumerate(VARIANTS.items()):
    if pars is None:
        tops[name] = fx.op('out_top')
        continue
    pars = dict(pars)
    c = host.copy(fx, name='ascii_' + name)
    c.nodeX, c.nodeY = 600 * (i + 1), -600
    src = None if pars.pop('Sample', False) else clip
    res = pars.pop('Res', None)
    if res:
        src = host.create(fitTOP, 't_fit_' + name)
        src.par.outputresolution = 'custom'
        src.par.resolutionw, src.par.resolutionh = res
        src.inputConnectors[0].connect(clip)
        made.append(src)
    if src is not None:
        c.inputConnectors[0].connect(src)
    for k, v in pars.items():
        setattr(c.par, k, v)
    tops[name] = c.op('out_top')
    made.append(c)

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
DEBUG = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'debug')
os.makedirs(DEBUG, exist_ok=True)


def debug():
    c = host.op('ascii_clip')
    for n in ('atlas', 'edges', 'prep'):
        c.op(n).save(os.path.join(DEBUG, n + '.png'))
    s = c.op('stats')
    lines = ['stats white {:.3f} target {:.3f}'.format(s.sample(x=0, y=0)[0], s.sample(x=0, y=0)[1])]
    for o in [fx] + [m for m in made if m.isCOMP]:
        lines.append('{} grid {}x{} errors {!r} warnings {!r}'.format(
            o.name, o.op('cells').width, o.op('cells').height, o.errors(recurse=True), o.warnings(recurse=True)))
    open(os.path.join(DEBUG, 'info.txt'), 'w').write('\n'.join(lines) + '\n')


def cleanup():
    for m in made:
        m.destroy()
    off(host)


run('args[0]()', debug, delayMilliSeconds=int(AT[-1] * 1000) - 300)
capture(tops, OUT, at=AT, keep_cooking=True)
run('args[0]()', cleanup, delayMilliSeconds=int(AT[-1] * 1000) + 1500)
