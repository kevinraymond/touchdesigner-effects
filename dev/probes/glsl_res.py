"""DEV ONLY. The GLSL TOP's resolution, format and input parameters and their menus (2025.33230), for Bent Cam's
sensor size (fit the input's aspect into a fixed size)."""
host = op(TDLIB_PARENT)
g = host.create(glslTOP, 'probe_glsl')
for p in g.pars():
    if p.name in ('outputresolution', 'resolutionw', 'resolutionh', 'outputaspect', 'resmult', 'format', 'fillmode',
                  'filtertype', 'inputfiltertype', 'inputextenduv', 'npasses', 'inputsmoothness', 'aspectw', 'aspecth',
                  'inputmapping') or (p.page is not None and p.page.name == 'Common'):
        print(p.page.name, p.name, repr(p.label), p.default, p.menuNames if p.isMenu else '')
g.destroy()
