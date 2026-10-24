"""DEV ONLY. Is there a camera TouchDesigner can read? Makes a Video Device In TOP in TDLIB_PARENT,
lists the devices it offers and, after a moment, its size, errors and one frame
(dev/out/camera/frame.png). dev/td.sh dev/probes/camera.py; dev/td.sh --pull dev/out/camera/done"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, 'dev', 'out', 'camera')
os.makedirs(OUT, exist_ok=True)
if os.path.exists(os.path.join(OUT, 'done')):
    os.remove(os.path.join(OUT, 'done'))
host = op(TDLIB_PARENT)
cam = host.op('camera') or host.create(videodeviceinTOP, 'camera')
cam.comment = 'DEV: the Mac camera, for testing effects live (dev/probes/camera.py).'
print('device menu:', list(cam.par.device.menuLabels) if hasattr(cam.par, 'device') else [p.name for p in cam.pars()][:40])


def later():
    cam.cook(force=True)
    cam.save(os.path.join(OUT, 'frame.png'))
    with open(os.path.join(OUT, 'done'), 'w') as f:
        f.write('size {} x {}; errors {!r}; warnings {!r}; device {!r}\n'.format(
            cam.width, cam.height, cam.errors(), cam.warnings(), cam.par.device.eval() if hasattr(cam.par, 'device') else None))


run('args[0]()', later, delayMilliSeconds=3000)
