"""DEV ONLY. Set /tdlib_demo's Effect and Play for a measurement condition (TD_ARGS='particles 1').
dev/probes/demo_pause.py's resume puts back what it kept. dev/td.sh dev/probes/demo_set.py"""
demo = op('/tdlib_demo')
demo.par.Effect, demo.par.Play = TDLIB_ARGS[0], TDLIB_ARGS[1] == '1'
print('Effect', demo.par.Effect.eval(), 'Play', demo.par.Play.eval())
