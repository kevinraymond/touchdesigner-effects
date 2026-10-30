"""Build Schlieren. Run from a textport: __file__ = '/path/to/build_schlieren.py'; exec(open(__file__).read())

The warm air rising off the live picture's subject made visible, as a schlieren camera shows it (G. S. Settles,
"Schlieren and Shadowgraph Techniques", 2001; the four looks after Brownlee et al., IEEE TVCG 2011). What stands out in
front (depth or a mask on input 3), what is bright and what moves warms the air (lib warmth()); the air rises in a
column above it, sways and curls (stable fluids, Stam 1999, at a quarter of the picture's size), and carries the heat
up at half the picture's size (MacCormack's step, Selle et al. 2008). The heat bends the light through it, and the
picture is shown through that bending as Knife Edge relief, Rainbow color, Shadowgraph lines or Interferogram fringes,
with the subject opaque.

The lift comes from the picture's warmth at its source, made afresh every frame, never from the heat the air carries,
and the heat is shown only by how it bends the light (patents: private notes; README CREDITS, Not used).
dev/protos/schlieren/offline.py tried it first on the clips (board #4847): a source warm all over gave smooth heat and
nearly no relief until its edge was sharpened; relief added to the picture kept a dark room readable where relief that
multiplied it vanished; relief over the subject striped it, so the subject is opaque, as it is to a real camera; and
noise on the heating (eddies) striped the subject too, so the noise wavers the lift instead.

The network, left to right:
  picture  source -> look (the picture through the air, by Style)
  motion   optical_flow() (lum8, lum8p, seen, change, change_avg, clock, lk8) -> flow_speed() (pace, motion);
           subject (what warms, what is opaque, a quarter of the picture's size) -> warmth() (+ warmth_fb); clear is
           where every Feedback TOP starts
  air      lift (a column above what is warm) -> air (+ velocity_fb) -> incompressible() (divergence, pressure,
           velocity); heat (+ heat_fb: carried, heated, cooling, half size) -> bend (deflection, Laplacian)
  audio    audio_in() -> counts -> steps -> puffs -> ask -> flash_limit -> flash -> puff_env, drop_env; bar_steps ->
           bar_gap -> bars -> turn_lag (the blade's turn); level_pick -> level_smooth; band_pick -> bands_smooth
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
# Unwired, it shows grass swaying in front of a colorful building (TouchDesigner's sample) with a soft white light
# circling over it on a slow figure of eight, BALL_TIME seconds round: the still banana warmed nothing, and a light that
# moves shows at once what warms the air and how the warm air rises and trails behind it.
SAMPLE = "app.samplesFolder + '/Map/Nature/Movie.2.mp4'"
BALL_TIME = 10.0
STYLES = (('knife', 'Knife Edge'), ('rainbow', 'Rainbow'), ('shadow', 'Shadowgraph'), ('fringes', 'Interferogram'))
INPUT3 = (('depth', 'Depth Map'), ('mask', 'Mask'))
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')
# How strongly the bending shows at Strength 1 (the default 0.35 gives about the prototype's 1, which read clearly on a
# dark room without blotting it black).
GAIN = 3.0
# The air (dev/protos/schlieren): at Rise 1 the lift is RISE frame heights a second^2 where it is warmest (1.6 churned the
# air over flowers swaying in the wind, warm all over, into eddies that flashed 1.5 times a second over the clip with
# Flashing Off, even with the air's speed capped; the default 0.7 gives 0.56), reaching
# REACH frame heights above what is warm, wavered by WOBBLE of slow noise; at Swirl 1 the vorticity confinement is
# SWIRL frame heights (Fluid's 0.4 blew up; it runs 0.02-0.06); the velocity halves every HALF s; PASSES Jacobi
# iterations of the pressure a frame.
RISE, REACH, WOBBLE, SWIRL, HALF, PASSES = 0.8, 0.35, 0.6, 0.06, 1.0, 20
# The heat: a warm source heats the air above it at HEAT a second at Heat 1, and the heat halves every COOL s once
# carried away at Linger 0.5 (0 a quarter of that, 1 four times).
HEAT, COOL = 12.0, 1.5
# The picture behind shifts REFRACT frame heights where the air bends light by 1 (2 pixels at 360 high), and no further:
# a lamp's bright point slid back and forth over a dark room flashed the cells around it.
REFRACT = 2.0 / 360
# Warmth (lib warmth()): a bright part warms from LIGHT_FROM of full brightness; movement of MOVE_DEAD in luma a frame
# warms nothing (haze drifting) and MOVE_FULL fully; it rises over RISE_T s and falls over FALL_T s.
LIGHT_FROM, MOVE_DEAD, MOVE_FULL, RISE_T, FALL_T = 0.55, 0.03, 0.1, 0.15, 1.5
# A beat's puff at Beat Puffs 1, falling off evenly over PUFF_TIME s: the warm air thrown up at PUFF_LIFT frame heights a
# second^2 and heated PUFF_HEAT times faster, weaker where more than a twentieth of the picture is warm (air.glsl); a drop's
# is DROP times as strong and lasts DROP_TIME s. 6 and 3 shook a lamp's air so hard its shifted point flashed.
PUFF_TIME, PUFF_LIFT, PUFF_HEAT, DROP, DROP_TIME = 0.3, 3.0, 2.0, 2.0, 1.0
# A bar turns the blade only TURN_GAP s or more after the last turn, and the turn eases over TURN_EASE s: turned on every
# bar of the stress beat (two a second), the relief swept from light to dark and back faster than the clip's own
# changes (half a flash a second more with Flashing Off). At 120 BPM every bar turns it.
TURN_GAP, TURN_EASE = 2.0, 1.5
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right, nearer
# than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale), as in Fluid and Frost.
STAND_OUT, FAR = 0.1, (0.5, 0.05)
DTF = Expr('min(absTime.stepSeconds, 0.05)')
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
    'schlieren', 'Schlieren',
    'Schlieren {}: the warm air rising off the live picture made visible, as a schlieren camera shows it, from the '
    'papers.'.format(VERSION),
    README, tags=('schlieren', 'shadowgraph', 'heat', 'fluid', 'optics', 'audio-reactive'),
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
menu(page, 'Style', 'Style', STYLES, 'knife',
     'Knife Edge shows the warm air as gray relief, lit from the side the blade faces. Rainbow shows it in color, '
     'the way the light bends picking the hue. Shadowgraph shows its sharpest folds as bright and dark lines. '
     'Interferogram lays straight fringes across the picture that the warm air bends.').startSection = True
custom(page, 'Float', 'Strength', 'Strength', 0.35, 'How strongly the bending shows, 0-1.', 0, 1, True)
custom(page, 'Float', 'Angle', 'Edge Angle', 0.0,
       "Which way the blade faces, in degrees: at 0 it stands upright and shows the plume's sides, at 90 it lies flat "
       'and shows its tops. In Rainbow it turns the colors.', 0, 360, True).enableExpr = \
    "me.par.Style in ('knife', 'rainbow')"
custom(page, 'Float', 'Fringes', 'Fringes', 10.0,
       "How many straight fringes the Interferogram lays across a frame height, which the warm air bends. At 0 only "
       "the air's own fringes show.", 0, 20, True).enableExpr = "me.par.Style == 'fringes'"
custom(page, 'Float', 'Backdrop', 'Backdrop', 1.0,
       'How much of the picture shows behind the air, 0-1. At 0 it is a schlieren photograph: an even gray field, '
       'the subject a dark silhouette.', 0, 1, True)

custom(page, 'Float', 'Heat', 'Heat', 0.5, 'How quickly warm things heat the air above them, 0-1.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Rise', 'Rise', 0.7, 'How hard the warm air rises, 0-1.', 0, 1, True)
custom(page, 'Float', 'Swirl', 'Swirl', 0.5, 'How much the air curls into eddies, 0-1.', 0, 1, True)
custom(page, 'Float', 'Linger', 'Linger', 0.5,
       'How long the heat lasts once carried away: 0.5 halves it every {:g} s, 0 four times as fast, 1 four times as '
       'slowly.'.format(COOL), 0, 1, True)
custom(page, 'Float', 'Stir', 'Stir', 1.0, "How much the picture's movement drags the air along, 0-2.", 0, 2, True)
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Clear the air: no heat left, and still.')

custom(page, 'Float', 'Warmmove', 'Warm by Movement', 0.75,
       'How much whatever moves warms the air, quickly, leaving it to cool behind it, 0-1.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Warmnear', 'Warm by Nearness', 1.0,
       'How much what stands out in front in the depth map on input 3 (or what is inside the mask) warms the air, '
       '0-1. It also hides the air behind it.', 0, 1, True)
custom(page, 'Float', 'Warmlight', 'Warm by Light', 0.5,
       "How much the picture's lights warm the air, as a lamp or a candle does: what is bright and brighter than what "
       'is around it (a bright sky is not a light), 0-1.', 0, 1, True)
menu(page, 'Input3', 'Input 3 Holds', INPUT3, 'depth',
     'Depth Map: what stands in front of its surroundings warms the air (floors and walls drop out). Mask: what is '
     'inside the mask (white inside) warms it.')
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

custom(page, 'Float', 'Puff', 'Beat Puffs', 0.5,
       'On the beats of input 2 the warm air puffs up at once and rolls up into eddies. It moves a wide area at once, '
       'so it is a flash: Calm allows one a second, Up to 3 per second every beat up to 180 BPM, Off none. 0 turns it '
       'off.', 0, 1, True).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much louder music on input 2 heats the air faster (and quiet passages slower), 0-1.', 0, 1, True)
custom(page, 'Float', 'Bands', 'Band Heights', 0.5,
       "How much the music's seven bands each heat one height of the frame, the lowest at the bottom and the highest "
       'at the top, 0-1.', 0, 1, True)
custom(page, 'Float', 'Turn', 'Bar Turn', 45.0,
       'How far each bar of input 2 turns the blade, in degrees (Knife Edge and Rainbow), at most once every {:g} s and '
       'over {:g} s. 0 keeps it still.'.format(TURN_GAP, TURN_EASE), 0, 90, True).enableExpr = \
    "me.par.Style in ('knife', 'rainbow')"
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a drop sends up a big puff (a flash, as Beat Puffs; Fosfora's drop "
       'detection is experimental).')

# ---- Audio (input 2) ------------------------------------------------------------------------------
section('audio', 'Audio (input 2): puffs on the beats, heat with loudness, the bands by height, bars turn the blade')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count bar_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
# A beat's puff throws the warm air up over a wide area at once: a flash, so beats and drops pass through the gate.
puffs = mk(comp, selectCHOP, 'puffs', [steps], 'Beats and drops.', channames='beat_count drop_count')
ask = mk(comp, renameCHOP, 'ask', [puffs], 'Beats and drops, asking to puff.',
         renamefrom='beat_count drop_count', renameto='puff drop')
flash = flash_gate(comp, ask)
puff_sel = mk(comp, selectCHOP, 'puff_sel', [flash], 'Beats that passed the gate.', channames='puff')
mk(comp, triggerCHOP, 'puff_env', [puff_sel], "A beat's puff: 1 at the beat, none {:g} s later.".format(PUFF_TIME),
   attack=0, peak=1, peaklen=0, decay=PUFF_TIME, dshape='linear', sustain=0, release=0)
drop_sel = mk(comp, selectCHOP, 'drop_sel', [flash], 'Drops that passed the gate.', channames='drop')
mk(comp, triggerCHOP, 'drop_env', [drop_sel], "A drop's big puff: 1 at the drop, none {:g} s later.".format(DROP_TIME),
   attack=0, peak=1, peaklen=0, decay=DROP_TIME, dshape='linear', sustain=0, release=0)
# The bars counted from when the effect started, one at a time: audio_in()'s bar_count is the song's, and wiring a
# signal in mid-song would spin the blade through every bar so far.
bar_steps = mk(comp, selectCHOP, 'bar_steps', [steps], 'Bars.', channames='bar_count')
bar_gap = mk(comp, triggerCHOP, 'bar_gap', [bar_steps], 'Bars at least {:g} s apart.'.format(TURN_GAP),
             retrigger=TURN_GAP, retriggerunit='seconds', attack=0, peak=1, decay=0, sustain=0)
bars = mk(comp, countCHOP, 'bars', [bar_gap], 'Turns since the effect started, one a bar at most.')
mk(comp, lagCHOP, 'turn_lag', [bars], 'The turns, eased over {:g} s: the blade turns smoothly.'.format(TURN_EASE),
   lag1=TURN_EASE, lag2=TURN_EASE, lagunit='seconds')
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
mk(comp, filterCHOP, 'level_smooth', [level_pick], 'Loudness eased over half a second.', width=0.5)
band_pick = mk(comp, selectCHOP, 'band_pick', [audio], 'The seven bands, lowest to highest.', channames=' '.join(BANDS))
mk(comp, filterCHOP, 'bands_smooth', [band_pick], 'The bands eased over a sixth of a second.', width=0.15)
PUFF_NOW = ("(parent().par.Puff * (op('puff_env')[0] + {} * op('drop_env')[0] * parent().par.Moments) if {} else 0)"
            .format(DROP, WIRED))

# ---- Depth (input 3) ------------------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): what stands out warms the air and hides the air behind it')
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

# ---- Movement and warmth ---------------------------------------------------------------------------
section('warmth', 'Warmth: what stands out, what is bright and what moves warm the air', lane='motion')
clear = mk(comp, constantTOP, 'clear', comment='Nothing yet (alpha 0): where the warmth, the air and the heat start, '
           'and Reset.', outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
mo = optical_flow(comp, _ROOT, source, levels=(8,))
pace, motion = flow_speed(comp, _ROOT, mo, clear)
WIRED3 = 'parent().inputConnectors[2].connections'
subject = glsl(comp, 'subject', [source, find], src('subject.glsl'),
               'What warms the air (what stands out in front, what is bright) and what is opaque (what stands out), '
               "at a quarter of the picture's size.", fmt='rgba16float',
               uS=(Expr('parent().par.Warmnear if {} else 0'.format(WIRED3)), par('Warmlight'),
                   Expr('1 if {} else 0'.format(WIRED3)), LIGHT_FROM))
setpars(subject, outputresolution='quarter', inputfiltertype='mipmap')
warm = warmth(comp, _ROOT, subject, mo, clear, subject_warms=1.0, move_warms=par('Warmmove'), full=MOVE_FULL,
              dead=MOVE_DEAD, rise=RISE_T, fall=FALL_T)

# ---- The air --------------------------------------------------------------------------------------
section('air', 'The air: rising above what is warm, swirling, stirred by movement; the heat it carries', lane='air')
lift = glsl(comp, 'lift', [warm], lib_glsl(_ROOT, 'common.glsl') + src('lift.glsl'),
            'Where the air rises: in a column above what is warm, falling off with height, wavered by slow noise; and '
            'the warmth smoothed, which heats it.',
            fmt='rgba16float', uL=(REACH, WOBBLE, clock_seconds()))
setpars(lift, inputfiltertype='mipmap')
velocity_fb = mk(comp, feedbackTOP, 'velocity_fb', [clear], 'The velocity last frame.', top='velocity')
warm_area = mk(comp, analyzeTOP, 'warm_area', [warm], 'How much of the picture is warm (the warmth\'s average): a puff '
               'is weaker where more of it is.', op='average', analyzechannel='independent')
air = glsl(comp, 'air', [lift, velocity_fb, motion, warm_area], src('air.glsl'),
           'The air: carried by itself, kept swirling, lifted above what is warm, puffed on the beats, dragged by the '
           "picture's movement.", fmt='rgba32float',
           uT=(DTF, Expr('{} * parent().par.Rise'.format(RISE)), Expr('{} * parent().par.Swirl'.format(SWIRL)), HALF),
           uP=(par('Stir'), Expr('{} * {}'.format(PUFF_LIFT, PUFF_NOW))))
setpars(air, inputextenduv='hold')
divergence, pressure, velocity = incompressible(comp, _ROOT, air, PASSES, carries='the heat')
heat_fb = mk(comp, feedbackTOP, 'heat_fb', [clear], 'The heat last frame.', top='heat')
LOUD = "(1 - parent().par.Loudness / 2 + parent().par.Loudness * op('level_smooth')[0] if {} else 1)".format(WIRED)
heat = glsl(comp, 'heat', [source, heat_fb, velocity, lift, warm_area], src('heat.glsl'),
            'The heat the air carries, at half the picture\'s size: carried (MacCormack), heated where warm (louder '
            'hotter, the bands by height), cooling.', fmt='rgba16float',
            uH=(DTF, Expr('{} * parent().par.Heat * {}'.format(HEAT, LOUD)),
                Expr('{} * 4 ** (2 * parent().par.Linger - 1)'.format(COOL)), Expr('{} * {}'.format(PUFF_HEAT, PUFF_NOW))),
            uB0=tuple(Expr("op('bands_smooth')['{}'] if {} else 0.5".format(b, WIRED)) for b in BANDS[:4]),
            uB1=tuple(Expr("op('bands_smooth')['{}'] if {} else 0.5".format(b, WIRED)) for b in BANDS[4:]) +
            (Expr('parent().par.Bands if {} else 0'.format(WIRED)),))
setpars(heat, outputresolution='half')
bend = glsl(comp, 'bend', [heat], src('bend.glsl'),
            'How the heat bends the light: rg the deflection, b its Laplacian (what a shadowgraph sees), a the heat.',
            fmt='rgba16float')
setpars(bend, inputextenduv='hold')
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset: the air starts again, still and without heat.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        for name in ('velocity_fb', 'pressure_fb', 'heat_fb', 'warmth_fb', 'motion_fb'):\n"
              '            op(name).par.resetpulse.pulse()\n')
setpars(reset, op='..', pars='Reset', onpulse=True, valuechange=False)

# ---- The look -------------------------------------------------------------------------------------
section('look', 'The look: the picture seen through the air, as a schlieren camera shows it', lane='picture')
TURNED = ("math.radians(parent().par.Angle + (parent().par.Turn * op('turn_lag')[0] if {} else 0))".format(WIRED))
look = glsl(comp, 'look', [source, bend, subject],
            lib_glsl(_ROOT, 'common.glsl') + lib_glsl(_ROOT, 'spectrum.glsl') + lib_glsl(_ROOT, 'red_guard.glsl') +
            src('look.glsl'),
            'The picture through the air: Knife Edge relief, Rainbow color, Shadowgraph lines or Interferogram '
            'fringes; the subject opaque.',
            uL=(menu_index('Style'), Expr('{} * parent().par.Strength'.format(GAIN)), par('Backdrop'), REFRACT),
            uE=(Expr('math.cos({})'.format(TURNED)), Expr('math.sin({})'.format(TURNED)), par('Fringes')))

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
