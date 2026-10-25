"""DEV ONLY. Point cloud prototypes: a few ways to turn a clip and its depth into a cloud of dots,
side by side, the same frame seen from a few camera angles. Builds them in TDLIB_PARENT and saves
each render at each angle:

    TD_ARGS='clip=b1_dancer frame=40 out=r2' dev/td.sh dev/protos/point_cloud/look.py
    dev/td.sh --pull dev/out/point_cloud/r2/done
    uv run --with pillow dev/sheet.py dev/out/point_cloud/r2 --width 480

Words: clip=<name> (private/assets/ready/<name>.mp4 and <name>_depth.mp4), frame=<index> (the
frame to hold), out=<folder under dev/out/point_cloud>, depth=<Depth for every variant>, only=<a,b>
(build only these variants), at=<capture times>.
Variants (pos.glsl, dots_vertex.glsl, dots_pixel.glsl, splat_norm.glsl), round 3:
  a_dots        320 x 180 round solid dots facing the camera, each jittered within its cell
  b_fine        the same at 640 x 360
  c_glow        640 x 360 soft dots added up
  d_splats      Gaussian splats lying in the surface, blended and divided out (two passes)
  e_fine_splats the same at 640 x 360
  f_drop        a_dots with edge points dropped instead of snapped to a side
"""
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')

opts = dict(clip='b1_dancer', frame='40', out='r1', depth='1.5', only='', at='1,2.5,4,5.5')
opts.update(w.split('=', 1) for w in TDLIB_ARGS if '=' in w)
DEPTH, EDGE, SMOOTH = float(opts['depth']), 0.05, 0.03
# name: (edge cut, edges 0 dropped / 1 snapped, smoothing, grid w, h, dot 0 billboard / 1 disc,
#        look 0 solid / 1 soft / 2 square / 'splat', size in grid steps, jitter)
VARIANTS = dict(
    a_dots=(EDGE, 1, SMOOTH, 320, 180, 0, 0, 0.8, 1.0),
    b_fine=(EDGE, 1, SMOOTH, 640, 360, 0, 0, 0.9, 1.0),
    c_glow=(EDGE, 1, SMOOTH, 640, 360, 0, 1, 2.0, 1.0),
    d_splats=(EDGE, 1, SMOOTH, 320, 180, 1, 'splat', 2.5, 0.0),
    e_fine_splats=(EDGE, 1, SMOOTH, 640, 360, 1, 'splat', 2.5, 0.0),
    f_drop=(EDGE, 0, SMOOTH, 320, 180, 0, 0, 0.8, 1.0),
)
if opts['only']:
    VARIANTS = {k: v for k, v in VARIANTS.items() if k.split('_')[0] in opts['only'].split(',')}
# (yaw, tilt in degrees, distance as a share of the starting one) at each capture
ANGLES = [(0, 0, 1.0), (25, 0, 1.0), (-40, 15, 1.0), (65, 25, 0.8)]

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
clip, _ = testbed(host, dict(clip=opts['clip'], beat='none'))
setpars(clip, playmode='specify', indexunit='indices', index=int(opts['frame']))
clip.cook(force=True)
depth = host.op('clip_depth')
aspect = clip.width / max(1, clip.height)

cam = mk(host, cameraCOMP, 'cam', 0, 600, comment='Orbits the target.', projection='perspective', near=0.01, far=100)
for o in list(cam.children):
    o.destroy()
fov_pars = [p.name for p in cam.pars() if any(k in p.name for k in ('fov', 'viewangle', 'focal', 'aperture'))]
FOV = 40.0
cam.par.fov = FOV
method = cam.par.viewanglemethod.eval() if hasattr(cam.par, 'viewanglemethod') else 'horizontal (assumed)'
if hasattr(cam.par, 'viewanglemethod'):
    vert = [n for n in cam.par.viewanglemethod.menuNames if 'vert' in n.lower()]
    if vert:
        cam.par.viewanglemethod = vert[0]
        method = vert[0]
vertical = 'vert' in str(method).lower()
D0 = (0.5 if vertical else aspect / 2) / math.tan(math.radians(FOV / 2))
target = mk(host, nullCOMP, 'target', 200, 600, comment='What the camera looks at: the middle of the cloud.',
            tz=-0.4 * D0)
cam.par.lookat = 'target'


def aim(yaw, tilt, k):
    r = 1.4 * D0 * k
    cam.par.tx = r * math.sin(math.radians(yaw)) * math.cos(math.radians(tilt))
    cam.par.ty = r * math.sin(math.radians(tilt))
    cam.par.tz = target.par.tz.eval() + r * math.cos(math.radians(yaw)) * math.cos(math.radians(tilt))


aim(*ANGLES[0])
renders = {}


for i, (name, (edge, snap, smooth, gw, gh, disc, look, size, jitter)) in enumerate(VARIANTS.items()):
    x = i * 400
    pos = glsl(host, 'pos_' + name, x, 0, [depth], open(os.path.join(_HERE, 'pos.glsl')).read(),
               'Every grid point in 3D.', res=(gw, gh), fmt='rgba32float',
               uGeo=(aspect, DEPTH, edge, snap), uSmooth=(smooth, round(3 * gh / 180)), uCam=(D0, jitter))
    splat = look == 'splat'
    mats = []
    for suffix, pass_, lk in ((('vis', (1, 0.03), 4), ('acc', (0, 0), 3)) if splat else (('', (0, 0), look),)):
        mat = mk(host, glslMAT, 'mat{}_{}'.format(suffix, name), x + (100 if suffix == 'acc' else 0), -150,
                 comment='Dots from pos.')
        docked(mat, '_vertex', open(os.path.join(_HERE, 'dots_vertex.glsl')).read(), 'The dots.')
        docked(mat, '_pixel', open(os.path.join(_HERE, 'dots_pixel.glsl')).read(), 'A dot.')
        mat.seq.sampler.numBlocks = 2
        setpars(mat, sampler0name='sPos', sampler0top=pos.name, sampler1name='sColor', sampler1top=clip.name)
        uniforms(mat, uDot=(size, disc, 1.0 / gh, edge), uPass=pass_ + (jitter,), uLook=(lk,))
        if lk == 1:
            setpars(mat, blending=True, srcblend='one', destblend='one', depthtest=False, depthwriting=False)
        if lk == 3:
            setpars(mat, blending=True, srcblend='one', destblend='one', srcblenda='one', destblenda='one',
                    depthtest=True, depthwriting=False, premultrgbbyalpha=False)
        mats.append(mat)
    geo = mk(host, geometryCOMP, 'geo_' + name, x, -300, comment='A square per grid point.', instancing=True,
             instancecountmode='oplength', instanceop=pos.name, instancetx='r', instancety='g', instancetz='b',
             material=mats[0].name)
    for o in list(geo.children):
        o.destroy()
    quad = mk(geo, rectangleSOP, 'quad', 0, 0, comment='One dot.', sizex=1, sizey=1)
    quad.render = quad.display = True
    render = mk(host, renderTOP, 'render_' + name, x, -450, comment='The cloud.', camera='cam',
                geometry=geo.name, lights='', bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=1,
                outputresolution='custom', resolutionw=clip.width, resolutionh=clip.height)
    if splat:
        # A Render Pass TOP draws into its input's buffers, so the float format the sums need is set here.
        setpars(render, drawdepthonly=True, format='rgba16float', bgcolora=0)
        acc = mk(host, renderpassTOP, 'pass_' + name, x, -600, [render], 'The splats added up over the depth pass.',
                 camera='cam', geometry=geo.name, lights='', cleardepth=False, clearcolor=True,
                 overridemat=mats[1].name, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=0)
        render = glsl(host, 'norm_' + name, x, -750, [acc], open(os.path.join(_HERE, 'splat_norm.glsl')).read(),
                      'Color divided by weight.')
        print('render pass', acc.name, 'format', getattr(acc, 'pixelFormat', '?'), 'errors', acc.errors())
    renders[name] = render

out_dir = os.path.join(_ROOT, 'dev', 'out', 'point_cloud', opts['out'])
at = [float(t) for t in opts['at'].split(',')]
for t, angle in zip(at[1:], ANGLES[1:]):
    run('args[0](*args[1])', aim, angle, delayMilliSeconds=int((t - 0.6) * 1000))


def costs():
    lines = ['D0 {:.3f} fov {} method {} aspect {:.3f}; camera pars {}'.format(D0, FOV, method, aspect, fov_pars)]
    for name, r in renders.items():
        p = host.op('pos_' + name)
        mats = [m for m in (host.op('mat_' + name), host.op('matvis_' + name), host.op('matacc_' + name)) if m]
        lines.append('{}: errors {!r} {!r}'.format(name, r.errors(), [(m.errors(), m.warnings()) for m in mats]))
        for m in mats:
            info = [d for d in m.docked if d.name.endswith('_info')]
            if info and info[0].text.count('Successfully') < 3:
                lines.append('  info: ' + info[0].text[:800])
    with open(os.path.join(out_dir, 'costs.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')


os.makedirs(out_dir, exist_ok=True)
run('args[0]()', costs, delayMilliSeconds=int((at[-1] - 0.3) * 1000))
tops = dict(renders)
tops['zz_depth'] = depth
print('variants', list(VARIANTS), 'D0', round(D0, 3), 'method', method, 'aspect', round(aspect, 3), 'cam pars', fov_pars)
capture(tops, out_dir, at=at, keep_cooking=True)
