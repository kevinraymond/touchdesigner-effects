"""DEV ONLY. Pixel Art's New Palette and Hold Palette: load the built .tox on a clip, then after 2 s pulse New Palette
and read the palette's state over the next second (it should start again: phase 0 or 1, then 2 with the fade going
up), then turn Hold Palette on and check the palette stays put while the clip moves:

    TD_ARGS='clip=d3b_flowers' dev/td.sh dev/probes/pixel_art_controls.py
    dev/td.sh --pull dev/out/probes/pixel_art_controls/done
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
OUT = os.path.join(_ROOT, 'dev', 'out', 'probes', 'pixel_art_controls')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
names, opts = test_args(TDLIB_ARGS)
clip, beat = testbed(host, dict(opts, beat='none'))
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'pixel_art', 'pixel_art.tox'))
wire(fx, clip, None)
view = mk(host, nullTOP, 'view', [fx.outputConnectors[0]], comment='Pulls the output every frame.', at=(400, 0))
view.viewer = True
log = []


def state(tag):
    pal = fx.op('palette').numpyArray(delayed=False)
    on = [k for k in range(32) if pal[3, k][3] > 0]
    log.append('{:<10} t {:5.2f}  T {:8.2f} phase {:.0f} colors {:2.0f} fade {:.2f}  first colors L {}'.format(
        tag, absTime.seconds - t0, pal[2, 0][0], pal[2, 0][1], pal[2, 0][3], pal[2, 1][0],
        ' '.join('{:.1f}'.format(pal[3, k][0]) for k in on[:4])))


def tick(i):
    view.cook(force=True)
    if i == 120:
        state('before')
        fx.par.Newpalette.pulse()
    if 121 <= i <= 200 and i % 8 == 1:
        state('new')
    if i == 210:
        fx.par.Hold = True
        state('hold on')
    if i in (240, 280, 320):
        state('held')
    if i < 330:
        run('args[0](args[1])', tick, i + 1, delayFrames=1)
    else:
        fx.par.Hold = False
        with open(os.path.join(OUT, 'done'), 'w') as f:
            f.write('\n'.join(log) + '\n')


t0 = absTime.seconds
tick(0)
print('probing New Palette and Hold Palette for about 6 s')
