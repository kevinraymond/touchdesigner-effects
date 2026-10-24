"""DEV ONLY. Read-only: every Particles in the open project (anything with a Capture pulse and a
capture_exec DAT), what feeds its input 1, its Find, how many captures it counted, and what plate
and subject hold. dev/td.sh dev/probes/capture_state.py"""
for fx in root.findChildren(type=COMP, maxDepth=6):
    ex = fx.op('capture_exec')
    if ex is None or not hasattr(fx.par, 'Capture'):
        continue
    ins = [[c.owner.path for c in i.connections] for i in fx.inputConnectors]
    print(fx.path, '| Find', fx.par.Find.eval(), '| Show', fx.par.Show.eval(), '| inputs', ins,
          '| allowCooking', fx.allowCooking, '| cookedThisFrame', fx.op('look').cookFrame, absTime.frame)
    print('  capture_exec active', ex.par.active.eval(), 'op', ex.par.op.eval(), 'pars', ex.par.pars.eval(),
          'onpulse', ex.par.onpulse.eval(), 'errors', ex.errors(), ex.scriptErrors())
    print('  captures', fx.op('captures').par.const0value.eval(), '| Capture enabled', fx.par.Capture.enable)
    for name in ('source', 'small', 'plate', 'plate_in', 'subject'):
        o = fx.op(name)
        try:
            s = o.sample(x=0, y=0)
        except Exception as e:
            s = repr(e)
        print('  ', name, o.width, 'x', o.height, 'cookFrame', o.cookFrame, 'px(0,0)', s, 'errors', o.errors())
