"""Build Video Vocoder. Run from a textport: __file__ = '/path/to/build_video_vocoder.py'; exec(open(__file__).read())

A channel vocoder with the picture as the carrier. Dudley's vocoder (1939) splits a voice into bands of pitch and
lets each band of another sound through as loud as the voice's matching band; here the picture is split into seven
octaves of detail, from its largest shapes to its finest grain (lib pyramid(), after Burt and Adelson's Laplacian
pyramid, 1983), and each octave is gained by the matching band of the music (lib audio_in()'s seven bands, Fosfora's
split): the bass pumps the big shapes and the glow, the treble sparkles the fine detail. With nothing on input 2 the
bands are a graphic EQ for the picture's detail, and a slow wave sweeps through them (Idle Sweep).

The music's gain for a band follows the band against its usual level (its average over the last few seconds), so the
picture keeps its look and the music's changes show, whatever the mix's balance. A band jumps up at once only through
the flash gate (lib flash_gate(): once a second at Calm), all seven together, and otherwise rises slowly: pumped at
every hi-hat, the octaves flashed the red flowers 4 times a second at 140 BPM.

Prior art: stoatworks-labs/vocoder (MIT, 2026), the same idea as an FFGL plugin for Resolume; this effect was written
from Dudley's and Burt and Adelson's descriptions, not from its code.

The network, left to right:
  picture  source -> pyramid() (g1 ... g7) -> collapse6 (the largest band, over g7) ... collapse0 (the finest band:
           the picture) -> out
  audio    audio_in() -> bands (its seven bands) -> rises -> ask (a band jumping) -> flash_gate() -> open; bands ->
           bands_jump (up at once while open, then down over Release) and bands_steady (smoothed over a second) ->
           bands_now (the higher) -> bands_usual (the last 4 s); the gains are expressions on the collapse passes
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
# The picture's seven bands, finest first, each named after the band of the music that drives it, with its
# parameter: (name, label, the audio channel, the size of what it holds, at 720 high).
BANDS = (('Brilliance', 'Brilliance', 'brilliance', 'the finest grain, a pixel or two'),
         ('Presence', 'Presence', 'presence', 'fine detail, 2 to 4 pixels'),
         ('Uppermid', 'Upper Mid', 'upper_mid', 'small detail, 4 to 8 pixels'),
         ('Mid', 'Mid', 'mid', 'edges and features, 8 to 16 pixels'),
         ('Lowmid', 'Low Mid', 'low_mid', 'shapes, 16 to 32 pixels'),
         ('Bass', 'Bass', 'bass', 'large shapes and soft light, 32 to 64 pixels'),
         ('Subbass', 'Sub Bass', 'sub_bass', 'the largest shapes and the glow, 64 to 128 pixels'))
USUAL = 4.0          # a band's usual level: its average over the last 4 s
# Drive 1: the music's gain for an octave is 1 + SPAN x (its band now - its usual level), within LIMIT. The fine
# octaves (Brilliance to Mid, up to 16 px) change the picture's texture more than any area's brightness: a band 0.25
# above usual doubles them. The coarse octaves move whole areas' brightness, so they swing half as far and within half
# and one and a half. Either kind, pumped at every eighth note, flashed the flowers 2.5 times a second by itself.
SPAN = (4.0, 4.0, 4.0, 4.0, 2.0, 2.0, 2.0)
LIMIT = ((0.0, 3.0),) * 4 + ((0.5, 1.5),) * 3
SWEEP = (4.0, 1.0)   # Idle Sweep: one wave through the bands every 4 s, each band's gain 1 -/+ 1 at Drive 1 (in LIMIT)
# A band jumps when it rises faster than JUMP a second (raw audio's bands, eased over 0.08 s, rise at 4 a second and
# more on a hit; their frame-to-frame wobble at 1 or so); through the gate, every band rises at once for OPEN seconds,
# long enough for a hit to finish rising, then only falls, over Release. Between jumps a band follows itself smoothed
# over SLOW seconds: rising slowly but falling over Release, it rippled at every hit, and with a 0.05 s Release the
# ripple flipped reds near WCAG's line 3 times a second at Calm (the red flowers at 140 BPM, Drive 1).
JUMP, OPEN, SLOW = 3.0, 0.1, 1.0
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))


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


README = src('readme.txt').format(v=VERSION)
comp, page, source = new_effect(
    'video_vocoder', 'Video Vocoder',
    'Video Vocoder {}: a channel vocoder with the picture as the carrier, its octaves of detail gained by the '
    "music's bands: the bass pumps the big shapes, the treble sparkles the fine detail.".format(VERSION),
    README, tags=('vocoder', 'laplacian-pyramid', 'equalizer', 'audio-reactive'), audio=True, depth=True, flashing=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.4.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
for i, (name, label, chan, size) in enumerate(BANDS):
    p = custom(page, 'Float', name, label, 1.0,
               "How strong the picture's {} are, 0-3, before the music: 1 as they are, 0 gone, 3 three times as "
               "strong. The music's {} band drives it, swinging it no further above 1 than at 1.".format(
                   size, label.lower()), 0, 3, True)
    if i == 0:
        p.startSection = True
custom(page, 'Float', 'Drive', 'Drive', 0.75,
       "How much the music on input 2 moves each band, 0-1: a band of the music above its usual level makes its "
       'octave of the picture stronger, below it weaker. At 1 a band 0.25 above its usual level (of 0 to 1) doubles '
       'a fine octave; the three largest octaves swing half as far, since they move whole areas\' brightness. With '
       'nothing on input 2, how far Idle Sweep swings them.',
       0, 1, True).startSection = True
custom(page, 'Float', 'Release', 'Release', 0.25,
       'How long an octave takes to settle after the music makes it jump, in seconds, 0.05-1. It jumps up at once as '
       'often as Flashing allows (once a second at Calm); in between it follows the music smoothed over a second.',
       0.05, 1, True)
custom(page, 'Toggle', 'Sweep', 'Idle Sweep', True,
       'With nothing on input 2, a slow wave moves through the bands, finest to largest every 4 seconds, so you can '
       'see what each one holds. Off: the sliders alone.')
p = custom(page, 'Float', 'Depthfocus', 'Depth Focus', 0.5,
           'With a depth map or mask on input 3: how much the music moves only near things (or what lies inside the '
           'mask), 0-1. At 1 far things keep the sliders alone. Nothing changes without input 3.', 0, 1, True)
p.startSection = True
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

# ---- Audio (input 2): the music's seven bands ----------------------------------------------------
section('audio', "Audio (input 2): the music's seven bands, against their usual level")
audio = audio_in(comp, _ROOT)
bands = mk(comp, selectCHOP, 'bands', [audio], "The music's seven bands, lowest to highest.",
           channames=' '.join(b[2] for b in reversed(BANDS)))
rises = mk(comp, slopeCHOP, 'rises', [bands], 'How fast each band rises, a second.', timeslice=True)
ask = mk(comp, mathCHOP, 'ask', [rises], 'Above 0 while any band jumps (rises faster than {:g} a second): all seven '
         'ask to follow at once, as one.'.format(JUMP), chanop='max', postoff=-JUMP)
flash = flash_gate(comp, ask)
gate_open = mk(comp, triggerCHOP, 'open', [flash], 'Open for {:g} s from each jump the gate lets through.'.format(OPEN),
               attack=0, peak=1, peaklen=OPEN, decay=0, sustain=0, release=0)
bands_jump = mk(comp, lagCHOP, 'bands_jump', [bands],
                'Each band jumping up at once while the gate is open, and between jumps only falling, over Release.',
                lag1=Expr("0 if op('open')[0] > 0 else 3600"), lag2=par('Release'))
bands_steady = mk(comp, filterCHOP, 'bands_steady', [bands],
                  'Each band smoothed over {:g} s: how it moves between jumps (and with Flashing Off, all it '
                  'does).'.format(SLOW), width=SLOW)
bands_now = mk(comp, mathCHOP, 'bands_now', [bands_jump, bands_steady], 'Each band now: its jump or its steady '
               'level, whichever is higher.', chopop='max')
bands_usual = mk(comp, filterCHOP, 'bands_usual', [bands_now],
                 "Each band's usual level: its average over the last {:g} s.".format(USUAL), type='box', width=USUAL)
WIRED = "op('audio')['source'].eval() > 0"


def music(i, chan):
    """The music's gain for band i (0 the finest) now: its band against its usual level, or Idle Sweep's wave."""
    swing = ("{span} * (op('bands_now')['{c}'] - op('bands_usual')['{c}'])".format(span=SPAN[i], c=chan))
    wave = ("({amp} * math.sin(2 * math.pi * ((absTime.seconds % {period}) / {period} - {k} / 7)) "
            "if parent().par.Sweep else 0)").format(amp=SWEEP[1], period=SWEEP[0], k=i)
    return Expr('min(max(1 + parent().par.Drive * ({swing} if {wired} else {wave}), {lo}), {hi})'.format(
        swing=swing, wired=WIRED, wave=wave, lo=LIMIT[i][0], hi=LIMIT[i][1]))


# ---- Depth (input 3): the music moves near things ---------------------------------------------------
section('depth', 'Depth or a mask (input 3): the music moves near things, or what lies inside the mask')
flat = mk(comp, constantTOP, 'depth_none', comment='Near everywhere: with nothing on input 3 the music moves it all.',
          outputresolution='custom', resolutionw=1, resolutionh=1, colorr=1, colorg=1, colorb=1, alpha=1)
depth = depth_in(comp, fallback=flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black is no reading).',
            fmt='rgba16float', uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')

# ---- The picture's octaves ------------------------------------------------------------------------
section('pyramid', "The picture's octaves: the picture halved again and again (Gaussian pyramid)")
levels = pyramid(comp, _ROOT, source, len(BANDS))
section('collapse', 'Each octave gained by its band of the music, the smallest first, back up to the picture')
collapse = levels[-1]
for i in reversed(range(len(BANDS))):
    name, label, chan, size = BANDS[i]
    collapse = glsl(comp, 'collapse{}'.format(i), [levels[i], levels[i + 1], collapse, near],
                    lib_glsl(_ROOT, 'pyramid.glsl') + src('collapse.glsl'),
                    'The {} ({}), gained by {} and the music\'s {} band, and the octaves below added back.'.format(
                        size, label, label, label.lower()),
                    fmt=None if i == 0 else 'rgba32float',
                    uB=(par(name), music(i, chan),
                        Expr('parent().par.Depthfocus if parent().inputConnectors[2].connections else 0')))
    setpars(collapse, inputextenduv='hold')

finish_effect(comp, collapse, VERSION, page)
save_effect(comp, _HERE, _ROOT)
