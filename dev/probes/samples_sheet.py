# DEV ONLY probe: the sample movies an effect can show with nothing wired, side by side over time.
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
host = op(TDLIB_PARENT)
box = host.op('samples') or host.create(baseCOMP, 'samples')
for o in list(box.children):
    o.destroy()
tops = {}
for i, rel in enumerate(['Map/Nature/Movie.1.mp4', 'Map/Nature/Movie.2.mp4', 'Map/Nature/Movie.3.mp4',
                         'Map/Nature/Movie.4.mp4', 'Map/Nature/Movie.5.mp4', 'Map/Count.mov']):
    m = box.create(moviefileinTOP, 'm{}'.format(i))
    m.par.file.expr = "app.samplesFolder + '/{}'".format(rel)
    m.nodeY = -150 * i
    tops[rel.split('/')[-1].replace('.', '_')] = m
for name, m in tops.items():
    m.cook(force=True)
    print(name, m.width, 'x', m.height, 'length', round(m.par.file.eval() and m.numImages / max(m.rate, 1), 1) if hasattr(m, 'numImages') else '?', 's')
capture(tops, os.path.join(_ROOT, 'dev', 'out', 'samples'), at=(1, 3, 5, 7))
