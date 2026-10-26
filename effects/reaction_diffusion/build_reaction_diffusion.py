"""Build Reaction-Diffusion. Run from a textport:
__file__ = '/path/to/build_reaction_diffusion.py'; exec(open(__file__).read())

The live picture drawn by a reaction-diffusion pattern whose stripes follow its edges. Two chemicals react and
diffuse on a grid (the Gray-Scott model, Pearson 1993) and settle into stripes, spots or coral; the diffusion runs
faster along the picture's edges than across them (Witkin and Kass 1991), from lib structure_tensor(), so the
stripes run along its contours. Lines draws the picture by the width of its lines, as an engraving does; Dots and
Coral move their kill rate with the picture's darkness, so the pattern itself changes from dense to sparse.

The pattern lives in a Feedback loop at the grid's size (Size: the picture's, a half or a quarter), 32-bit float:
seed takes last frame's state, react steps the model Speed x RATE times a second (its Passes, each pass reading the
last), and look draws it at the picture's size. The beat moves only the drawing (a ripple), so the pattern keeps
its order; ripples come as often as Flashing allows.

The network, left to right:
  picture  source -> grid (the picture at the grid's size) -> structure_tensor() (tensor, tensor_h, tensor_v ->
           flow); seed (state_fb's state, this frame's kill rates, seeds where it may grow) -> react -> state_fb;
           look (the pattern drawn at the picture's size, rippled by the beats)
  grow     grid_fb -> moved (what moved lately); grow_from (Switch: only what Grow On needs cooks); exposure (the
           picture's darkest and brightest, eased) -> where (where it may grow, and the ink the picture asks for)
  audio    audio_in() -> counts -> steps -> ask (beats and drops as one) -> flash_limit -> flash (as often as
           Flashing allows) -> ring, beat_n (each ripple and where it starts); drop_step, flash -> drop_now (a
           ripple on a drop) -> drop_ring; level_pick -> level_smooth (bolder lines when loud)
  depth    input 3 (depth_in()) -> near -> find
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
PATTERNS = (('lines', 'Lines'), ('dots', 'Dots'), ('coral', 'Coral'))
# Each pattern's place in Gray-Scott's map (Pearson 1993): F, k where the picture asks for all ink, k where it asks
# for none, and V's range (for drawing). Lines and Dots sit just past where the even state turns unstable into
# stripes (or spots), whose waves turn readily along the edges (dev/protos/reaction_diffusion: a flow of concentric
# circles drew rings there, and mazes in Coral's region); Lines draws the picture by line width, so its k stays put.
# Dots' k runs from holes (dark) through a maze to spots (bright), Coral's from dense coral to scattered spots.
PATTERN = {'lines': (0.028, 0.0555, 0.0555, 0.03, 0.30),
           'dots': (0.030, 0.0555, 0.0615, 0.0, 0.34),
           'coral': (0.055, 0.0605, 0.0655, 0.0, 0.37)}
K_DEAD = 0.07        # where the pattern may not grow: it breaks into spots and fades
DU, DV = 0.21, 0.105
STRETCH = 3.0        # Follow Edges 1: diffusion 3 times faster along clear edges, 3 times slower across
DT = round(0.9 * 2 / (4 * DU * (STRETCH + 1 / STRETCH)), 4)   # the step, stable at the full stretch
CLEAR = 0.4          # the clarity (anisotropy) at which the stretch is full
CHANGE = (1e-5, 1e-4)   # the change (squared gradient per cell) from which a direction counts: 8-bit noise
                        # is about 5e-5, a soft edge 2e-3
RATE = 1200.0        # the model's time units a second at Speed 1
MAX_PASSES = 48      # steps in one frame at most, so a slow frame doesn't slow the next
TENSOR_SIGMA = 8.0   # the tensor's smoothing, in grid cells (about a stripe's spacing: 4 followed skin texture)
# How long the edges' direction and the ink the picture asks for take to ease to a new value (s). Followed at once,
# the drifting smoke on the dancer clip turned and thickened the stripes back and forth: 1.5 flashes a second more
# than the clip's own, the same with no beat (dev/flash.py, counted after the pattern had grown in).
TENSOR_EASE, INK_EASE = 0.5, 0.25
# After a start or Reset the drawing shows the ink the picture asks for as an even tone while the pattern grows in,
# and from FADE_IN s crossfades into it over as long again.
FADE_IN = 2.0
SEEDS = (12.0, 0.004, 30.0)   # a seed's block (cells), its chance per draw, draws a second
MOVE_LASTS = 1.0     # Grow On Movement: how long what moved keeps the pattern growing (s)
EXPOSE = 1.0         # how long the picture's darkest and brightest take to ease to a new level (s)
LEAST_RANGE = 0.2    # a flatter picture than this isn't stretched further (its noise would be)
SIZES = (('fine', 'Fine'), ('medium', 'Medium'), ('coarse', 'Coarse'))
SIZE_RES = ('useinput', 'half', 'quarter')
GROW_ON = (('everywhere', 'Everywhere'), ('brightness', 'Brightness'), ('movement', 'Movement'),
           ('depth', 'Depth (Input 3)'), ('mask', 'Mask (Input 3)'))
COLORS = (('ink', 'Ink on Paper'), ('over', 'Over the Picture'), ('light', 'Light on Dark'),
          ('orangeblue', 'Orange and Blue'))
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
# The music. Each beat sends a ripple out across the picture in RING s (to the farthest corner), from a point that
# turns round the middle by the golden angle each beat, RING_FROM picture heights out: across a band RING_W picture
# heights wide the drawing reads the pattern from up to DEPTH grid cells farther out and then in (at Beat Kick 1), so
# the stripes slide out and back. It moves the drawing, not the pattern: rings that turned the pattern over (ink to
# paper) at every beat scrambled it into a maze that never settled along the edges. A drop sends one from the middle,
# DROP times as broad and DROP_DEPTH times as deep, over DROP_TIME s. The stripes are about as wide as the flash
# test's cells (20 px), so a slide swings a cell between light and dark: on the dancer, Beat Kick 1 at 140 BPM and the
# default under the test's 8 beats and a drop a second each added a flash a second or more (dev/flash.py), so beats and
# drops pass through the flash gate (Flashing).
# Loudness 1 shifts the ink by up to LOUD (bolder lines when loud, finer when quiet), eased over half a second.
RING, RING_FROM, RING_W, DEPTH = 0.6, 0.25, 0.08, 6.0
DROP, DROP_DEPTH, DROP_TIME, LOUD = 3.0, 2.0, 1.2, 0.15
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right, nearer
# than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale), as in Fluid.
STAND_OUT, FAR, BRIGHT_FAR = 0.1, (0.5, 0.05), 0.5


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu_index(name):
    return Expr('parent().par.{}.menuIndex'.format(name))


def per_pattern(i):
    return Expr('{}[parent().par.Pattern.menuIndex]'.format([PATTERN[n][i] for n, _ in PATTERNS]))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


README = src('readme.txt').format(v=VERSION)
comp, page, source = new_effect(
    'reaction_diffusion', 'Reaction-Diffusion',
    'Reaction-Diffusion {}: the live picture drawn by a growing reaction-diffusion pattern whose stripes follow its '
    'edges, from the papers.'.format(VERSION),
    README, tags=('reaction-diffusion', 'gray-scott', 'turing-pattern', 'engraving', 'generative', 'audio-reactive'),
    audio=True, depth=True, flashing=True, sample="app.samplesFolder + '/Map/Nature/Movie.4.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Pattern', 'Pattern', PATTERNS, 'lines',
     'Lines draws stripes along the edges, broad where the picture is dark and thin where it is bright, like an '
     'engraving. Dots draws holes in the dark, a maze in between and spots in the light. Coral grows a branching '
     'coral, dense where the picture is dark and scattered where it is bright.').startSection = True
menu(page, 'Size', 'Size', SIZES, 'medium',
     "How big the pattern is, Fine, Medium or Coarse, each twice the last. The pattern grows on a grid the "
     "picture's size, half or a quarter of it, so Fine costs four times Medium.")
custom(page, 'Float', 'Follow', 'Follow Edges', 1.0,
       "How much the stripes turn to run along the picture's edges, 0-1. At 0 they wander every way.", 0, 1, True)
custom(page, 'Float', 'Speed', 'Speed', 1.0,
       'How fast the pattern grows and reshapes as the picture changes, 0.25-2.', 0.25, 2, True)
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Clear the pattern; it grows back from new seeds.')
menu(page, 'Growon', 'Grow On', GROW_ON, 'everywhere',
     'Where the pattern grows: everywhere, on what is bright, on what moved in the last second, on what stands in '
     'front of its surroundings in the depth map on input 3, or inside the mask on input 3 (white inside). '
     'Elsewhere it breaks up and fades.').startSection = True
custom(page, 'Float', 'Sense', 'Sensitivity', 0.5,
       'How easily the pattern grows: dimmer brightness, slower movement, farther depth or a grayer mask counts as '
       'well.', 0, 1, True).enableExpr = "me.par.Growon != 'everywhere'"
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.').enableExpr = "me.par.Growon in ('depth', 'mask')"
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Growon in ('depth', 'mask') and me.par.Depthtype == 'meters'"
custom(page, 'Float', 'Inklevel', 'Ink Level', 0.5,
       "How much ink the picture's middle brightness takes, 0-1: lower for a lighter drawing, higher for a darker "
       "one. The picture's brightness is stretched between its darkest and brightest first, so a gray river reads "
       'as well as a dark stage; that follows the picture over a second.', 0, 1, True).startSection = True
custom(page, 'Float', 'Contrast', 'Contrast', 1.0,
       "How strongly the picture's brightness sets the ink, 0-2. At 1 it runs from all ink at its darkest to none "
       "at its brightest; at 0 the pattern is the same everywhere and only its direction follows the picture.",
       0, 2, True)
menu(page, 'Colors', 'Colors', COLORS, 'ink',
     'Ink on paper, the ink over the picture itself, light lines on black where the picture is bright, or blue ink '
     'on orange.')

custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'How deep the ripple is that the beats of input 2 send across the picture, 0-1: the stripes it passes slide '
       'out and back, as through a wave in glass. Each starts from another place. A ripple swings the stripes '
       'between light and dark, so it counts as a flash: Calm sends one a second at most (every second or third '
       'beat at dance tempos), Up to 3 per second every beat up to 180 BPM, Off none.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much louder music on input 2 thickens the lines (and quiet passages thin them), 0-1. It eases over half '
       'a second.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a drop sends a broad, deep ripple out from the middle (a flash, as Beat "
       "Kick's; Fosfora's drop detection is experimental).")

# ---- Audio (input 2) ------------------------------------------------------------------------------
section('audio', 'Audio (input 2): ripples on the beats, through the flash gate; bolder lines when loud')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
# One channel for beats and drops, so the gate lets one ripple through a second at Calm, whichever asks: gated
# apart, a beat's ripple and a drop's each came once a second, and Beat Kick 1 measured 3.0 flashes a second at Calm
# under the test's drop a second (dev/flash.py).
ask = mk(comp, mathCHOP, 'ask', [steps], 'Beats and drops as one, asking to ripple.', chanop='max')
flash = flash_gate(comp, ask)
ring = mk(comp, triggerCHOP, 'ring', [flash],
          "Each ripple: 0 to 1 over {:g} s as it crosses the picture, then 0.".format(RING),
          attack=RING, peak=1, peaklen=0, decay=0, sustain=0, release=0)
beat_n = mk(comp, countCHOP, 'beat_n', [flash], 'Ripples so far: where each starts.')
drop_step = mk(comp, selectCHOP, 'drop_step', [steps], 'A drop arriving (Fosfora, experimental).',
               channames='drop_count')
drop_now = mk(comp, mathCHOP, 'drop_now', [flash, drop_step], 'A ripple that passed the gate on a drop.',
              chopop='mul')
drop_ring = mk(comp, triggerCHOP, 'drop_ring', [drop_now],
               "A drop's broad ripple: 0 to 1 over {:g} s, then 0.".format(DROP_TIME),
               attack=DROP_TIME, peak=1, peaklen=0, decay=0, sustain=0, release=0)
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick],
           'Loudness eased over half a second, so the lines thicken and thin instead of jittering.', width=0.5)
WIRED = "op('audio')['source'].eval() > 0"

# ---- Depth (input 3) ------------------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): what the pattern grows on')
depth = depth_in(comp)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black is no reading).', fmt='rgba16float',
            uNear=(menu_index('Depthtype'), par('Maxdist')))
setpars(near, outputresolution='quarter')
find = glsl(comp, 'find', [near], lib_glsl(_ROOT, 'depth_find.glsl'),
            'In the depth: what stands in front of what lies left and right of it, nearer than a limit (Sensitivity).',
            fmt='rgba16float',
            uFind=(0, STAND_OUT, Expr('max({0} * ({1} / {0}) ** parent().par.Sense, 0 if parent().inputConnectors[2]'
                                      '.connections else {2})'.format(FAR[0], FAR[1], BRIGHT_FAR))))

# ---- The picture at the grid's size, and its edges -------------------------------------------------
section('grid', "The picture at the pattern's grid size (Size)")
grid = glsl(comp, 'grid', [source], src('grid.glsl'), "The picture at the grid's size: each cell the mean of its "
            'pixels.')
setpars(grid, inputfiltertype='mipmap',
        outputresolution=Expr('{}[parent().par.Size.menuIndex]'.format(list(SIZE_RES))))
section('edges', "Edges: which way the picture's edges run (structure tensor)")
st = structure_tensor(comp, _ROOT, grid, sigma=Expr('{} * {}[parent().par.Size.menuIndex]'.format(
    TENSOR_SIGMA, [720 / 720, 720 / 360, 720 / 180])), ease=TENSOR_EASE)
flow = st['flow']

# ---- Where it grows -------------------------------------------------------------------------------
section('grow', 'Where it grows (Grow On) and how much ink the picture asks for', lane='grow')
none = mk(comp, constantTOP, 'none', comment='Nothing, not yet set (alpha 0): Grow On Everywhere or Brightness, and '
          'where moved and exposure start.', outputresolution='custom', resolutionw=1, resolutionh=1,
          colorr=0, colorg=0, colorb=0, alpha=0)
grid_fb = mk(comp, feedbackTOP, 'grid_fb', [grid], "The grid's picture last frame.", top='grid')
moved_fb = mk(comp, feedbackTOP, 'moved_fb', [none], "moved's last frame.", top='moved')
moved = glsl(comp, 'moved', [grid, grid_fb, moved_fb], lib_glsl(_ROOT, 'common.glsl') + src('moved.glsl'),
             'What moved in the last moment: the change in brightness, held for a second.', fmt='r16float',
             uM=(Expr('min(absTime.stepSeconds, 0.1)'), MOVE_LASTS))
grow_from = mk(comp, switchTOP, 'grow_from', [none, moved, find, near],
               'What Grow On needs (movement, the depth, the mask), else nothing: only that one cooks.',
               index=Expr("{'movement': 1, 'depth': 2, 'mask': 3}.get(parent().par.Growon.eval(), 0)"))
expo_fb = mk(comp, feedbackTOP, 'exposure_fb', [none], "exposure's last frame.", top='exposure')
expo = glsl(comp, 'exposure', [grid, expo_fb], lib_glsl(_ROOT, 'common.glsl') + src('exposure.glsl'),
            "The picture's darkest and brightest, eased over a second: what its brightness is stretched between.",
            res=(1, 1), fmt='rgba32float', uX=(Expr('min(absTime.stepSeconds, 0.1)'), EXPOSE))
setpars(expo, inputfiltertype='mipmap')
where_fb = mk(comp, feedbackTOP, 'where_fb', [none], "where's last frame.", top='where')
grow = glsl(comp, 'where', [grid, grow_from, expo, where_fb], lib_glsl(_ROOT, 'common.glsl') + src('where.glsl'),
            'Where the pattern may grow (Grow On, Sensitivity), and how much ink the picture asks for (Ink Level, '
            'Contrast).',
            fmt='rgba16float',
            uW=(menu_index('Growon'), par('Sense'), par('Contrast'), Expr("1 if parent().par.Colors == 'light' else 0")),
            uG=(par('Inklevel'), Expr("{} * parent().par.Loudness * (op('level_smooth')[0] - 0.5) * 2 if {} else 0".format(
                LOUD, WIRED)), LEAST_RANGE),
            uE=(Expr('min(absTime.stepSeconds, 0.1)'), INK_EASE))

# ---- The pattern ----------------------------------------------------------------------------------
section('pattern', 'The pattern: Gray-Scott reaction-diffusion, its diffusion steered along the edges')
still = mk(comp, constantTOP, 'still', comment='An empty grid (U 1, V 0): where the pattern starts, and Reset.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=1, colorg=0, colorb=0, alpha=0)
state_fb = mk(comp, feedbackTOP, 'state_fb', [still], 'The pattern last frame.', top='react')
seed = glsl(comp, 'seed', [grid, state_fb, grow], lib_glsl(_ROOT, 'common.glsl') + src('seed.glsl'),
            "The pattern last frame, this frame's kill rates, and seeds where it may grow but hasn't.",
            fmt='rgba32float',
            uK=(per_pattern(0), per_pattern(1), per_pattern(2), K_DEAD),
            uS=(clock_seconds(), SEEDS[1], SEEDS[0], SEEDS[2]))
react = glsl(comp, 'react', [seed, flow], src('react.glsl'),
             'The pattern, a few steps of the Gray-Scott model on, diffusing faster along the edges (Follow Edges).',
             fmt='rgba32float', uR=(DU, DV, DT, Expr('{} * parent().par.Follow'.format(round(math.log(STRETCH), 6)))),
             uA=(CLEAR,) + CHANGE)
setpars(react, npasses=Expr('max(1, min({}, round(parent().par.Speed * {} * min(absTime.stepSeconds, 0.05) / {})))'.format(
    MAX_PASSES, RATE, DT)))
section('look', "The look: the pattern drawn at the picture's size, in ink, rippled by the beats")
look = glsl(comp, 'look', [source, react, grow, expo], lib_glsl(_ROOT, 'common.glsl') + src('look.glsl'),
            "The pattern drawn at the picture's size: ink by line width (Lines) or where V is (Dots, Coral); the "
            "beats' ripples.",
            uL=(menu_index('Pattern'), menu_index('Colors'), per_pattern(3), per_pattern(4)),
            uB=(Expr("op('ring')[0]"), Expr("op('beat_n')[0] % 4096 * 2.3999632"),
                Expr('parent().par.Kick * {}'.format(DEPTH)), RING_W),
            uF=(FADE_IN,),
            uR=(RING_FROM, DROP, DROP_DEPTH, Expr("op('drop_ring')[0] if parent().par.Moments else 0")))

section('pattern')
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset: the pattern starts again from an empty grid, and '
          'fades in again.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        op('state_fb').par.resetpulse.pulse()\n"
              "        op('exposure_fb').par.resetpulse.pulse()\n")
setpars(reset, op='..', pars='Reset', onpulse=True, valuechange=False)

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
