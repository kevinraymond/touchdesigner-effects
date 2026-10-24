"""DEV ONLY. TD_ARGS="geometryCOMP renderTOP" for only some. The parameters of the operators a GPU particle system is drawn with (Geometry COMP
instancing, Render TOP, Camera COMP, GLSL MAT, Constant MAT, Render Select TOP, a GLSL TOP's
color buffers), by page, so a builder names them right. dev/td.sh dev/probes/particle_pars.py"""

host = op(TDLIB_PARENT)
probe = host.op('particle_pars')
if probe:
    probe.destroy()
probe = host.create(baseCOMP, 'particle_pars')
KINDS = [eval(k) for k in TDLIB_ARGS] or [geometryCOMP, renderTOP, cameraCOMP, glslMAT, constantMAT, renderselectTOP,
                                         glslTOP, feedbackTOP, analyzeTOP, circleTOP, rectangleSOP]
geo = probe.create(geometryCOMP, 'geo_default')
print('a new Geometry COMP holds:', [(c.name, c.OPType, c.render, c.display) for c in geo.children])
mat = probe.create(constantMAT, 'mat_default')
print('blend menus:', list(mat.par.srcblend.menuNames), 'defaults', mat.par.srcblend.default, mat.par.destblend.default)
try:
    for kind in KINDS:
        o = probe.create(kind)
        print('==', o.OPType)
        pages = {}
        for p in o.pars():
            pages.setdefault(p.page.name if p.page else '-', []).append(
                p.name + ('=' + '|'.join(p.menuNames) if p.isMenu and p.menuNames and len(p.menuNames) < 16 else ''))
        for page, names in pages.items():
            if o.OPType == 'geometryCOMP' and page not in ('Instance', 'Instance 2', 'Render', 'Xform'):
                continue
            print('  [{}] {}'.format(page, ' '.join(names)))
finally:
    probe.destroy()
