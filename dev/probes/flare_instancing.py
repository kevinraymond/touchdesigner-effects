"""DEV ONLY probe for Lens Flare (2025.33230): can a GLSL MAT's vertex shader place every instance itself? A Geometry
COMP with Instance Count Mode Manual (no instance TOPs), its vertex shader reading a Table DAT -> DAT to CHOP -> CHOP to
TOP texture with texelFetch(..., ivec2(TDInstanceID(), row)), writing gl_Position in clip space directly, added up by
blending, drawn by a Render TOP. The table: one row per instance (x, y, size, brightness). Prints the rendered sum
against the table's, and where the brightest pixel is.

    dev/td.sh dev/probes/flare_instancing.py"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid and o.name.startswith('probe_fi'):
        o.destroy()
box = host.create(baseCOMP, 'probe_fi')

rows = [(-0.5, -0.5, 0.2, 0.25), (0.5, 0.5, 0.1, 0.5), (0.0, 0.0, 0.3, 0.125), (0.5, -0.5, 0.05, 1.0)]
table = mk(box, tableDAT, 'table', at=(0, 0))
table.clear()
table.appendRow(['x', 'y', 'size', 'bright'])
for r in rows:
    table.appendRow([str(v) for v in r])
d2c = mk(box, dattoCHOP, 'd2c', at=(200, 0), dat='table', output='chanpercol', firstrow='names', firstcolumn='values')
c2t = mk(box, choptoTOP, 'c2t', at=(400, 0), chop='d2c', dataformat='r')
setpars(c2t, format='r32float')

VERT = '''uniform sampler2D sTable;
out vec2 vUV;
out float vBright;
void main() {
    int id = TDInstanceID();
    float x = texelFetch(sTable, ivec2(id, 0), 0).r;
    float y = texelFetch(sTable, ivec2(id, 1), 0).r;
    float size = texelFetch(sTable, ivec2(id, 2), 0).r;
    vBright = texelFetch(sTable, ivec2(id, 3), 0).r;
    vUV = TDPos().xy * 2.0;
    gl_Position = vec4(vec2(x, y) + TDPos().xy * 2.0 * size, 0.0, 1.0);
}
'''
PIXEL = '''in vec2 vUV;
in float vBright;
out vec4 oFragColor;
void main() {
    TDCheckDiscard();
    oFragColor = TDOutputSwizzle(vec4(vBright, vBright, vBright, 1.0));
}
'''
mat = mk(box, glslMAT, 'mat', at=(400, -200), blending=True, srcblend='one', destblend='one', depthtest=False,
         depthwriting=False)
docked(mat, '_vertex', VERT, 'probe')
docked(mat, '_pixel', PIXEL, 'probe')
mat.seq.sampler.numBlocks = 1
mat.par.sampler0name = 'sTable'
mat.par.sampler0top = 'c2t'
geo = mk(box, geometryCOMP, 'geo', at=(600, -200), instancing=True, instancecountmode='manual',
         numinstances=len(rows), material='mat')
for o in list(geo.children):
    o.destroy()
quad = mk(geo, rectangleSOP, 'quad', at=(0, 0), sizex=1, sizey=1, texture='face')
quad.render = quad.display = True
cam = mk(box, cameraCOMP, 'cam', at=(600, -400), projection='ortho', tz=5)
for o in list(cam.children):
    o.destroy()
render = mk(box, renderTOP, 'render', at=(800, -200), camera='cam', geometry='geo', lights='', bgcolorr=0, bgcolorg=0,
            bgcolorb=0, bgcolora=0, format='rgba32float', outputresolution='custom', resolutionw=200, resolutionh=200)
render.cook(force=True)
a = render.numpyArray(delayed=False)
print('info:', mat.op('mat_info').text if mat.op('mat_info') else [d.text for d in mat.docked if 'info' in d.name])
print('errors:', render.errors(recurse=True), render.warnings(recurse=True), mat.errors(), mat.warnings())
print('table texture', c2t.width, 'x', c2t.height, c2t.numpyArray(delayed=False)[..., 0].tolist())
expect = sum(r[3] * (2 * r[2] * 100) ** 2 for r in rows)
print('rendered sum', float(a[..., 0].sum()), 'expected about', expect)
for r in rows:
    px, py = int((r[0] + 1) * 100), int((r[1] + 1) * 100)
    print('at', r[:2], 'pixel', float(a[py, px, 0]), 'expected', r[3])
