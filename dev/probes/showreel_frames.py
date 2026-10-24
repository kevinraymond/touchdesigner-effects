"""DEV ONLY. Inside TouchDesigner: load bundles/showreel/showreel.tox fresh into TDLIB_PARENT, feed it a
test clip (TD_ARGS: its name, default b2_plaza; none: nothing wired, its own clip) and save one frame of each View after showing it for
2 s, pulling the picture every frame as a viewer would (an effect that needs history, like Blob
Track, has none if nothing pulls it), to dev/out/showreel/<view>.jpg; then dev/out/showreel/done.
The loaded copy is removed after.

    dev/td.sh dev/probes/showreel_frames.py && dev/td.sh --pull dev/out/showreel/done
"""
import glob
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_ROOT, 'dev', 'out', 'showreel')
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, '*')):
    os.remove(f)
host = op(TDLIB_PARENT) or op('/').create(baseCOMP, TDLIB_PARENT.strip('/'))
for o in list(host.children):
    if o.valid:
        o.destroy()
clip = host.create(moviefileinTOP, 'clip')
name = (globals().get('TDLIB_ARGS') or ['b2_plaza'])[0]
clip.par.file = os.path.join(_ROOT, 'private', 'assets', 'ready', name + '.mp4')
reel = host.loadTox(os.path.join(_ROOT, 'bundles', 'showreel', 'showreel.tox'))
if name != 'none':
    reel.inputConnectors[0].connect(clip)
views = list(reel.par.View.menuNames)


def show(i):
    if i >= len(views):
        open(os.path.join(OUT, 'done'), 'w').write('\n'.join(views) + '\n')
        reel.destroy()
        clip.destroy()
        return
    reel.par.View = views[i]
    run('args[0](args[1], args[2])', pull, i, absTime.seconds, delayFrames=1)


def pull(i, start):
    reel.op('out_top').cook()
    if absTime.seconds - start < 2.0:
        run('args[0](args[1], args[2])', pull, i, start, delayFrames=1)
    else:
        save(i)


def save(i):
    reel.op('out_top').save(os.path.join(OUT, '{}.jpg'.format(views[i])))
    print(views[i], 'view index', reel.op('view').par.index.eval(), reel.errors(recurse=True) or 'no errors')
    run('args[0](args[1])', show, i + 1, delayFrames=1)


show(0)
print('saving', views)
