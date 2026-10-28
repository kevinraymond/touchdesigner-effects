"""DEV ONLY probe for Words (board #4673): the built .tox as a drag-in leaves it, nothing wired, once per variant;
save each output after a few seconds. Writes dev/out/words/unwired/v<k>.png, then done:

    TD_ARGS='Layout=cloud Layout=portrait Layout=lines' dev/td.sh dev/probes/words_unwired.py
    dev/td.sh --pull dev/out/words/unwired/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'words', 'unwired')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
variants = [{} if w == 'default' else dict(kv.split('=', 1) for kv in w.split(',')) for w in TDLIB_ARGS] or [{}]
views = []
for k, v in enumerate(variants):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'words', 'words.tox'))
    fx.name = 'v{}'.format(k)
    for name, value in v.items():
        p = getattr(fx.par, name)
        p.val = value if p.isMenu or p.isString else float(value)
    view = mk(host, nullTOP, 'view{}'.format(k), comment='pulls', at=(400, 200 * k))
    view.inputConnectors[0].connect(fx.outputConnectors[0])
    views.append(view)
t0 = absTime.seconds


def tick():
    for v in views:
        v.cook()
    if absTime.seconds - t0 < 4.0:
        run('args[0]()', tick, delayFrames=1)
        return
    for k, v in enumerate(views):
        v.save(os.path.join(OUT, 'v{}.png'.format(k)))
    open(os.path.join(OUT, 'done'), 'w').write('ok\n')


run('args[0]()', tick, delayFrames=1)
print('unwired', variants)
