"""Build Particles. Run from a textport: __file__ = '/path/to/build_particles.py'; exec(open(__file__).read())

Particles peel off the subject and drift away like smoke, in the picture's colors. The subject is
whatever the effect can find: with a depth map or mask on input 3 (a depth camera, a depth
estimator, a segmentation tool), what stands in front of its surroundings; with only a picture (a
webcam, a video), what moves, or what differs from the empty room once Capture Background is
pressed. Find on Auto picks for itself and the Subject view says which it took. Music on input 2
drives them: loudness thickens the stream, each beat fires a burst and kicks the whole cloud
outward, each bar swings the wind; Fosfora's signal adds a build's turbulence and a drop's shockwave.

The network, left to right:
  subject    depth (input 3, or input 1's brightness) -> near (small, as nearness; Depth Type flips a
             depth camera's distance; depth_stats: is there any depth?) -> find (nearer than Far Limit
             and, on Stand Out, than what lies left and right in the row); source -> small -> motion
             (what moves, against a background a couple of seconds behind) and plate (the empty room
             at Capture Background, counted by captures; gain, gain_sum and drift: the camera's
             exposure drift since, from a histogram; plate_in and drift_in pass them only for
             Background, so the chain cooks only then); subject picks one by Find -> emit (where
             particles are born; emit_stats averages it) and subject_blur (which way is out)
  particles  sim: up to PW x PH particles in three float buffers (sim, then sim_life and sim_color
             picked out by Render Select TOPs), read back through Feedback TOPs; alive_stats counts
             the living, so births come to the rate asked for
  drawing    geo instances a square (dot is its texture, dot_mat adds them up) at every particle,
             placed, scaled and colored from the buffers; cam looks at it flat; render draws it at the
             picture's size; glow blurs it; look lays both over the picture, or shows the subject
  audio      audio_in() -> counts -> steps (Slope CHOP) -> beat_env (bursts and kicks) and drop_env
             (the shockwave); level_lag (the stream), gust -> gust_lag (the wind's swing on each
             bar), build_lag (turbulence)
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# The particles' buffers: at most PW x PH alive at once.
PW, PH = 256, 256
# The subject is found on a small copy of the picture and the depth: the row search in find.glsl
# reads a whole row per pixel, and particles are born across a pixel, so finer would cost more and
# show nothing.
MW, MH = 320, 180
# A beat's burst: births per second on top of Rate at its peak (Beat Bursts at 1), falling to none
# over BURST_TIME seconds; particles born in it leave up to 3 times as fast.
BURST_RATE, BURST_TIME = 20000, 0.25
# A drop's shockwave: a ring that leaves the subject's middle and reaches WAVE_REACH frame heights
# in WAVE_TIME seconds, shoving less as it goes.
WAVE_REACH, WAVE_TIME = 1.4, 1.2
# Loudness (0-1 from audio_in) scales Rate by STREAM[0] + STREAM[1] x loudness, at Loudness 1. Raw
# audio's loudness sits high (it is measured against its own recent peak): median 0.56-0.67, 90th
# percentile 0.83-0.90 on the library's two songs (dev/probes/level_stats.py), so a typical passage
# stays near Rate, quiet ones thin out to a third and the loudest go a fifth over.
STREAM = (0.3, 0.9)
# Each bar the wind swings to GUST_ANGLE x sin(bar x 2.4) radians from straight up (about 35 degrees
# either way at Gusts 1, a new angle each bar), easing there over GUST_EASE seconds.
GUST_ANGLE, GUST_EASE = 0.6, 0.6
# Sensitivity 0..1 sets how far from the background (Movement) or the empty room (Background) a pixel
# must be to count: SENSE[0] luma at 0, SENSE[1] at 1 (a webcam's noise is a few hundredths).
SENSE = (0.15, 0.02)
# The Subject view's labels, by subject.glsl's code: how the subject was found.
LABELS = (
    'AUTO: DEPTH ON INPUT 3 - STAND OUT',
    'AUTO: NO DEPTH ON INPUT 3 - MOVEMENT',
    'DEPTH ON INPUT 3 - STAND OUT',
    'DEPTH ON INPUT 3 - NEARER THAN FAR LIMIT',
    'NO DEPTH: BRIGHTNESS AS DEPTH - STAND OUT',
    'NO DEPTH: BRIGHTNESS AS DEPTH - NEARER THAN FAR LIMIT',
    'MOVEMENT',
    'BACKGROUND',
    'BACKGROUND: PRESS CAPTURE BACKGROUND - MOVEMENT TILL THEN',
    'INPUT 3 IS ALL BLACK - NOTHING FOUND',
    'AUTO: SAMPLE MOVIE - BRIGHTNESS AS DEPTH, STAND OUT',
)
DT = Expr('absTime.stepSeconds')


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu(name):
    return Expr('parent().par.{}.menuIndex'.format(name))


def choices(p, names, labels, default):
    p.menuNames, p.menuLabels = names, labels
    p.default = p.val = default
    return p


def labels_head():
    """The Subject view's labels for look.glsl, in the library's font."""
    font = lib_module(_ROOT, 'font5x7')
    at = [sum(len(t) for t in LABELS[:k]) for k in range(len(LABELS))]
    return ('#define N_LABELS {}\n'.format(len(LABELS)) + font['glsl_font']() + font['glsl_ints']('LABELS', ''.join(LABELS))
            + 'const int LABEL_AT[{0}] = int[]({1});\nconst int LABEL_LEN[{0}] = int[]({2});\n'.format(
                len(LABELS), ', '.join(map(str, at)), ', '.join(str(len(t)) for t in LABELS)))


README = src('readme.txt').format(v=VERSION, n=PW * PH)
comp, page, source = new_effect(
    'particles', 'Particles',
    'Particles {}: particles peel off the subject (found by depth on input 3, or by movement) and drift '
    'away like smoke; the music thickens, kicks and sways them.'.format(VERSION),
    README, tags=('particles', 'depth', 'interactive', 'audio-reactive'), audio=True, depth=True,
    # A white birch among dark leaves (TouchDesigner's own sample): Auto reads its brightness as depth
    # while it shows (the sample movies barely move), and the trunk stands out from what is beside it.
    sample="app.samplesFolder + '/Map/Nature/Movie.5.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
choices(custom(page, 'Menu', 'Show', 'Show', None,
               'Particles: the effect. Subject: what the particles come from (orange; the depth beside it in '
               'blue), over the dimmed picture, with a label saying how it was found: for tuning Find and the '
               'settings under it.'),
        ['particles', 'subject'], ['Particles', 'Subject'], 'particles')
find = choices(custom(page, 'Menu', 'Find', 'Find', None,
                      'What the particles come from. Auto: the depth on input 3 (Stand Out) when it carries any, '
                      'else what moves. Stand Out: what is nearer than Far Limit and than what lies to its left and '
                      'right, which leaves out floors and walls. Nearer Than Far Limit: everything nearer, for a mask '
                      'or a camera that sees no floor. (Both read input 1\'s brightness as depth when nothing is on '
                      'input 3.) Movement: what moves. Background: what differs from the empty room; press Capture '
                      'Background with the subject out of the frame.'),
               ['auto', 'standout', 'nearer', 'movement', 'background'],
               ['Auto', 'Stand Out', 'Nearer Than Far Limit', 'Movement', 'Background'], 'auto')
find.startSection = True
custom(page, 'Pulse', 'Capture', 'Capture Background', None,
       "For Find on Background: with the subject out of the frame, press this to keep input 1's picture as "
       'the empty room. The effect never opens a camera itself: wire one (Video Device In) into input 1. Press '
       'it again after the camera or the light changes.').enableExpr = "me.par.Find == 'background'"
custom(page, 'Float', 'Sense', 'Sensitivity', 0.5,
       'For Movement and Background (and Auto with no depth): how small a change counts. Raise it to catch '
       'slight movement; lower it if a still picture or camera noise emits.', 0, 1, True).enableExpr = \
    "me.par.Find in ('auto', 'movement', 'background')"
custom(page, 'Float', 'Standout', 'Stand Out', 0.08,
       'How much nearer than what lies to its left and right something must be to count, 0-1 of the depth '
       'range.', 0, 0.3, True).enableExpr = "me.par.Find in ('auto', 'standout')"
custom(page, 'Float', 'Far', 'Far Limit', 0.5,
       'Anything farther than this never counts, 0 (farthest) to 1 (nearest). Raise it to drop the background, '
       'lower it if parts of the subject go missing.', 0, 1, True).enableExpr = "me.par.Find in ('auto', 'standout', 'nearer')"
choices(custom(page, 'Menu', 'Depthtype', 'Depth Type', None,
               'What input 3 holds. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance '
               '0-1: the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left '
               'out). Distance in Meters: the Kinect Azure TOP, scaled by Max Distance.'),
        ['nearness', 'distance', 'meters'],
        ['Brighter Is Nearer', 'Distance 0-1 (RealSense, Kinect)', 'Distance in Meters (Kinect Azure)'],
        'nearness').enableExpr = "me.par.Find in ('auto', 'standout', 'nearer')"
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth (Far Limit and '
       'Stand Out are fractions of it).', 0.5, 15, True).enableExpr = "me.par.Depthtype == 'meters'"

emitfrom = choices(custom(page, 'Menu', 'Emitfrom', 'Emit From', None,
                          'Where particles are born: anywhere on the subject (Body) or only along its edges '
                          '(Outline).'),
                   ['body', 'outline'], ['Body', 'Outline'], 'body')
emitfrom.startSection = True
custom(page, 'Float', 'Rate', 'Rate', 5000,
       'Particles born per second (at most {:,} alive at once).'.format(PW * PH), 0, 30000, True)
custom(page, 'Float', 'Life', 'Life', 2.5, 'How long a particle lives, in seconds (each one a little more or less).',
       0.2, 8, True)
custom(page, 'Float', 'Size', 'Size', 3, 'Size of a particle in pixels at 720 high (scales with the picture).',
       1, 16, True)
custom(page, 'Float', 'Speed', 'Speed', 0.15, 'How fast particles leave the subject, in frame heights per second.',
       0, 1, True)
custom(page, 'Float', 'Drift', 'Drift', 0.1,
       'How fast the air carries particles up, in frame heights per second; below 0, down.', -0.5, 0.5, True)
custom(page, 'Float', 'Turbulence', 'Turbulence', 0.5, 'How much the air swirls the particles around.', 0, 2, True)

color = choices(custom(page, 'Menu', 'Color', 'Color', None,
                       "Particles take the picture's color where they are born (lifted, so dark clothes still "
                       'glow), or one color.'),
                ['picture', 'orange', 'blue', 'white'], ['Picture', 'Orange', 'Blue', 'White'], 'picture')
color.startSection = True
custom(page, 'Float', 'Glow', 'Glow', 0.5, 'How much the particles glow around themselves, 0-1.', 0, 1, True)
custom(page, 'Float', 'Backdrop', 'Backdrop', 0.6, 'How bright the picture behind the particles is, 0 (black) to 1.',
       0, 1, True)

custom(page, 'Float', 'Loudness', 'Loudness', 0.7,
       'How much the loudness of input 2 thickens and thins the stream: at 1, quiet passages emit a '
       'third of Rate and the loudest a fifth more; 0 for a steady Rate.', 0, 1, True).startSection = True
custom(page, 'Float', 'Burst', 'Beat Bursts', 0.5,
       'On each beat of input 2, a burst of particles leaves the subject faster than the rest and the whole '
       'cloud is kicked outward; 0 for neither.', 0, 1, True)
custom(page, 'Float', 'Gusts', 'Bar Gusts', 0.5,
       'On each bar of input 2 (every 4 beats when it has no bars), the wind swings to a new direction; '
       '0 keeps it blowing the same way.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a build stirs the air up as it rises, and a drop sends a shockwave "
       "out from the subject (Fosfora's drop detection is experimental).")

# ---- Audio (input 2) ---------------------------------------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -400, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', -200, -350, [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beat_step = mk(comp, selectCHOP, 'beat_step', 0, -300, [steps], 'A beat.', channames='beat_count')
beat_env = mk(comp, triggerCHOP, 'beat_env', 200, -300, [beat_step],
              "A beat's burst: 1 at the beat, none {:g} s later.".format(BURST_TIME),
              attack=0, peak=1, peaklen=0, decay=BURST_TIME, dshape='linear', sustain=0, release=0)
drop_step = mk(comp, selectCHOP, 'drop_step', 0, -450, [steps], 'A drop.', channames='drop_count')
drop_env = mk(comp, triggerCHOP, 'drop_env', 200, -450, [drop_step],
              "A drop's shockwave: 1 as it leaves the subject, 0 when it is {:g} frame heights out, {:g} s "
              'later.'.format(WAVE_REACH, WAVE_TIME),
              attack=0, peak=1, peaklen=0, decay=WAVE_TIME, dshape='linear', sustain=0, release=0)
build = mk(comp, selectCHOP, 'build', 0, -600, [audio], "Fosfora's build, 0..1.", channames='build')
build_lag = mk(comp, lagCHOP, 'build_lag', 200, -600, [build], 'The build, easing out after a drop.',
               lag1=0.5, lag2=2.0, lagunit='seconds')
level = mk(comp, selectCHOP, 'level', 0, -750, [audio], 'Loudness, 0..1.', channames='level')
level_lag = mk(comp, lagCHOP, 'level_lag', 200, -750, [level], 'Loudness, smoothed (up in 0.1 s, down in 0.8 s).',
               lag1=0.1, lag2=0.8, lagunit='seconds')
gust = mk(comp, constantCHOP, 'gust', 0, -900, comment="The wind's angle for this bar, from straight up (radians).",
          const0name='angle', const0value=Expr("math.sin(op('audio')['bar_count'] * 2.4) * {} * parent().par.Gusts"
                                               .format(GUST_ANGLE)))
gust_lag = mk(comp, lagCHOP, 'gust_lag', 200, -900, [gust], 'The wind easing to its new angle over {:g} s.'.format(GUST_EASE),
              lag1=GUST_EASE, lag2=GUST_EASE, lagunit='seconds')

# ---- The subject ---------------------------------------------------------------------------------
depth = depth_in(comp, x=-600, y=-1100)
near = glsl(comp, 'near', -400, -1100, [depth], src('near.glsl'),
            'The depth, {} x {}, as nearness; Depth Type flips distance (black: no reading).'.format(MW, MH),
            res=(MW, MH), fmt='rgba16float', uNear=(menu('Depthtype'), par('Maxdist')))
depth_stats = mk(comp, analyzeTOP, 'depth_stats', -400, -1250, [near],
                 'The nearest reading in the depth: none (black) means input 3 carries no depth.',
                 op='maximum', analyzechannel='independent', format='rgba16float')
people = glsl(comp, 'find', -200, -1100, [near], src('find.glsl'),
              'In the depth: nearer than Far Limit and (Stand Out) than what lies left and right of it.',
              res=(MW, MH), fmt='rgba16float',
              uFind=(Expr("1 if parent().par.Find == 'nearer' else 0"), par('Standout'), par('Far')))
small = glsl(comp, 'small', -400, -1450, [source], src('small.glsl'),
             'The picture, {} x {}, for Movement and Background.'.format(MW, MH), res=(MW, MH), fmt='rgba16float')
motion_start = mk(comp, constantTOP, 'motion_start', -400, -1600, comment="motion's starting state: no frame yet.",
                  outputresolution='custom', resolutionw=MW, resolutionh=MH, format='rgba32float',
                  colorr=0, colorg=0, colorb=0, alpha=-1)
motion_fb = mk(comp, feedbackTOP, 'motion_fb', -200, -1600, [motion_start], "motion's last frame.", top='motion')
motion = glsl(comp, 'motion', -200, -1450, [small, motion_fb], src('motion.glsl'),
              'What moves: the picture against a background a couple of seconds behind (Movement).',
              res=(MW, MH), fmt='rgba32float',
              uMotion=(DT, Expr('{} + ({} - {}) * parent().par.Sense'.format(SENSE[0], SENSE[1], SENSE[0]))))
captures = mk(comp, constantCHOP, 'captures', -200, -1750, comment='How many times Capture Background has been pressed.',
              const0name='count', const0value=0)
capture_exec = mk(comp, parameterexecuteDAT, 'capture_exec', 0, -1750,
                  comment='Capture Background: counts the press, and plate keeps the picture for that count.')
capture_exec.text = ('def onPulse(par):\n'
                     "    if par.name == 'Capture':\n"
                     "        n = op('captures').par.const0value\n"
                     '        n.val = n.eval() + 1\n')
setpars(capture_exec, op='..', pars='Capture', onpulse=True, valuechange=False)
plate_start = mk(comp, constantTOP, 'plate_start', 0, -1600, comment="plate's starting state: nothing captured.",
                 outputresolution='custom', resolutionw=MW, resolutionh=MH, format='rgba32float',
                 colorr=0, colorg=0, colorb=0, alpha=0)
plate_fb = mk(comp, feedbackTOP, 'plate_fb', 200, -1600, [plate_start], "plate's last frame.", top='plate')
plate = glsl(comp, 'plate', 0, -1450, [small, plate_fb], src('plate.glsl'),
             'The empty room: the picture when Capture Background was last pressed (Background).',
             res=(MW, MH), fmt='rgba32float', uPlate=(Expr("op('captures')['count']"),))
gain = glsl(comp, 'gain', 200, -1450, [small, plate], src('gain.glsl'),
            "How much brighter the picture is than the empty room: a 64-bin histogram, row by row.",
            res=(64, MH // 2), fmt='rgba32float')
gain_sum = glsl(comp, 'gain_sum', 400, -1450, [gain], src('gain_sum.glsl'), "The histogram's rows added up.",
                res=(64, 1), fmt='rgba32float')
drift = glsl(comp, 'drift', 600, -1450, [gain_sum], src('drift.glsl'),
             "The camera's exposure drift since the capture: the histogram's tallest bin (the room).",
             res=(1, 1), fmt='rgba32float')
# Only Find on Background needs the empty room and the drift: these Switch TOPs show black otherwise,
# and a Switch TOP cooks only what it shows, so none of that chain runs in the other modes.
BACKGROUND = Expr("1 if parent().par.Find == 'background' else 0")
none = mk(comp, constantTOP, 'none', 400, -1750, comment='Black: no empty room, no drift (Find is not Background).',
          outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
plate_in = mk(comp, switchTOP, 'plate_in', 400, -1300, [none, plate], 'The empty room, while Find is Background.',
              index=BACKGROUND)
drift_in = mk(comp, switchTOP, 'drift_in', 800, -1450, [none, drift], 'The drift, while Find is Background.',
              index=BACKGROUND)
subject = glsl(comp, 'subject', 0, -1100, [people, motion, plate_in, small, depth_stats, drift_in], src('subject.glsl'),
               'The subject, as Find says: the depth, what moves, or what differs from the empty room.',
               res=(MW, MH), fmt='rgba16float',
               uFind=(menu('Find'), Expr('1 if parent().inputConnectors[2].connections else 0'),
                      Expr('{} + ({} - {}) * parent().par.Sense'.format(SENSE[0], SENSE[1], SENSE[0])),
                      Expr('1 if parent().inputConnectors[0].connections else 0')))
emit = glsl(comp, 'emit', 200, -1100, [subject], src('emit.glsl'), 'Where particles may be born: the subject, its outline.',
            res=(MW, MH), fmt='rgba32float')
emit_stats = mk(comp, analyzeTOP, 'emit_stats', 400, -1100, [emit],
                'How much of the frame the subject and its outline cover, and their middle (the average of emit).',
                op='average', analyzechannel='independent', format='rgba32float')
subject_blur = mk(comp, blurTOP, 'subject_blur', 200, -1250, [subject],
                  'The subject, blurred: particles leave it down its slope, outward.', size=8)

# ---- The particles ---------------------------------------------------------------------------------
empty = mk(comp, constantTOP, 'empty', -200, 300, comment="The particles' starting state: every one free.",
           outputresolution='custom', resolutionw=PW, resolutionh=PH, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
fb = [mk(comp, feedbackTOP, name + '_fb', 0, y, [empty], "{}'s last frame.".format(name), top=name)
      for name, y in (('sim', 450), ('sim_life', 300), ('sim_color', 150))]
alive = mk(comp, analyzeTOP, 'alive_stats', 200, 600, [fb[1]], 'How many particles were alive last frame (a).',
           op='average', analyzechannel='independent', format='rgba32float')
sim = glsl(comp, 'sim', 400, 300, fb + [emit, subject_blur, source, alive, emit_stats], src('sim.glsl'),
           'The particles: born on the subject, carried by the air, the turbulence and the music.',
           res=(PW, PH), fmt='rgba32float',
           uClock=(DT, Expr('absTime.seconds'), Expr('absTime.frame % 16777216'),
                   Expr("op('source').width / max(1, op('source').height)")),
           uEmit=(Expr("(parent().par.Rate * ((1 - parent().par.Loudness + parent().par.Loudness * ({} + {} * op('level_lag')[0]))"
                       " if op('audio')['source'] > 0 else 1) + {} * parent().par.Burst * op('beat_env')[0])"
                       " * min(absTime.stepSeconds, 0.1)".format(STREAM[0], STREAM[1], BURST_RATE)),
                  par('Life'), par('Speed'), Expr("1 if parent().par.Emitfrom == 'outline' else 0")),
           uMove=(par('Drift'), Expr("parent().par.Turbulence * (1 + 2 * op('build_lag')[0] * parent().par.Moments)"),
                  Expr('parent().par.Size / 720'), Expr("op('beat_env')[0] * parent().par.Burst")),
           uWave=(Expr("(1 - op('drop_env')[0]) * {}".format(WAVE_REACH)), Expr("op('drop_env')[0] * parent().par.Moments"),
                  Expr("op('gust_lag')[0]")),
           uLook=(menu('Color'),))
setpars(sim, numcolorbufs=3)
for name, i, y, what in (('sim_life', 1, 300, 'age, life, size, alive'), ('sim_color', 2, 150, 'color and how visible')):
    mk(comp, renderselectTOP, name, 600, y, comment="sim's buffer {}: each particle's {}.".format(i, what),
       top='sim', bufferindex=i)

# ---- Drawing -------------------------------------------------------------------------------------
dot = mk(comp, circleTOP, 'dot', 600, -100, comment='One particle: a soft white dot.',
         outputresolution='custom', resolutionw=32, resolutionh=32, radiusx=0.45, radiusy=0.45, radiusunit='fraction',
         softness=0.35, softnessunit='fraction', fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1,
         bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=0, borderwidth=0)
mk(comp, constantMAT, 'dot_mat', 800, -100, comment='The dot, its color from the particle, added onto what is drawn.',
   colormap='dot', blending=True, srcblend='one', destblend='one', depthtest=False, depthwriting=False)
geo = mk(comp, geometryCOMP, 'geo', 800, 300, comment="A dot at every particle: instancing reads sim's buffers.",
         instancing=True, instancecountmode='oplength', instanceop='sim', instancetx='r', instancety='g',
         instancesop='sim_life', instancesx='b', instancesy='b', instancecolorop='sim_color', instancer='r',
         instanceg='g', instanceb='b', instancea='a', instancecolorpremult='premultinshader', material='dot_mat')
for o in list(geo.children):             # a new Geometry COMP holds a torus
    o.destroy()
quad = mk(geo, rectangleSOP, 'quad', 0, 0, comment='A square one unit across, which instancing scales to Size.',
          sizex=1, sizey=1, texture='face')
quad.render = quad.display = True
cam = mk(comp, cameraCOMP, 'cam', 800, 450, comment='Looks straight at the particles, flat: one frame height tall.',
   projection='ortho', orthowidth=Expr("op('source').width / max(1, op('source').height)"), tz=5)
# A new Camera COMP holds a File In POP (its own picture in the viewer); nothing here draws it.
for o in list(cam.children):
    o.destroy()
render = mk(comp, renderTOP, 'render', 1000, 300, comment='The particles, drawn at the picture size.',
            camera='cam', geometry='geo', lights='', bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=0,
            format='rgba16float', outputresolution='custom', resolutionw=Expr("op('source').width"),
            resolutionh=Expr("op('source').height"))
glow = mk(comp, blurTOP, 'glow', 1200, 150, [render], 'The particles blurred, half size: their glow.',
          size=12, outputresolution='half')
look = glsl(comp, 'look', 1400, 0, [source, render, glow, subject], labels_head() + src('look.glsl'),
            'The particles and their glow over the picture (Backdrop), or the subject and how it was found (Show).',
            uLook=(par('Backdrop'), par('Glow'), menu('Show')))

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
