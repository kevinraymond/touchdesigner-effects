"""DEV ONLY probe: a GLSL TOP's Number of Passes (2025.33230). Does each pass after the first read
the previous pass's output as sTD2DInputs[0], do the other inputs stay put, and is the pass index a
uniform? The fluid's pressure solve wants its Jacobi iterations in one TOP. dev/td.sh dev/probes/glsl_passes.py"""
host = op(TDLIB_PARENT)
for n in ('probe_passes', 'probe_passes_a', 'probe_passes_b'):
    if host.op(n):
        host.op(n).destroy()
a = host.create(constantTOP, 'probe_passes_a')
a.par.format = 'rgba32float'
a.par.colorr, a.par.colorg, a.par.colorb, a.par.alpha = 0, 0, 0, 1
b = host.create(constantTOP, 'probe_passes_b')
b.par.format = 'rgba32float'
b.par.colorr, b.par.colorg, b.par.colorb, b.par.alpha = 10, 0, 0, 1
g = host.create(glslTOP, 'probe_passes')
g.inputConnectors[0].connect(a)
g.inputConnectors[1].connect(b)
g.par.format = 'rgba32float'
print('pass pars:', [(p.name, p.label, p.eval()) for p in g.pars() if 'pass' in p.name.lower() or 'pass' in p.label.lower()])
pix = [d for d in g.docked if d.name.endswith('_pixel')][0]
# r: +1 per pass on top of input 0; g: input 1 as this pass sees it; b: the pass index uniform, if any.
pix.text = '''out vec4 fragColor;
void main() {
    vec4 prev = texture(sTD2DInputs[0], vUV.st);
    float other = texture(sTD2DInputs[1], vUV.st).r;
    fragColor = vec4(prev.r + 1.0, other, float(uTDPass), 1.0);
}
'''
for n in (1, 4, 30):
    g.par.npasses = n
    g.cook(force=True)
    print('npasses', n, '->', [round(v, 3) for v in g.sample(x=0, y=0)], 'errors:', g.errors(), 'warnings:', g.warnings())
