"""DEV ONLY probe: Fluid's unwired demo (the ball over the sample movie): what the source Switch shows, the
ball's and the Over TOP's pixels where the ball should be. Run after dev/protos/fluid/look.py clip=sample.
dev/td.sh dev/probes/fluid_ball.py"""
import os
fx = op(TDLIB_PARENT + '/fluid')
ball, demo, source = fx.op('ball'), fx.op('demo'), fx.op('source')
print('source index', source.par.index.eval(), 'inputs', [i.name for i in source.inputs])
print('demo inputs', [i.name for i in demo.inputs], demo.width, 'x', demo.height, demo.errors(), demo.warnings())
print('ball', ball.width, 'x', ball.height, 'center', ball.par.centerx.eval(), ball.par.centery.eval(), ball.errors(), ball.warnings())
print('ball pars', [(p.name, p.eval()) for p in ball.pars() if p.name.startswith(('center', 'radius', 'fill', 'bg', 'soft'))])
cx, cy = ball.par.centerx.eval(), ball.par.centery.eval()
x, y = int((0.5 + cx * 720 / 1280) * 1280), int((0.5 + cy) * 720)
for o in (ball, demo, source):
    o.cook(force=True)
    print(o.name, 'at', (x, y), [round(v, 3) for v in o.sample(x=x, y=y)], 'center px', [round(v, 3) for v in o.sample(x=640, y=360)])
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out', 'fluid_ball')
os.makedirs(out, exist_ok=True)
for o in (ball, demo):
    o.save(os.path.join(out, o.name + '.png'))
