"""DEV ONLY probe: parameter names Slit-Scan's builder needs (2025.33230): the Texture 3D TOP's pixel formats and
resolution menu, the Trigger CHOP's envelope shapes, the Filter and Lag CHOPs' smoothing. dev/td.sh dev/probes/slit_pars.py"""
host = op(TDLIB_PARENT)
for kind, name, want in ((texture3dTOP, 'probe_sp_t3', ('format', 'outputresolution', 'resolutionw', 'inputfiltertype',
                                                         'filtertype')),
                         (triggerCHOP, 'probe_sp_trig', None), (filterCHOP, 'probe_sp_filter', None),
                         (lagCHOP, 'probe_sp_lag', None)):
    if host.op(name):
        host.op(name).destroy()
    o = host.create(kind, name)
    print('==', o.OPType)
    for p in o.pars():
        if p.page is None or p.page.name == 'Common' and want is None:
            continue
        if want is not None and p.name not in want:
            continue
        print('  ', p.page.name, p.name, repr(p.label), repr(p.eval()), list(p.menuNames)[:40] if p.isMenu else '')
    o.destroy()
