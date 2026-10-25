"""DEV ONLY. Read only: which effect /tdlib_demo shows, whether its clip plays, and the frame rate,
before measuring (the demo running an effect costs the GPU time a measurement counts).
dev/td.sh dev/probes/demo_effect.py"""
demo = op('/tdlib_demo')
print('demo Effect', demo.par.Effect.eval() if demo else None, '| Play', demo.par.Play.eval() if demo else None,
      '| Source', demo.par.Source.eval() if demo else None, '| fps', round(project.cookRate), 'perform', ui.performMode)
