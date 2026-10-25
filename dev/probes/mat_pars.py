"""DEV ONLY. The parameter names of a GLSL MAT, a Render TOP and a Render Pass TOP in this build
(samplers, uniforms, blending, depth, override material), and the DATs a GLSL MAT docks.
dev/td.sh dev/probes/mat_pars.py"""
import re

host = op(TDLIB_PARENT)
for kind, pat in ((glslMAT, r'sampler|vec\d|blend|depth|cull|wire|point|inst|dat|shader|pre'),
                  (renderTOP, r'override|mat|depth|cull|blend|camera|geometry|transp|order|antialias|mult'),
                  (renderpassTOP, r'.')):
    o = host.create(kind, 'probe_' + kind.__name__)
    names = [p.name for p in o.pars() if re.search(pat, p.name)]
    print(kind.__name__, ':', ' '.join(names))
    if kind is glslMAT:
        print('  docked:', [d.name for d in o.docked])
        for d in o.docked:
            print('  ---', d.name, '---')
            print(d.text)
    for d in list(o.docked):
        d.destroy()
    o.destroy()
