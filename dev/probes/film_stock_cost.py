"""DEV ONLY. Where Film Stock's big-grain cost goes (board #4622): load the built .tox at Super 8, Grain 3 on the dancer,
then swap the negative's shader for variants (text substitutions in its docked DAT) and read the GLSL TOP's GPU cook
time over WATCH frames each:

    dev/td.sh dev/probes/film_stock_cost.py
    dev/td.sh --pull dev/out/film_stock/cost/done; cat dev/out/film_stock/cost/report.txt
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'film_stock', 'cost')
os.makedirs(OUT, exist_ok=True)
for f in ('report.txt', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
SETTLE, WATCH = 20, 60

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, dict(clip='b1_dancer', beat='stress'))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'film_stock', 'film_stock.tox'))
fx.nodeX = 300
wire(fx, clip, beat)
fx.par.Gauge = 's8'
fx.par.Grain = 3
view = mk(host, nullTOP, 'view', comment='Pulls the effect every frame.', at=(600, 0))
view.inputConnectors[0].connect(fx.outputConnectors[0])
neg = fx.op('negative')
dat = [d for d in neg.docked if d.name.endswith('_pixel')][0]
base = dat.text
VARIANTS = [
    ('as built', []),
    ('fine model only (U_FINE 0)', [('#define U_FINE 0.9 ', '#define U_FINE 0.0 ')]),
]
state = {'i': 0, 'frames': 0, 'gpu': [], 'lines': []}


def start(i):
    text = base
    for old, new in VARIANTS[i][1]:
        assert old in text, (VARIANTS[i][0], old)
        text = text.replace(old, new)
    dat.text = text
    state.update(i=i, frames=0, gpu=[])


def tick():
    view.cook()  # nothing views it: pull the effect every frame
    state['frames'] += 1
    if state['frames'] > SETTLE:
        state['gpu'].append(neg.gpuCookTime)
    if state['frames'] < SETTLE + WATCH:
        run('args[0]()', tick, delayFrames=1)
        return
    g = sorted(state['gpu'])
    state['lines'].append('{:40s} negative GPU {:.2f} ms (median {:.2f}), errors: {}'.format(
        VARIANTS[state['i']][0], sum(g) / len(g), g[len(g) // 2], neg.errors() or 'none'))
    if state['i'] + 1 < len(VARIANTS):
        start(state['i'] + 1)
        run('args[0]()', tick, delayFrames=1)
        return
    dat.text = base
    with open(os.path.join(OUT, 'report.txt'), 'w') as f:
        f.write('\n'.join(state['lines']) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')


start(0)
run('args[0]()', tick, delayFrames=1)
print('measuring', len(VARIANTS), 'variants')
