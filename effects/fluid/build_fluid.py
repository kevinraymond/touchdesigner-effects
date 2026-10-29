"""Build Fluid. Run from a textport: __file__ = '/path/to/build_fluid.py'; exec(open(__file__).read())

The picture pours ink, smoke or fire into a fluid simulation that its own movement stirs. A stable-fluids
solver (Stam 1999, as Harris laid it out for the GPU in 2004) runs at a quarter of the input's size: the
velocity carries itself, vorticity confinement keeps its swirls, what it carries rises, the input's motion
(this library's Lucas-Kanade optical flow) drags it along, and a pressure solve keeps it from piling up.
What it carries (ink, smoke or heat) lives at the input's size, poured in where the input moves, is bright,
or stands out in the depth (or mask) on input 3. On the beats the music makes it leap, churn and flare.

The network, left to right:
  motion   lib optical_flow(): lum8, lum4 and the previous frame's (lum8p, lum4p), the new-frame and cut
           test (change, change_avg, clock), the flow (lk8, lk4) -> lib flow_speed(): pace (when the last
           frame came, the gap between frames) -> motion (the flow as a speed, held between the input's frames)
  emit     where the input pours into the fluid: motion, the picture, or input 3 (depth -> near -> find, or
           near alone for a mask; subject passes them only for Depth and Mask, so they cook only then)
  fluid    advect (the velocity carried by itself, swirled, risen and dragged by the motion) -> lib incompressible():
           divergence -> pressure (Jacobi, PASSES iterations in one TOP) -> velocity (made incompressible), read back
           through velocity_fb; dye (what it carries, carried by velocity), read back through dye_fb; still
           is where every Feedback TOP starts, and Reset starts them again
  look     the dye drawn over the picture as ink, smoke or flames
  audio    audio_in() -> counts -> steps -> ask -> flash_limit -> flash (beats and drops, as often as Flashing
           allows) -> puff_env (a beat's puff and flare), drop_env (a drop's big puff); build_lag, level_lag
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.2'
# Unwired, it shows grass swaying in front of a colorful building (TouchDesigner's sample) with a soft white
# ball circling over it on a slow figure of eight, BALL_TIME seconds round: the grass alone moves too little and
# too thinly to pour much, and the ball's trail shows what the effect does at once.
SAMPLE = "app.samplesFolder + '/Map/Nature/Movie.2.mp4'"
BALL_TIME = 8.0
LOOKS = (('ink', 'Ink'), ('smoke', 'Smoke'), ('fire', 'Fire'))
EMIT_FROM = (('movement', 'Movement'), ('brightness', 'Brightness'), ('depth', 'Depth (Input 3)'),
             ('mask', 'Mask (Input 3)'))
# Each look's own character, by Look: how long what it carries takes to fade to half (seconds, at Linger
# 0.5), how much it rises (frame heights per second^2 where it is thick, added to Rise), how much it
# swirls (times Swirl), and the velocity's half-life (seconds): ink in water is slow and heavy, flames quick.
HALF = (4.0, 1.2, 0.4)
RISE = (0.0, 1.0, 3.0)
SWIRL = (0.6, 1.0, 1.5)
FLOW_HALF = (0.8, 2.0, 1.0)
# Swirl 1's vorticity confinement, in frame heights: a swirl L cells across grows at about SWIRL_K x the grid's
# height / L a second (0.4 grew small swirls 18 times a second and the velocity blew up within a second).
SWIRL_K = 0.04
POUR = 6.0           # what pours in per second where the input emits fully, at Amount 1
PASSES = 40          # Jacobi iterations of the pressure a frame
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right,
# nearer than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale; 0.16 at 0.5, near
# Particles' 0.15). Brightness standing in for depth (nothing on input 3) counts only above BRIGHT_FAR.
STAND_OUT, FAR, BRIGHT_FAR = 0.1, (0.5, 0.05), 0.5
# A beat's puff, at Beat Puffs 1, falling off evenly over PUFF_TIME seconds: the fluid leaps up where it is thick
# (LEAP frame heights per second^2 more rise), churns (vorticity confinement CHURN times stronger at once) and the
# pour flares to 1 + FLARE times. A drop's puff is DROP times as strong and lasts DROP_TIME. Both are flashes, as
# often as Flashing allows. Rise and swirl are forces the solver handles cleanly. Making the fluid expand did not
# work: a divergence source (Feldman et al. 2003) needs a pressure solve 40 Jacobi passes can't reach across a
# cloud (dev/reaction.py: 0.93-0.95 times the change after a beat as before), and an outward push after the
# projection inflated the clouds into balloons with hard walls where they met.
PUFF_TIME, DROP, DROP_TIME = 0.3, 3.0, 1.0
LEAP, CHURN = 4.0, 3.0
FLARE = 3.0
# Loudness (0-1 from audio_in) scales the pour by STREAM[0] + STREAM[1] x loudness at Loudness 1, as in
# Particles (raw audio's loudness has a median of 0.56-0.67 on the library's songs).
STREAM = (0.3, 0.9)
DT = Expr('min(absTime.stepSeconds, 0.05)')
# How hard the beat moves the fluid right now, 0 to DROP: a puff, or a drop's (both through the flash gate).
BEAT = "parent().par.Puff * (op('puff_env')[0] + {} * op('drop_env')[0] * parent().par.Moments)".format(DROP)


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu(name):
    return Expr('parent().par.{}.menuIndex'.format(name))


def per_look(values):
    return '{}[parent().par.Look.menuIndex]'.format(list(values))


def choices(p, items, default):
    p.menuNames = [n for n, _ in items]
    p.menuLabels = [label for _, label in items]
    p.default = p.val = default
    return p


SUMMARY = ('Fluid {}: the picture pours ink, smoke or fire into a fluid that its own movement stirs; the music '
           'makes it leap on the beats.'.format(VERSION))
README = src('readme.txt').format(v=VERSION, passes=PASSES, half=HALF)
comp, page, source = new_effect('fluid', 'Fluid', SUMMARY, README,
                                tags=('fluid', 'smoke', 'fire', 'ink', 'simulation', 'depth', 'audio-reactive'),
                                audio=True, depth=True, flashing=True, sample=SAMPLE)

# Unwired: the ball circling over the sample movie.
T = 'absTime.seconds * {:.6f}'.format(2 * 3.141592653589793 / BALL_TIME)
section('input')
ball = mk(comp, circleTOP, 'ball', comment='A soft white ball on a figure of eight (unwired only).',
          outputresolution='custom', resolutionw=1280, resolutionh=720, radiusx=0.07, radiusy=0.07,
          radiusunit='fraction', softness=0.05, softnessunit='fraction', centerunit='fraction',
          centerx=Expr('0.32 * math.sin({})'.format(T)), centery=Expr('0.2 * math.sin(2 * {})'.format(T)),
          fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgalpha=0, borderwidth=0)
demo = mk(comp, overTOP, 'demo', [ball, comp.op('sample')], 'Unwired: the ball over the sample movie.',
          outputresolution='custom', resolutionw=1280, resolutionh=720)
source.inputConnectors[1].connect(demo)

# ---- Parameters -------------------------------------------------------------------------------
choices(custom(page, 'Menu', 'Look', 'Look', None,
               "What the fluid carries. Ink: the picture's colors, swirling and lingering like ink in water. "
               'Smoke: soft, see-through smoke that rises. Fire: flames that rise and flicker, colored by their '
               'heat.'), LOOKS, 'fire')
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Clear the fluid: no ink, smoke or heat left, and still.')
emitfrom = choices(custom(page, 'Menu', 'Emitfrom', 'Emit From', None,
                          'Where the picture pours into the fluid. Movement: what moves. Brightness: what is '
                          'bright. Depth: what stands in front of its surroundings in the depth map on input 3 '
                          '(floors and walls drop out). Mask: what is inside the mask on input 3 (white inside).'),
                   EMIT_FROM, 'movement')
emitfrom.startSection = True
custom(page, 'Float', 'Sense', 'Sensitivity', 0.5,
       'How easily the picture pours: slower movement, dimmer brightness, farther depth or a grayer mask counts '
       'as well.', 0, 1, True)
choices(custom(page, 'Menu', 'Depthtype', 'Depth Type', None,
               'What input 3 holds. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance 0-1: '
               'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). '
               'Distance in Meters: the Kinect Azure TOP, scaled by Max Distance.'),
        (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
         ('meters', 'Distance in Meters (Kinect Azure)')),
        'nearness').enableExpr = "me.par.Emitfrom in ('depth', 'mask')"
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Emitfrom in ('depth', 'mask') and me.par.Depthtype == 'meters'"
custom(page, 'Float', 'Amount', 'Amount', 0.5, 'How much pours in where the picture emits.', 0, 1, True)
custom(page, 'Float', 'Linger', 'Linger', 0.5,
       "How long it lasts before it fades: 0.5 is the look's own (half gone after about {:g} s for Ink, {:g} s for "
       'Smoke, {:g} s for Fire), 0 a quarter of that, 1 four times.'.format(*HALF), 0, 1, True)
custom(page, 'Float', 'Push', 'Push', 1.0, "How strongly the picture's movement pushes the fluid along.",
       0, 2, True).startSection = True
custom(page, 'Float', 'Swirl', 'Swirl', 0.5, 'How much the fluid curls into swirls and eddies.', 0, 1, True)
custom(page, 'Float', 'Rise', 'Rise', 0.0,
       "Added to the look's own rise (Ink none, Smoke some, Fire a lot); below 0 it sinks.", -1, 1, True)
color = choices(custom(page, 'Menu', 'Color', 'Color', None,
                       "For Ink and Smoke: the picture's colors where they pour in (for Smoke lifted, so dark "
                       'clothes still show), or one color. Fire has its own.'),
                (('picture', 'Picture'), ('orange', 'Orange'), ('blue', 'Blue'), ('white', 'White')), 'picture')
color.startSection = True
color.enableExpr = "me.par.Look != 'fire'"
custom(page, 'Float', 'Backdrop', 'Backdrop', 0.6, 'How bright the picture behind the fluid is, 0 (black) to 1.',
       0, 1, True)
custom(page, 'Float', 'Loudness', 'Loudness', 0.7,
       'How much the loudness of input 2 thickens and thins the pour: at 1, quiet passages pour a third of Amount '
       'and the loudest a fifth more; 0 for a steady pour.', 0, 1, True).startSection = True
custom(page, 'Float', 'Puff', 'Beat Puffs', 0.5,
       'On the beats of input 2 the fluid puffs: it leaps up and churns, the pour flares, and the flames burn hotter '
       '(the smoke glows) for a moment. It lights the whole fluid at once, so it is a flash: Calm allows one a '
       'second (every second or third beat at dance tempos), Up to 3 per second every beat up to 180 BPM, Off '
       'none. 0 turns it off.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a build stirs the fluid into more and more swirls, and a drop sends a big "
       "puff out (a flash, as Beat Puffs; Fosfora's drop detection is experimental).")

# ---- Audio (input 2) ---------------------------------------------------------------------------
section('audio', 'Audio (input 2): puffs on beats and drops, through the flash gate')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
# A beat's puff throws the fluid (bright flames, thick smoke) up at once and makes it flare and glow: a flash,
# so beats and drops pass through the gate (Flashing). Every beat puffing measured 2.0 flashes a second with
# Flashing Off under the stress beat (dev/flash.py on the dancer, Fire), against the clip's 1.0.
ask = mk(comp, renameCHOP, 'ask', [steps], 'Beats and drops, asking to puff.',
         renamefrom='beat_count drop_count', renameto='puff drop')
flash = flash_gate(comp, ask)
puff_sel = mk(comp, selectCHOP, 'puff_sel', [flash], 'Beats that passed the gate.', channames='puff')
mk(comp, triggerCHOP, 'puff_env', [puff_sel],
   "A beat's puff and flare: 1 at the beat, none {:g} s later.".format(PUFF_TIME),
   attack=0, peak=1, peaklen=0, decay=PUFF_TIME, dshape='linear', sustain=0, release=0)
drop_sel = mk(comp, selectCHOP, 'drop_sel', [flash], 'Drops that passed the gate.', channames='drop')
mk(comp, triggerCHOP, 'drop_env', [drop_sel],
   "A drop's big puff: 1 at the drop, none {:g} s later.".format(DROP_TIME),
   attack=0, peak=1, peaklen=0, decay=DROP_TIME, dshape='linear', sustain=0, release=0)
build = mk(comp, selectCHOP, 'build', [audio], "Fosfora's build, 0..1.", channames='build')
mk(comp, lagCHOP, 'build_lag', [build], 'The build, easing out after a drop.',
   lag1=0.5, lag2=2.0, lagunit='seconds')
level = mk(comp, selectCHOP, 'level', [audio], 'Loudness, 0..1.', channames='level')
mk(comp, lagCHOP, 'level_lag', [level], 'Loudness, smoothed (up in 0.1 s, down in 0.8 s).',
   lag1=0.1, lag2=0.8, lagunit='seconds')

# ---- Motion ------------------------------------------------------------------------------------
section('motion', "Motion: the picture's optical flow, as a speed", lane='motion')
mo = optical_flow(comp, _ROOT, source)
still = mk(comp, constantTOP, 'still', comment='Nothing, and still: where the fluid starts, and Reset.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
pace, motion = flow_speed(comp, _ROOT, mo, still)

# ---- Where it emits ------------------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): where the subject is')
depth = depth_in(comp)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black: no reading).', fmt='rgba16float',
            uNear=(menu('Depthtype'), par('Maxdist')))
setpars(near, outputresolution='quarter')
find = glsl(comp, 'find', [near], lib_glsl(_ROOT, 'depth_find.glsl'),
            'In the depth: what stands in front of what lies left and right of it, nearer than a limit (Sensitivity).',
            fmt='rgba16float',
            uFind=(0, STAND_OUT, Expr('max({0} * ({1} / {0}) ** parent().par.Sense, 0 if parent().inputConnectors[2]'
                                      '.connections else {2})'.format(FAR[0], FAR[1], BRIGHT_FAR))))
none = mk(comp, constantTOP, 'none', comment='Black: nothing from input 3 (Emit From is Movement or '
          'Brightness).', outputresolution='custom', resolutionw=1, resolutionh=1, colorr=0, colorg=0, colorb=0,
          alpha=1)
subject = mk(comp, switchTOP, 'subject', [none, find, near],
             'The subject on input 3 for Depth (find), the mask for Mask (near), else nothing: only that one cooks.',
             index=Expr("{'depth': 1, 'mask': 2}.get(parent().par.Emitfrom.eval(), 0)"))
section('emit', 'Where it emits: movement, brightness, depth or the mask', lane='motion')
emit = glsl(comp, 'emit', [motion, source, subject], src('emit.glsl'),
            'Where the picture pours into the fluid: by Emit From and Sensitivity.', fmt='rgba16float',
            uE=(menu('Emitfrom'), par('Sense')))

# ---- The fluid -----------------------------------------------------------------------------------
section('fluid', 'The fluid: velocity advected and made incompressible, the dye carried')
velocity_fb = mk(comp, feedbackTOP, 'velocity_fb', [still], 'The velocity last frame.', top='velocity')
dye_fb = mk(comp, feedbackTOP, 'dye_fb', [still], 'The dye last frame.', top='dye')
advect = glsl(comp, 'advect', [motion, velocity_fb, dye_fb], src('velocity.glsl'),
              "The velocity carried by itself, swirled, risen by the dye, dragged by the motion; a beat's puff "
              'makes it leap and churn.',
              fmt='rgba32float', uT=(DT,),
              uF=(par('Push'),
                  Expr("parent().par.Swirl * {} * {} * (1 + 2 * op('build_lag')[0] * parent().par.Moments) * (1 + {} * "
                       "{})".format(SWIRL_K, per_look(SWIRL), CHURN, BEAT)),
                  Expr('{} + parent().par.Rise + {} * {}'.format(per_look(RISE), LEAP, BEAT)),
                  Expr(per_look(FLOW_HALF))))
divergence, pressure, velocity = incompressible(comp, _ROOT, advect, PASSES)
# Hold: a cell off the edge reads as the edge, so the velocity's differences don't jump there (the default,
# Zero, would; incompressible() holds the divergence's). The pressure keeps Zero: the fluid flows out freely.
setpars(advect, inputextenduv='hold')
dye = glsl(comp, 'dye', [source, dye_fb, velocity, emit], lib_glsl(_ROOT, 'common.glsl') + src('dye.glsl'),
           'What the fluid carries: ink, smoke or heat, carried by the velocity, poured in where the picture emits.',
           fmt='rgba16float',
           uT=(DT, clock_seconds()),
           uD=(Expr("parent().par.Amount * {} * ((1 - parent().par.Loudness + parent().par.Loudness * ({} + {} * "
                    "op('level_lag')[0])) if op('audio')['source'] > 0 else 1) * (1 + {} * parent().par.Puff * "
                    "op('puff_env')[0])".format(POUR, STREAM[0], STREAM[1], FLARE)),
               Expr('{} * 4 ** (2 * parent().par.Linger - 1)'.format(per_look(HALF))), menu('Look'), menu('Color')))
section('look', 'The look: fire, smoke or ink over the picture')
look = glsl(comp, 'look', [source, dye], src('look.glsl'),
            'The dye over the picture as ink, smoke or flames; on a puff the flames burn hotter, the smoke glows.',
            uL=(menu('Look'), par('Backdrop'), Expr("parent().par.Puff * op('puff_env')[0]")))

section('fluid')
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset: the fluid starts again, empty and still.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        for name in ('velocity_fb', 'pressure_fb', 'dye_fb', 'motion_fb'):\n"
              '            op(name).par.resetpulse.pulse()\n')
setpars(reset, op='..', pars='Reset', onpulse=True, valuechange=False)

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
