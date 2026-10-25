"""DEV ONLY. Every camera in Bent Cam's lot on the same frame, for the docs page's contact sheet: loads
effects/bent_cam/bent_cam.tox, holds the test clip on one frame, turns off what isn't the shorts (bursts, clock
slips, block errors), and saves the output once per Camera, then lot_draw.py lays them out with each camera's
pins:

    TD_ARGS='frame=32 Shorts=0.35' dev/td.sh dev/protos/bent_cam/lot.py
    dev/td.sh --pull dev/out/bent_cam/lot/done
    uv run --with pillow dev/protos/bent_cam/lot_draw.py dev/out/bent_cam/lot docs/effects/bent_cam_lot.png

Words: clip=<name>, frame=<index> (the clip's frame to hold), out=<folder under dev/out/bent_cam>, and
<Par>=<value> for the effect's parameters.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')     # testbed's own is relative to the script it runs in
LOT = {}
exec(compile(open(os.path.join(_ROOT, 'effects', 'bent_cam', 'src', 'lot.py')).read(), 'lot.py', 'exec'), LOT)

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'bent_cam', 'bent_cam.tox'))
opts = dict(clip='b1_dancer', frame='32', out='lot')
pars = dict(Bursts='off', Clockslip='0', Blockerr='0')
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
clip, _ = testbed(host, dict(clip=opts['clip'], beat='none'))
setpars(clip, playmode='specify', indexunit='indices', index=int(opts['frame']))
wire(fx, clip, None)
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = v if p.isMenu else type(p.default)(float(v))
out_dir = os.path.join(_ROOT, 'dev', 'out', 'bent_cam', opts['out'])
os.makedirs(out_dir, exist_ok=True)
if os.path.exists(os.path.join(out_dir, 'done')):
    os.remove(os.path.join(out_dir, 'done'))
top = fx.op('out_top')
SETTLE, STEP = 90, 4      # frames: the loop settling on the held frame, then each camera


def shoot(cam):
    top.cook(force=True)
    top.save(os.path.join(out_dir, 'cam_{:02d}.png'.format(cam)))
    if cam == LOT['CAMERAS']:
        with open(os.path.join(out_dir, 'done'), 'w') as f:
            f.write('{}\n'.format(pars))
    else:
        fx.par.Camera = cam + 1


def keep(n):
    top.cook(force=True)
    if n > 0:
        run('args[0](args[1])', keep, n - 1, delayFrames=1)


fx.par.Camera = 1
keep(SETTLE + STEP * LOT['CAMERAS'] + 4)
for cam in range(1, LOT['CAMERAS'] + 1):
    run('args[0](args[1])', shoot, cam, delayFrames=SETTLE + STEP * cam)
print('lot: {} cameras into {} ({})'.format(LOT['CAMERAS'], out_dir, pars))
