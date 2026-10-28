"""DEV ONLY. Parameter names Lens Flare needs (2025.33230): a Geometry COMP's instancing, DAT to CHOP, CHOP to TOP.
dev/td.sh dev/probes/flare_pars.py"""
import re

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid and o.name.startswith('probe_'):
        o.destroy()
for kind, pat in ((dattoCHOP, r'.'), (choptoTOP, r'.')):
    o = host.create(kind, 'probe_' + kind.__name__)
    names = ['{}={}'.format(p.name, p.val if p.mode == ParMode.CONSTANT else p.expr) for p in o.pars() if re.search(pat, p.name) and (p.page is None or p.page.name != 'Common')]
    print(kind.__name__, ':', ' '.join(names))
    for p in o.pars():
        if p.isMenu and re.search(pat, p.name) and (p.page is None or p.page.name != 'Common'):
            print('   ', p.name, p.menuNames)
    for d in list(o.docked):
        d.destroy()
    o.destroy()
