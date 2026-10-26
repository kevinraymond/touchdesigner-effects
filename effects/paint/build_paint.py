"""Build Paint. Run from a textport: __file__ = '/path/to/build_paint.py'; exec(open(__file__).read())

The live picture as a painting: flat strokes that follow its edges, from the papers. The structure tensor (lib
structure_tensor()) gives the direction of the edges at every pixel; the anisotropic Kuwahara filter with polynomial
weights (Kyprianidis et al. 2009, 2010) averages each pixel over the evenest of 8 sectors of an ellipse turned along
that direction, so regions go flat and their edges stay sharp; a flow-based difference of Gaussians (XDoG,
Winnemoeller et al. 2012) draws ink lines along the edges. Oil lays the painting on canvas, Watercolor washes it onto
paper (Bousseau et al. 2006: wobble, edge darkening, pigment pooling, paper grain), and Ink thresholds it into two
tones.

kuwahara1 costs most of the frame, and its cost would grow with the brush's area if it read every pixel of the
ellipse; it reads a grid turned with the ellipse instead, SAMPLES along a radius, each from the mipmap level that
averages as many pixels as lie between samples, so a stroke costs the same at any size. Passes are separate TOPs
(npasses would halve the picture again on every pass with Half Size on); a Switch picks the last, so the passes not
asked for don't cook. Half Size paints at half the size and joint bilateral upsampling brings it back.

The network, left to right:
  picture  source -> structure_tensor() (tensor, tensor_h, tensor_v -> flow); input 3 (depth_in()) -> near ->
           brush_scale; kuwahara1 (source, flow, brush_scale) -> kuwahara2 -> kuwahara3 -> kuwahara (the last pass
           asked for) -> upsample (Half Size) -> painted -> dog (across the flow) -> lic (along it); mean; paint
  audio    audio_in() -> counts -> steps -> beat_now -> sweep, beat_n (each beat's band of broad strokes, and its
           direction) -> brush_scale; drop_now -> drop_env (a drop's broad strokes); level_pick -> level_smooth;
           swell (how much bigger the whole brush is now) -> kuwahara1-3's radius
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
STYLES = (('oil', 'Oil'), ('watercolor', 'Watercolor'), ('ink', 'Ink'))
WASH = 1.5           # Watercolor's strokes are this much broader than Brush: a wash covers more than a stroke
MAX_RADIUS = 40      # pixels: the brush's largest radius, after depth and the music
SAMPLES = 4.0        # samples along a radius: about pi 16 = 50 a pixel at any brush size
SMOOTH_FLOW = 2.0    # the structure tensor's smoothing, pixels at 720 high (the papers' sigma 2)
UP_SIGMA = 0.08      # Half Size's upsampling: how unlike two colors are (0-1) before one stops counting for the other
# Ink lines (XDoG): the DoG's sigma_e is Line Width; k, the line integral's sigma_m (pixels at 720 high), the edge
# strength a line starts at (eps) and how fast it darkens past it (phi).
K, LINE_SMOOTH, LINE_EDGE, LINE_SOFT = 1.6, 3.0, 0.01, 200.0
INK_P, INK_SOFT = 20.0, 20.0   # Ink's sharpening (p) and how soft its threshold is (phi)
# The music. Each beat sweeps a band of broad strokes across the picture in SWEEP s, from another direction each time
# (turning by the golden angle): at Beat Kick 1 the brush is 1 + KICK times its size in the band's middle, and the
# band's half-width is BAND picture heights. A swell of the whole picture barely showed, since the filter keeps a
# picture whatever its radius (twice the brush changed 5% of a still flower's pixels), and a moving edge is easy to
# see. Ink doesn't sweep: there a band of broad strokes flips whole patches between ink and paper, a flash (the flowers
# measured 2 a second under the stress beat, 1 without sweeps, the clip's own). Loudness 1 spans the brush from
# 2^(-LOUD/2) to 2^(LOUD/2) of its size from quiet to loud; a build broadens it by up to BUILD, and a drop by DROP for
# Length s (Song Moments).
KICK, SWEEP, BAND, LOUD, BUILD, DROP = 2.0, 0.35, 0.15, 1.0, 0.5, 1.0
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


README = src('readme.txt').format(v=VERSION, wash=WASH, kick=1 + KICK, sweep=SWEEP)
comp, page, source = new_effect(
    'paint', 'Paint',
    'Paint {}: the live picture as a painting, flat strokes that follow its edges, in oil, watercolor or ink, '
    'from the papers.'.format(VERSION),
    README, tags=('paint', 'painterly', 'kuwahara', 'watercolor', 'audio-reactive'), audio=True, depth=True,
    # A river running over rocks (TouchDesigner's own sample): water and stone turn to strokes.
    sample="app.samplesFolder + '/Map/Nature/Movie.4.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
p = menu(page, 'Style', 'Style', STYLES, 'oil',
         'Oil: flat strokes on canvas, with ink lines along the edges. Watercolor: broader washes on paper, their '
         'edges darker and their pigment pooling unevenly. Ink: two tones, ink on paper, a woodcut.')
p.startSection = True
custom(page, 'Float', 'Brush', 'Brush', 12.0,
       "The strokes' size: their radius in pixels at 720 high (it scales with the picture). Strokes stretch to twice "
       'that along clear edges. The cost stays the same at any size.', 2, 24, True)
custom(page, 'Float', 'Sharpness', 'Sharpness', 8.0,
       'How crisply neighboring strokes meet, 2-12: higher keeps regions flatter and their borders harder, lower '
       'blends them more softly.', 2, 12, True)
custom(page, 'Float', 'Stretch', 'Stretch', 1.0,
       'How far strokes stretch along the edges in the picture: at 1, up to twice Brush along a clear edge and half '
       'across it; higher, longer and thinner.', 0.25, 4, True)
custom(page, 'Int', 'Passes', 'Passes', 1,
       'Paint over the painting again, up to 3 times: each pass flattens the regions further, and costs as much as '
       'the first.', 1, 3, True)
custom(page, 'Toggle', 'Halfsize', 'Half Size', False,
       "Paint at half the picture's size, then bring it back up along the picture's edges: the painting costs about "
       'half as much, and its strokes are softer.')
custom(page, 'Float', 'Texture', 'Texture', 0.5,
       'The surface, 0-1: a canvas weave under Oil, paper grain and pigment pooling under Watercolor, paper under '
       'Ink. It stays put while the picture moves over it, as paper would.', 0, 1, True)
p = custom(page, 'Float', 'Lines', 'Lines', 0.5,
           'How dark the ink lines along the edges are, 0-1 (Oil and Watercolor).', 0, 1, True)
p.startSection = True
p.enableExpr = "me.par.Style != 'ink'"
custom(page, 'Float', 'Linewidth', 'Line Width', 1.0,
       "How wide the ink lines are, in pixels at 720 high (Ink's lines too). Wider lines also leave out finer "
       'detail.', 0.5, 3, True)
custom(page, 'Float', 'Inklevel', 'Ink Level', 0.5,
       "Ink: how much of the picture fills with ink, 0-1. At 0.5 everything darker than the picture's average "
       'brightness does.', 0, 1, True).enableExpr = "me.par.Style == 'ink'"
p = custom(page, 'Float', 'Depthbrush', 'Depth Brush', 0.5,
           'With a depth map or mask on input 3: how much finer strokes are near (or inside) and broader far (or '
           'outside), 0-1. At 1, the nearest are half Brush and the farthest twice. Nothing changes without input 3.',
           0, 1, True)
p.startSection = True
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance 0-1: the '
     'RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in '
     'Meters: the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"
p = custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
           'How broad the stroke is that sweeps across the picture on each beat of input 2, 0-1 (Oil and Watercolor): '
           'in its middle the brush is up to {:g} times its size at 1. Each beat comes from another direction. Ink '
           "doesn't sweep: a sweep would flip whole patches between ink and paper, a flash.".format(1 + KICK),
           0, 1, True)
p.startSection = True
p.enableExpr = "me.par.Style != 'ink'"
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much louder music on input 2 broadens the strokes (and quiet passages refine them), 0-1. It eases over '
       'half a second.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a build broadens the strokes as it rises, and a drop paints in broad "
       "strokes for Length seconds (Fosfora's drop detection is experimental).")
custom(page, 'Float', 'Length', 'Length', 1.0, 'How long a drop paints in broad strokes, in seconds.', 0.2, 3,
       True).enableExpr = 'me.par.Moments'

# ---- Audio (input 2): how much bigger the brush is now --------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -200, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', 0, -350, [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beat_now = mk(comp, selectCHOP, 'beat_now', 200, -300, [steps], 'A beat arriving.', channames='beat_count')
sweep = mk(comp, triggerCHOP, 'sweep', 400, -250, [beat_now],
           "Each beat's sweep: 0 to 1 over {:g} s as its band crosses the picture, then 0.".format(SWEEP),
           attack=SWEEP, peak=1, peaklen=0, decay=0, sustain=0, release=0)
beat_n = mk(comp, countCHOP, 'beat_n', 400, -350, [beat_now], 'Beats so far: which way each sweep runs.')
drop_now = mk(comp, selectCHOP, 'drop_now', 200, -450, [steps], 'A drop arriving (Fosfora, experimental).',
              channames='drop_count')
drop_env = mk(comp, triggerCHOP, 'drop_env', 400, -450, [drop_now],
              "A drop's broad strokes: up in 0.3 s, held for Length, back over 0.8 s.",
              attack=0.3, peak=1, peaklen=par('Length'), decay=0.8, sustain=0, release=0)
level_pick = mk(comp, selectCHOP, 'level_pick', 200, -150, [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', 400, -150, [level_pick],
           'Loudness eased over half a second, so the strokes swell and shrink instead of jittering.', width=0.5)
WIRED = "op('audio')['source'].eval() > 0"
SWELL = ("(2 ** ({loud} * parent().par.Loudness * (op('level_smooth')[0] - 0.5)) if {wired} else 1)"
         " * ((1 + {build} * op('audio')['build'] + {drop} * op('drop_env')[0])"
         " if parent().par.Moments else 1)").format(loud=LOUD, wired=WIRED, build=BUILD, drop=DROP)
swell = mk(comp, constantCHOP, 'swell', 600, -150, comment='How much bigger the whole brush is now: loudness, a build '
           'or a drop.', const0name='swell', const0value=Expr(SWELL))

# ---- Depth (input 3): finer near, broader far -----------------------------------------------------
flat = mk(comp, constantTOP, 'depth_none', -800, -800, comment='Halfway: with nothing on input 3 the brush keeps its '
          'size.', outputresolution='custom', resolutionw=1, resolutionh=1, colorr=0.5, colorg=0.5, colorb=0.5, alpha=1)
depth = depth_in(comp, fallback=flat)
near = glsl(comp, 'near', -400, -650, [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black: no reading).', fmt='rgba16float',
            uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')
scale = glsl(comp, 'brush_scale', -200, -650, [source, near], src('scale.glsl'),
             "How big the brush is at each pixel: finer near, broader far (Depth Brush), and the beat's sweep.",
             fmt='mono16float', uD=(par('Depthbrush'),),
             uS=(Expr("op('sweep')[0]"), Expr("op('beat_n')[0] % 4096 * 2.3999632"),
                 Expr("parent().par.Kick * {} if parent().par.Style != 'ink' else 0".format(KICK)), BAND))
setpars(scale, outputresolution='quarter')

# ---- The picture ----------------------------------------------------------------------------------
st = structure_tensor(comp, _ROOT, source, -400, 300, sigma=SMOOTH_FLOW)
flow = st['flow']
RADIUS = "parent().par.Brush * ({} if parent().par.Style == 'watercolor' else 1) * op('swell')[0]".format(WASH)
passes = []
for i in range(3):
    k = glsl(comp, 'kuwahara{}'.format(i + 1), 400 + 200 * i, 150 - 150 * i,
             [passes[-1] if passes else source, flow, scale], src('kuwahara.glsl'),
             'The painting, pass {}: each pixel the evenest sectors of an ellipse along the flow (anisotropic '
             'Kuwahara).'.format(i + 1),
             uK=(Expr(RADIUS), par('Sharpness'), Expr('1 / parent().par.Stretch'), MAX_RADIUS), uQ=(SAMPLES,))
    setpars(k, inputextenduv='hold', inputfiltertype='mipmap')
    passes.append(k)
setpars(passes[0], outputresolution=Expr("'half' if parent().par.Halfsize else 'useinput'"))
last = mk(comp, switchTOP, 'kuwahara', 1000, 0, passes, 'The last pass asked for (Passes): only its passes cook.',
          index=Expr('parent().par.Passes - 1'))
up = glsl(comp, 'upsample', 1200, 150, [source, last], src('upsample.glsl'),
          'Half Size: the painting back at full size, its strokes ending on the picture\'s edges.', uU=(UP_SIGMA, 1.0))
setpars(up, inputfiltertype='mipmap')
painted = mk(comp, switchTOP, 'painted', 1400, 0, [last, up], 'The painting at full size.',
             index=Expr('1 if parent().par.Halfsize else 0'))
dog = glsl(comp, 'dog', 1600, 150, [painted, flow], src('dog.glsl'),
           "The painting's brightness, blurred twice across the edges (Line Width).", fmt='rg16float',
           uE=(par('Linewidth'), K))
lic = glsl(comp, 'lic', 1800, 150, [dog, flow], src('lic.glsl'), 'Both blurs smoothed along the edges.',
           fmt='rg16float', uM=(LINE_SMOOTH,))
for o in (dog, lic):
    setpars(o, inputextenduv='hold')
mean = mk(comp, analyzeTOP, 'mean', 1800, 300, [source], "The picture's average color: Ink's middle level.",
          op='average')
paint = glsl(comp, 'paint', 2000, 0, [painted, lic, mean], lib_glsl(_ROOT, 'common.glsl') + src('paint.glsl'),
             'The finished picture in the chosen style: lines, canvas, wash or ink.',
             uS=(Expr('parent().par.Style.menuIndex'), par('Lines'), LINE_EDGE, LINE_SOFT),
             uI=(INK_P, par('Inklevel'), INK_SOFT, par('Texture')))

finish_effect(comp, paint, VERSION, page)
save_effect(comp, _HERE, _ROOT)
