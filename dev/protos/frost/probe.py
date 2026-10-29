"""DEV ONLY. Print Frost's state in /tdlib_dev/frost (after dev/protos/frost/look.py built it): the passes a frame,
and the pane's and the ice's values at a few cells."""
fx = op(TDLIB_PARENT + '/frost')
for n in ('fern', 'stars'):
    o = fx.op(n)
    print(n, 'npasses', o.par.npasses.eval(), 'expr', o.par.npasses.expr)
print('stepSeconds', absTime.stepSeconds, 'audio source', fx.op('audio')['source'].eval())
for n in ('pane', 'seed', 'fern', 'warmth', 'near'):
    o = fx.op(n)
    vals = []
    for u, v in ((0.1, 0.9), (0.5, 0.5), (0.8, 0.3), (0.02, 0.5), (0.9, 0.95)):
        vals.append(tuple(round(x, 3) for x in o.sample(u=u, v=v)))
    print(n, vals)
for n in ('seed', 'fern', 'look'):
    o = fx.op(n)
    print(n, [(o.par['vec{}name'.format(i)].eval(), [round(o.par['vec{}value{}'.format(i, a)].eval(), 6) for a in 'xyzw'])
              for i in range(o.seq.vec.numBlocks)])
