"""Build Detail. Run from a textport: __file__ = '/path/to/build_detail.py'; exec(open(__file__).read())

The picture's fine detail made stronger or smoothed away, its edges kept clean: a local Laplacian filter (Paris,
Hasinoff and Kautz, SIGGRAPH 2011) in its fast form (Aubry, Paris, Hasinoff, Kautz and Durand, TOG 2014). The output's
Laplacian pyramid is built coefficient by coefficient from the picture's brightness remapped around the brightness
there: differences smaller than Edge Contrast are detail, made Detail times stronger (or smoothed away), and larger ones
are edges, kept as they are (or made Tone times as large). The fast form remaps the whole brightness around eight
values from black to white, packed four to a texture, and takes each coefficient between the two copies whose values
bracket the brightness there; eight copies came within 37 dB of 64 at the lowest Edge Contrast
(dev/protos/detail/offline.py). It works on the brightness alone and adds its change to every channel, so the colors
stay as they were.

The beats make the detail jump through the flash gate (pumping detail counts as flashing: Video Vocoder, board #4718),
and the loudness against its usual level swells it smoothly.

No patent was found on local Laplacian filters (Adobe's, MIT's or the authors'); Adobe's US 8,831,340 and 9,230,312
claim tone mapping a high dynamic range picture with a bilateral base layer packed into the lower part of the output's
range, which this doesn't do, and Stewart's US 10,839,487 an enhancement whose 'frequency blender' keeps each level's
amplified band within the dynamic range, which this has no part like (private/patents/detail.md).

The network, left to right:
  picture  source -> luma -> pyramid() l1 ... l7; collapse6 (the smallest octave, over l7) ... collapse0 (the picture)
           -> out
  copies   luma -> copies_a, copies_b (remapped around 0 ... 3/7 and 4/7 ... 1) -> pyramid() a1 ... a7, b1 ... b7
  audio    audio_in() -> counts -> steps -> flash_gate() -> kick_env (a beat's jump); level_pick -> level_now (over a
           second) -> level_usual (the last 4 s); detail_now (Detail with the music), read by the copies and the
           collapse passes
  depth    input 3 (depth_in()) -> near
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
LEVELS = 7           # the pyramid's levels below the picture: the smallest is 10 x 6 at 1280 x 720
# The music: Beat Kick 1 adds KICK to Detail on a beat, back over FALL seconds; Loudness 1 adds LOUD times the level
# above its usual level (its average over USUAL seconds), within SWELL either way, the level smoothed over SLOW.
KICK, FALL = 2.0, 0.3
LOUD, SWELL, USUAL, SLOW = 4.0, 1.0, 4.0, 1.0
DETAIL = (-1.0, 4.0)  # Detail with the music, at most
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
PERF = '3'           # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


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


README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'detail', 'Detail',
    "Detail {}: the picture's fine detail made stronger or smoothed away, its edges kept clean, by a local Laplacian "
    'filter.'.format(VERSION),
    README, tags=('detail', 'local-laplacian', 'edge-aware', 'local-contrast', 'audio-reactive'), audio=True,
    depth=True, flashing=True, sample="app.samplesFolder + '/Map/Nature/Movie.3.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
custom(page, 'Float', 'Detail', 'Detail', 1.0,
       'How much stronger the fine detail gets, -1 to 3: 0 as it is, 1 twice as strong, 3 four times. Below 0 it '
       'smooths away (-1: gone) while the edges stay sharp.', -1, 3, True).startSection = True
custom(page, 'Float', 'Tone', 'Tone', 1.0,
       "How large the picture's big changes of light stay, 0-2: 1 as they are, lower flattens them (the shadows "
       'open, the highlights come down), higher deepens them. The detail stays either way.', 0, 2, True)
custom(page, 'Float', 'Edge', 'Edge Contrast', 0.2,
       'How large a step in brightness counts as an edge, kept as it is, rather than as detail, 0.1-0.5 (of black to '
       'white). Higher lets Detail reach larger features; lower keeps it to fine texture.', 0.1, 0.5, True)
custom(page, 'Float', 'Floor', 'Noise Floor', 0.015,
       'While Detail boosts, detail fainter than this (of black to white) is left nearly as it is, so the video\'s '
       "noise and compression blocks don't grow with the detail, 0-0.05. 0 boosts everything.", 0, 0.05, True)
custom(page, 'Float', 'Beatkick', 'Beat Kick', 0.5,
       'How much the detail jumps on each beat of input 2, 0-1: at 1, Detail 2 higher for a moment, back over '
       '0.3 s. As often as Flashing allows.', 0, 1, True).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much the detail swells as the music on input 2 gets louder than it has been over the last few seconds '
       '(and eases as it quietens), 0-1. Smoothed over a second.', 0, 1, True)
p = custom(page, 'Float', 'Depthfocus', 'Depth Focus', 0.5,
           'With a depth map or mask on input 3: how much the change is kept to near things (or what lies inside '
           'the mask), 0-1. At 1 far things stay as they are. Nothing changes without input 3.', 0, 1, True)
p.startSection = True
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

# ---- Audio (input 2): a jump on each beat, a swell when loud -------------------------------------
section('audio', 'Audio (input 2): the detail jumps on a beat and swells when the music is loud')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
flash = flash_gate(comp, steps)
kick_env = mk(comp, triggerCHOP, 'kick_env', [flash], "A beat's jump: up at once, back over {:g} s.".format(FALL),
              attack=0, peak=1, decay=FALL, sustain=0, release=0)
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level_now = mk(comp, filterCHOP, 'level_now', [level_pick],
               'Loudness smoothed over {:g} s, so the detail swells and eases instead of pumping.'.format(SLOW),
               width=SLOW)
level_usual = mk(comp, filterCHOP, 'level_usual', [level_now],
                 'The usual loudness: its average over the last {:g} s.'.format(USUAL), type='box', width=USUAL)
WIRED = "op('audio')['source'].eval() > 0"
SWELLS = ("(min(max({loud} * parent().par.Loudness * (op('level_now')[0] - op('level_usual')[0]), -{s}), {s}) "
          "if {wired} else 0)").format(loud=LOUD, s=SWELL, wired=WIRED)
KICKS = "{} * parent().par.Beatkick * op('kick_env')[0]".format(KICK)
detail_now = mk(comp, constantCHOP, 'detail_now', comment="Detail with the music: the beat's jump and the swell "
                'when loud added to the parameter, within {:g} to {:g}.'.format(*DETAIL), const0name='detail',
                const0value=Expr('min(max(parent().par.Detail + {} + {}, {}), {})'.format(KICKS, SWELLS, *DETAIL)))
DETAIL_NOW = Expr("op('detail_now')[0]")

# ---- Depth (input 3): the change kept to near things ------------------------------------------------
section('depth', 'Depth or a mask (input 3): the change kept to near things, or inside the mask')
flat = mk(comp, constantTOP, 'depth_none', comment='Near everywhere: with nothing on input 3 the whole picture changes.',
          outputresolution='custom', resolutionw=1, resolutionh=1, colorr=1, colorg=1, colorb=1, alpha=1)
depth = depth_in(comp, fallback=flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black is no reading).',
            fmt='rgba16float', uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')
FOCUS = Expr('parent().par.Depthfocus if parent().inputConnectors[2].connections else 0')
FLOOR = Expr("parent().par.Floor if op('detail_now')[0] > 0 else 0")

# ---- The picture's brightness and its octaves -------------------------------------------------------
section('luma', "The picture's brightness, and its octaves (Gaussian pyramid)")
luma = glsl(comp, 'luma', [source], src('luma.glsl'), "The picture's brightness (luma), the channel the filter works on.",
            fmt='mono32float')
lum = pyramid(comp, _ROOT, luma, LEVELS, fmt='mono32float', prefix='l', what="The picture's brightness")

# ---- The remapped copies and their octaves -----------------------------------------------------------
section('copies', 'Eight copies of the brightness, each remapped around its own level, and their octaves', lane='copies')
REMAP = dict(uR=(DETAIL_NOW, par('Tone'), par('Edge')))
copies = []
for half, name in enumerate(('a', 'b')):
    c = glsl(comp, 'copies_' + name, [luma], src('remap.glsl'),
             'The brightness remapped around {} of black to white, one copy in each channel: detail near each level '
             'made Detail times stronger, larger steps kept or made Tone times as large.'.format(
                 ', '.join('{}/7'.format(4 * half + k) for k in range(4))),
             fmt='rgba32float', uG=tuple(round((4 * half + k) / 7, 6) for k in range(4)), **REMAP)
    copies.append(pyramid(comp, _ROOT, c, LEVELS, prefix=name,
                          what='Copies {}-{}'.format(4 * half, 4 * half + 3)))

# ---- The output's octaves, back up to the picture -----------------------------------------------------
section('collapse', 'Each octave of detail taken between the two nearest copies, the smallest first, back up to the '
                    'picture')
below = lum[LEVELS]
for k in reversed(range(LEVELS)):
    last = k == 0
    a, b = copies
    below = glsl(comp, 'collapse{}'.format(k),
                 ([source] if last else []) + [lum[k], lum[k + 1], a[k], a[k + 1], b[k], b[k + 1], below, near],
                 lib_glsl(_ROOT, 'pyramid.glsl') + ('#define LAST\n' if last else '') + src('collapse.glsl'),
                 ("The picture: the brightness's change added to its colors, down to the finest detail." if last else
                  'Octave {} of the output: its detail taken between the two copies around the brightness there, and '
                  'the octaves below added back.'.format(k)),
                 fmt=None if last else 'mono32float', uC=(FOCUS, FLOOR))
    setpars(below, inputextenduv='hold')

finish_effect(comp, below, VERSION, page)
save_effect(comp, _HERE, _ROOT)
