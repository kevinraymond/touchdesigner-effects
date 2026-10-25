"""DEV ONLY. What one beat does to Bent Cam, frame by frame: loads effects/bent_cam/bent_cam.tox with the test clip
and a dance-tempo beat (dev/testbed.py's beat=music), waits for a beat after SETTLE seconds, and saves the output on
the frame before it and the FRAMES after it:

    TD_ARGS='Kick=0.5 out=seq' dev/td.sh dev/protos/bent_cam/beat_seq.py
    dev/td.sh --pull dev/out/bent_cam/seq/done

Words: clip=<name>, out=<folder under dev/out/bent_cam>, frames=<n>, and <Par>=<value> for the effect's parameters.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')     # testbed's own is relative to the script it runs in
SETTLE = 2.0
LIMIT = 15.0     # give up after this many seconds without a beat

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'bent_cam', 'bent_cam.tox'))
opts = dict(clip='b1_dancer', out='seq', frames='12')
pars = {}
for w in [w for w in TDLIB_ARGS if '=' in w]:
    k, v = w.split('=', 1)
    (opts if k in opts else pars)[k] = v
clip, beat = testbed(host, dict(clip=opts['clip'], beat='music'))
wire(fx, clip, beat)
for k, v in pars.items():
    p = getattr(fx.par, k)
    p.val = v if p.isMenu else type(p.default)(float(v))
out_dir = os.path.join(_ROOT, 'dev', 'out', 'bent_cam', opts['out'])
os.makedirs(out_dir, exist_ok=True)
if os.path.exists(os.path.join(out_dir, 'done')):
    os.remove(os.path.join(out_dir, 'done'))
top, count, n = fx.op('out_top'), fx.op('beat_n'), int(opts['frames'])
state = dict(start=absTime.seconds, shot=-1, beats=None)


def tick():
    if not top.valid or absTime.seconds - state['start'] > LIMIT:
        with open(os.path.join(out_dir, 'done'), 'w') as f:
            f.write('no beat: beat_n {}, beat_env {}\n'.format(fx.op('beat_n')[0], fx.op('beat_env')[0]))
        return
    top.cook(force=True)
    if state['shot'] < 0:
        top.save(os.path.join(out_dir, 'f_before.png'))      # overwritten until the beat comes
        beats = count[0].eval()     # watch the count (its value, not the Channel): a one-frame pulse can be missed
        if state['beats'] is not None and beats != state['beats'] and absTime.seconds - state['start'] > SETTLE:
            state['shot'] = 0
        state['beats'] = beats
    if state['shot'] >= 0:
        top.save(os.path.join(out_dir, 'f_{:02d}.png'.format(state['shot'])))
        state['shot'] += 1
        if state['shot'] >= n:
            with open(os.path.join(out_dir, 'done'), 'w') as f:
                f.write('{}\n'.format(pars))
            return
    run('args[0]()', tick, delayFrames=1)


tick()
print('waiting for a beat, then {} frames into {}'.format(n, out_dir))
