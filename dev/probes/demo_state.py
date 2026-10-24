"""DEV ONLY. Inside TouchDesigner: print /tdlib_demo's state (read-only: it changes nothing).

    dev/td.sh dev/probes/demo_state.py
"""

d = op('/tdlib_demo')
if d is None:
    print('no /tdlib_demo')
else:
    show, beat = d.op('show'), d.op('beat')
    print('Effect:', repr(d.par.Effect.eval()), '(menu index {}),'.format(d.par.Effect.menuIndex),
          'Play:', d.par.Play.eval(), '| show index', show.par.index.eval(), 'of',
          [i.name for i in show.inputs], '| beat index', beat.par.index.eval())
    now = absTime.frame
    for fx in d.findChildren(type=COMP, depth=1):
        print('  {}: last cooked {} frames ago, allowCooking {}, bypass {}, problems {}'.format(
            fx.name, now - fx.cookAbsFrame, fx.allowCooking, fx.bypass,
            (fx.errors(recurse=True) + fx.warnings(recurse=True)) or 'none'))
