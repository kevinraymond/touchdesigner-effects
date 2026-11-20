"""Build Ferrofluid. Run from a textport: __file__ = '/path/to/build_ferrofluid.py'; exec(open(__file__).read())

A black glossy liquid over the live picture that bristles into spikes where the picture is bright or what stands out
in front is, on the bass, as a magnetic fluid bristles over a magnet: the Rosensweig instability (M. D. Cowley and
R. E. Rosensweig, J. Fluid Mech. 1967), its hexagons as measured (A. Gollwitzer, I. Rehberg and R. Richter,
2006), grown by the Swift-Hohenberg equation (J. Swift and P. C. Hohenberg, 1977) on a grid a quarter of the picture's
size. The spikes are drawn as cones in a view that leans a little, so their tips stand above their bases, the liquid a
mirror that reflects the picture and a soft light above it; where it lies flat the picture shows through.

dev/protos/ferrofluid/offline.py tried it first on the clips (board #4849): the equation's steepest ripples limit the
step, so the spikes are six cells apart and stepped 20 times a frame; a drive past about 0.3 turns the hexagons into
ridges, a strong quadratic term spreads them over the whole frame; raw nearness bristled the whole floor, so what
stands out in front drives it; seen straight on the cones read as beads, so the view leans. The height field is never
carried along by any velocity (patents: private notes; README CREDITS, Not used).

The network, left to right:
  picture  source -> drive (the field at the grid: what is bright, what stands out, the magnet, the bass) -> seed (+
           height_fb: the height last frame, a trace of noise) -> field (Swift-Hohenberg steps) -> shape (each spike's
           peak) -> surface (cones at the picture's size) -> look (the liquid over the picture)
  audio    audio_in() -> counts -> steps -> beats -> ask -> flash_limit -> flash -> beat_env; bar_steps -> bar_gap ->
           bars -> magnet_lag (the magnet's path); bass_pick -> bass_lag (quick up, slower down)
  depth    input 3 (depth_in()) -> near (nearness at a quarter size) -> find (what stands out, or the mask)
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
STYLES = (('black', 'Black'), ('tinted', 'Tinted'))
SIZES = (('small', 'Small'), ('medium', 'Medium'), ('large', 'Large'))
SIZE_RES = ('half', 'quarter', 'eighth')
CELL = (2, 4, 8)              # a grid cell is this many of the picture's pixels, by Spike Size
INPUT3 = (('depth', 'Depth Map'), ('mask', 'Mask'))
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
# The height field (dev/protos/ferrofluid, dev/out/ferrofluid/regimes.png): the spikes WAVE cells apart, DT model time a
# step (stable to 0.13 at six cells), RATE steps a second (20 a frame at 60 fps, at most MAX_STEPS a frame), G the
# quadratic term (hexagons; 2 spread them over the whole frame, 3 blew up). R_LO is r where nothing drives it (flat),
# R_HI where fully driven at Strength 1 (hexagons; Strength 2 reaches ridges); NOISE the trace of noise a frame.
WAVE, DT, RATE, MAX_STEPS, G = 6.0, 0.1, 1200.0, 40, 1.0
R_LO, R_HI, NOISE = -0.3, 0.25, 0.01
SOFT = 3.0                    # the field is spread over about this many cells
# A spike at Height 1 stands HEIGHT[1] cells tall, at 0 HEIGHT[0] (a share of their spacing sets how steep it is).
HEIGHT = (4.0, 16.0)
# The bass: at Bass 1 the field is the bass's share of Strength (silence lays the liquid flat), eased up over BASS_UP s
# and down over BASS_DOWN s (a real spike takes a moment to rise, and falls back a little slower).
BASS_UP, BASS_DOWN = 0.05, 0.3
# A beat lifts r by BEAT_LIFT where driven at Beat Pulse 1, falling over BEAT_TIME s.
BEAT_LIFT, BEAT_TIME = 0.4, 0.3
# The magnet: a soft disc MAGNET_R frame heights across, wandering on a path; each bar moves it one place along (at
# most once every BAR_GAP s, eased over BAR_EASE s); unwired it drifts a place every DRIFT s.
MAGNET_R, BAR_GAP, BAR_EASE, DRIFT = 0.3, 2.0, 1.5, 8.0
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right, nearer
# than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale), as in Fluid and Frost.
STAND_OUT, FAR = 0.1, (0.5, 0.05)
WIRED = "op('audio')['source'].eval() > 0"


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu_index(name):
    return Expr('parent().par.{}.menuIndex'.format(name))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


README = src('readme.txt').format(v=VERSION)
comp, page, source = new_effect(
    'ferrofluid', 'Ferrofluid',
    'Ferrofluid {}: a black glossy liquid over the live picture that bristles into spikes where it is bright or near, '
    'on the bass, from the papers.'.format(VERSION),
    README, tags=('ferrofluid', 'magnetic', 'liquid', 'pattern', 'audio-reactive'),
    audio=True, depth=True, flashing=True, sample=SAMPLE_MOVIE)

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Style', 'Style', STYLES, 'black',
     'Black: the liquid is black, as a magnetic fluid is, a mirror that reflects the picture, which shows through '
     'it where it lies flat (Picture). Tinted: the liquid is the picture itself, its colors on the spikes.'
     ).startSection = True
menu(page, 'Spikesize', 'Spike Size', SIZES, 'medium',
     "How far apart the spikes are, Small, Medium or Large, each twice the last (about 14, 28 and 56 pixels on a "
     "1280-wide picture). The spikes grow on a grid half, a quarter or an eighth of the picture's size, so Small "
     'costs about one and a half times Medium.')
custom(page, 'Float', 'Height', 'Height', 0.5, 'How tall the spikes stand for their spacing, 0-1.', 0, 1, True)
custom(page, 'Float', 'Tilt', 'Tilt', 0.6,
       'How far the view leans, so each spike shows its side and hides what is behind it, 0-1. At 0 the liquid is '
       'seen straight on.', 0, 1, True)
custom(page, 'Float', 'Picture', 'Picture', 0.5,
       'Black: how much of the picture shows through the liquid where it lies flat, 0-1. At 0 a black pool.', 0, 1,
       True).enableExpr = "me.par.Style == 'black'"

custom(page, 'Float', 'Strength', 'Strength', 1.0,
       'How strong the field is, 0-2. Below about 0.3 the liquid lies flat; past 1 the spikes join into ridges.',
       0, 2, True).startSection = True
custom(page, 'Float', 'Bylight', 'By Brightness', 1.0, 'How much the bright parts of the picture draw the spikes up, 0-1.',
       0, 1, True)
custom(page, 'Float', 'Bynear', 'By Nearness', 1.0,
       'How much what stands out in front in the depth map on input 3 (or what is inside the mask) draws the spikes '
       'up, 0-1.', 0, 1, True)
custom(page, 'Float', 'Magnet', 'Magnet', 0.3,
       'How strong a magnet under the liquid is: it draws spikes up wherever it is, and wanders, a step each bar of '
       'input 2, 0-1.', 0, 1, True)
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Lay the liquid flat; the spikes grow back.')
menu(page, 'Input3', 'Input 3 Holds', INPUT3, 'depth',
     'Depth Map: what stands in front of its surroundings draws the spikes up (floors and walls drop out). Mask: what '
     'is inside the mask (white inside) does.').startSection = True
custom(page, 'Float', 'Sense', 'Sensitivity', 0.5,
       'How easily something in the depth map counts as standing out (farther counts as well), or how gray a mask '
       'counts as inside.', 0, 1, True)
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

custom(page, 'Float', 'Bass', 'Bass', 0.6,
       "How much the bass of input 2 sets the field's strength, 0-1: at 1 silence lays the liquid flat and every bass "
       'note raises the spikes.', 0, 1, True).startSection = True
custom(page, 'Float', 'Beatpulse', 'Beat Pulse', 0.5,
       'On the beats of input 2 the spikes jump up at once. It changes a wide area at once, so it is a flash: Calm '
       'allows one a second, Up to 3 per second every beat up to 180 BPM, Off none. 0 turns it off.', 0, 1, True)

# ---- Audio (input 2) ------------------------------------------------------------------------------
section('audio', 'Audio (input 2): the bass sets the field, beats pulse it, bars move the magnet')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beats = mk(comp, selectCHOP, 'beats', [steps], 'Beats.', channames='beat_count')
ask = mk(comp, renameCHOP, 'ask', [beats], 'Beats, asking to pulse.', renamefrom='beat_count', renameto='pulse')
flash = flash_gate(comp, ask)
mk(comp, triggerCHOP, 'beat_env', [flash], "A beat's pulse: 1 at the beat, none {:g} s later.".format(BEAT_TIME),
   attack=0, peak=1, peaklen=0, decay=BEAT_TIME, dshape='linear', sustain=0, release=0)
# The bars counted from when the effect started: audio_in()'s bar_count is the song's, and wiring a signal in mid-song
# would send the magnet through every bar so far.
bar_steps = mk(comp, selectCHOP, 'bar_steps', [steps], 'Bars.', channames='bar_count')
bar_gap = mk(comp, triggerCHOP, 'bar_gap', [bar_steps], 'Bars at least {:g} s apart.'.format(BAR_GAP),
             retrigger=BAR_GAP, retriggerunit='seconds', attack=0, peak=1, decay=0, sustain=0)
bars = mk(comp, countCHOP, 'bars', [bar_gap], "The magnet's steps since the effect started, one a bar at most.")
mk(comp, lagCHOP, 'magnet_lag', [bars], "The magnet's steps, eased over {:g} s.".format(BAR_EASE),
   lag1=BAR_EASE, lag2=BAR_EASE, lagunit='seconds')
bass_pick = mk(comp, selectCHOP, 'bass_pick', [audio], 'How much bass there is now.', channames='bass')
mk(comp, lagCHOP, 'bass_lag', [bass_pick], 'The bass, eased up over {:g} s and down over {:g} s.'.format(
    BASS_UP, BASS_DOWN), lag1=BASS_UP, lag2=BASS_DOWN, lagunit='seconds')
STRONG = ("parent().par.Strength * (1 - parent().par.Bass + parent().par.Bass * op('bass_lag')[0] if {} else 1)"
          .format(WIRED))
LIFT = "({} * parent().par.Beatpulse * op('beat_env')[0] if {} else 0)".format(BEAT_LIFT, WIRED)
# The magnet's place on its path: m steps along it (the bars, or the clock unwired), each a turn of the golden angle.
STEP = "(op('magnet_lag')[0] if {} else absTime.seconds / {})".format(WIRED, DRIFT)
MAG_X = 'math.sin(2.39996 * {} + 0.7)'.format(STEP)
MAG_Y = 'math.cos(1.7 * {})'.format(STEP)

# ---- Depth (input 3) ------------------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): what stands out draws the spikes up')
depth = depth_in(comp)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness. Depth Type flips distance (black is no reading).',
            fmt='rgba16float', uNear=(menu_index('Depthtype'), par('Maxdist')))
setpars(near, outputresolution='quarter')
find = glsl(comp, 'find', [near], lib_glsl(_ROOT, 'depth_find.glsl'),
            'What stands in front of what lies left and right of it (Depth Map), or inside the mask (Mask), nearer '
            'than a limit (Sensitivity).', fmt='rgba16float',
            uFind=(Expr("1 if parent().par.Input3 == 'mask' else 0"), STAND_OUT,
                   Expr("{0} * ({1} / {0}) ** parent().par.Sense if parent().par.Input3 == 'depth' else "
                        "0.95 - 0.9 * parent().par.Sense".format(FAR[0], FAR[1]))))

# ---- The field ------------------------------------------------------------------------------------
section('field', "The field: where it is strong enough for spikes, at the spikes' grid (Spike Size)")
WIRED3 = 'parent().inputConnectors[2].connections'
SIZEI = 'parent().par.Spikesize.menuIndex'
drive = glsl(comp, 'drive', [source, find], src('drive.glsl'),
             'The field the liquid feels, as the growth rate of its spikes: strong where the picture is bright, what '
             'stands out in front and the magnet are, as strong as Strength and the bass say.', fmt='rgba16float',
             uD=(par('Bylight'), Expr('parent().par.Bynear if {} else 0'.format(WIRED3)), par('Magnet'),
                 Expr('math.log2({} * {}[{}])'.format(SOFT, list(CELL), SIZEI))),
             uM=(Expr('0.5 + 0.3 * {}'.format(MAG_X)), Expr('0.5 + 0.3 * {}'.format(MAG_Y)), MAGNET_R),
             uR=(R_LO, R_HI, Expr(STRONG), Expr(LIFT)))
setpars(drive, inputfiltertype='mipmap', outputresolution=Expr('{}[{}]'.format(list(SIZE_RES), SIZEI)))

# ---- The surface ----------------------------------------------------------------------------------
section('surface', "The surface: the spikes grown by the Swift-Hohenberg equation, and shaped into cones")
clear = mk(comp, constantTOP, 'clear', comment='Nothing yet (alpha 0): where the height starts, and Reset.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
height_fb = mk(comp, feedbackTOP, 'height_fb', [clear], 'The height last frame.', top='field')
seed = glsl(comp, 'seed', [drive, height_fb], lib_glsl(_ROOT, 'common.glsl') + src('seed.glsl'),
            "The height last frame, and a trace of noise the spikes grow from.", fmt='rgba32float',
            uN=(NOISE, clock_seconds()))
STEPS = 'max(1, min({}, round({} * min(absTime.stepSeconds, 0.1))))'.format(MAX_STEPS, RATE)
field = glsl(comp, 'field', [seed, drive], src('field.glsl'),
             'The height: steps of the Swift-Hohenberg equation, {:g} a second, spikes {:g} cells apart rising where '
             'the field is past the threshold.'.format(RATE, WAVE), fmt='rgba32float',
             uF=(DT, (WAVE / (2 * math.pi)) ** 2, G))
setpars(field, npasses=Expr(STEPS))
shape = glsl(comp, 'shape', [field], src('shape.glsl'), "Each spike's peak: the highest height within half a spike's "
             'spacing.', fmt='rgba16float')
surface = glsl(comp, 'surface', [source, shape], lib_glsl(_ROOT, 'common.glsl') + src('surface.glsl'),
               "The surface at the picture's size, each spike a cone with a sharp tip.", fmt='r16float')
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset: the liquid lies flat again.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        op('height_fb').par.resetpulse.pulse()\n")
setpars(reset, op='..', pars='Reset', onpulse=True, valuechange=False)

# ---- The look -------------------------------------------------------------------------------------
section('look', 'The look: the liquid over the picture, seen leaning, a mirror')
TALL = '({0} + ({1} - {0}) * parent().par.Height) * {2}[{3}]'.format(HEIGHT[0], HEIGHT[1], list(CELL), SIZEI)
look = glsl(comp, 'look', [source, surface], lib_glsl(_ROOT, 'red_guard.glsl') + src('look.glsl'),
            'The liquid over the picture: spikes seen leaning, a glossy mirror of the picture and a soft light, the '
            'picture showing through where it lies flat.',
            uL=(menu_index('Style'), par('Picture'), Expr(TALL), par('Tilt')))
setpars(look, inputfiltertype='mipmap')
for g in (drive, seed, field, shape, surface, look):
    setpars(g, inputextenduv='hold')

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
