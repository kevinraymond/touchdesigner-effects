"""Build Frost. Run from a textport: __file__ = '/path/to/build_frost.py'; exec(open(__file__).read())

Ice grown over the live picture, as frost grows on a window: from the picture's edges and the frame's rims, where
the room behind is far or dark, thawing where something stands out or moves. Fern grows it as R. Kobayashi's phase
field (Physica D 1993), steered as T. Kim and M. C. Lin steered it (SCA 2003), its arms along the picture's edges;
Stars as C. A. Reiter's hexagonal cellular model (2005); Dew as breath figures, droplets that grow and merge (Beysens
and Knobler 1986). The glass draws Fern's heat out toward a temperature the picture sets, and what stands out in front
or moves (lib warmth()) melts the ice. Fern's and Stars' ice is drawn as frost looks, a translucent body that blurs
and lights the picture behind it, edges and arms that catch the light; Dew's droplets as small lenses over a haze.

dev/protos/frost/offline.py and dew.py tried it first on the clips (board #4846): drawn out fast, the heat let the ice
grow in compact sheets that swallowed the frame; many crystals crowded into coral; a flat white fill read as paper
cut-outs. In TouchDesigner, warming the ice's temperature through the glass kept a thawed patch unfreezable for 10 s,
so warmth melts the ice instead, and a faint warmth (drifting haze) wore Stars down to specks until it was cut off.

The network, left to right:
  picture  source -> grid (the picture at the grid's size) -> structure_tensor() (tensor, tensor_h, tensor_v,
           tensor_fb, tensor_ease -> flow); edges (the flow, or nothing in Dew) -> pane (+ pane_fb: cold, warm,
           where crystals start) -> seed (+ ice_fb: last frame's ice, new crystals, how long frozen) -> fern
           (Kobayashi's steps) or stars (Reiter's half-steps) -> ice (Switch: only the Style's cooks) -> look (the
           ice drawn over the picture) -> show (Switch: the Style's look)
  dew      dew_grow (+ dew_fb: the droplets last frame) -> dew_merge -> dew_level -> dew_look (the droplets drawn)
  motion   optical_flow() (no flow: lum8, seen, change, change_avg, clock) -> warmth() (+ warmth_fb: what stands out
           and what moves, quick to warm, slow to cool); clear is where every Feedback TOP starts
  audio    audio_in() -> counts -> steps (a beat or a drop this frame) -> glint (a beat's glint); level_pick ->
           level_smooth (louder grows faster); bass_pick -> bass_smooth (bass warms what stands out)
  depth    input 3 (depth_in()) -> near (nearness at a quarter size: the cold) -> find (what stands out, or the mask)
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
STYLES = (('fern', 'Fern'), ('stars', 'Stars'), ('dew', 'Dew'))
SIZES = (('fine', 'Fine'), ('medium', 'Medium'), ('coarse', 'Coarse'))
SIZE_RES = ('useinput', 'half', 'quarter')
INPUT3 = (('depth', 'Depth Map'), ('mask', 'Mask'))
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
# Fern: Kobayashi's constants (eps_bar, tau, alpha, gamma), with the grid step DX and model step DT a cell and a step
# (his 0.03 and 1e-4 gave arms twice as thick for the cells; DT keeps his DT / DX^2), K and DELTA for thin arms that
# branch (dev/protos/frost: K 2.2 grew thinner arms but half as fast; DELTA 0.02 grew rounder ones).
EPS, TAU, ALPHA, GAMMA = 0.01, 3e-4, 0.9, 10.0
DX, DT, K, DELTA = 0.0625, 4.5e-4, 2.0, 0.06
# How the glass steers it: it draws T toward its own temperature at SINK per unit of model time (2 grew compact sheets),
# UNDER below the melting point where coldest; warm ice melts at MELT per unit of model time and its interface tips
# toward melting by PUSH, leaving T alone (warming T through the glass kept a thawed patch unfreezable for 10 s and
# more); NOISE sets off side branches.
SINK, UNDER, MELT, PUSH, NOISE = 0.5, 1.3, 60.0, 0.45, 0.01
# Stars: Reiter's gamma and beta (needle-like arms with side branches), how fast the glass condenses vapor (a share a
# step) and melts warm ice (a step).
R_GAMMA, R_BETA, R_SUPPLY, R_MELT = 1e-4, 0.4, 0.002, 0.02
RATE = 600.0        # model steps a second at Growth 1: an arm's tip runs about 0.04 cells a step, 24 cells a second
MAX_STEPS = 32      # steps in one frame at most, so a slow frame doesn't slow the next
LOUD = 0.8          # Loudness 1: growth from 1 - LOUD / 2 times when silent to 1 + LOUD / 2 at full loudness
# New crystals: CRYSTALS a second on the picture's cold edges at Crystals 1, RIMS a second along the frame's rims at
# Rims 1, KICK on a beat at Beat Crystals 1 (DROP_KICK times as many on a drop).
CRYSTALS, RIMS, KICK, DROP_KICK = 2.0, 40.0, 16.0, 4.0
# A beat also makes the ice glint (its edges GLINT_EDGE times as bright, its sparkles GLINT_SPARK times, falling off
# over GLINT_TIME s) and grow in a spurt (SPURT times as many steps that frame) at Beat Crystals 1.
GLINT_TIME, GLINT_EDGE, GLINT_SPARK, SPURT = 0.2, 1.0, 3.0, 3.0
EDGE = (2e-4, 2e-3)  # the change (squared gradient a pixel at 720 high) from which an edge starts crystals, and fully
TENSOR_SIGMA, TENSOR_EASE = 4.0, 0.5   # the edges' direction: smoothed over cells, eased over seconds
COLD_EASE = 1.0      # how long the cold takes to follow the picture (s)
THICKEN = 1.5        # how long ice takes to thicken (s)
# The look: the room's light the ice scatters, how bright its edges are, the middles of its arms, its grain.
LOOK = (0.35, 0.35, 0.7, 0.2)
# Warmth (lib warmth()): what stands out warms fully, movement of a change of MOVE_FULL in luma a frame does; it rises
# over RISE s and falls over FALL s, so a hand that moved leaves the glass to cool behind it. Bass Thaw 1 makes what
# stands out warm 1 + BASS_THAW times as much at full bass.
MOVE_FULL, RISE, FALL, BASS_THAW = 0.04, 0.15, 1.5, 1.0
# Dew: the droplets' atlas is DEW_N cells of the smallest level across the picture's longer side at Size Fine, Medium
# and Coarse (4 pixels a cell at Medium on 1280 x 720), stacked 1.875 times as tall (dew_atlas.glsl). Sizes are in
# pixels of a 1280-wide picture at Medium, scaled with Size: a new droplet's radius, the smallest kept, the largest;
# growth and drying are radius a second; DEW_NUC is the chance a second that a free cell starts a droplet at Crystals 1,
# DEW_KICK how many times more on a beat at Beat Crystals 1.
DEW_N = (640, 320, 160)
DEW_NEW, DEW_MIN, DEW_MAX = 0.5, 0.25, 10.0
DEW_GROW, DEW_DRY = 2.0, 8.0
DEW_NUC, DEW_KICK = 8.0, 3.0
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right, nearer
# than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale), as in Fluid.
STAND_OUT, FAR = 0.1, (0.5, 0.05)
DTF = Expr('min(absTime.stepSeconds, 0.1)')
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
    'frost', 'Frost',
    'Frost {}: ice grown over the live picture from its edges and the frame, thawing where it is near or moves, '
    'from the papers.'.format(VERSION),
    README, tags=('frost', 'ice', 'crystal', 'phase-field', 'generative', 'audio-reactive'),
    audio=True, depth=True, sample="app.samplesFolder + '/Map/Nature/Movie.4.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Style', 'Style', STYLES, 'fern',
     'Fern grows soft, branching ferns whose arms follow the picture\'s edges. Stars grows crisp six-armed stars of '
     'fine needles, all on one lattice, as snow crystals grow. Dew beads the glass with droplets that grow and merge, '
     'each a small lens.').startSection = True
menu(page, 'Size', 'Size', SIZES, 'medium',
     "How big the crystals are, Fine, Medium or Coarse, each twice the last. The ice grows on a grid the picture's "
     'size, half or a quarter of it, so Fine costs four times Medium.')
custom(page, 'Float', 'Growth', 'Growth', 1.0,
       'How fast the ice grows and thaws, 0.25-2.', 0.25, 2, True)
custom(page, 'Float', 'Crystals', 'Crystals', 0.5,
       "How many new crystals start each second on the picture's edges where it is cold, 0-1. In Dew, how quickly new "
       'droplets bead clear glass.', 0, 1, True)
custom(page, 'Float', 'Rims', 'From the Rims', 0.5,
       "How much frost creeps in from the frame's edges, 0-1.", 0, 1, True).enableExpr = "me.par.Style != 'dew'"

custom(page, 'Float', 'Follow', 'Follow Edges', 1.0,
       "How much the ferns' arms turn to run along the picture's edges, 0-1. At 0 they all point one way.",
       0, 1, True).enableExpr = "me.par.Style == 'fern'"
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Clear the glass; the frost grows back.')

custom(page, 'Float', 'Even', 'Freeze Evenly', 0.3,
       'At 0 only the far or dark parts of the picture freeze (the depth on input 3, else the picture\'s brightness); '
       'at 1 all of it freezes alike.', 0, 1, True).startSection = True
custom(page, 'Float', 'Thawmove', 'Thaw by Movement', 0.7,
       'How much whatever moves warms the glass, so the frost thaws there and grows back behind it, 0-1.', 0, 1, True)
custom(page, 'Float', 'Thawnear', 'Thaw by Nearness', 1.0,
       'How much what stands out in front in the depth map on input 3 (or what is inside the mask) warms the glass, '
       '0-1.', 0, 1, True)
menu(page, 'Input3', 'Input 3 Holds', INPUT3, 'depth',
     'Depth Map: what stands in front of its surroundings warms the glass (floors and walls drop out). Mask: what is '
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

custom(page, 'Float', 'Ice', 'Ice', 0.75,
       'How much the frost hides the picture behind it, 0-1.', 0, 1, True).startSection = True
custom(page, 'Float', 'Glow', 'Glow', 0.6,
       'How much the light behind shows through the frost, so it glows where a lamp is behind it, 0-1.', 0, 1, True)
tint = page.appendRGB('Tint', label='Tint')
for p, v in zip(tint, (0.93, 0.97, 1.0)):
    p.default = p.val = v
    p.normMin, p.normMax = 0, 1
    p.help = "The frost's color: a cold white."

custom(page, 'Float', 'Beatseeds', 'Beat Crystals', 0.5,
       "How many new crystals each beat of input 2 starts along the picture's cold edges, 0-1. In Dew, how many new "
       'droplets bead the clear glass on a beat.', 0, 1, True).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much louder music on input 2 makes the frost grow faster (and quiet passages slower), 0-1.', 0, 1, True)
custom(page, 'Float', 'Bassthaw', 'Bass Thaw', 0.5,
       'How much the bass of input 2 warms what stands out, so the frost backs away from it on the bass, 0-1.',
       0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a drop starts crystals all along the picture's edges at once (Fosfora's "
       'drop detection is experimental).')

# ---- Audio (input 2) ------------------------------------------------------------------------------
section('audio', 'Audio (input 2): crystals on the beats, faster growth when loud, bass warms')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick], 'Loudness eased over half a second.', width=0.5)
bass_pick = mk(comp, selectCHOP, 'bass_pick', [audio], 'How much bass there is now.', channames='bass')
bass = mk(comp, filterCHOP, 'bass_smooth', [bass_pick], 'The bass eased over a fifth of a second.', width=0.2)
glint = mk(comp, triggerCHOP, 'glint', [steps],
           "A beat's glint: 1 on the beat, falling over {:g} s.".format(GLINT_TIME),
           attack=0, peak=1, peaklen=0, decay=GLINT_TIME, sustain=0, release=0)
BEAT_NOW = "(op('steps')['beat_count'].eval() > 0)"
DROP_NOW = "(op('steps')['drop_count'].eval() > 0 and parent().par.Moments)"

# ---- Depth (input 3) ------------------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): the cold, and what stands out warms the glass')
depth = depth_in(comp)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness: far is cold. Depth Type flips distance (black is no reading).',
            fmt='rgba16float', uNear=(menu_index('Depthtype'), par('Maxdist')))
setpars(near, outputresolution='quarter')
find = glsl(comp, 'find', [near], lib_glsl(_ROOT, 'depth_find.glsl'),
            'What stands in front of what lies left and right of it (Depth Map), or inside the mask (Mask), nearer '
            'than a limit (Sensitivity).', fmt='rgba16float',
            uFind=(Expr("1 if parent().par.Input3 == 'mask' else 0"), STAND_OUT,
                   Expr("{0} * ({1} / {0}) ** parent().par.Sense if parent().par.Input3 == 'depth' else "
                        "0.95 - 0.9 * parent().par.Sense".format(FAR[0], FAR[1]))))

# ---- Movement and warmth ---------------------------------------------------------------------------
section('warmth', 'Warmth: what stands out and what moves warm the glass, quick to warm, slow to cool', lane='motion')
clear = mk(comp, constantTOP, 'clear', comment='Nothing yet (alpha 0): where the warmth, the pane and the ice start, '
           'and Reset.', outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
mo = optical_flow(comp, _ROOT, source, levels=(8,), flow=False)
warm = warmth(comp, _ROOT, find, mo, clear,
              subject_warms=Expr("parent().par.Thawnear * (1 + {} * parent().par.Bassthaw * op('bass_smooth')[0] if {} "
                                 "else 1) if parent().inputConnectors[2].connections else 0".format(BASS_THAW, WIRED)),
              move_warms=par('Thawmove'), full=MOVE_FULL, rise=RISE, fall=FALL)

# ---- The picture at the grid's size, and its edges -------------------------------------------------
section('grid', "The picture at the ice's grid size (Size)")
grid = glsl(comp, 'grid', [source], src('grid.glsl'), "The picture at the grid's size: each cell the mean of its "
            'pixels.')
setpars(grid, inputfiltertype='mipmap',
        outputresolution=Expr('{}[parent().par.Size.menuIndex]'.format(list(SIZE_RES))))
section('edges', "Edges: which way the picture's edges run (structure tensor)")
st = structure_tensor(comp, _ROOT, grid, sigma=Expr('{} * {}[parent().par.Size.menuIndex]'.format(
    TENSOR_SIGMA, [1, 2, 4])), ease=TENSOR_EASE)
flow = st['flow']

# ---- The pane ---------------------------------------------------------------------------------------
section('pane', 'The pane: cold where the room is far or dark, warm where something stands out or moves')
pane_fb = mk(comp, feedbackTOP, 'pane_fb', [clear], "pane's last frame.", top='pane')
edges = mk(comp, switchTOP, 'edges', [flow, clear], "The edges for where crystals start; Dew starts its droplets "
           'anywhere, so its tensor doesn\'t cook.', index=Expr("1 if parent().par.Style == 'dew' else 0"))
pane = glsl(comp, 'pane', [grid, edges, near, warm, pane_fb], src('pane.glsl'),
            'The glass: how cold (far or dark, eased), how warm, and where crystals may start (cold edges).',
            fmt='rgba16float', uC=(DTF, COLD_EASE, par('Even')), uE=EDGE)

# ---- The ice ----------------------------------------------------------------------------------------
section('ice', "The ice: Kobayashi's phase field (Fern) or Reiter's snow crystals (Stars), stepped as it grows")
ice_fb = mk(comp, feedbackTOP, 'ice_fb', [clear], 'The ice last frame.', top='ice')
STARS = "(1 if parent().par.Style == 'stars' else 0)"
seed = glsl(comp, 'seed', [pane, ice_fb], lib_glsl(_ROOT, 'common.glsl') + src('seed.glsl'),
            "The ice last frame, new crystals where they start (cold edges, the rims, the beats), and how long each "
            'cell has been frozen.', fmt='rgba32float',
            uN=(Expr('{} * parent().par.Crystals'.format(CRYSTALS)), Expr('{} * parent().par.Rims'.format(RIMS)),
                Expr("{} * parent().par.Beatseeds * ({} + {} * {}) if {} else 0".format(
                    KICK, BEAT_NOW, DROP_KICK, DROP_NOW, WIRED)), clock_seconds()),
            uI=(DTF, Expr(STARS), UNDER, R_BETA))
GROW = ("parent().par.Growth * ((1 - {0} / 2 * parent().par.Loudness + {0} * parent().par.Loudness * "
        "op('level_smooth')[0]) if {1} else 1)".format(LOUD, WIRED))
SPURTS = "(1 + {} * parent().par.Beatseeds * {} if {} else 1)".format(SPURT, BEAT_NOW, WIRED)
STEPS = 'max(1, min({}, round({} * {} * {} * min(absTime.stepSeconds, 0.1))))'.format(MAX_STEPS, RATE, GROW, SPURTS)
fern = glsl(comp, 'fern', [seed, pane, flow], lib_glsl(_ROOT, 'common.glsl') + src('fern.glsl'),
            "Fern: steps of Kobayashi's phase field, the arms along the picture's edges (Follow Edges), the heat drawn "
            'out by the glass, melting where warm.', fmt='rgba32float',
            uM=(EPS, DELTA, K, DT / TAU), uS=(DT, 1 / DX, ALPHA / math.pi, GAMMA),
            uP=(SINK, UNDER, 0, MELT), uT=(PUSH, NOISE, par('Follow'), clock_seconds()))
setpars(fern, npasses=Expr(STEPS))
stars = glsl(comp, 'stars', [seed, pane], src('stars.glsl'),
             "Stars: Reiter's snow-crystal steps on a hexagonal lattice, two passes a step (which cells are receptive, "
             'then the step); the glass condenses vapor where cold, warm ice melts.', fmt='rgba32float',
             uR=(R_GAMMA, R_BETA, R_SUPPLY, R_MELT))
setpars(stars, npasses=Expr('2 * ' + STEPS))
for g in (pane, seed, fern, stars):
    setpars(g, inputextenduv='hold')
ice = mk(comp, switchTOP, 'ice', [fern, stars], "The Style's ice: only that one cooks.",
         index=menu_index('Style'))
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset, or a new Style: the glass starts again clear (the '
          "styles' ice means different things).")
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        op('ice_fb').par.resetpulse.pulse()\n"
              "        op('dew_fb').par.resetpulse.pulse()\n"
              '\n'
              'def onValueChange(par, prev):\n'
              "    if par.name == 'Style':\n"
              "        op('ice_fb').par.resetpulse.pulse()\n"
              "        op('dew_fb').par.resetpulse.pulse()\n")
setpars(reset, op='..', pars='Reset Style', onpulse=True, valuechange=True)

# ---- The look -------------------------------------------------------------------------------------
section('look', 'The look: the ice drawn over the picture as frost on a window')
look = glsl(comp, 'look', [source, ice], lib_glsl(_ROOT, 'common.glsl') + src('look.glsl'),
            'The frost over the picture: a translucent body that blurs and lights the picture behind it, edges and '
            'arms that catch the light.',
            uL=(par('Ice'), par('Glow'), Expr(STARS), THICKEN),
            uTint=(par('Tintr'), par('Tintg'), par('Tintb')), uX=LOOK,
            uB=(Expr("{} * parent().par.Beatseeds * op('glint')[0] if {} else 0".format(GLINT_EDGE, WIRED)),
                Expr("{} * parent().par.Beatseeds * op('glint')[0] if {} else 0".format(GLINT_SPARK, WIRED))))
setpars(look, inputfiltertype='mipmap')

# ---- Dew ------------------------------------------------------------------------------------------
section('dew', 'Dew: breath figures, droplets that start on the clear glass, grow and merge, a level a size',
        lane='dew')
DEWI = 'parent().par.Size.menuIndex'
SCALE = '{}[{}]'.format([0.5, 1, 2], DEWI)      # sizes scale with Size
def dewpx(v):
    return Expr('{} / 1280 * {}'.format(v, SCALE))
dew_fb = mk(comp, feedbackTOP, 'dew_fb', [clear], 'The droplets last frame.', top='dew_level')
dew_grow = glsl(comp, 'dew_grow', [dew_fb, pane], lib_glsl(_ROOT, 'common.glsl') + src('dew_atlas.glsl') +
                src('dew_grow.glsl'),
                'The droplets grown where the glass is cold, dried where it is warm, each picking the one it goes into '
                'if it touches a bigger one.', fmt='rgba32float',
                uG=(DTF, Expr('{} * {}'.format(dewpx(DEW_GROW).text, GROW)), dewpx(DEW_DRY), dewpx(DEW_MAX)),
                uA=(dewpx(DEW_MIN),))
setpars(dew_grow, outputresolution='custom', resolutionw=Expr('{}[{}]'.format(list(DEW_N), DEWI)),
        resolutionh=Expr('int({}[{}] * 1.875)'.format(list(DEW_N), DEWI)))
dew_merge = glsl(comp, 'dew_merge', [dew_grow], src('dew_atlas.glsl') + src('dew_merge.glsl'),
                 'Droplets that touch become one, at their center of volume; one grown to half its cell moves up a '
                 'level.', fmt='rgba32float')
dew_level = glsl(comp, 'dew_level', [dew_merge, pane], lib_glsl(_ROOT, 'common.glsl') + src('dew_atlas.glsl') +
                 src('dew_level.glsl'),
                 'Droplets moving up a level, small ones going into the big ones they touch, and new ones on the clear '
                 'glass.', fmt='rgba32float',
                 uN=(Expr("{} * parent().par.Crystals * (1 + {} * parent().par.Beatseeds * ({} + {} * {}) / "
                          "max(absTime.stepSeconds, 0.001) / 60 if {} else 1)".format(
                              DEW_NUC, DEW_KICK, BEAT_NOW, DROP_KICK, DROP_NOW, WIRED)),
                     dewpx(DEW_NEW), DTF, clock_seconds()))
dew_look = glsl(comp, 'dew_look', [source, dew_level], lib_glsl(_ROOT, 'common.glsl') + src('dew_atlas.glsl') +
                src('dew_look.glsl'),
                'The dew over the picture: droplets as small lenses, a milky haze where they are too small to see.',
                uL=(par('Ice'), par('Glow'), LOOK[0]), uTint=(par('Tintr'), par('Tintg'), par('Tintb')),
                uB=(Expr("{} * parent().par.Beatseeds * op('glint')[0] if {} else 0".format(GLINT_EDGE, WIRED)),))
setpars(dew_look, inputfiltertype='mipmap')
section('look')
show = mk(comp, switchTOP, 'show', [look, dew_look], "The Style's look: only that one cooks.",
          index=Expr("1 if parent().par.Style == 'dew' else 0"))

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
