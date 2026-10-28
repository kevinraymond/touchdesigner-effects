"""DEV ONLY probe for Words (board #4673): change the words while it runs (Case to Upper after 3 s, by default) and save
the output before and after, to see the old words give way rather than show stretched:

    TD_ARGS='Case=upper' dev/td.sh dev/probes/words_textchange.py && dev/td.sh --pull dev/out/words/textchange/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'words', 'textchange')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, beat = testbed(host, dict(clip='b1_dancer', beat='none'))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'words', 'words.tox'))
wire(fx, clip, beat)
change = dict(w.split('=', 1) for w in TDLIB_ARGS) or {'Case': 'upper'}


def apply():
    for k, v in change.items():
        getattr(fx.par, k).val = v


run('args[0]()', apply, delayMilliSeconds=3000)
capture({'fx': fx.op('out_top')}, OUT, at=(2.8, 3.1, 3.3, 4.8), keep_cooking=True)
print('textchange', change)
