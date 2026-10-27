"""Build Chladni Sand. Run from a textport: __file__ = '/path/to/build_chladni_sand.py'; exec(open(__file__).read())

The picture's light moved like sand on a vibrating plate. Chladni (1787) strewed sand on a plate and bowed it: the sand
leaves the parts that shake and gathers on the nodal lines, the parts that keep still, drawing a figure. Here the
plate's figure comes from the music: each of lib audio_in()'s seven bands sets one of the square plate's modes
(Wheatstone, 1833: cos(n pi x) cos(m pi y) - cos(m pi x) cos(n pi y), the lowest band the fewest lines), weighted by how
far the band has risen above its usual level, and each beat strikes the plate through the flash gate. The picture's
light is the sand: carried along the plate's flow with its mass kept, it piles on the lines in the picture's own colors
and drains from between them, then settles back to the live picture between strikes. With nothing on input 2, Idle
Strike strikes the plate every 2 s, each time in the next mode.

dev/protos/chladni/offline.py tried it first on the clips with a song, as sand (this) and as a warp of the picture
(Motion Magnify's carried displacement), which read as a liquid lens rather than sand (board #4724).

The network, left to right:
  picture  source -> sand (the light carried along the plate's flow, its mass gathering on the lines; sand_fb) -> show
           (lit by its mass) -> out
  plate    plate (the figure and its flow, at a quarter size, from figure's weights and Depth Focus)
  audio    audio_in() -> bands -> bands_now (over a second) -> bands_usual (the last 4 s); counts -> steps and
           idle_count -> idle_steps -> strike_ask -> flash_gate() -> strike_env (a strike ringing down); figure (the
           seven modes' weights and how hard the plate shakes), read by plate
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
BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')   # audio_in()'s, lowest first
# The plate shakes as hard as SWELL x Swell x the largest rise of a band above its usual level, plus KICK x Strike as a
# strike rings down over RING s, at most SHAKE. A band is smoothed over SLOW s and its usual level is its average over
# USUAL s; each mode's weight is the band's rise plus FLOOR of the band, so some figure is always there to strike.
SWELL, KICK, RING, SHAKE = 1.0, 2.0, 0.35, 1.5
SLOW, USUAL, FLOOR = 1.0, 4.0, 0.15
SPEED = 0.44         # the sand's speed at Speed 1 where the plate shakes hardest, in picture heights a second
IDLE = 2.0           # Idle Strike: a strike every 2 s, each in the next mode
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
PERF = '0.6'         # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


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
    'chladni_sand', 'Chladni Sand',
    "Chladni Sand {}: the picture's light moved like sand on a vibrating plate, piling on the lines of a figure the "
    'music sets and settling back between beats.'.format(VERSION),
    README, tags=('chladni', 'cymatics', 'sand', 'audio-reactive'), audio=True, depth=True, flashing=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.1.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
custom(page, 'Float', 'Speed', 'Speed', 1.0,
       'How fast the sand travels toward the lines, 0.25-2. At 1 it moves up to nearly half the picture\'s height in '
       'a second while the plate shakes hardest.', 0.25, 2, True).startSection = True
custom(page, 'Float', 'Settle', 'Settle', 0.4,
       'How long the picture takes to come back after the sand moves, in seconds, 0.1-2. Short lets the figure '
       'form on each strike and clear between them; long keeps it hanging.', 0.1, 2, True)
custom(page, 'Float', 'Strike', 'Strike', 0.75,
       'How hard each beat on input 2 strikes the plate, 0-1. A strike rings down over a third of a second. The plate '
       'is struck as often as Flashing allows.', 0, 1, True).startSection = True
custom(page, 'Float', 'Swell', 'Swell', 0.5,
       "How much the music's bands rising above their usual level shake the plate between beats, 0-1. It follows "
       'them smoothed over a second.', 0, 1, True)
custom(page, 'Toggle', 'Idle', 'Idle Strike', True,
       'With nothing on input 2, the plate is struck every 2 seconds, each time in the next of its seven figures, so '
       'you can see them. Off: the picture rests. Flashing Off stops it too.')
p = custom(page, 'Float', 'Depthfocus', 'Depth Focus', 0.5,
           'With a depth map or mask on input 3: how much the sand moves only on near things (or inside the mask), '
           '0-1. At 1 far things stay still. Nothing changes without input 3.', 0, 1, True)
p.startSection = True
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

# ---- Audio (input 2): the figure from the bands, a strike on each beat ------------------------------
section('audio', "Audio (input 2): the plate's figure from the music's bands, a strike on each beat")
audio = audio_in(comp, _ROOT)
WIRED = "op('audio')['source'].eval() > 0"
bands = mk(comp, selectCHOP, 'bands', [audio], "The music's seven bands, lowest to highest.", channames=' '.join(BANDS))
bands_now = mk(comp, filterCHOP, 'bands_now', [bands], 'Each band smoothed over {:g} s.'.format(SLOW), width=SLOW)
bands_usual = mk(comp, filterCHOP, 'bands_usual', [bands_now],
                 "Each band's usual level: its average over the last {:g} s.".format(USUAL), type='box', width=USUAL)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
idle_count = mk(comp, constantCHOP, 'idle_count',
                comment='Idle Strike: a count that goes up every {:g} s while nothing is on input 2.'.format(IDLE),
                const0name='idle', const0value=Expr('int(absTime.seconds / {:g}) % 1024 if parent().par.Idle and not '
                                                    '{} else 0'.format(IDLE, WIRED)))
idle_steps = mk(comp, slopeCHOP, 'idle_steps', [idle_count], 'Above 0 on the frame Idle Strike strikes.',
                timeslice=True)
strike_ask = mk(comp, mathCHOP, 'strike_ask', [steps, idle_steps], 'A beat or an idle strike asking to strike.',
                chopop='max')
flash = flash_gate(comp, strike_ask)
strike_env = mk(comp, triggerCHOP, 'strike_env', [flash], 'A strike: up at once, ringing down over {:g} s.'.format(RING),
                attack=0, peak=1, decay=RING, sustain=0, release=0)
RISE = "max(op('bands_now')[{k}] - op('bands_usual')[{k}], 0)"
weights = ["{rise} + {floor} * op('bands_now')[{k}] if {wired} else (1 if int(absTime.seconds / {idle:g}) % 7 == {k} "
           "else 0)".format(rise=RISE.format(k=k), floor=FLOOR, wired=WIRED, idle=IDLE, k=k) for k in range(7)]
shake = ("min(({swell} * parent().par.Swell * max({rises}) if {wired} else 0) + {kick} * parent().par.Strike * "
         "op('strike_env')[0], {top})").format(swell=SWELL, rises=', '.join(RISE.format(k=k) for k in range(7)),
                                               wired=WIRED, kick=KICK, top=SHAKE)
figure = mk(comp, constantCHOP, 'figure', comment="The plate: each mode's weight (w0, the sub bass's, to w6) and how "
            'hard it shakes (shake).')
figure.seq.const.numBlocks = 8
for k, text in enumerate(weights + [shake]):
    setpars(figure, **{'const{}name'.format(k): 'w{}'.format(k) if k < 7 else 'shake',
                       'const{}value'.format(k): Expr(text)})


def chan(i):
    return Expr("op('figure')[{}]".format(i))


# ---- Depth (input 3): the sand moves on near things --------------------------------------------------
section('depth', 'Depth or a mask (input 3): the sand moves on near things, or inside the mask')
flat = mk(comp, constantTOP, 'depth_none', comment='Near everywhere: with nothing on input 3 the sand moves everywhere.',
          outputresolution='custom', resolutionw=1, resolutionh=1, colorr=1, colorg=1, colorb=1, alpha=1)
depth = depth_in(comp, fallback=flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black is no reading).',
            fmt='rgba16float', uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')

# ---- The plate ----------------------------------------------------------------------------------------
section('plate', "The plate: its figure from the music's bands, and the flow that carries sand to the figure's lines",
        lane='plate')
plate = glsl(comp, 'plate', [source, near], src('plate.glsl'),
             "The plate's seven modes summed by figure's weights: the sand's flow toward the nodal lines and where it "
             'gathers (a quarter size).', fmt='rgba32float',
             uW0=(chan(0), chan(1), chan(2), chan(3)), uW1=(chan(4), chan(5), chan(6), chan(7)),
             uP=(Expr('{} * parent().par.Speed'.format(SPEED)),
                 Expr('parent().par.Depthfocus if parent().inputConnectors[2].connections else 0')))
setpars(plate, outputresolution='quarter')

# ---- The sand -----------------------------------------------------------------------------------------
section('sand', "The sand: the picture's light carried along the flow, piling on the lines and settling back")
empty = mk(comp, constantTOP, 'empty', comment='Nothing yet: where the sand starts (alpha 0, so sand takes the picture).',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float', colorr=0, colorg=0, colorb=0,
           alpha=0)
sand_fb = mk(comp, feedbackTOP, 'sand_fb', [empty], "sand's last frame.", top='sand')
sand = glsl(comp, 'sand', [source, sand_fb, plate], src('sand.glsl'),
            "The picture's light carried along the plate's flow, its mass gathering where the flow converges, both "
            'settling back to the live picture.', fmt='rgba32float',
            uS=(Expr('min(absTime.stepSeconds, 0.1)'), par('Settle')))
show = glsl(comp, 'show', [source, sand], src('show.glsl'),
            'The sand lit by how much of it lies there: brighter piled on the lines, darker where it drained.')
for o in (plate, sand, show):
    setpars(o, inputextenduv='hold')

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
