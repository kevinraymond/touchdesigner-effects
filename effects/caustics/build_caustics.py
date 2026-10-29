"""Build Caustics. Run from a textport: __file__ = '/path/to/build_caustics.py'; exec(open(__file__).read())

The picture as the floor of a pool under moving water, lit by the light its waves focus, after Yuksel and Keyser's
caustics from height fields (2009). The water is a height field stepped by the damped wave equation (as Evan Wallace's
WebGL Water steps it, MIT) under a base sea of slow swells; whatever moves in the picture pushes it into broad wakes,
and each beat drops a raindrop into it. A compute shader gathers the caustics: every surface sample refracts the sun's
light to the floor, a one-pixel square there lighting the pixels it overlaps. The floor is seen through the surface,
lit by the caustics and absorbed by the water's depth (input 3 makes nearer shallower), with the sun's glint.

dev/protos/caustics/offline.py tried it first on the clips with a song (board #4671): fine ripples (raindrops, the
picture's change pushed as it came) focused light into a grain that flashed 3 to 5 times a second, and only broad
swells and broad wakes kept to the clip's own flashes.

The network, left to right:
  picture  source -> surface (the surface at half size: height, slope, depth) -> caustics (a compute shader: the
           light on the floor) -> light (softened a pixel) -> show (the floor seen through the water, lit, absorbed,
           glinting) -> out
  water    optical_flow() (no flow: lum4, lum4p, clock) -> push (the change since the last input frame) ->
           push_blur (broad wakes) -> water (+ water_fb: the wave equation)
  depth    input 3 (depth_in(), else flat) -> near (nearness at a quarter size) -> near_soft
  audio    audio_in() -> counts -> steps -> drop_env (a drop pours for a tenth of a second), drops (their count, for
           where); level_pick -> level_smooth (louder, higher waves); wind (the swells' clock)
"""
import math
import os
import random

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.1'
IOR = 1.333                  # water
SUN = (0.25, -0.15, -1.0)    # the sun's direction, a little off overhead
GLINT = 0.6                  # the sun's glint on the surface
SWELLS, SLOPE, PERIOD = 10, 0.03, 2.5   # the base sea: SWELLS swells, each sloping at most SLOPE at Waves 1, a Size swell
                                        # taking PERIOD s at Wind 1
SPREAD = 1.1                 # radians the swells' headings spread about the wind's
SIZE0 = 0.12                 # Size's default; the swells' slope grows with Size from SLOPE there, so a longer swell
                             # focuses at the same depth (a wave of length L and slope s focuses at about L / s), which
                             # keeps the light's reach within the caustics' window
RAINBOW = 0.08               # Rainbow 1 spreads the index of refraction this much either side (0.03 barely showed)
WAKE = 3.6                   # Wake 1 pushes the water by this much per unit of change in luma (6 at Wake 0.5 flashed
                             # half a flash a second more than the dancer clip)
WAKE_SIGMA = 10.0            # the wakes' breadth, in the water's pixels (a quarter of the picture's); 3 flashed, and 6
                             # added half a flash a second where everything moves (flowers in wind)
DROP = (20.0 / 180, 2.0, 0.1)   # a beat's drop: radius (a share of the height), how much it adds at Beat Kick 1, over s
                                # (12 / 180 rang in short, steep rings that added half a flash a second on the dancer)
# The wave equation, per second (it steps once a frame): the pull toward the neighbors is 2 at 30 steps a second, which
# 0.5 at 60 matches; the water keeps DAMP of its motion a second; VISCOSITY of the finest ripples goes in 1/30 s.
DAMP, VISCOSITY = 0.635, 0.15
PERF = '2.2'                 # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


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


def swell_table():
    """The base sea, fixed at build time: each swell's heading (unit), length (a share of Size) and phase."""
    rng = random.Random(4671)
    wind = 0.6
    rows = []
    for _ in range(SWELLS):
        ang = wind + rng.gauss(0, SPREAD)
        rows.append('vec4({:.5f}, {:.5f}, {:.5f}, {:.5f})'.format(math.cos(ang), math.sin(ang), 2 ** rng.uniform(-1, 1),
                                                                rng.uniform(0, 2 * math.pi)))
    return '#define SWELLS {}\nconst vec4 SWELL[SWELLS] = vec4[SWELLS](\n    {});\n'.format(SWELLS, ',\n    '.join(rows))


SUN_UNIT = tuple(c / math.sqrt(sum(x * x for x in SUN)) for c in SUN)
README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'caustics', 'Caustics',
    'Caustics {}: the picture as the floor of a pool under moving water, lit by the bright lines of light its waves '
    'focus; whatever moves makes wakes and the beats drop into it.'.format(VERSION),
    README, tags=('caustics', 'water', 'refraction', 'audio-reactive'), audio=True, depth=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.2.mp4'")   # grass swaying in front of a building: it makes wakes

# ---- Parameters -------------------------------------------------------------------------------
p = custom(page, 'Float', 'Depth', 'Depth', 1.0,
           "How deep the water is, as a share of the picture's height, 0.25-2. The waves focus the light sharpest about "
           'Depth 1; shallower water lights the floor more evenly, deeper water crosses the lines into a busier net, '
           'bends the view further and colors it more. With a depth map or mask on input 3, nearer is shallower.',
           0.25, 2, True)
p.startSection = True
custom(page, 'Float', 'Waves', 'Waves', 1.0, "How high the water's waves are, 0-2. 0 stills the swells.", 0, 2, True)
custom(page, 'Float', 'Wind', 'Wind', 1.0, 'How fast the swells roll, 0-3. 0 holds them still.', 0, 3, True)
custom(page, 'Float', 'Size', 'Size', 0.12,
       "How long the swells are, as a share of the picture's width, 0.05-0.16: the size of the caustics' net. Longer "
       'swells are steeper too, so they still focus at the same depth.', 0.05, 0.16, True)
p = custom(page, 'Float', 'Caustics', 'Caustics', 0.5,
           'How much of the focused light shows, 0-1: at 1 the bright lines and the dark between them are as the water '
           'focuses them, at 0 the floor is lit evenly.', 0, 1, True)
p.startSection = True
custom(page, 'Float', 'Rainbow', 'Rainbow', 0.0,
       "How far the light's colors split as they bend, 0-1, giving the bright lines colored fringes, as sunlight "
       'through real water does faintly.', 0, 1, True)
custom(page, 'Float', 'Refraction', 'Refraction', 0.25,
       'How far the waves bend the view of the floor, 0-1, as a share of what the water would bend it.', 0, 1, True)
custom(page, 'Float', 'Watercolor', 'Water Color', 0.18,
       'How much the water colors the floor, 0-1: it takes red first, so deeper water is bluer.', 0, 1, True)
p = custom(page, 'Float', 'Wake', 'Wake', 0.5,
           'How hard whatever moves in the picture pushes the water, 0-1, leaving broad wakes behind it.', 0, 1, True)
p.startSection = True
custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'How big a raindrop each beat on input 2 drops into the water, 0-1, somewhere new each time.', 0, 1, True)
custom(page, 'Float', 'Loudness', 'Loudness', 0.5, 'How much higher louder music on input 2 raises the waves, 0-1.', 0, 1,
       True)
p = menu(page, 'Depthtype', 'Depth Type',
         (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
          ('meters', 'Distance in Meters (Kinect Azure)')), 'nearness',
         'What input 3 holds, a depth map or a mask: the water is shallower over what is nearer, down to half of Depth '
         'over the nearest. Brighter Is Nearer: depth estimators (Depth Anything) and masks. '
         'Distance 0-1: the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance '
         'in Meters: the Kinect Azure TOP, scaled by Max Distance. With nothing on input 3 the water is evenly Depth '
         'deep.')
p.startSection = True
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

# ---- Audio (input 2): drops on the beats, the waves with loudness ------------------------------------
section('audio', 'Audio (input 2): a raindrop on each beat, higher waves when it is loud, the swells rolling')
audio = audio_in(comp, _ROOT)
WIRED = "op('audio')['source'].eval() > 0"
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
drop_env = mk(comp, triggerCHOP, 'drop_env', [steps],
              'A drop: 1 for the {:g} s it pours into the water, then 0.'.format(DROP[2]),
              attack=0, peak=1, peaklen=DROP[2], decay=0, sustain=0, release=0)
drops = mk(comp, countCHOP, 'drops', [steps], 'Drops so far: where each one falls.')
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick],
           'Loudness eased over a second, so the waves swell and calm with the music.', width=1.0)
wind_rate = mk(comp, constantCHOP, 'wind_rate', comment='How fast the swells roll: Wind.', const0name='wind',
               const0value=par('Wind'))
wind = mk(comp, speedCHOP, 'wind', [wind_rate],
          "The swells' clock (s at Wind 1), wrapping every 16384 s.", limittype='loop', min=0, max=16384)
LOUD = "(max(0.5, 1 + parent().par.Loudness * 1.5 * (op('level_smooth')[0] - 0.6)) if {} else 1)".format(WIRED)

# ---- Depth or a mask (input 3) ----------------------------------------------------------------------
section('depth', "Depth or a mask (input 3): the water's depth, shallower over what is nearer")
flat = mk(comp, constantTOP, 'flat', comment='With nothing on input 3: one depth everywhere.',
          outputresolution='custom', resolutionw=8, resolutionh=8, colorr=0.5, colorg=0.5, colorb=0.5, alpha=1)
depth = depth_in(comp, flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black: no reading).', fmt='rgba16float',
            uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')
near_soft = mk(comp, blurTOP, 'near_soft', [near], "The nearness softened, so a step in the depth doesn't seam the light.",
               type='gaussian', size=12)

# ---- The water ----------------------------------------------------------------------------------
section('water', 'The water: the wave equation, pushed by what moves and by the drops', lane='water')
mo = optical_flow(comp, _ROOT, source, flow=False)
push = glsl(comp, 'push', [mo['lum4'], mo['lum4p'], mo['clock']], src('push.glsl'),
            'How the picture changed since its last frame, a quarter of its size: what moves pushes the water.',
            fmt='rgba16float')
push_blur = mk(comp, blurTOP, 'push_blur', [push],
               'The push spread into broad wakes (fine ones focused light into a flashing grain).', type='gaussian',
               size=3 * WAKE_SIGMA)
water_fb = mk(comp, feedbackTOP, 'water_fb', [push_blur], "water's last frame.", top='water')
DT = 'min(absTime.stepSeconds, 0.1)'
DROP_AT = ("((op('drops')[0] * 0.6180339887) % 0.6 + 0.2)", "((op('drops')[0] * 0.7548776662) % 0.6 + 0.2)")
water = glsl(comp, 'water', [push_blur, water_fb], src('water.glsl'),
             "The water's surface, a quarter of the picture's size: the damped wave equation, a step a frame.",
             fmt='rgba32float',
             uW=(Expr('min(2.0, 0.5 * ({} * 60) ** 2)'.format(DT)), Expr('{} ** {}'.format(DAMP, DT)),
                 Expr('1 - {} ** (30 * {})'.format(1 - VISCOSITY, DT)), Expr('parent().par.Wake * {}'.format(WAKE))),
             uD=(Expr(DROP_AT[0]), Expr(DROP_AT[1]), DROP[0],
                 Expr("op('drop_env')[0] * parent().par.Kick * {} * {} / {}".format(DROP[1], DT, DROP[2]))))

# ---- The floor ------------------------------------------------------------------------------------
section('floor', 'The floor: the surface, the light it focuses, the floor seen through it', lane='picture')
surface = glsl(comp, 'surface', [source, water, near_soft], swell_table() + src('surface.glsl'),
               "The surface at half the picture's size: the water and the swells, their slope, and the depth.",
               fmt='rgba32float',
               uS=(par('Size'), Expr('parent().par.Waves * {}'.format(LOUD)), Expr("op('wind')[0]"), PERIOD),
               uH=(par('Waves'), par('Depth'), Expr('1 if parent().inputConnectors[2].connections else 0'),
                   Expr('{} * parent().par.Size / {}'.format(SLOPE, SIZE0))))
setpars(surface, outputresolution='half')
caustics = mk(comp, glslTOP, 'caustics', [surface],
              'The light the surface focuses on the floor: a compute shader, a workgroup a 16 x 16 patch.',
              mode='compute', format='rgba16float')
docked(caustics, '_compute', src('caustics.glsl'), "The caustics, gathered a patch at a time (Yuksel and Keyser).")
uniforms(caustics, uC=SUN_UNIT + (IOR,), uR=(Expr('parent().par.Rainbow * {}'.format(RAINBOW)),))
light = mk(comp, blurTOP, 'light', [caustics],
           'The caustics softened by about a pixel: one sample a pixel aliases into a fine mesh where the light focuses.',
           type='gaussian', size=3)
show = glsl(comp, 'show', [source, surface, light], lib_glsl(_ROOT, 'red_guard.glsl') + src('show.glsl'),
            'The floor seen through the water: refracted, lit by the caustics, colored by the depth, the sun glinting; '
            'every pixel through the red guard.', fmt='rgba8fixed',
            uV=(par('Refraction'), par('Caustics'), par('Watercolor'), IOR), uL=SUN_UNIT + (GLINT,))
setpars(show, inputextenduv='hold')   # the view bent past the picture's edge reads its edge, not black

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
