"""DEV ONLY. Particles live on the Mac's camera, nothing on input 3 (the webcam case): loads the built
particles.tox into TDLIB_PARENT, wires a Video Device In TOP into input 1 and captures the output, the
subject and the camera:

    TD_ARGS='out=cam1 at=2,4,6 Show=subject' dev/td.sh dev/protos/particles/webcam.py
    dev/td.sh --pull dev/out/particles/cam1/done

Words: out=<folder under dev/out/particles>, at=<seconds>, capture=<seconds> (press Capture Background
then), device=<part of the camera's name> (FaceTime: the built-in one), and <Par>=<value> for the
effect's parameters. The camera stays on until the next run destroys it.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())

host = op(TDLIB_PARENT)
opts = dict(out='cam1', at='2,4,6', capture='', device='FaceTime')
pars = {}
for w in TDLIB_ARGS:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
for o in list(host.children):
    if o.valid:
        o.destroy()
cam = mk(host, videodeviceinTOP, 'camera', comment="The Mac's camera.", at=(-600, 0))
# The first device isn't always the built-in one: an iPhone nearby joins as a Continuity Camera.
names, labels = list(cam.par.device.menuNames), list(cam.par.device.menuLabels)
pick = [n for n, l in zip(names, labels) if opts['device'].lower() in l.lower()]
if pick:
    cam.par.device = pick[0]
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'particles', 'particles.tox'))
fx.inputConnectors[0].connect(cam)
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = type(p.default)(float(v)) if isinstance(p.default, (int, float)) and not isinstance(p.default, bool) else v
if opts['capture']:
    run("args[0].par.Capture.pulse()", fx, delayMilliSeconds=int(float(opts['capture']) * 1000))
print('camera', cam.par.device.eval().split('|||')[-1], 'into particles, pars', pars, 'capture at', opts['capture'] or 'never')
capture({'out': fx.op('out_top'), 'subject': fx.op('subject'), 'camera': cam},
        os.path.join(_ROOT, 'dev', 'out', 'particles', opts['out']), at=[float(t) for t in opts['at'].split(',')],
        keep_cooking=True)
