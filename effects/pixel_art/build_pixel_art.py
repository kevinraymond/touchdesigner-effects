"""Build Pixel Art. Run from a textport: __file__ = '/path/to/build_pixel_art.py'; exec(open(__file__).read())

The picture as pixel art with a small palette it picks itself, after Gerstner, DeCarlo, Alexa, Finkelstein, Gingold and
Nealen, "Pixelated Image Abstraction" (NPAR 2012). Each art pixel is a superpixel of the picture: SLIC's clustering
(Achanta et al. 2010) on the art's grid, with each pixel's color distance taken to the palette color its superpixel
shows, Laplacian smoothing that keeps the superpixels in rows and columns, and a bilateral filter on their colors. The
palette comes from mass-constrained deterministic annealing (Rose 1998): one color, the picture's mean, splitting into
more as the palette cools, until it has Colors of them. The paper runs its loop to convergence on one image; here it
runs one iteration a frame and never stops, each frame starting from the last one's superpixels and palette, so the
art follows the video and the palette follows the picture's colors. For video (ours): each superpixel's color eased
where it changed a little, a pixel keeping its color until another is clearly nearer, a color nobody uses taking half
of the most spread-out one. Input 3 is the paper's importance map: Subject Colors spends more of the palette on near
things (or inside a mask).

dev/protos/pixel_art/offline.py tried it first on the clips beside the paper's two plain methods (board #4728).

The network, left to right:
  picture      source -> lab (the picture in Lab, with each pixel's importance) -> assign (each pixel joins one of
               the 9 superpixels around its cell; centers_fb and index_fb are last frame's centers and colors) ->
               gather (each superpixel's center and mean color) -> centers (Laplacian smoothing) and
               colors (a bilateral filter, eased over time; colors_fb) -> index (each art pixel's palette color;
               index_next) -> show -> out
  palette      colors -> assoc -> totals (per entry, over the picture) -> palette (one MCDA iteration; palette_fb)
  audio        audio_in() -> counts -> steps -> flash_gate() -> kick (the mosaic's hold); level -> level_now (over a
               second) -> level_usual (the last 4 s)
  depth        input 3 (depth_in()) -> near
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# The superpixels (Gerstner et al.'s values): m weighs place against color, LAPLACE how far a center moves toward its
# neighbors, SIGMA the bilateral filter's color sigma (Lab; the paper gives none).
M, LAPLACE, SIGMA = 45.0, 0.4, 10.0
# For video: a superpixel's color eases over EASE s where it changed under EASE_SMALL Lab and is taken at once over
# EASE_BIG; a pixel keeps its color until another is HOLD Lab nearer.
EASE, EASE_SMALL, EASE_BIG, HOLD = 0.2, 10.0, 30.0, 10.0
# The palette's annealing: the temperature falls by ALPHA to TF; it falls when the palette changes less than SETTLED
# (Lab, summed) or after AT_MOST s at one temperature (4 iterations at 60 fps); two entries further apart than APART
# (Lab) split.
# PERTURB (Lab) sets a color's two entries apart. A color holding less than UNUSED superpixels is unused; one with a
# variance under SPREAD (Lab^2) isn't split. Once the palette is whole, the art fades from its superpixels' own colors
# to the palette's over REVEAL s.
ALPHA, TF, SETTLED, AT_MOST, APART = 0.7, 1.0, 1.0, 0.06, 0.25
PERTURB, UNUSED, SPREAD, REVEAL = 0.8, 0.5, 4.0, 0.5
ENTRIES = 64         # the palette's entries: two for each of up to 32 colors while it cools
# The beat's mosaic: blocks of 1 + KICK_BLOCK x Mosaic Kick art pixels (rounded) for KICK_HOLD s. Loudness: Dither
# rises by SWELL x Swell x how far the level, over SLOW s, is above its average over USUAL s.
KICK_BLOCK, KICK_HOLD = 4, 0.15
SWELL, SLOW, USUAL = 2.5, 1.0, 4.0
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
PERF = '2'           # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def shader(name):
    return src('common.glsl') + src(name)


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


GRID = Expr('math.ceil({} / parent().par.Pixelsize)'.format(MAX_RES))   # the grid's textures, G x G
DT = Expr('min(absTime.stepSeconds, 0.1)')

README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'pixel_art', 'Pixel Art',
    'Pixel Art {}: the picture as pixel art, each art pixel a region shaped around the picture\'s features, in a small '
    'palette it picks itself and keeps following.'.format(VERSION),
    README, tags=('pixel-art', 'palette', 'superpixels', 'audio-reactive'), audio=True, depth=True, flashing=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.1.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
custom(page, 'Int', 'Pixelsize', 'Pixel Size', 8,
       "How many of the picture's pixels across one pixel of the art is, 2-32. At 8 a 1280 x 720 picture becomes art "
       '160 x 90 pixels big.', 2, 32, True).startSection = True
custom(page, 'Int', 'Colors', 'Colors', 12,
       'How many colors the palette has, 2-32. It picks them itself from the picture and keeps following it.', 2, 32,
       True)
custom(page, 'Float', 'Dither', 'Dither', 0.0,
       'Mixes two colors in a checkerboard where an art pixel sits between them, 0-1. At 0 every pixel is one color; at '
       '1 every in-between shade is dithered, as on old consoles.', 0, 1, True)
custom(page, 'Float', 'Saturation', 'Saturation', 1.1,
       "How colorful the palette is drawn, 0.5-2. 1 shows the colors as found; pixel artists push them a little (1.1, "
       "the paper's).", 0.5, 2, True)
custom(page, 'Toggle', 'Hold', 'Hold Palette', False,
       'Keeps the palette as it is now: the art still follows the picture, in these colors only.').startSection = True
custom(page, 'Pulse', 'Newpalette', 'New Palette', None,
       'Starts the palette again: it picks its colors afresh from the picture over about a second, and the art fades '
       'into them.')
custom(page, 'Float', 'Kick', 'Mosaic Kick', 0.75,
       'On each beat on input 2 the art jumps to bigger blocks for a moment, as the Super Nintendo\'s mosaic did, 0-1. '
       'At 0.75 the blocks are 4 art pixels across, at 1 five. As often as Flashing allows.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Swell', 'Swell', 0.5,
       'How much the music getting louder than usual dithers the art, 0-1, on top of Dither. It follows the loudness '
       'over a second.', 0, 1, True)
custom(page, 'Float', 'Subject', 'Subject Colors', 0.75,
       'With a depth map or mask on input 3: how much of the palette goes to near things (or inside the mask), 0-1. '
       'At 1 far things get only the colors near ones chose. Nothing changes without input 3.', 0, 1,
       True).startSection = True
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

# ---- Audio (input 2): the mosaic on each beat, the swell with the loudness ----------------------------
section('audio', 'Audio (input 2): the mosaic on each beat, dither with the loudness')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
flash = flash_gate(comp, steps)
mk(comp, triggerCHOP, 'kick', [flash], 'The mosaic: above 0 for {:g} s after a beat the gate let through.'.format(
    KICK_HOLD), attack=0, peak=1, decay=KICK_HOLD, sustain=0, release=0)
level = mk(comp, selectCHOP, 'level', [audio], 'How loud the music is now.', channames='level')
level_now = mk(comp, filterCHOP, 'level_now', [level], 'The loudness smoothed over {:g} s.'.format(SLOW), width=SLOW)
mk(comp, filterCHOP, 'level_usual', [level_now], 'The usual loudness: its average over the last {:g} s.'.format(USUAL),
   type='box', width=USUAL)
WIRED = "op('audio')['source'].eval() > 0"
MOSAIC = Expr("1 + round({} * parent().par.Kick) if op('kick')[0] > 0.001 else 1".format(KICK_BLOCK))
DITHER = Expr("min(parent().par.Dither + ({} * parent().par.Swell * max(op('level_now')[0] - op('level_usual')[0], 0) "
              "if {} else 0), 1)".format(SWELL, WIRED))

# ---- Depth (input 3): the importance map --------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): what counts most toward the palette')
flat = mk(comp, constantTOP, 'depth_none', comment='Near everywhere: with nothing on input 3 every pixel counts the same.',
          outputresolution='custom', resolutionw=1, resolutionh=1, colorr=1, colorg=1, colorb=1, alpha=1)
depth = depth_in(comp, fallback=flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black is no reading).',
            fmt='rgba16float', uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')

# ---- The superpixels ----------------------------------------------------------------------------------
section('superpixels', "The superpixels: one per art pixel, shaped by SLIC around the palette's colors, kept in rows "
        'and columns')
empty = mk(comp, constantTOP, 'empty', comment='Nothing yet: what every Feedback TOP starts from.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float', colorr=0, colorg=0, colorb=0,
           alpha=0)
centers_fb = mk(comp, feedbackTOP, 'centers_fb', [empty], "centers' last frame: the superpixels' centers.",
                top='centers')
index_fb = mk(comp, feedbackTOP, 'index_fb', [empty], "index's last frame: each art pixel's palette color.",
              top='index')
colors_fb = mk(comp, feedbackTOP, 'colors_fb', [empty], "colors' last frame: the superpixels' eased colors.",
               top='colors')
lab = glsl(comp, 'lab', [source, near], shader('lab.glsl'),
           "The picture in L*a*b*, with each pixel's importance for the palette (Subject Colors).", fmt='rgba16float',
           uImp=(Expr('parent().par.Subject if parent().inputConnectors[2].connections else 0'),))
assign = glsl(comp, 'assign', [lab, centers_fb, index_fb], shader('assign.glsl'),
              'Each pixel joins the nearest of the 9 superpixels around its cell, in color (to their palette colors) '
              'and place.', fmt='rgba8fixed', uGrid=(par('Pixelsize'), GRID, M))
gather = mk(comp, glslTOP, 'gather', [assign, lab, centers_fb],
            "Each superpixel's new center (and S) and the mean color of the pixels that joined it, side by side. A "
            'compute shader, one workgroup a superpixel.', mode='compute', autodispatchsize=False, dispatchsizex=GRID,
            dispatchsizey=GRID, dispatchsizez=1, outputresolution='custom', resolutionw=Expr('2 * ' + GRID.text),
            resolutionh=GRID, format='rgba32float')
docked(gather, '_compute', shader('gather.glsl'), "The superpixels' update, a compute shader: one workgroup each, "
       'its 64 invocations sharing the window.')
uniforms(gather, uGrid=(par('Pixelsize'), GRID))
centers = glsl(comp, 'centers', [gather], shader('centers.glsl'),
               "The superpixels' centers, each moved toward its neighbors' (Laplacian smoothing).", res=(GRID, GRID),
               fmt='rgba32float', uGrid=(par('Pixelsize'), GRID, LAPLACE, SIGMA))
colors = glsl(comp, 'colors', [gather, colors_fb], shader('colors.glsl'),
              "The superpixels' colors through a bilateral filter, eased over time where they changed a little.",
              res=(GRID, GRID), fmt='rgba32float', uGrid=(par('Pixelsize'), GRID, LAPLACE, SIGMA),
              uEase=(DT, EASE, EASE_SMALL, EASE_BIG))

# ---- The palette ----------------------------------------------------------------------------------------
section('palette', 'The palette: one iteration of deterministic annealing a frame, splitting as it cools, then '
        'following the picture', lane='palette')
palette_fb = mk(comp, feedbackTOP, 'palette_fb', [empty], "palette's last frame.", top='palette')
assoc = glsl(comp, 'assoc', [colors, palette_fb], shader('assoc.glsl'),
             'How strongly each superpixel belongs to each palette entry (its largest exponent and the sum).',
             res=(GRID, GRID), fmt='rgba32float')
totals = mk(comp, glslTOP, 'totals', [colors, assoc, palette_fb],
            "Each entry's share of the picture and its superpixels' mean color and spread. A compute shader, one "
            'workgroup an entry.', mode='compute', autodispatchsize=False, dispatchsizex=ENTRIES, dispatchsizey=1,
            dispatchsizez=1, outputresolution='custom', resolutionw=3 * ENTRIES, resolutionh=1, format='rgba32float')
docked(totals, '_compute', shader('totals.glsl'), "The palette's sums, a compute shader: one workgroup an entry, its "
       '256 invocations sharing the superpixels.')
palette = glsl(comp, 'palette', [totals, palette_fb], shader('palette.glsl'),
               'The palette: its entries, its colors as shown, its state (temperature, phase, colors) and its colors.',
               res=(ENTRIES, 4), fmt='rgba32float',
               uP=(par('Colors'), par('Hold'), TF, DT), uQ=(ALPHA, AT_MOST, SETTLED, APART),
               uR=(PERTURB, UNUSED, SPREAD, REVEAL), uS=(par('Saturation'),))

# ---- The art -----------------------------------------------------------------------------------------
section('art', "The art: each art pixel's palette color, drawn at the picture's size")
index = glsl(comp, 'index', [colors, palette, index_fb], shader('index.glsl'),
             "Each art pixel's palette color, kept until another is clearly nearer; buffer 1 the next nearest.",
             res=(GRID, GRID), fmt='rgba32float', uH=(HOLD, GRID))
setpars(index, numcolorbufs=2)
index_next = mk(comp, renderselectTOP, 'index_next', comment="index's buffer 1: the next nearest color, for Dither.",
                top='index', bufferindex=1)
show = glsl(comp, 'show', [source, index, index_next], shader('show.glsl'),
            'The art at the picture\'s size: each art pixel a square, dithered, saturated, in mosaic blocks on a beat.',
            uS=(par('Pixelsize'), GRID, DITHER), uM=(MOSAIC,))

section('palette')
reset = mk(comp, parameterexecuteDAT, 'reset', comment='New Palette: the palette starts again from one color.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Newpalette':\n"
              "        op('palette_fb').par.resetpulse.pulse()\n")
setpars(reset, op='..', pars='Newpalette', onpulse=True, valuechange=False)

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
