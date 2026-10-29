"""DEV ONLY. What the Blur TOP's Filter Size means in sigma (2025.33230), for Film Stock's blurs: a single bright pixel
blurred at several sizes, Gaussian and bartlette (triangle), and the standard deviation of the result measured:

    dev/td.sh dev/probes/blur_sigma.py
"""
import numpy as np

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
dot = host.create(glslTOP, 'probe_dot')
dot.par.outputresolution = 'custom'
dot.par.resolutionw = dot.par.resolutionh = 128
dot.par.format = 'rgba32float'
[d for d in dot.docked if d.name.endswith('_pixel')][0].text = (
    'out vec4 fragColor;\nvoid main() { ivec2 p = ivec2(gl_FragCoord.xy); '
    'fragColor = vec4((p.x == 64 && p.y == 64) ? 1.0 : 0.0); }')
for kind in ('gaussian', 'bartlette', 'box'):
    for size in (0.5, 1, 1.5, 2, 3, 4, 6, 9, 12, 20, 40):
        b = host.create(blurTOP, 'probe_blur')
        b.inputConnectors[0].connect(dot)
        b.par.type = kind
        b.par.size = size
        b.cook(force=True)
        a = b.numpyArray()[..., 0].astype(np.float64)
        ys, xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        s = a.sum()
        mx = (a * xs).sum() / s
        var = (a * (xs - mx) ** 2).sum() / s
        print('{:9s} size {:5.1f}: sum {:.3f} sigma {:.3f} px, peak {:.4f}'.format(kind, size, s, np.sqrt(var), a.max()))
        b.destroy()
dot.destroy()
