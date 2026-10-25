"""DEV ONLY probe: what a beat's puff looks like in Fluid. Loads the built fluid.tox with the test clip and a
beat (140 BPM by default), and at the first EVENTS puffs that pass the gate saves out_top at the puff and
0.1, 0.2 and 0.35 s after it, as dev/out/fluid_puff/<look>_<k>_<ms>.png.
TD_ARGS='Look=smoke' dev/td.sh dev/probes/fluid_puff_frames.py; dev/td.sh --pull dev/out/fluid_puff/done"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')     # testbed.py's own is relative to this file
EVENTS, AFTER = 2, (0, 100, 200, 350)
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
opts = dict(clip='b1_dancer', beat='music')
pars = {}
for w in TDLIB_ARGS:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'fluid', 'fluid.tox'))
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = type(p.default)(float(v)) if isinstance(p.default, (int, float)) and not isinstance(p.default, bool) else v
clip, beat = testbed(host, opts)
wire(fx, clip, beat)
view = host.create(nullTOP, 'view')
view.inputConnectors[0].connect(fx.outputConnectors[0])
out = os.path.join(_ROOT, 'dev', 'out', 'fluid_puff')
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    os.remove(os.path.join(out, f))
look = fx.par.Look.eval()
state = dict(events=0, last=0.0, end=absTime.seconds + 20, warm=absTime.seconds + 2)


def save(k, ms):
    fx.op('out_top').save(os.path.join(out, '{}_{}_{:03d}.png'.format(look, k, ms)))
    if k == EVENTS - 1 and ms == AFTER[-1]:
        open(os.path.join(out, 'done'), 'w').write('ok\n')


def tick():
    view.cook(force=True)
    env = fx.op('puff_env')[0].eval()
    if absTime.seconds > state['warm'] and env > 0.95 and state['last'] <= 0.95 and state['events'] < EVENTS:
        for ms in AFTER:
            run('args[0](args[1], args[2])', save, state['events'], ms, delayMilliSeconds=max(ms, 1))
        state['events'] += 1
    state['last'] = env
    if state['events'] < EVENTS and absTime.seconds < state['end']:
        run('args[0]()', tick, delayFrames=1)


tick()
print('waiting for {} puffs ({})'.format(EVENTS, look))
