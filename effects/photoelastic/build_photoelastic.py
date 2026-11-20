"""Build Photoelastic. Run from a textport: __file__ = '/path/to/build_photoelastic.py'; exec(open(__file__).read())

The live picture as clear plastic between polarizers. What stands out in front (depth or a mask on input 3), the
picture's lights and what moves warm the plastic (lib warmth()), and a plastic warmed unevenly is stressed: the
thermoelastic potential psi with lap psi = warmth (Goodier 1937), solved afresh each frame by cascadic multigrid on the
warmth's pyramid (its coarsest level summed directly through the Laplacian's Green's function), gives the stress as psi's Hessian less its trace. Stressed plastic is birefringent (Brewster 1816), so
between polarizers white light comes out in Michel-Levy's interference colors (Sorensen 2013's first-principles chart,
summed through Wyman, Sloan and Shirley's CIE fit): fringes that ring what is warm, crowding at its outline, in a dark
field, a light field, plane polarizers (with the isoclinics' dark bands) or with a tint plate.

The stress stays where it is, never carried along by the picture's movement; the only state is the warmth (patents:
private notes; README CREDITS, Not used). dev/protos/photoelastic/offline.py tried it first on the clips (board #4853):
stress from the depth's curvature and from the optical flow's strain rate drew fringes over every bit of noise, so the
warmth, which already ignores noise, heats the plastic; the cascade matched an exact solve on a padded domain closely
with the edges held, where clamped edges drew fringes along the frame.

The network, left to right:
  picture  source -> look (the picture through the polariscope, by Style; w2, the warmth at 1/16, for its thickness)
  motion   optical_flow() (lum8, seen, change, change_avg, clock); subject (what warms: what stands out, the lights, a
           quarter of the picture's size) -> warmth() (+ warmth_fb); clear is where warmth_fb starts
  stress   pyramid() of the warmth (w1 to w4), warm_mean -> solve4 (the coarsest, summed) -> solve3 ... solve0 (psi) ->
           stress
  chart    chart (what the polariscope lets through, by order and angle; cooks when Style changes)
  audio    audio_in() -> counts -> steps -> beats -> ask -> flash_limit -> flash -> squeeze_env; bar_steps -> bar_gap ->
           bars -> turn_lag (the polarizers' turn); level_pick -> level_smooth (the load)
  depth    input 3 (depth_in()) -> near (nearness at a quarter size) -> find (what stands out, or the mask)
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# Unwired, it shows TouchDesigner's banana with a soft white light circling over it on a slow figure of eight,
# BALL_TIME seconds round: the bright banana on its gray ground is ringed by fringes at once, and the light that moves
# warms the plastic around it and leaves the fringes to fade behind it. Schlieren's grass behind the light drew barely a
# fringe: a light's trail is a thin streak.
SAMPLE = SAMPLE_MEDIA
BALL_TIME = 10.0
STYLES = (('dark', 'Dark Field'), ('light', 'Light Field'), ('plane', 'Plane'), ('tint', 'Tint Plate'))
INPUT3 = (('depth', 'Depth Map'), ('mask', 'Mask'))
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
# Fringe orders per unit of stress at Stress 1 (a warm disc's rim is a stress of 0.5 per unit of warmth); the orders
# saturate toward CAP, and the chart runs to CHART_MAX. At 8 the banana's fringes stayed in the first order's grays.
ORDERS, CAP = 12.0, 4.0
CHART_MAX = CAP + 0.5
CHART_SIZE = (512, 64)
TINT = 1.0                     # the tint plate's retardation, in orders (550 nm, a full wave of green)
# The warmth's pyramid: LEVELS halvings below a quarter of the picture's size (320 x 180 down to 20 x 11). The coarsest
# level is summed directly (direct.glsl), and every finer one gets FINE Jacobi passes from the coarser one's solution.
# Each pass costs about 0.04 ms on the M2 Pro whatever its size: 60 Jacobi passes at 10 x 5 for the coarsest took
# 1.9 ms, and the whole solve 4.5 ms.
LEVELS, FINE = 4, 6
# Warmth (lib warmth()): movement of MOVE_DEAD in luma a frame
# warms nothing (haze drifting) and MOVE_FULL fully; it rises over RISE_T s and falls over FALL_T s at Linger 0.5 (0 a
# quarter of that, 1 four times).
MOVE_DEAD, MOVE_FULL, RISE_T, FALL_T = 0.03, 0.1, 0.15, 1.5
# A beat squeezes the plastic: the stress rises by SQUEEZE at Beat Squeeze 1 at once and falls back over SQUEEZE_TIME s.
SQUEEZE, SQUEEZE_TIME = 0.25, 0.3
# A bar turns the polarizers only TURN_GAP s or more after the last turn, and the turn eases over TURN_EASE s (Schlieren's
# blade measured half a flash a second more turned on every bar).
TURN_GAP, TURN_EASE = 2.0, 1.5
# The load follows the loudness eased over LEVEL_EASE s: a load that pumps on every hit pumps the fringes (Video
# Vocoder's bands did).
LEVEL_EASE = 1.0
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right, nearer
# than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale), as in Schlieren.
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
    'photoelastic', 'Photoelastic',
    'Photoelastic {}: the live picture as clear plastic between polarizers, its warm parts stressing it into '
    'interference colors, from the papers.'.format(VERSION),
    README, tags=('photoelastic', 'polariscope', 'birefringence', 'interference', 'optics', 'audio-reactive'),
    audio=True, depth=True, flashing=True, sample=SAMPLE)

# Unwired: the light circling over the sample movie.
T = 'absTime.seconds * {:.6f}'.format(2 * 3.141592653589793 / BALL_TIME)
section('input')
ball = mk(comp, circleTOP, 'ball', comment='A soft white light on a figure of eight (unwired only).',
          outputresolution='custom', resolutionw=1280, resolutionh=720, radiusx=0.04, radiusy=0.071,
          radiusunit='fraction', softness=0.03, softnessunit='fraction', centerunit='fraction',
          centerx=Expr('0.3 * math.sin({})'.format(T)), centery=Expr('-0.15 + 0.12 * math.sin(2 * {})'.format(T)),
          fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgalpha=0, borderwidth=0)
demo = mk(comp, overTOP, 'demo', [ball, comp.op('sample')], 'Unwired: the light over the sample movie.',
          outputresolution='custom', resolutionw=1280, resolutionh=720)
source.inputConnectors[1].connect(demo)

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Style', 'Style', STYLES, 'dark',
     'Dark Field shows the stress in color on black, as crossed circular polarizers do. Light Field lets the light '
     'through where the plastic is unstressed and shows the stress in the complementary colors. Plane uses crossed '
     'straight polarizers, which also darken wherever the stress lies along them (the isoclinics). Tint Plate adds a '
     'full-wave plate: unstressed plastic turns magenta, and stress turns it blue one way and yellow the other.'
     ).startSection = True
custom(page, 'Float', 'Stress', 'Stress', 0.5, 'How strongly the warmth stresses the plastic, 0-1: more fringes.', 0, 1,
       True)
custom(page, 'Float', 'Angle', 'Polarizer Angle', 0.0,
       'Which way the polarizers face, in degrees (Plane and Tint Plate): the dark isoclinics and the blue and yellow '
       'turn with them.', 0, 180, True).enableExpr = "me.par.Style in ('plane', 'tint')"
custom(page, 'Float', 'Backlight', 'Backlight', 0.25,
       'The light behind the plastic, 0-1: at 0 the picture itself, at 1 a plain white light, so the colors show in '
       "the picture's dark parts too.", 0, 1, True)
custom(page, 'Float', 'Cast', 'Cast', 1.0,
       'How much the plastic is cast to what warms it, 0-1: at 1 it is thick where the picture is warm and thin '
       'elsewhere, so the colors gather on the subject and the rest stays dark; at 0 it is an even sheet, and the '
       'stress shows wherever it reaches.', 0, 1, True)
custom(page, 'Float', 'Backdrop', 'Backdrop', 0.2,
       'How much of the picture shows as it is where the plastic is unstressed, 0-1, as polarizers short of perfect '
       'let it through (all but Light Field, which shows it anyway).', 0, 1, True).enableExpr = \
    "me.par.Style != 'light'"

custom(page, 'Float', 'Warmmove', 'Warm by Movement', 0.75,
       'How much whatever moves warms the plastic, quickly, leaving it to cool behind it, 0-1.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Warmnear', 'Warm by Nearness', 1.0,
       'How much what stands out in front in the depth map on input 3 (or what is inside the mask) warms the '
       'plastic, 0-1.', 0, 1, True)
custom(page, 'Float', 'Warmlight', 'Warm by Light', 0.5,
       "How much the picture's light warms the plastic, as light falling on it would: the brighter, the warmer, 0-1. "
       'An evenly bright area is stressed only at its outline.', 0, 1, True)
custom(page, 'Float', 'Linger', 'Linger', 0.5,
       'How long the plastic stays warm once what warmed it has gone: 0.5 cools it over about {:g} s, 0 four times '
       'as fast, 1 four times as slowly.'.format(FALL_T), 0, 1, True)
menu(page, 'Input3', 'Input 3 Holds', INPUT3, 'depth',
     'Depth Map: what stands in front of its surroundings warms the plastic (floors and walls drop out). Mask: what '
     'is inside the mask (white inside) warms it.')
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
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Cool the plastic at once: no warmth left, no stress.')

custom(page, 'Float', 'Squeeze', 'Beat Squeeze', 0.5,
       'On the beats of input 2 the plastic is squeezed, and every fringe jumps outward and settles back. It changes '
       'a wide area at once, so it is a flash: Calm allows one a second, Up to 3 per second every beat up to 180 BPM, '
       'Off none. 0 turns it off.', 0, 1, True).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much louder music on input 2 loads the plastic harder (more fringes) and quiet passages lighter, '
       'following the loudness over about a second, 0-1.', 0, 1, True)
custom(page, 'Float', 'Turn', 'Bar Turn', 22.5,
       'How far each bar of input 2 turns the polarizers, in degrees (Plane and Tint Plate), at most once every {:g} s '
       'and over {:g} s. 0 keeps them still.'.format(TURN_GAP, TURN_EASE), 0, 90, True).enableExpr = \
    "me.par.Style in ('plane', 'tint')"

# ---- Audio (input 2) ------------------------------------------------------------------------------
section('audio', 'Audio (input 2): a squeeze on the beats, the load with loudness, bars turn the polarizers')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
# A beat's squeeze moves every fringe at once: a flash, so beats pass through the gate.
beats = mk(comp, selectCHOP, 'beats', [steps], 'Beats.', channames='beat_count')
ask = mk(comp, renameCHOP, 'ask', [beats], 'Beats, asking to squeeze.', renamefrom='beat_count', renameto='squeeze')
flash = flash_gate(comp, ask)
mk(comp, triggerCHOP, 'squeeze_env', [flash], "A beat's squeeze: 1 at the beat, none {:g} s later.".format(
   SQUEEZE_TIME), attack=0, peak=1, peaklen=0, decay=SQUEEZE_TIME, dshape='linear', sustain=0, release=0)
# The bars counted from when the effect started, one at a time: audio_in()'s bar_count is the song's, and wiring a
# signal in mid-song would spin the polarizers through every bar so far.
bar_steps = mk(comp, selectCHOP, 'bar_steps', [steps], 'Bars.', channames='bar_count')
bar_gap = mk(comp, triggerCHOP, 'bar_gap', [bar_steps], 'Bars at least {:g} s apart.'.format(TURN_GAP),
             retrigger=TURN_GAP, retriggerunit='seconds', attack=0, peak=1, decay=0, sustain=0)
bars = mk(comp, countCHOP, 'bars', [bar_gap], 'Turns since the effect started, one a bar at most.')
mk(comp, lagCHOP, 'turn_lag', [bars], 'The turns, eased over {:g} s: the polarizers turn smoothly.'.format(TURN_EASE),
   lag1=TURN_EASE, lag2=TURN_EASE, lagunit='seconds')
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
mk(comp, filterCHOP, 'level_smooth', [level_pick], 'Loudness eased over {:g} s.'.format(LEVEL_EASE), width=LEVEL_EASE)
LOAD = ("((1 - parent().par.Loudness / 2 + parent().par.Loudness * op('level_smooth')[0]) * "
        "(1 + {} * parent().par.Squeeze * op('squeeze_env')[0]) if {} else 1)".format(SQUEEZE, WIRED))

# ---- Depth (input 3) ------------------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): what stands out warms the plastic')
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

# ---- Warmth ---------------------------------------------------------------------------------------
section('warmth', 'Warmth: what stands out, what is bright and what moves warm the plastic', lane='motion')
clear = mk(comp, constantTOP, 'clear', comment='Nothing yet (alpha 0): where the warmth starts, and Reset.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
mo = optical_flow(comp, _ROOT, source, levels=(8,), flow=False)
WIRED3 = 'parent().inputConnectors[2].connections'
subject = glsl(comp, 'subject', [source, find], src('subject.glsl'),
               "What warms the plastic: what stands out in front, the light, at a quarter of the picture's size.",
               fmt='rgba16float',
               uS=(Expr('parent().par.Warmnear if {} else 0'.format(WIRED3)), par('Warmlight'),
                   Expr('1 if {} else 0'.format(WIRED3))))
setpars(subject, outputresolution='quarter', inputfiltertype='mipmap')
warm = warmth(comp, _ROOT, subject, mo, clear, subject_warms=1.0, move_warms=par('Warmmove'), full=MOVE_FULL,
              dead=MOVE_DEAD, rise=RISE_T, fall=Expr('{} * 4 ** (2 * parent().par.Linger - 1)'.format(FALL_T)))
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset: the plastic cools at once.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        op('warmth_fb').par.resetpulse.pulse()\n")
setpars(reset, op='..', pars='Reset', onpulse=True, valuechange=False)

# ---- The stress -----------------------------------------------------------------------------------
section('stress', 'The stress: the warm plastic swells, and its potential, solved coarse to fine, gives the stress',
        lane='stress')
levels = pyramid(comp, _ROOT, warm, LEVELS, fmt='mono32float', prefix='w', what='The warmth')
warm_mean = mk(comp, analyzeTOP, 'warm_mean', [levels[LEVELS]], "The warmth's mean: an even warmth stresses nothing.",
               op='average', analyzechannel='independent')
solve_src = lib_glsl(_ROOT, 'common.glsl') + src('solve.glsl')
psi = glsl(comp, 'solve{}'.format(LEVELS), [levels[LEVELS], warm_mean], src('direct.glsl'),
           "The plastic's potential at 1/{} of the picture's size, summed directly over every cell.".format(
               4 * 2 ** LEVELS), fmt='mono32float', uS=4.0 ** LEVELS)
for k in range(LEVELS - 1, -1, -1):
    w = levels[k]
    s = glsl(comp, 'solve{}'.format(k), [w, psi, w, warm_mean], solve_src,
             "The plastic's potential at 1/{} of the picture's size: {} Jacobi passes from solve{}'s.".format(
                 4 * 2 ** k, FINE, k + 1), fmt='mono32float', uS=(4.0 ** k, 1))
    setpars(s, npasses=FINE + 1, inputextenduv='hold')
    psi = s
stress = glsl(comp, 'stress', [psi], src('stress.glsl'),
              "The stress: the potential's Hessian less its trace (rg), at a quarter of the picture's size.",
              fmt='rgba32float')
setpars(stress, inputextenduv='hold')

# ---- The chart ------------------------------------------------------------------------------------
section('chart', "The chart: what the polariscope lets through, by the stress's order and angle", lane='chart')
chart = glsl(comp, 'chart', [], lib_glsl(_ROOT, 'spectrum.glsl') + src('chart.glsl'),
             "What the Style's polariscope lets through, by fringe order (across) and angle to the polarizers (down), "
             'summed over wavelengths. Cooks when Style changes.',
             res=CHART_SIZE, fmt='rgba16float', uC=(menu_index('Style'), CHART_MAX, TINT))

# ---- The look -------------------------------------------------------------------------------------
section('look', 'The look: the picture through the stressed plastic, between polarizers', lane='picture')
TURNED = ("math.radians(parent().par.Angle + (parent().par.Turn * op('turn_lag')[0] if {} else 0))".format(WIRED))
look = glsl(comp, 'look', [source, stress, chart, levels[2]],
            lib_glsl(_ROOT, 'common.glsl') + lib_glsl(_ROOT, 'red_guard.glsl') + src('look.glsl'),
            'The picture through the stressed plastic, as thick as Cast makes it: the fringe order and angle looked up '
            'in the chart.',
            uL=(menu_index('Style'), Expr('{} * parent().par.Stress * {}'.format(ORDERS, LOAD)), CAP, CHART_MAX),
            uP=(par('Backdrop'), par('Backlight'), Expr(TURNED), par('Cast')))

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
