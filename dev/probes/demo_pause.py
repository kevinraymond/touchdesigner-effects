"""DEV ONLY. Pause /tdlib_demo for a measurement and put it back after: TD_ARGS=pause shows Source only
with the clip stopped, keeping what it was showing; TD_ARGS=resume puts that back. Measurements want
the Mac otherwise idle, and the demo running an effect lands in their GPU times.
TD_ARGS=pause dev/td.sh dev/probes/demo_pause.py; ...measure...; TD_ARGS=resume dev/td.sh dev/probes/demo_pause.py"""
demo = op('/tdlib_demo')
word = (TDLIB_ARGS or ['pause'])[0]
if word == 'pause':
    if demo.fetch('paused', None) is None:
        demo.store('paused', {'Effect': demo.par.Effect.eval(), 'Play': demo.par.Play.eval()})
    demo.par.Effect, demo.par.Play = 'clip', False
else:
    kept = demo.fetch('paused', None) or {}
    for k, v in kept.items():
        setattr(demo.par, k, v)
    demo.unstore('paused')
print(word, '-> Effect', demo.par.Effect.eval(), 'Play', demo.par.Play.eval(), '| kept', demo.fetch('paused', None))
