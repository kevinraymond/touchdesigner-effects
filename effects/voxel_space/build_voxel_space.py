"""Build Voxel Space. Run from a textport: __file__ = '/path/to/build_voxel_space.py'; exec(open(__file__).read())

The picture as the terrain of Comanche (NovaLogic, 1992), flown over: its depth (input 3, or its brightness) the height
map and its colors the color map, drawn a screen column at a time front to back with a y-buffer, as Kyle Freeman's
Voxel Space drew it (US 5,550,959 and 6,020,893, expired; board #4745). A depth map is brightest where the floor runs up
to the camera, so the heights are each row's nearness above its own far baseline: the floor and the far wall lie flat
and whatever stands in front of them stands up. The heights and the colors ease toward the picture's together with a
leak, a low sun lights the hills, and the music lifts them (the bass), dips the camera (each beat, through the flash
gate) and sets the pace (the tempo). Seen in perspective the near ground is the picture enlarged, so the land eases
over a quarter of a second, cliff faces take their tops' colors and the camera flies slowly, slower still zoomed in:
each of those was a flash a second more than the clip (board #4746). Brightness standing in for depth is softened first, or its fine detail
bristled into spikes that shimmered in flight, and every pixel goes through the red guard, since the land sweeps reds
back and forth. Position, Altitude, Yaw, Pitch, Roll and Zoom move and turn each flight's camera, eased; Pitch and Roll
move and slant the horizon, as Comanche's did, since a view drawn in columns keeps upright things upright.

dev/protos/voxel_space/offline.py tried it first on the clips with a song.

The network, left to right:
  picture  source -> colors (colors_fb: the picture eased) -> render (a compute shader: a workgroup a column, the
           y-buffer a running minimum) -> out
  terrain  near -> rows (each row's baseline and reach) -> span (the tallest row's, eased) -> relief (the heights,
           0-1) -> smooth -> ease (ease_fb) -> terrain (height, light)
  flight   flight_size -> flight (the camera, the camera's settings eased, flight_fb; mean is the picture's mean
           color, for the sky)
  audio    audio_in() -> lows -> lows_mean -> lows_now -> lows_usual (the low end over a second, its usual level);
           counts -> steps -> flash_gate() -> dip_env (a beat's dip); steps -> tempo -> pace_ask -> pace; drive (the
           lift and the dip)
  depth    depth_in() (input 3, or depth_guess -> depth_soft: the brightness softened) -> near (lib depth_near.glsl,
           half size)
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
FLIGHTS = (('fly', 'Fly'), ('orbit', 'Orbit'), ('hover', 'Hover'))
WORLD = 1024.0        # the picture's width in world units, whatever its size (render.glsl, flight.glsl)
PEAK = 180.0          # the terrain's tallest at Height 1, in world units
LIFT = 0.8            # the bass lifts it by up to this share
TAN_HALF = math.tan(0.8)   # the view is 92 degrees wide, as Comanche's was about 90
# render.glsl's 512 steps: each 0.5 + 0.007 x its distance longer than the last, from 1 unit out to about 2490.
STEP0, STEP_GROW = 0.5, 0.007
Z_C = STEP0 / STEP_GROW
Z_A, Z_B = 1.0 + Z_C, math.log(1.0 + STEP_GROW)
FAR = Z_A * math.exp(Z_B * 511) - Z_C
ROWS = 256            # rows.glsl's bands of rows
EASE = 0.25           # s the heights and the colors take to follow the picture (most of the way)
CAMERA = 0.3          # s Position, Altitude, Yaw, Pitch, Roll and Zoom take to follow their settings (most of the way)
SETTLE = 0.1          # s the view eases over, a quarter of that at a dip's deepest (it smeared each dip into a blur)
SOFT = 6              # the brightness standing in for depth, blurred at a quarter size (about 24 pixels at 1280)
SLOW, USUAL = 1.0, 4.0     # the bass smoothed over SLOW s, its usual level over USUAL s
DIP = (0.25, 0.5)     # a beat's dip: down in DIP[0] s, back up over DIP[1] s
TEMPO = 6.0           # s of beats the tempo is counted over
PERF = '1.7'          # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


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


def pair(page, name, label, help_text, lo, hi):
    """An XY parameter, both halves 0 by default, between lo and hi; returns its first half."""
    pars = page.appendXY(name, label=label)
    for p in pars:
        p.default = p.val = 0.0
        p.normMin, p.min, p.clampMin = lo, lo, True
        p.normMax, p.max, p.clampMax = hi, hi, True
        p.help = help_text
    return pars[0]


README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'voxel_space', 'Voxel Space',
    'Voxel Space {}: the picture as the terrain of Comanche (1992), its depth the hills and its colors the land, '
    'flown over to the music.'.format(VERSION),
    README, tags=('voxel-space', 'terrain', 'comanche', 'heightmap', 'retro', 'audio-reactive', 'depth'), audio=True,
    flashing=True, depth=True, sample="app.samplesFolder + '/Map/Nature/Movie.1.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Flight', 'Flight', FLIGHTS, 'fly',
     'How the camera flies. Fly goes forward over the picture, repeated mirrored at its edges, weaving along the seam '
     'where it meets its mirror image, banking into its turns and keeping clear of the hills ahead, as the helicopter '
     'in Comanche flew. Orbit circles the picture, '
     'an island in a flat sea, looking down at it. Hover stands off its near edge and looks across it, swaying from '
     'side to side.')
custom(page, 'Float', 'Speed', 'Speed', 1.0,
       'How fast the camera flies, circles or sways, 0-2, faster with a faster tempo on input 2. 0 holds it still.',
       0, 2, True)
custom(page, 'Float', 'Height', 'Height', 1.0,
       "How tall the hills stand, 0-2. The terrain's tallest is about a sixth of the picture's width at 1.", 0, 2, True)
custom(page, 'Float', 'Smooth', 'Smooth', 0.4,
       'How rounded the hills are, 0-1: 0 keeps every edge of the depth (cliffs and spires), 1 rolls them into '
       'gentle hills.', 0, 1, True)
custom(page, 'Float', 'Light', 'Light', 0.7,
       "How much a low sun from the left shades the hills, 0-1. Flat ground keeps the picture's own colors.", 0, 1,
       True)
custom(page, 'Float', 'Fog', 'Fog', 0.5,
       'How soon the distance fades into the sky, 0-1. 0 fades only the farthest ground.', 0, 1, True)
pair(page, 'Position', 'Position',
     'Where the camera is, moved across the land from where the flight puts it: x across the picture and y up it, in '
     'its widths and heights, -1 to 1. With Speed at 0 it places a still camera.', -1, 1).startSection = True
custom(page, 'Float', 'Altitude', 'Altitude', 1.0,
       'How high the camera is above the ground, 0-3: 1 where the flight puts it, 2 twice as high, 0 just above the '
       'ground (in Fly, the hills ahead).', 0, 3, True)
custom(page, 'Float', 'Yaw', 'Yaw', 0.0,
       'Which way the camera looks, turned from where the flight points it, in degrees: positive to the right, 180 '
       'behind.', -180, 180, True)
custom(page, 'Float', 'Pitch', 'Pitch', 0.0,
       "How far the camera looks up (positive) or down from the flight's own view, in degrees. As in Comanche it "
       'moves the horizon rather than tilting the view, so upright things stay upright.', -45, 45, True)
custom(page, 'Float', 'Roll', 'Roll', 0.0,
       "How far the view banks, in degrees, on top of Fly's banking into its turns: positive banks to the right. As "
       'in Comanche it slants the horizon and keeps upright things upright.', -30, 30, True)
custom(page, 'Float', 'Zoom', 'Zoom', 1.0,
       "How near the lens brings the land, 0.5-4: 1 is Comanche's view, about 92 degrees wide, 2 shows half as much "
       'and 0.5 twice as much. Above 1 the flight slows to match, so the land crosses the view at the same pace.',
       0.5, 4, True)
p = custom(page, 'Float', 'Basslift', 'Bass Lift', 0.5,
           "How much the bass on input 2 lifts the hills, 0-1, smoothed over a second and more while it's above its "
           'usual level.', 0, 1, True)
p.startSection = True
custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'How far each beat on input 2 dips the camera, 0-1, down over a quarter of a second and back up over half a '
       'second, as often as Flashing allows.', 0, 1, True)
menu(page, 'Depthtype', 'Depth Type',
     (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
      ('meters', 'Distance in Meters (Kinect Azure)')), 'nearness',
     'What input 3 holds. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance 0-1: the RealSense '
     'and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left flat). Distance in Meters: the '
     "Kinect Azure TOP, scaled by Max Distance. With nothing on input 3 the picture's brightness is the height."
     ).startSection = True
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

# ---- Audio (input 2): the bass's lift, a dip on each beat, the tempo's pace ---------------------
section('audio', "Audio (input 2): the bass lifting the hills, each beat dipping the camera, the tempo setting the pace")
audio = audio_in(comp, _ROOT)
WIRED = "op('audio')['source'].eval() > 0"
lows = mk(comp, selectCHOP, 'lows', [audio], 'The sub bass and the bass.', channames='sub_bass bass')
lows_mean = mk(comp, mathCHOP, 'lows_mean', [lows], 'The two averaged: the low end.', chopop='average')
lows_now = mk(comp, filterCHOP, 'lows_now', [lows_mean], 'The low end smoothed over {:g} s.'.format(SLOW), width=SLOW)
lows_usual = mk(comp, filterCHOP, 'lows_usual', [lows_now],
                "The low end's usual level: its average over the last {:g} s.".format(USUAL), type='box', width=USUAL)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
flash = flash_gate(comp, steps)
dip_env = mk(comp, triggerCHOP, 'dip_env', [flash],
             'A beat\'s dip: down in {:g} s, back up over {:g} s.'.format(*DIP), attack=DIP[0], peak=1, decay=DIP[1],
             sustain=0, release=0)
tempo = mk(comp, filterCHOP, 'tempo', [steps],
           'Beats a second, counted over the last {:g} s.'.format(TEMPO), type='box', width=TEMPO)
pace_ask = mk(comp, constantCHOP, 'pace_ask',
              comment='The pace the tempo asks for: 1 at 120 BPM, between 0.75 and 1.3, 1 without beats.',
              const0name='pace', const0value=Expr("min(max(op('tempo')[0] / 2, 0.75), 1.3) if op('tempo')[0] > 0.5 "
                                                  'else 1'))
pace = mk(comp, filterCHOP, 'pace', [pace_ask], 'The pace, eased over 2 s.', width=2.0)
drive = mk(comp, constantCHOP, 'drive', comment="What the terrain and the camera read: the bass's lift and a beat's "
           'dip, each 0-1.')
LIFT_EXPR = ("parent().par.Basslift * min(0.5 * op('lows_now')[0] + 1.5 * max(op('lows_now')[0] - "
             "op('lows_usual')[0], 0), 1) if {} else 0".format(WIRED))
drive.seq.const.numBlocks = 2
setpars(drive, const0name='lift', const0value=Expr(LIFT_EXPR), const1name='dip',
        const1value=Expr("parent().par.Kick * op('dip_env')[0]"))
HEIGHT = Expr("{} * parent().par.Height * (1 + {} * op('drive')['lift'])".format(PEAK, LIFT))
DT = Expr('min(absTime.stepSeconds, 0.1)')

# ---- Depth (input 3): nearness at half size --------------------------------------------------------
section('depth', "Depth (input 3), or the picture's brightness softened: nearness at half size")
guess = mk(comp, monochromeTOP, 'depth_guess', [source],
           "Input 1's brightness at a quarter size, standing in for depth while nothing is wired into input 3.",
           outputresolution='quarter')
soft = mk(comp, blurTOP, 'depth_soft', [guess], "The brightness softened: its fine detail stays in the land's colors "
          'instead of bristling as spikes, which shimmered in flight.', type='gaussian', size=SOFT)
depth = depth_in(comp, soft)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at half size, as nearness; Depth Type flips distance (black: no reading).', fmt='rgba16float',
            uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='half')

# ---- The terrain ----------------------------------------------------------------------------------
section('terrain', "The terrain: each row's nearness above its far baseline, smoothed, eased and lit", lane='terrain')
rows = glsl(comp, 'rows', [near], src('rows.glsl'),
            "Each band of rows' far baseline (its 12th percentile) and how far above it the row reaches.",
            res=(1, ROWS), fmt='rgba32float')
span_size = mk(comp, constantTOP, 'span_size', comment='One pixel: the size of span.', outputresolution='custom',
               resolutionw=1, resolutionh=1, format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=1)
span_fb = mk(comp, feedbackTOP, 'span_fb', [span_size], "span's last frame.", top='span')
span = glsl(comp, 'span', [rows, span_fb], src('span.glsl'),
            "How far the tallest row reaches above its baseline, eased over 1.5 s: the terrain's scale.",
            res=(1, 1), fmt='rgba32float', uS=(DT,))
relief = glsl(comp, 'relief', [near, rows, span], src('relief.glsl'),
              "The heights, 0-1: nearness above the row's baseline over the span; an island's shore in Orbit.",
              fmt='rgba16float', uR=(Expr("1 if parent().par.Flight == 'orbit' else 0"),))
smooth = mk(comp, blurTOP, 'smooth', [relief], 'The hills rounded by Smooth.', type='gaussian',
            size=Expr('max(0.01, parent().par.Smooth * 20)'))
ease_fb = mk(comp, feedbackTOP, 'ease_fb', [smooth], "ease's last frame.", top='ease')
ease = glsl(comp, 'ease', [smooth, ease_fb], src('ease.glsl'),
            "The heights eased toward the picture's over {:g} s, as the colors are.".format(EASE),
            fmt='rgba16float', uE=(DT, EASE))
terrain = glsl(comp, 'terrain', [ease], src('terrain.glsl'),
               'The terrain: its height and the light of a low sun on it.', fmt='rgba16float',
               uT=(HEIGHT, WORLD, par('Light')))

# ---- The flight ----------------------------------------------------------------------------------
section('flight', 'The flight: where the camera is, where it looks and the sky behind the hills', lane='flight')
mean = mk(comp, analyzeTOP, 'mean', [source], "The picture's mean color, for the sky.", op='average',
          analyzechannel='independent', format='rgba32float')
flight_size = mk(comp, constantTOP, 'flight_size', comment='Five pixels: the size of flight.',
                 outputresolution='custom', resolutionw=5, resolutionh=1, format='rgba32float', colorr=0, colorg=0,
                 colorb=0, alpha=0)
flight_fb = mk(comp, feedbackTOP, 'flight_fb', [flight_size], "flight's last frame.", top='flight')
flight = glsl(comp, 'flight', [flight_size, flight_fb, source, terrain, mean], src('flight.glsl'),
              "The camera: where it is, its heading, height, horizon and roll, the sky's color, and Position to "
              'Zoom eased over {:g} s.'.format(CAMERA), fmt='rgba32float',
              uF=(Expr('parent().par.Flight.menuIndex'), Expr("parent().par.Speed * op('pace')[0]"),
                  DT, clock_seconds()),
              uH=(HEIGHT, Expr("op('drive')['dip']"), TAN_HALF, CAMERA),
              uC=(par('Yaw'), par('Pitch'), par('Roll'), par('Zoom')),
              uP=(par('Positionx'), par('Positiony'), par('Altitude')))

# ---- The view -------------------------------------------------------------------------------------
section('view', 'The view: the land eased, then drawn a column at a time, front to back, over a y-buffer',
        lane='picture')
colors_fb = mk(comp, feedbackTOP, 'colors_fb', [source], "colors' last frame.", top='colors')
colors = glsl(comp, 'colors', [source, colors_fb], src('colors.glsl'),
              "The land's colors: the picture eased over {:g} s, as the heights are.".format(EASE), fmt='rgba16float',
              uE=(DT, EASE))
render = mk(comp, glslTOP, 'render', [colors, terrain, flight],
            'The view: one workgroup a column steps out from the camera; each pixel takes the first step that '
            'reaches it.', mode='compute', autodispatchsize=False, dispatchsizex=1280, dispatchsizey=1,
            dispatchsizez=1, inputfiltertype='mipmap')
docked(render, '_compute', lib_glsl(_ROOT, 'red_guard.glsl') + src('render.glsl'),
       'The view, a compute shader (src/render.glsl), every pixel through the red guard.')
uniforms(render, uV=(HEIGHT, par('Fog'), Expr('parent().par.Flight.menuIndex'), TAN_HALF), uZ=(Z_A, Z_B, Z_C, FAR))

settle_fb = mk(comp, feedbackTOP, 'settle_fb', [render], "settle's last frame.", top='settle')
settle = glsl(comp, 'settle', [render, settle_fb], src('settle.glsl'),
              'The view eased over {:g} s, as a shutter blurs what moves, less while a beat dips the camera.'.format(
                  SETTLE), fmt='rgba16float', uE=(DT, Expr("{} * (1 - 0.75 * op('dip_env')[0])".format(SETTLE))))

finish_effect(comp, settle, VERSION, page)
save_effect(comp, _HERE, _ROOT)
