# DEV ONLY probe: does the GLSL TOP's TOPs parameter append inputs after the wired ones?
host = op(TDLIB_PARENT)
for n in ('pi_g', 'pi_c0', 'pi_c1', 'pi_c2', 'pi_c3', 'pi_c4'):
    if host.op(n):
        host.op(n).destroy()
cs = []
for i in range(5):
    c = host.create(constantTOP, 'pi_c{}'.format(i))
    c.par.colorr = i / 10.0
    c.par.resolutionw = c.par.resolutionh = 8
    cs.append(c)
g = host.create(glslTOP, 'pi_g')
g.par.outputresolution = 'custom'; g.par.resolutionw = g.par.resolutionh = 8
for i in range(3):
    g.inputConnectors[i].connect(cs[i])
g.par.tops = 'pi_c3 pi_c4'
g.par.format = 'rgba32float'
(dat,) = [d for d in g.docked if d.name.endswith('_pixel')]
dat.text = '''out vec4 fragColor;
void main() {
    fragColor = vec4(texture(sTD2DInputs[0], vUV.st).r, texture(sTD2DInputs[2], vUV.st).r,
                     texture(sTD2DInputs[3], vUV.st).r, texture(sTD2DInputs[4], vUV.st).r);
}'''
g.cook(force=True)
a = g.numpyArray()
print('errors', repr(g.errors()), 'warnings', repr(g.warnings()))
print('pixel', [round(float(x), 3) for x in a[0, 0]])
for o in [g] + cs:
    o.destroy()
