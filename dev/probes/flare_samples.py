"""DEV ONLY. Lens Flare with nothing wired, on each of TouchDesigner's sample movies: which one shows a flare when the
effect is dragged in? Saves each one's output at 2 and 4 s.

    dev/td.sh dev/probes/flare_samples.py && dev/td.sh --pull dev/out/lens_flare/samples/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'lens_flare', 'samples')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
tops = {}
for k in (1, 2, 3, 4, 5):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'lens_flare', 'lens_flare.tox'))
    fx.name = 'm{}'.format(k)
    fx.op('sample').par.file.expr = "app.samplesFolder + '/Map/Nature/Movie.{}.mp4'".format(k)
    tops['movie{}'.format(k)] = fx.op('out_top')
capture(tops, OUT, at=(2, 4), keep_cooking=True)
