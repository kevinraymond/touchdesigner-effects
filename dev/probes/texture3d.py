"""DEV ONLY probe: the Texture 3D TOP as a frame history (2025.33230), for slit-scan. Which parameters does it
have, does each frame add one slice, where does the newest slice go (a ring buffer or a shift), and what does a
GLSL TOP see of it (sTD3DInputs, uTD3DInfos[0].depth)? Forced cooks within one Python call add nothing, so it
steps one frame at a time and writes dev/out/probe_t3/result.txt, then done:

    dev/td.sh dev/probes/texture3d.py && dev/td.sh --pull dev/out/probe_t3/done"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
host = op(TDLIB_PARENT)
out_dir = os.path.join(_ROOT, 'dev', 'out', 'probe_t3')
os.makedirs(out_dir, exist_ok=True)
for f in ('done', 'result.txt'):
    if os.path.exists(os.path.join(out_dir, f)):
        os.remove(os.path.join(out_dir, f))
for n in ('probe_t3_c', 'probe_t3', 'probe_t3_g', 'probe_t3_a', 'probe_t3_ga'):
    if host.op(n):
        host.op(n).destroy()
lines = []
N = 8
# x: which slice this pixel reads; r: what that slice holds (the constant's red when it was cached).
SHADER = '''out vec4 fragColor;
void main() {
    int i = int(gl_FragCoord.x);
    float r = texelFetch(SAMPLER, ivec3(0, 0, i), 0).r;
    vec4 d = INFOS[0].depth;
    fragColor = vec4(r, d.x, d.y, d.z);
}
'''


def chain(suffix, kind):
    c = host.op('probe_t3_c') or host.create(constantTOP, 'probe_t3_c')
    c.par.outputresolution = 'custom'
    c.par.resolutionw, c.par.resolutionh = 4, 4
    c.par.format = 'rgba32float'
    # Red counts frames since the probe began, so each slice says when it was cached.
    c.par.colorr.expr = 'absTime.frame - {}'.format(absTime.frame)
    t = host.create(texture3dTOP, 'probe_t3' + suffix)
    t.inputConnectors[0].connect(c)
    t.par.cachesize = N
    t.par.type = kind
    g = host.create(glslTOP, 'probe_t3_g' + suffix)
    g.inputConnectors[0].connect(t)
    g.par.outputresolution = 'custom'
    g.par.resolutionw, g.par.resolutionh = N, 1
    g.par.format = 'rgba32float'
    sampler, infos = (('sTD3DInputs[0]', 'uTD3DInfos') if kind == 'texture3d'
                      else ('sTD2DArrayInputs[0]', 'uTD2DArrayInfos'))
    [d for d in g.docked if d.name.endswith('_pixel')][0].text = SHADER.replace('SAMPLER', sampler).replace('INFOS', infos)
    return t, g


t, g = chain('', 'texture3d')
ta, ga = chain('_a', 'texture2darray')
for p in t.pars():
    if p.page is not None and p.page.name not in ('Common',):
        lines.append('par {} {} {!r} {!r} {}'.format(p.page.name, p.name, p.label, p.eval(),
                                                     list(p.menuNames) if p.isMenu else ''))


def step(k):
    for name, tex, glsl in (('3d', t, g), ('array', ta, ga)):
        glsl.cook()
        row = [glsl.sample(x=i, y=0) for i in range(N)]
        lines.append('frame {:2d} {:5s} slices r: {} | depth (1/d, d, offset): {} | res {}x{} {}'.format(
            k, name, [round(px[0], 1) for px in row], [round(v, 4) for v in row[0][1:]], tex.width, tex.height,
            (glsl.errors() or '') + (glsl.warnings() or '')))
    if k < 14:
        run('args[0](args[1])', step, k + 1, delayFrames=1)
    else:
        with open(os.path.join(out_dir, 'result.txt'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        open(os.path.join(out_dir, 'done'), 'w').close()


run('args[0](args[1])', step, 1, delayFrames=1)
print('probing over 14 frames into', out_dir)
