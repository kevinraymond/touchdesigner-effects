"""DEV ONLY. Frost's ice values along the feedback loop."""
fx = op(TDLIB_PARENT + '/frost')
for n in ('still', 'ice_fb', 'seed', 'fern', 'ice', 'pane'):
    o = fx.op(n)
    print(n, o.width, o.height, o.par.format.eval() if hasattr(o.par, 'format') else '', [tuple(round(x, 4) for x in o.sample(u=u, v=v)[:3]) for u, v in ((0.3, 0.6), (0.7, 0.3))])
print('Even', fx.par.Even.eval(), 'Thawmove', fx.par.Thawmove.eval())
