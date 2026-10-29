"""Build Relight. Run from a textport: __file__ = '/path/to/build_relight.py'; exec(open(__file__).read())

The picture lit again by colored lights that move over it, its shape from the depth map on input 3. The depth becomes a
height field (Relief high, rounded at its edges); its slope gives the normals, Lambert's diffuse and a GGX highlight
light it, and marching the height field toward each light gives its shadow. Ambient occlusion darkens what lies below
its surroundings (Luft, Colditz and Deussen's unsharp masking of the depth buffer). Light scatters under the surface and
comes through thin parts from behind (Jimenez et al.'s separable subsurface scattering and translucency), the same
everywhere: nothing in the picture is singled out. Each beat flares the lights through the flash gate; louder music
brightens them.

Patents (private/patents/relight.md) shaped three things. No region of the picture is ever found or set apart (Canon's
US 11,948,282 and 11,106,938 claim shading a specified region by its normals), so skin isn't found by color. A shadow
multiplies its samples' light let through and never shades by the highest point seen (Adobe's US 8,379,021). And no two
Gaussian blurs are ever added: the broad smoothings are triangle averages (NVIDIA's US 8,064,726).

dev/protos/relight/offline.py tried it first on the clips with a song (board #4677): dividing the picture by its blurred
brightness to take out its own light lifted a video's darks into blocks and posterized smoke, so it only dims; the
occlusion without a range check gave every figure a black halo; and the picture's brightness as a stand-in for depth
made a landscape's sky the nearest thing in it, so without input 3 only its brighter parts bulge, against their
broad average.

The network, left to right:
  picture  source -> luma8 -> shade (its brightness blurred), shade_avg (its average) -> show (the picture lit) -> out
  shape    input 3's nearness -> near_fine, near_round -> relief; or source -> luma -> luma_fine, luma_broad -> bumps;
           shape (whichever) -> surface (height, normal, occlusion at half size) -> shadows (one channel a light)
  light    lights (where each light is, its color) -> irradiance (the light on the surface, and through thin parts, from
           surface_wide) -> sss_h -> sss_v (scattered under the surface)
  depth    input 3 (depth_in(), else nothing) -> near
  audio    audio_in() -> counts -> steps -> flash gate -> flare_env (each beat's flare); level_pick -> level_smooth;
           clock (the lights' paths)
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
# The looks, four lights each, in the picture's own terms (x right, y down, both shares of the picture): color (linear
# RGB), intensity, then a lamp's path (center x, y; sway x, y; their periods in seconds; a phase; its height as a share
# of the picture's height), or a sun's (heading sway and heading in radians, 0 toward the right, then 0, 0; the
# heading's period; 0; a phase; its elevation in degrees, negative). A light of intensity 0 is off.
LOOKS = (
    ('stage', 'Stage', (((0.55, 0.15, 1.0), 2.2, (0.3, 0.3, 0.25, 0.2), (9.0, 7.0, 0.0, 0.35)),
                        ((0.05, 0.85, 0.75), 2.0, (0.7, 0.35, 0.25, 0.2), (11.0, 8.0, 2.0, 0.35)),
                        ((1.0, 0.55, 0.05), 1.6, (0.5, 0.8, 0.35, 0.1), (13.0, 10.0, 4.0, 0.3)))),
    ('studio', 'Studio', (((1.0, 0.85, 0.7), 2.6, (0.25, 0.25, 0.08, 0.06), (17.0, 13.0, 0.0, 0.6)),
                          ((0.6, 0.75, 1.0), 0.6, (0.8, 0.45, 0.05, 0.05), (19.0, 15.0, 1.0, 0.5)),
                          ((1.0, 1.0, 1.0), 1.6, (0.55, -0.05, 0.3, 0.02), (23.0, 11.0, 3.0, 0.08)))),
    ('sun', 'Sun', (((1.0, 0.8, 0.55), 2.6, (1.2, -2.4, 0.0, 0.0), (30.0, 1.0, 0.0, -25.0)),
                    ((0.35, 0.55, 1.0), 0.35, (0.0, -1.57, 0.0, 0.0), (1.0, 1.0, 0.0, -80.0)))),
    ('twotone', 'Two Tone', (((1.0, 0.5, 0.1), 3.0, (0.0, 0.4, 0.05, 0.2), (13.0, 9.0, 0.0, 0.25)),
                             ((0.1, 0.4, 1.0), 3.0, (1.0, 0.4, 0.05, 0.2), (11.0, 10.0, 1.5, 0.25)))),
)
MAX_SLOPE = 1.0      # the normals see slopes up to this (45 degrees); a depth map's cliffs facing sideways went black
RADIUS = 0.9         # a lamp's light falls to half this far away, as a share of the picture's height
REACH, STEPS = 0.35, 32   # a shadow is looked for this far toward its light (a share of the picture's width), in steps
AMBIENT = 0.3        # Ambient 1 lights everything this much (linear)
SOFT = 0.3           # Softness 1: a penumbra widening this much per pixel of distance from its occluder
SSS_RED = 8.0        # how far red light spreads at Scatter 1 (pixels at half of 720 high); green 0.4, blue 0.2 of it
THIN = 40            # a pixel standing well above the surface's triangle average over this many pixels is thin
BROAD = 'bartlette'  # the broad smoothings are triangle (Bartlett) averages: never two Gaussians added (patents)
FLARE = 1.0          # a beat's flare at Beat Kick 1 adds this much to the lights
FADE = 0.6           # and fades over this many seconds (over 0.35 s, three a second each fell fully: 3.5 a second)
PERF = '4.6'          # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


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


def look_table():
    """LOOK_COLOR, LOOK_PATH and LOOK_TIME for lights.glsl, four lights a look, in texture terms (y up)."""
    col, path, time = [], [], []
    for _, _, lights in LOOKS:
        for k in range(4):
            if k >= len(lights):
                col.append((0, 0, 0, 0))
                path.append((0.5, 0.5, 0, 0))
                time.append((1, 1, 0, 1))
                continue
            c, inten, (a, b, sx, sy), (px, py, ph, z) = lights[k]
            col.append(tuple(c) + (inten,))
            # A lamp's y and a sun's heading are flipped, since a texture's y runs up.
            path.append((a, 1 - b, sx, -sy) if z >= 0 else (-a, -b, 0, 0))
            time.append((px, py, ph, z))
    out = '#define LOOKS {}\n'.format(len(LOOKS))
    for name, rows in (('LOOK_COLOR', col), ('LOOK_PATH', path), ('LOOK_TIME', time)):
        out += 'const vec4 {}[{}] = vec4[{}](\n    {});\n'.format(
            name, len(rows), len(rows), ',\n    '.join('vec4({})'.format(', '.join('{:.5f}'.format(x) for x in r))
                                                      for r in rows))
    return out


README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'relight', 'Relight',
    'Relight {}: the picture lit again by colored lights that move over it, its shape from a depth map, with shadows, '
    'highlights and light glowing through thin parts; the beats flare the lights.'.format(VERSION),
    README, tags=('relight', 'lighting', 'depth', 'audio-reactive'), audio=True, depth=True, flashing=True)

# ---- Parameters -------------------------------------------------------------------------------
p = menu(page, 'Look', 'Look', [(n, label) for n, label, _ in LOOKS], 'stage',
         'Which lights. Stage: violet, teal and amber lamps sweeping over the picture. Studio: a warm key light, a cool '
         'fill and a white light from above. Sun: a warm, low sun swinging slowly round, with long shadows, and a blue '
         'sky. Two Tone: '
         'amber from the left, blue from the right.')
p.startSection = True
custom(page, 'Float', 'Brightness', 'Brightness', 1.0, 'How bright the lights are, 0-2.', 0, 2, True)
custom(page, 'Float', 'Ambient', 'Ambient', 0.1,
       "How much light reaches everything evenly, 0-1, so what no light reaches isn't black.", 0, 1, True)
custom(page, 'Float', 'Height', 'Height', 1.0,
       'How high the lights hang over the shapes, 0.25-2: lower lights cast longer shadows and light it more unevenly '
       '(for Sun, how high the sun stands).', 0.25, 2, True)
custom(page, 'Float', 'Speed', 'Speed', 1.0, 'How fast the lights move, 0-3. 0 holds them still.', 0, 3, True)
p = custom(page, 'Float', 'Relief', 'Relief', 0.25,
           "How far what is nearest stands out of the picture, as a share of its height, 0-1: the depth of the shapes "
           'the light falls on. 0 lights the picture flat.', 0, 1, True)
p.startSection = True
custom(page, 'Float', 'Roundness', 'Roundness', 0.5,
       'How far the shapes round off at their edges, 0-1, so a figure cut out of a depth map lights like a relief '
       'rather than a flat cutout.', 0, 1, True)
custom(page, 'Float', 'Flatten', 'Flatten', 0.5,
       "How much of the picture's own light is taken out before the new lights light it, 0-1: its bright parts are "
       'dimmed toward its average.', 0, 1, True)
custom(page, 'Float', 'Shininess', 'Shininess', 0.5,
       'How sharp the highlights are, 0-1: 0 broad and soft, 1 small and glossy.', 0, 1, True)
custom(page, 'Float', 'Specular', 'Specular', 1.0, 'How bright the highlights are, 0-2.', 0, 2, True)
custom(page, 'Float', 'Shadows', 'Shadows', 1.0, 'How dark the shadows are, 0-1. 0 casts none.', 0, 1, True)
custom(page, 'Float', 'Softness', 'Softness', 0.5, "How soft the shadows' edges are, 0-1.", 0, 1, True)
custom(page, 'Float', 'Occlusion', 'Occlusion', 0.5,
       'How much darker what lies below its surroundings is, 0-1 (ambient occlusion): creases, folds and the gaps '
       'between fingers.', 0, 1, True)
p = custom(page, 'Float', 'Scatter', 'Scatter', 0.5,
           'How far light spreads under the surface before it comes out, 0-1, red furthest, as in skin, wax or marble: '
           "it softens the light and warms its shadows' edges.", 0, 1, True)
p.startSection = True
custom(page, 'Float', 'Glow', 'Glow', 0.5,
       'How much light from behind comes through thin parts, 0-1, glowing red at the edges of fingers and ears.', 0, 1,
       True)
p = custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
           'How bright a flare each beat on input 2 gives the lights, 0-1. Flashing limits how often.', 0, 1, True)
p.startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5, 'How much brighter louder music on input 2 makes the lights, 0-1.', 0,
       1, True)
p = menu(page, 'Depthtype', 'Depth Type',
         (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
          ('meters', 'Distance in Meters (Kinect Azure)')), 'nearness',
         'What input 3 holds, a depth map or a mask, the shape the light falls on. Brighter Is Nearer: depth estimators '
         '(Depth Anything) and masks. Distance 0-1: the RealSense and Kinect TOPs, 0 near to 1 far, black where the '
         'camera got no reading. Distance in Meters: the Kinect Azure TOP, scaled by Max Distance.')
p.startSection = True
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"
custom(page, 'Float', 'Bumps', 'Bumps', 0.5,
       "With nothing on input 3: how far the picture's fine detail stands out, 0-1, as the shape the light falls on.",
       0, 1, True)

# ---- Audio (input 2): a flare on each beat, brighter when it is loud ------------------------------------
section('audio', 'Audio (input 2): a flare on each beat, brighter lights when it is loud, the lights moving')
audio = audio_in(comp, _ROOT)
WIRED = "op('audio')['source'].eval() > 0"
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
gate = flash_gate(comp, steps)
flare_env = mk(comp, triggerCHOP, 'flare_env', [gate], "A beat's flare: up at once, fading over {:g} s.".format(FADE),
               attack=0, peak=1, decay=FADE, sustain=0, release=0)
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick],
           'Loudness eased over a second, so the lights swell and calm with the music.', width=1.0)
speed = mk(comp, constantCHOP, 'speed', comment='How fast the lights move: Speed.', const0name='speed',
           const0value=par('Speed'))
clock = mk(comp, speedCHOP, 'clock', [speed], "The lights' clock (s at Speed 1), wrapping every 16384 s.",
           limittype='loop', min=0, max=16384)
LOUD = "(max(0.5, 1 + parent().par.Loudness * 1.5 * (op('level_smooth')[0] - 0.6)) if {} else 1)".format(WIRED)

# ---- Depth or a mask (input 3) ----------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): the shape the light falls on')
flat = mk(comp, constantTOP, 'flat', comment='With nothing on input 3: nothing (the picture stands in instead).',
          outputresolution='custom', resolutionw=8, resolutionh=8, colorr=0, colorg=0, colorb=0, alpha=1)
depth = depth_in(comp, flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at half size, as nearness; Depth Type flips distance (black: no reading).', fmt='rgba16float',
            uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='half')

# ---- The shape ----------------------------------------------------------------------------------
section('shape', 'The shape: the depth (or the picture\'s detail) as a surface, its normals, occlusion and shadows',
        lane='shape')
near_fine = mk(comp, blurTOP, 'near_fine', [near], "The nearness smoothed finely: an 8-bit map's steps gone.",
               type='gaussian', size=6)
near_round = mk(comp, blurTOP, 'near_round', [near], 'The nearness averaged broadly with a triangle filter: Roundness.',
                type=BROAD,
                size=Expr('max(1, 32 * parent().par.Roundness)'))
relief = glsl(comp, 'relief', [near_fine, near_round, near], src('relief.glsl'),
              'The shape from the depth: half fine, half round, never nearer than the depth.', fmt='mono32float')
luma = glsl(comp, 'luma', [source], src('luma.glsl'), "The picture's brightness at half size.", fmt='rgba16float')
setpars(luma, outputresolution='half')
luma_fine = mk(comp, blurTOP, 'luma_fine', [luma], 'The brightness blurred.', type='gaussian', size=9)
luma_broad = mk(comp, blurTOP, 'luma_broad', [luma], 'The brightness averaged broadly with a triangle filter.',
                type=BROAD, size=40)
bumps = glsl(comp, 'bumps', [luma_fine, luma_broad], src('bumps.glsl'),
             "With nothing on input 3: the picture's fine detail as bumps on a plane.", fmt='mono32float',
             uB=(par('Bumps'),))
shape = mk(comp, switchTOP, 'shape', [relief, bumps],
           'The depth when input 3 is wired, else the bumps; only the chosen one cooks.',
           index=Expr('0 if parent().inputConnectors[2].connections else 1'))
surface = glsl(comp, 'surface', [source, shape], '#define MAX_SLOPE {}\n'.format(MAX_SLOPE) + src('surface.glsl'),
               "The surface at half the picture's size: its height, normal and occlusion.", fmt='rgba32float',
               uS=(par('Relief'), par('Occlusion')))
setpars(surface, outputresolution='half')

# ---- The lights -------------------------------------------------------------------------------
section('light', 'The light: the lights this frame, the light they cast, scattered under the surface', lane='light')
lights = glsl(comp, 'lights', [], look_table() + src('lights.glsl'),
              "Where each light is this frame and its color (a column a light).", res=(4, 2), fmt='rgba32float',
              uT=(Expr("op('clock')[0]"), Expr('parent().par.Look.menuIndex'),
                  Expr("parent().par.Kick * {} * op('flare_env')[0]".format(FLARE)),
                  Expr('parent().par.Brightness * {}'.format(LOUD))),
              uH=(par('Height'), par('Relief')))


def common(k):
    """common.glsl, reading the lights from input k."""
    return '#define LIGHTS sTD2DInputs[{}]\n'.format(k) + src('common.glsl')


shadows = glsl(comp, 'shadows', [surface, lights], common(1) + src('shadows.glsl'),
               "Each light's shadow, a channel a light, at a quarter of the picture's size: the surface marched toward it.",
               fmt='rgba8fixed',
               uH=(par('Shadows'), Expr('parent().par.Softness * {}'.format(SOFT)), REACH, STEPS))
setpars(shadows, outputresolution='half')
put(shadows, 'shape')
shadows_soft = mk(comp, blurTOP, 'shadows_soft', [shadows], "The shadows' grain smoothed.", type='gaussian', size=3)
put(shadows_soft, 'shape')
surface_wide = mk(comp, blurTOP, 'surface_wide', [surface],
                  'The surface averaged broadly with a triangle filter: how far each pixel stands above what is around '
                  'it (how thin).',
                  type=BROAD, size=THIN)
irradiance = glsl(comp, 'irradiance', [surface, shadows_soft, lights, surface_wide],
                  common(2) + src('irradiance.glsl'), 'The light falling on the surface, and through thin parts.',
                  fmt='rgba16float', uI=(RADIUS, par('Glow')))
SSS = Expr('parent().par.Scatter * {}'.format(SSS_RED))
sss_h = glsl(comp, 'sss_h', [irradiance, surface], src('sss.glsl'), 'The light scattered under the surface, across.',
             fmt='rgba16float', uD=(1, 0, 1, SSS))
sss_v = glsl(comp, 'sss_v', [sss_h, surface], src('sss.glsl'), 'The light scattered under the surface, down.',
             fmt='rgba16float', uD=(0, 1, 1, SSS))

# ---- The picture --------------------------------------------------------------------------------
section('picture', "The picture: its own light flattened, lit again", lane='picture')
luma8 = glsl(comp, 'luma8', [source], src('luma.glsl'), "The picture's brightness at an eighth of its size.",
             fmt='rgba16float')
setpars(luma8, outputresolution='eighth')
shade = mk(comp, blurTOP, 'shade', [luma8], "The picture's own light: its brightness blurred.", type='gaussian', size=18)
shade_avg = mk(comp, analyzeTOP, 'shade_avg', [luma8], "The picture's average brightness.", op='average',
               analyzechannel='independent')
show = glsl(comp, 'show', [source, sss_v, surface, shadows_soft, lights, shade, shade_avg],
            lib_glsl(_ROOT, 'red_guard.glsl') + common(4) + src('show.glsl'),
            'The picture lit again: its own light flattened, the lights, their highlights; every pixel through the red '
            'guard.', fmt='rgba8fixed',
            uL=(Expr('parent().par.Ambient * {}'.format(AMBIENT)), par('Specular'),
                Expr('0.8 - 0.7 * parent().par.Shininess'), par('Flatten')),
            uE=(RADIUS,))
for g in (surface, shadows, irradiance, sss_h, sss_v, relief, bumps):
    setpars(g, inputextenduv='hold')

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
