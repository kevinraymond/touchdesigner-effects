"""DEV ONLY probe: the Speed CHOP's and Constant CHOP's parameter names (2025.33230). dev/td.sh dev/probes/speed_pars.py"""
host = op(TDLIB_PARENT)
for kind in (speedCHOP, constantCHOP):
    o = host.create(kind, 'probe_pars')
    print('==', o.OPType, [(p.name, p.eval()) for p in o.pars() if p.page is not None and p.page.name != 'Common'][:40])
    if kind is constantCHOP:
        print('seq', [s.name for s in o.seq])
    o.destroy()
