"""DEV ONLY probe for Words (board #4673): load the built .tox on a clip (its depth on input 3) for each variant, and
every half second count its words: shown, fading in (younger than Fade), fading out; how many are younger than half a
second (born lately), and their sizes. Writes dev/out/words/stats/stats.txt, then done:

    TD_ARGS='clip=b1_dancer Layout=lines' dev/td.sh dev/probes/words_stats.py && dev/td.sh --pull dev/out/words/stats/done
"""
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')   # testbed.py's own is from this file's __file__
OUT = os.path.join(_ROOT, 'dev', 'out', 'words', 'stats')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
opts = dict(clip='b1_dancer', beat='none', seconds='4')
variants = []
for w in TDLIB_ARGS:
    k = w.split('=', 1)[0]
    if k in ('clip', 'beat', 'seconds'):
        opts[k] = w.split('=', 1)[1]
    else:
        variants.append({} if w == 'default' else dict(kv.split('=', 1) for kv in w.split(',')))
variants = variants or [{}]
clip, beat = testbed(host, dict(opts))
fxs = []
for k, v in enumerate(variants):
    fx = host.loadTox(os.path.join(_ROOT, 'effects', 'words', 'words.tox'))
    fx.name = 'v{}'.format(k)
    wire(fx, clip, beat)
    for name, value in v.items():
        p = getattr(fx.par, name)
        p.val = value if p.isMenu or p.isString else float(value)
    fxs.append(fx)
null = mk(host, nullTOP, 'pull', comment='Pulls the variants.', at=(600, 0))
lines = []
state = {'t0': absTime.seconds, 'next': 0.5}


def tick():
    for fx in fxs:
        fx.op('out_top').cook()
    now = absTime.seconds - state['t0']
    if now >= state['next']:
        state['next'] += 0.5
        for k, fx in enumerate(fxs):
            a = fx.op('layout').numpyArray(delayed=False)   # rows bottom first: row 0 boxes, 1 info, 2 more
            info, more, box = a[1], a[2], a[0]
            shown = info[:, 3] > 0.5
            out = info[:, 3] < -0.5
            young = shown & (more[:, 2] < 0.5)
            lines.append('t {:.1f} v{} {}: shown {} (younger than 0.5 s {}), fading out {}, heights {}'.format(
                now, k, variants[k], int(shown.sum()), int(young.sum()), int(out.sum()),
                np.percentile(box[shown, 3], (10, 50, 90)).round(1).tolist() if shown.any() else []))
    if now < float(opts['seconds']):
        run('args[0]()', tick, delayFrames=1)
        return
    open(os.path.join(OUT, 'stats.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('stats.txt\n')


run('args[0]()', tick, delayFrames=1)
print('stats running', variants)
