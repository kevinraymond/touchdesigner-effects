"""DEV ONLY. Does /tdlib_demo's Source switch input 1 and input 3? Sets Source to Camera, reports
after a few seconds (camera running, effects' inputs, Particles' label), sets it back to Clip and
reports again, in dev/out/demo_source/report.txt. The camera is on for those few seconds.
dev/td.sh dev/probes/demo_source.py; dev/td.sh --pull dev/out/demo_source/done"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, 'dev', 'out', 'demo_source')
os.makedirs(OUT, exist_ok=True)
for f in ('done', 'report.txt'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
demo = op('/tdlib_demo')


def report(when):
    cam, fx = demo.op('camera'), demo.op('particles')
    lines = ['{}: Source {} | camera active {} {} x {} errors {!r} | picture index {}'.format(
        when, demo.par.Source.eval(), cam.par.active.eval(), cam.width, cam.height, cam.errors(),
        demo.op('picture').par.index.eval())]
    for o in demo.findChildren(type=COMP, depth=1):
        if o.name != 'fosfora_signal':
            lines.append('  {} inputs {}'.format(o.name, [[c.owner.name for c in i.connections] for i in o.inputConnectors]))
    lines.append('  particles subject code (b) {}'.format(fx.op('subject').sample(x=0, y=0)[2]))
    with open(os.path.join(OUT, 'report.txt'), 'a') as f:
        f.write('\n'.join(lines) + '\n')


def back():
    report('camera')
    demo.par.Source = 'clip'
    run('args[0]("clip again"); open(args[1], "w").write("ok")', report, os.path.join(OUT, 'done'),
        delayMilliSeconds=1000)


report('before')
demo.par.Source = 'camera'
run('args[0]()', back, delayMilliSeconds=4000)
