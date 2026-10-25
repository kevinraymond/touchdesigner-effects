"""DEV ONLY probe: every TOP in the built Fluid with its Pixel Format parameter and size, for the idiom
review's C6. dev/td.sh dev/probes/fluid_formats.py"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
host = op(TDLIB_PARENT)
if host.op('fluid'):
    host.op('fluid').destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'fluid', 'fluid.tox'))
fx.op('out_top').cook(force=True)
for o in sorted(fx.findChildren(type=TOP, depth=1), key=lambda o: o.name):
    f = getattr(o.par, 'format', None)
    print('{:12} {:14} {}x{}'.format(o.name, f.eval() if f is not None else '-', o.width, o.height))
