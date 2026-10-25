"""DEV ONLY. Do VHS + CRT's enable expressions follow its toggles and menus? (me.par.Tape in a custom
parameter's enableExpr.) Prints which of the screens' parameters are enabled for each Screen."""
import os
host = op(TDLIB_PARENT)
for o in list(host.children):
    o.destroy()
fx = host.loadTox(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'effects', 'vhs_crt', 'vhs_crt.tox'))
SCREEN = ('Mask', 'Masksize', 'Scanlines', 'Curvature', 'Glow', 'Response', 'Angle', 'Subfields', 'Inkmode', 'Ghosting')
def show(what, names=('Speed', 'Wear', 'Masksize', 'Mask', 'Length')):
    print(what, [n for n in names if getattr(fx.par, n).enable])
show('defaults')
fx.par.Tape = False; fx.par.Mask = 'none'; fx.par.Bursts = 'off'; show('Tape off, Mask none, Bursts off')
fx.par.Mask = 'aperture'
for s in ('crt', 'lcd', 'plasma', 'eink', 'none'):
    fx.par.Screen = s
    show('Screen ' + s, SCREEN)
fx.par.Screen = 'crt'; fx.par.Mask = 'none'; show('CRT, Mask none', SCREEN)
