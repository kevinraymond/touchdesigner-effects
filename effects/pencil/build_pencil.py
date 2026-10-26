"""Build Pencil. Run from a textport: __file__ = '/path/to/build_pencil.py'; exec(open(__file__).read())

The live picture as a pencil drawing, from the papers. Lu, Xu and Jia ("Combining Sketch and Tone for Pencil Drawing
Production", NPAR 2012) draw a picture as two layers multiplied: lines along its edges, found by classifying the
gradient into eight directions of short line segments and spreading each class back along its own segment, so strokes
run on past corners and cross as a quick hand's do; and the picture's tone, first matched to the tones of real pencil
drawings (mostly paper, a band of mild strokes, a few dark accents), then drawn with a pencil pattern laid over
itself as often as the tone asks. Hatching draws that tone with tonal art maps instead (Praun et al., "Real-Time
Hatching", SIGGRAPH 2001), turned along the picture's edges by lib structure_tensor(), shared with Paint and
Reaction-Diffusion.

The pencil strokes are a texture strokes.glsl draws once (six nested levels of hatching and Sketch's tonal pattern,
repeating every TEX[0] pixels), so the
drawing costs the same whatever it draws. The lines cost most: classify and shape each read 8 segments of
2 TAPS + 1 samples a pixel. With Follow Movement the strokes travel with the picture's motion (lib optical_flow() and
flow_speed()), which costs about a quarter of the frame; at 0 none of it cooks.

The network, left to right:
  picture  source -> edges (G, eased; edges_fb) -> classify (each pixel's direction) -> shape (S'); draw (S', the tone,
           the strokes, the edges' direction, nearness, the strokes' offsets)
  tone     histogram (capped) -> tone (the tone table, eased; tone_fb); strokes (once) -> strokes_dark (levels 4-6);
           small -> structure_tensor() (tensor, tensor_h, tensor_v, tensor_fb, tensor_ease -> flow) -> orient
           (Hatching only)
  motion   optical_flow() (lum8, lum4, change, clock, lk8, lk4) -> flow_speed() (pace, motion) -> drift (two offsets;
           drift_fb) -> drifted (only while Follow Movement is above 0)
  audio    audio_in() -> counts -> steps -> beat_now -> beat_n (each beat's redraw); drop_now -> drop_env (a drop's
           long strokes); level_pick -> level_smooth (pressure)
  depth    input 3 (depth_in()) -> near
"""
import math
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
STYLES = (('sketch', 'Sketch'), ('hatching', 'Hatching'), ('lines', 'Lines'))
COLORS = (('graphite', 'Graphite'), ('colored', 'Colored Pencil'), ('blue', 'Blue Pencil'),
          ('light', 'Light on Dark'))
LINE = 1 / 30        # a line segment's length, a share of the picture's height (the paper's 1/30)
TAPS = 5             # samples each side of the pixel along a segment, whatever its length
LINE_GAIN = 24.0     # Lines 1: S' of 1/24 (a strong edge's gradient, spread along its segment) draws black
LINE_EASE = 0.2      # the gradient eases over 0.2 s: followed at once, a video's noise flickered the lines (a flash)
# The tone layers' weights, dark : mild : bright, at Shading 0, 0.5 and 1: the paper's Figure 11 (c), its Table 1, and
# its Figure 11 (b).
SHADES = ((2, 22, 76), (11, 37, 52), (29, 29, 42))
# The tone table eases over 1 s; the histogram spreads each sample over 4 levels and caps each level at 3 times an even
# share: uncapped, a picture crowded into a narrow band (the koi's dark pond) was stretched over every tone, its flicker
# with it (the koi's worst cell flashed 4 times a second, capped 3).
TONE_EASE, TONE_SOFT, TONE_CAP = 1.0, 4.0, 3.0
# The strokes, in pixels at 720 high. Hatching's: the repeat, a stroke's cell along its row, the rows' spacing, the half
# width; then the most a stroke turns (radians), its bow and its lightest and heaviest pressure. Long, straight, evenly
# spaced strokes, so it reads as hatching. Sketch's: short, light strokes turned every way (cell, spacing, half width,
# turn; bow and pressure), so it reads as graphite shading with no lines to follow.
TEX = (512.0, 48.0, 2.8, 0.75)
TEX_Q = (0.02, 0.6, 0.55, 0.85)
SKETCH_TEX = (28.0, 2.3, 0.6, 0.3)
SKETCH_Q = (1.4, 0.4, 0.75, 0.0)
HATCH = math.radians(60)              # the hatch where the edges have no clear direction: lower left to upper right
TENSOR_SIGMA, TENSOR_EASE = 6.0, 0.5   # the edges' direction: smoothed over 6 pixels at 720 high, eased over 0.5 s
DRIFT = 1.0          # each offset that carries the strokes along starts again every second (divides lib CLOCK)
# The music. Each beat redraws the drawing: the segments turn by up to TURN (radians) at Beat Kick 1, and the pencil
# strokes move by up to JUMP pixels. Loudness 1 presses the lines up to LOUD harder when loud (lighter when quiet) and
# raises the tone to a power up to TONE_LOUD from 1; a build lengthens the lines by up to BUILD, a drop by DROP for
# Length s (Song Moments).
TURN, JUMP, LOUD, TONE_LOUD, BUILD, DROP = math.pi / 16, 24.0, 0.5, 0.3, 0.5, 1.0
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


def shade(i):
    """Layer i's weight (0 dark, 1 mild, 2 bright) at the Shading set: SHADES' rows, straight between."""
    a, b, c = (s[i] / 100 for s in SHADES)
    return Expr('{a} + ({b} - {a}) * 2 * min(parent().par.Shading, 0.5) + ({c} - {b}) * 2 * max(parent().par.Shading '
                '- 0.5, 0)'.format(a=a, b=b, c=c))


README = src('readme.txt').format(v=VERSION)
comp, page, source = new_effect(
    'pencil', 'Pencil',
    'Pencil {}: the live picture as a pencil drawing, sketchy lines along its edges and its tones in pencil strokes, '
    'from the papers.'.format(VERSION),
    README, tags=('pencil', 'sketch', 'hatching', 'drawing', 'npr', 'audio-reactive'), audio=True, depth=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.4.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Style', 'Style', STYLES, 'sketch',
     'Sketch: lines along the edges, and the tones in soft graphite shading, short strokes laid every way, as Lu, Xu '
     'and Jia draw them. Hatching: the tones in long parallel strokes that follow the edges, crossing only in the '
     'darks. Lines: the lines alone.').startSection = True
menu(page, 'Colors', 'Colors', COLORS, 'graphite',
     "Graphite on white paper, Colored Pencil (the picture's own colors), Blue Pencil (an animator's blue), or Light "
     'on Dark: white pencil on black paper, drawing where the picture is light.')
custom(page, 'Float', 'Lines', 'Lines', 0.5,
       'How dark the lines along the edges are, 0-1. At 1, every strong edge is drawn black.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Linelength', 'Line Length', 1.0,
       "How far the lines run past their edges, 0.5-2: at 1 a stroke is 1/30 of the picture's height, so strokes "
       'cross at corners as a quick hand draws them; longer looks looser.', 0.5, 2, True)
p = custom(page, 'Float', 'Shading', 'Shading', 0.5,
           "How dark the drawing's tones are, 0-1: 0 mostly paper, 0.5 as the paper's pencil drawings, 1 darker, "
           'with more dark accents. The tones follow the picture over a second.', 0, 1, True)
p.startSection = True
p.enableExpr = "me.par.Style != 'lines'"
custom(page, 'Float', 'Strokesize', 'Stroke Size', 1.0,
       "How big the pencil strokes are, 0.5-2: at 1 a hatching stroke is 45 to 75 pixels long and Sketch's 25 to 45, "
       'at 720 high.', 0.5, 2,
       True).enableExpr = "me.par.Style != 'lines'"
custom(page, 'Float', 'Follow', 'Follow Movement', 1.0,
       'How much the pencil strokes travel with what moves in the picture, 0-1. At 0 they stay on the paper while '
       'the picture moves under them.', 0, 1, True).enableExpr = "me.par.Style != 'lines'"
custom(page, 'Float', 'Texture', 'Texture', 0.5,
       "How much the paper's grain shows in the graphite, 0-1. It stays put while the picture moves, as paper "
       'would.', 0, 1, True)
p = custom(page, 'Float', 'Depthfade', 'Depth Fade', 0.5,
           'With a depth map or mask on input 3: how much lighter far things (or what lies outside the mask) are '
           'drawn, 0-1. At 1 the farthest are left as paper. Nothing changes without input 3.', 0, 1, True)
p.startSection = True
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"
custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'How much each beat of input 2 redraws the drawing, 0-1: the lines turn a little and the pencil strokes move, '
       'as the next drawing of a hand-drawn animation would.', 0, 1, True).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much harder the pencil presses when music on input 2 is loud (and lighter when quiet), 0-1. It eases '
       'over half a second.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a build draws longer, looser lines as it rises, and a drop draws them "
       "twice as long for Length seconds (Fosfora's drop detection is experimental).")
custom(page, 'Float', 'Length', 'Length', 1.0, 'How long a drop draws long lines, in seconds.', 0.2, 3,
       True).enableExpr = 'me.par.Moments'

# ---- Audio (input 2): redraws on the beats, pressure from the loudness ----------------------------
section('audio', 'Audio (input 2): a redraw on each beat, the pencil pressed harder when loud')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beat_now = mk(comp, selectCHOP, 'beat_now', [steps], 'A beat arriving.', channames='beat_count')
beat_n = mk(comp, countCHOP, 'beat_n', [beat_now], 'Beats so far: each one redraws the drawing.')
drop_now = mk(comp, selectCHOP, 'drop_now', [steps], 'A drop arriving (Fosfora, experimental).',
              channames='drop_count')
drop_env = mk(comp, triggerCHOP, 'drop_env', [drop_now],
              "A drop's long lines: up in 0.3 s, held for Length, back over 0.8 s.",
              attack=0.3, peak=1, peaklen=par('Length'), decay=0.8, sustain=0, release=0)
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick],
           'Loudness eased over half a second, so the pressure swells and falls instead of jittering.', width=0.5)
WIRED = "op('audio')['source'].eval() > 0"
PRESS = "(parent().par.Loudness * 2 * (op('level_smooth')[0] - 0.5) if {} else 0)".format(WIRED)
REDRAW = "op('beat_n')[0] % 4096"
LENGTH = ("parent().par.Linelength * {half} * (1 + ({build} * op('audio')['build'] + {drop} * op('drop_env')[0] "
          "if parent().par.Moments else 0))").format(half=LINE / 2, build=BUILD, drop=DROP)
TURNED = "parent().par.Kick * {} * (({} * 0.6180339887 % 1) * 2 - 1)".format(TURN, REDRAW)

# ---- Depth (input 3): far things drawn lighter -----------------------------------------------------
section('depth', 'Depth or a mask (input 3): far things drawn lighter')
flat = mk(comp, constantTOP, 'depth_none', comment='Near everywhere: with nothing on input 3 nothing fades.',
          outputresolution='custom', resolutionw=1, resolutionh=1, colorr=1, colorg=1, colorb=1, alpha=1)
depth = depth_in(comp, fallback=flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black is no reading).', fmt='rgba16float',
            uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')

# ---- The lines -------------------------------------------------------------------------------------
section('lines', 'Lines: strokes along the edges, classified into eight directions and spread along them')
start = mk(comp, constantTOP, 'unset', comment='Nothing, not yet set (alpha 0): where the gradient starts.',
           outputresolution='custom', resolutionw=1, resolutionh=1, colorr=0, colorg=0, colorb=0, alpha=0)
edges_fb = mk(comp, feedbackTOP, 'edges_fb', [start], "edges' last frame.", top='edges')
edges = glsl(comp, 'edges', [source, edges_fb], src('edges.glsl'),
             "The picture's gradient, G, eased over {:g} s so a video's noise doesn't flicker the lines.".format(LINE_EASE),
             fmt='rg16float', uE=(Expr('min(absTime.stepSeconds, 0.1)'), LINE_EASE))
classify = glsl(comp, 'classify', [edges], src('classify.glsl'),
                'Each pixel joins the direction whose line segment gathers the most gradient around it.', fmt='rg16float',
                uC=(Expr(LENGTH), Expr(TURNED), TAPS))
shape = glsl(comp, 'shape', [classify], src('shape.glsl'),
             "Each direction's pixels spread back along its segment: the strokes.", fmt='r16float',
             uC=(Expr(LENGTH), Expr(TURNED), TAPS))

# ---- The tone and the pencil strokes -----------------------------------------------------------------
section('tone', "Tone: the picture's tones matched to a pencil drawing's", lane='tone')
none = mk(comp, constantTOP, 'none', comment='Nothing, not yet set (alpha 0): where the tone starts, and the '
          "edges' direction while Hatching isn't drawn.", outputresolution='custom', resolutionw=1, resolutionh=1,
          colorr=0, colorg=0, colorb=0, alpha=0)
tone_fb = mk(comp, feedbackTOP, 'tone_fb', [none], "tone's last frame.", top='tone')
hist = glsl(comp, 'histogram', [source], src('histogram.glsl'),
            "The picture's histogram, 256 levels, each capped at {:g} times an even share.".format(TONE_CAP),
            res=(256, 1), fmt='rgba32float',
            uH=(TONE_SOFT, TONE_CAP, Expr("1 if parent().par.Colors == 'light' else 0")))
setpars(hist, inputfiltertype='mipmap')
tone = glsl(comp, 'tone', [hist, tone_fb], src('tone.glsl'),
            "A table of 256 levels: each of the picture's levels as the tone a pencil drawing gives it (Shading), eased.",
            res=(256, 1), fmt='rgba32float', uW=(shade(0), shade(1), shade(2)),
            uE=(Expr('min(absTime.stepSeconds, 0.1)'), TONE_EASE))
section('strokes', "The pencil strokes, drawn once: hatching's six levels and Sketch's pattern", lane='tone')
strokes = glsl(comp, 'strokes', [], src('strokes.glsl'),
               "The pencil strokes, drawn once: hatching's levels 1-3 and Sketch's pattern (buffer 0), levels 4-6 (buffer "
               '1), repeating every {:g} pixels.'.format(TEX[0]), res=(int(TEX[0]), int(TEX[0])), fmt='rgba16float',
               uP=TEX, uQ=TEX_Q, uS=SKETCH_TEX, uT=SKETCH_Q)
setpars(strokes, numcolorbufs=2)
strokes_dark = mk(comp, renderselectTOP, 'strokes_dark', comment="Hatching's levels 4-6 (buffer 1).",
                  top='strokes', bufferindex=1)
section('edges', "Hatching's direction: which way the picture's edges run (structure tensor)", lane='tone')
small = mk(comp, resolutionTOP, 'small', [source], "The picture at half size: the edges' direction is smooth, "
           'and the tensor costs a quarter.', outputresolution='half')
st = structure_tensor(comp, _ROOT, small, sigma=TENSOR_SIGMA, ease=TENSOR_EASE)
orient = mk(comp, switchTOP, 'orient', [none, st['flow']],
            "The edges' direction for Hatching; nothing otherwise, so the tensor doesn't cook.",
            index=Expr("1 if parent().par.Style == 'hatching' else 0"))

# ---- The strokes travel with what moves ----------------------------------------------------------------
section('motion', 'Motion: the pencil strokes travel with what moves (optical flow)', lane='motion')
still = mk(comp, constantTOP, 'still', comment='Nothing, and still: where the motion starts.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
mo = optical_flow(comp, _ROOT, source)
# A small dead zone (cells per frame): a slow pan or a turning head should carry the strokes too, and drift.glsl
# averages the flow's noise away over blocks.
pace, motion = flow_speed(comp, _ROOT, mo, still, dead=0.03)
drift_fb = mk(comp, feedbackTOP, 'drift_fb', [still], "drift's last frame.", top='drift')
AGE = '(absTime.seconds % {}) / {}'.format(CLOCK, DRIFT)
drift = glsl(comp, 'drift', [motion, drift_fb], src('drift.glsl'),
             'How far the strokes have moved with the picture: two offsets, each starting again every {:g} s.'.format(
                 DRIFT), fmt='rgba32float',
             uD=(Expr('min(absTime.stepSeconds, 0.1)'), Expr('{} % 1'.format(AGE)), par('Follow'), DRIFT))
setpars(drift, inputfiltertype='mipmap')
drifted = mk(comp, switchTOP, 'drifted', [still, drift],
             "The strokes' offsets when they follow movement; nothing otherwise, so the optical flow doesn't cook.",
             index=Expr("1 if parent().par.Follow > 0 and parent().par.Style != 'lines' else 0"))

# ---- The drawing -------------------------------------------------------------------------------------
section('drawing', 'The drawing: the lines times the tone in pencil strokes, on paper')
# The strokes are wired (inputs 1 and 2): a GLSL TOP mipmaps only its wired inputs, not those its TOPs parameter adds.
draw = glsl(comp, 'draw', [source, strokes, strokes_dark, shape, tone, orient, near, drifted],
            lib_glsl(_ROOT, 'common.glsl') + lib_glsl(_ROOT, 'paper.glsl') + src('draw.glsl'),
            'The drawing: the lines times the tone drawn in pencil strokes (Sketch or Hatching), on paper, in the '
            'colors chosen.',
            uS=(Expr('parent().par.Style.menuIndex'), Expr('parent().par.Colors.menuIndex'), par('Texture'),
                par('Strokesize')),
            uL=(Expr('parent().par.Lines * {} * (1 + {} * {})'.format(LINE_GAIN, LOUD, PRESS)),
                Expr('1 + {} * {}'.format(TONE_LOUD, PRESS)),
                Expr('parent().par.Depthfade if parent().inputConnectors[2].connections else 0')),
            uR=(Expr('parent().par.Kick * {} * ({} * 0.7548776662 % 1 * 2 - 1)'.format(JUMP, REDRAW)),
                Expr('parent().par.Kick * {} * ({} * 0.5698402910 % 1 * 2 - 1)'.format(JUMP, REDRAW)),
                HATCH, TEX[0]),
            uM=(Expr('{} % 1'.format(AGE)), Expr("1 if parent().par.Follow > 0 and parent().par.Style != 'lines' else 0")))
setpars(draw, inputextenduv='repeat', inputfiltertype='mipmap')

finish_effect(comp, draw, VERSION, page)
save_effect(comp, _HERE, _ROOT)
