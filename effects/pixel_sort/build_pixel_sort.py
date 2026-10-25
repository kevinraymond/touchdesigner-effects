"""Build Pixel Sort. Run from a textport: __file__ = '/path/to/build_pixel_sort.py'; exec(open(__file__).read())

A real pixel sort, live. Along lines across the picture toward the sort's angle, runs of pixels (spans: those whose
brightness lies between two thresholds, those between the picture's edges, those inside a depth map or mask, or whole
lines, all optionally cut at random) are sorted by brightness, hue or saturation, so each span becomes a streak from
its lowest value to its highest. Every span of every line is fully sorted, every frame.

key decides, for each pixel, the value it sorts by and whether it lies in a span (with hysteresis against its last
frame, so span ends don't flicker with the picture's noise) or cuts its line. sort is a compute shader: one workgroup
a line, a digital line toward the angle (so every pixel is in exactly one line and nothing is resampled), which finds
the spans, sorts the whole line once by (span start, value, place) in shared memory, and writes each pixel back where
it lands (dev/probes/compute_sort.py: 1 ms on the reference Mac for every row of 1280 x 720).

The network, left to right:
  picture  source (+ key_fb) -> key -> sort (with source); depth (input 3, else the brightness) -> key
  audio    audio_in() -> counts -> steps (Slope CHOP); steady counts the time; beat_on, bar_on, steady_on pick the flips
           asked for and drop_on the drops -> flash_gate() -> flash_budget -> drop_kind; drop_pulse -> whole (every line
           sorted whole for Length); flip_pulse -> flip_n -> flip_parity (the sort turned end over end); beats (or
           steady ticks with nothing wired) -> beat_pulse -> beat_env, beat_n (each beat's tears); level_smooth ->
           widen_to -> widen (how much wider the spans are); spin_rate -> turned (Spin)
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
STEADY = 2.0         # flips this many seconds apart for Steady, and for On Beats or On Bars with nothing wired
TEAR = 0.15          # seconds a beat's tears stay open
HYSTERESIS = 0.04    # how far past Low or High (or the depth's) a pixel must go to leave or join a span
# How far loudness and a build may narrow and widen the spans: wider moves Low that share of the way to black and High
# to white (Edge and Cut Every follow), narrower moves both toward their middle. A fixed amount added to both ends
# sorted the whole picture under a loud build (Low 0.25 less 0.35).
WIDEN = (0.5, 0.6)
WIDEN_GLIDE = 0.5    # the spans widen or narrow by at most this much a second
# How fast Spin may turn the angle (degrees a second). Turning moves the steps in the digital lines, so pixels change
# lines and each span they leave or join re-sorts from end to end: with Flashing Off the plaza measured 1.5 flashes a
# second over the clip's 0.5 at 20 and 45, and none added at 10 (dev/flash.py).
SPIN_MAX = 10.0
# Workgroups the sort dispatches: one a line, and a picture up to 1280 x 1280 has at most 1280 + 1279 lines (at 45
# degrees). Those past the angle's own count return at once.
LINES = 2 * MAX_RES
SPANS = (('brightness', 'Brightness'), ('edges', 'Edges'), ('depth', 'Depth or Mask'), ('whole', 'Whole Lines'))
SORTS = (('brightness', 'Brightness'), ('hue', 'Hue'), ('saturation', 'Saturation'))
# After the gate, flips and drops at least this far apart (s): Calm a little over its one second, else about 1.3 a
# second (a flip changes every span at once, as Slit-Scan's flips do).
FLASH_SPACING = {'calm': 1.1, 'other': 0.75}


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


README = src('readme.txt').format(v=VERSION, steady=STEADY, tear=TEAR, spin=SPIN_MAX)
comp, page, source = new_effect(
    'pixel_sort', 'Pixel Sort',
    'Pixel Sort {}: runs of pixels (by brightness, edges, depth or whole lines) sorted into streaks along any angle, '
    'every span fully sorted every frame, on the music.'.format(VERSION),
    README, tags=('pixel-sort', 'glitch', 'audio-reactive'), audio=True, flashing=True, depth=True,
    # A tree against bright foliage (TouchDesigner's own sample): bright runs broken by dark branches.
    sample="app.samplesFolder + '/Map/Nature/Movie.3.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
SPAN = 'me.par.Spans'
p = menu(page, 'Spans', 'Spans', SPANS, 'brightness',
         'Which runs of pixels sort. Brightness sorts the pixels whose brightness lies between Low and High, and Edges '
         'the pixels between the edges in the picture. Depth or Mask sorts where input 3 lies between Low and High '
         '(with nothing on input 3, the brightness stands in). Whole Lines sorts every line from end to end, so use '
         'Cut Every with it.')
p.startSection = True
custom(page, 'Float', 'Low', 'Low', 0.25,
       "The darkest a pixel may be and still sort, 0-1 (input 3's value for Depth or Mask). Louder music on input 2 "
       'lowers it.', 0, 1, True).enableExpr = SPAN + " in ('brightness', 'depth')"
custom(page, 'Float', 'High', 'High', 0.8,
       "The brightest a pixel may be and still sort, 0-1 (input 3's value for Depth or Mask; with a mask, Low 0.5 and "
       'High 1 sort what lies inside it). Louder music raises it.', 0, 1, True).enableExpr = \
    SPAN + " in ('brightness', 'depth')"
custom(page, 'Float', 'Edge', 'Edge', 0.08,
       'How strong an edge must be to end a span, 0-0.5, where 1 would be a step from black to white. Higher, only the '
       'strongest edges end spans and the streaks run longer.', 0, 0.5, True).enableExpr = SPAN + " == 'edges'"
custom(page, 'Int', 'Cutevery', 'Cut Every', 0,
       'Cut the spans at random points about this many pixels apart, at 720 high (it scales with the picture), so '
       'streaks of many lengths sort side by side. The points stay put from frame to frame. At 0 spans run whole.',
       0, 400, True)
p = menu(page, 'Sortby', 'Sort By', SORTS, 'brightness',
         "What each span is sorted by. Brightness runs from dark to bright, Hue around the color wheel from red "
         'through yellow, green and blue to magenta, and Saturation from gray to the strongest colors. Hue jumps '
         'between neighbors in gray parts of the picture, so it shimmers more on video.')
p.startSection = True
custom(page, 'Float', 'Angle', 'Angle', 270.0,
       "Which way the sort runs, in degrees counterclockwise from the right: each span's values rise that way. At "
       '270, the default, the brightest end of each span is at the bottom, so light seems to pour down. At 0 the '
       'brightest is at the right and at 90 at the top. Any angle works, since the lines are steps of whole pixels.',
       0, 360, True)
custom(page, 'Float', 'Spin', 'Spin', 0.0,
       'How fast Angle turns, in degrees a second, at most {s:g} either way. Turning moves the steps in the lines, '
       'and each step that moves re-sorts the spans it crosses: faster, whole spans changed often enough to '
       'flash.'.format(s=SPIN_MAX), -SPIN_MAX, SPIN_MAX, True)
p = menu(page, 'Flips', 'Flips', (('beats', 'On Beats'), ('bars', 'On Bars'), ('steady', 'Steady'), ('off', 'Off')),
         'bars',
         "When the sort turns end over end, so each span's bright end swaps with its dark end. On Bars flips on the "
         "one of each of input 2's bars and On Beats on its beats (with nothing wired, every {s:g} s). Steady flips "
         'every {s:g} s, and Off never. A flip changes every span at once, so it is a flash, and Flashing limits how '
         'often they come.'.format(s=STEADY))
p.startSection = True
custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'How wide each beat tears the picture, 0-1. For {:g} s three thin slivers of lines, one in each third of the '
       'picture, sort whole from end to end and against the grain, 6 to 18 lines each at 1 (at 720 high). Flashing '
       'Off stops them.'.format(TEAR), 0, 1, True)
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much louder music on input 2 widens the spans, 0-1, so more of the picture sorts (and quiet passages '
       'less). It eases over half a second.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a build widens the spans as it rises, and a drop sorts every line whole for "
       "Length seconds (Fosfora's drop detection is experimental).")
custom(page, 'Float', 'Length', 'Length', 0.5, 'How long a drop sorts every line whole, in seconds.', 0.1, 1.5,
       True).enableExpr = 'me.par.Moments'

# ---- Audio (input 2): flips, drops, tears, the spans' width -------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -200, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count drop_count')
steady = mk(comp, constantCHOP, 'steady', -200, -500, comment='Counts {:g} s periods, for Steady flips.'.format(STEADY),
            const0name='steady_count', const0value=Expr('int(absTime.seconds / {})'.format(STEADY)))
both = mk(comp, mergeCHOP, 'all_counts', 0, -400, [counts, steady], 'Every count a flip or drop may follow.')
steps = mk(comp, slopeCHOP, 'steps', 200, -400, [both], 'Above 0 on the frame a count goes up.', timeslice=True)
WIRED = "op('audio')['source'].eval() > 0"
asks = []
for i, (name, chan, when, what) in enumerate((
        ('beat_on', 'beat_count', "parent().par.Flips == 'beats' and " + WIRED, 'beats, when Flips is On Beats'),
        ('bar_on', 'bar_count', "parent().par.Flips == 'bars' and " + WIRED, 'bars, when Flips is On Bars'),
        ('steady_on', 'steady_count',
         "parent().par.Flips == 'steady' or (parent().par.Flips in ('beats', 'bars') and not " + WIRED + ")",
         'the steady clock, when Flips is Steady (or On Beats or On Bars with nothing on input 2)'),
        ('drop_on', 'drop_count', 'parent().par.Moments', 'drops (Song Moments: every line sorted whole)'))):
    pick = mk(comp, selectCHOP, name + '_step', 400, -250 - 150 * i, [steps], 'Steps of {}.'.format(chan), channames=chan)
    asks.append(mk(comp, mathCHOP, name, 600, -250 - 150 * i, [pick], 'Flips on {}.'.format(what) if i < 3 else
                   'Whole sorts on {}.'.format(what), gain=Expr('1 if ({}) else 0'.format(when))))
ask = mk(comp, mergeCHOP, 'flip_asks', 800, -450, asks, 'Every flip and drop asked for.')
ask_any = mk(comp, mathCHOP, 'flip_any', 1000, -450, [ask], 'One channel: any flip or drop.', chanop='max')
gate = flash_gate(comp, ask_any, 1200, -450)
budget = mk(comp, triggerCHOP, 'flash_budget', 1600, -450, [gate],
            'After the gate: flips and drops {calm} s apart at Calm, {other} s otherwise, so the total stays well '
            'under WCAG.'.format(**FLASH_SPACING),
            retrigger=Expr("{calm} if parent().par.Flashing == 'calm' else {other}".format(**FLASH_SPACING)),
            retriggerunit='seconds', attack=0, peak=1, peaklen=0, decay=0, sustain=0, release=0)
drop_step = mk(comp, selectCHOP, 'drop_now', 1600, -650, [asks[3]], 'A drop asking for a whole sort.')
drop_env = mk(comp, triggerCHOP, 'drop_env', 1800, -650, [drop_step], 'How recent a drop is (fades over 0.3 s).',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
drop_kind = mk(comp, holdCHOP, 'drop_kind', 2000, -600, [drop_env, budget],
               "1 when what passed the gate was a drop's: a whole sort, not a flip.")
drop_pulse = mk(comp, mathCHOP, 'drop_pulse', 2200, -600, [budget, drop_kind], 'A drop passing the gate.',
                chopop='mul')
flip_pulse = mk(comp, mathCHOP, 'flip_pulse', 2200, -450, [budget, drop_pulse], 'A flip passing the gate.',
                chopop='sub')
flip_n = mk(comp, countCHOP, 'flip_n', 2400, -450, [flip_pulse], 'Flips so far.')
flip_parity = mk(comp, limitCHOP, 'flip_parity', 2600, -450, [flip_n],
                 'Flipped (1) or not (0): flips so far, odd or even.', type='loop', min=0, max=2)
whole = mk(comp, triggerCHOP, 'whole', 2400, -650, [drop_pulse], 'A drop: 1 for Length seconds, every line sorted whole.',
           attack=0, peak=1, peaklen=par('Length'), decay=0, sustain=0, release=0)

tick = mk(comp, mathCHOP, 'steady_tick', 800, -100, [asks[2].inputs[0]], 'Steady ticks, only while input 2 is empty.',
          gain=Expr('0 if ' + WIRED + ' else 1'))
beat_in = mk(comp, mergeCHOP, 'beat_in', 1000, -150, [asks[0].inputs[0], tick], 'Beats, or steady ticks.')
beat_pick = mk(comp, mathCHOP, 'beat_pulse', 1200, -150, [beat_in], 'One channel: a beat, for its tears.', chanop='max')
beat_env = mk(comp, triggerCHOP, 'beat_env', 1400, -150, [beat_pick],
              'Falls from 1 to 0 over the {:g} s after a beat: its tears stay open while it is above 0.'.format(TEAR),
              attack=0, peak=1, peaklen=0, decay=TEAR, sustain=0, release=0)
beat_n = mk(comp, countCHOP, 'beat_n', 1400, -50, [beat_pick], "Beats so far: where each beat's tears fall.")
level_pick = mk(comp, selectCHOP, 'level_pick', 1200, 0, [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', 1400, 0, [level_pick],
           'Loudness eased over half a second, so the spans swell and shrink instead of jittering.', width=0.5)
LOUD = "(parent().par.Loudness * 1.2 * (op('level_smooth')[0] - 0.5) if {} else 0)".format(WIRED)
BUILD = "(0.4 * op('audio')['build'] if parent().par.Moments else 0)"
widen_to = mk(comp, constantCHOP, 'widen_to', 1600, 0,
              comment='How much wider the spans are asked to be (-{} to {}): loudness and a build.'.format(*WIDEN),
              const0name='widen', const0value=Expr('max(-{}, min({}, {} + {}))'.format(*WIDEN, LOUD, BUILD)))
widen = mk(comp, lagCHOP, 'widen', 1800, 0, [widen_to],
           'How much wider the spans are, gliding to what is asked at up to {:g} a second.'.format(WIDEN_GLIDE),
           lag1=0, lag2=0, clamp=True, slope1=WIDEN_GLIDE, slope2=WIDEN_GLIDE)
spin_rate = mk(comp, constantCHOP, 'spin_rate', 1600, 150, comment='How fast Angle turns: Spin.', const0name='spin',
               const0value=par('Spin'))
turned = mk(comp, speedCHOP, 'turned', 1800, 150, [spin_rate], 'How far Angle has turned (degrees).',
            limittype='loop', min=0, max=360)

# ---- The picture ----------------------------------------------------------------------------------
depth = depth_in(comp)
start = mk(comp, constantTOP, 'start', -200, 300, comment="Nothing: where key's last frame starts, no pixel in a span.",
           outputresolution='custom', resolutionw=1, resolutionh=1, colorr=0, colorg=0, colorb=0, alpha=0)
key_fb = mk(comp, feedbackTOP, 'key_fb', 0, 300, [start], "key's last frame: which pixels were in a span.", top='key')
key = glsl(comp, 'key', 200, 150, [source, key_fb, depth], src('key.glsl'),
           'Each pixel: the value it sorts by, whether it is in a span, whether its line is cut there.',
           fmt='rgba16fixed',
           uSpan=(Expr('parent().par.Spans.menuIndex'), par('Low'), par('High'), par('Edge')),
           uSort=(Expr('parent().par.Sortby.menuIndex'),
                  par('Cutevery'),
                  Expr("op('widen')[0]"), HYSTERESIS))
ANGLE = "math.radians(parent().par.Angle + op('turned')[0] + 180 * op('flip_parity')[0])"
TEARING = "parent().par.Flashing != 'off' and op('beat_env')[0] > 0"
sort = mk(comp, glslTOP, 'sort', 400, 0, [source, key],
          'The sort: one workgroup a line toward Angle, every span sorted by value, each pixel written where it lands.',
          mode='compute', autodispatchsize=False, dispatchsizex=LINES, dispatchsizey=1, dispatchsizez=1)
docked(sort, '_compute', src('sort.glsl'), 'The sort, a compute shader: each line of pixels, its spans sorted.')
uniforms(sort, uLine=(Expr('math.cos({})'.format(ANGLE)), Expr('math.sin({})'.format(ANGLE)),
                      Expr('parent().par.Kick if {} else 0'.format(TEARING)), Expr("op('beat_n')[0] % 4096")),
         uWhole=(Expr("op('whole')[0]"),))

finish_effect(comp, sort, VERSION, page)
save_effect(comp, _HERE, _ROOT)
