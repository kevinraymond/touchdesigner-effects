"""DEV ONLY. Do VHS + CRT's enable expressions follow its toggles and menus? (me.par.Tape in a custom
parameter's enableExpr.)"""
import os
host = op(TDLIB_PARENT)
for o in list(host.children):
    o.destroy()
fx = host.loadTox(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'effects', 'vhs_crt', 'vhs_crt.tox'))
def show(what):
    print(what, {n: getattr(fx.par, n).enable for n in ('Speed', 'Wear', 'Masksize', 'Mask', 'Length')})
show('defaults')
fx.par.Tape = False; fx.par.Mask = 'none'; fx.par.Bursts = 'off'; show('Tape off, Mask none, Bursts off')
fx.par.Screen = False; show('Screen off too')
