"""Build Slit-Scan. Run from a textport: __file__ = '/path/to/build_slit_scan.py'; exec(open(__file__).read())

Each part of the picture from its own moment. The last History seconds of the input are kept on the GPU, and each
pixel comes from the moment its time map gives it: a sweep across the picture, rings, the depth on input 3, a
drifting noise, or a slit with film running past it (strip photography). Between the input's frames the picture is
filled in along the movement (Flow), so a slow clip bends smoothly.

The history is three Texture 3D TOPs (2D texture arrays), written once a cook, in step: the picture, its optical flow
(lib optical_flow()'s lk4) and a stamp (which cook wrote the slot, which input frame it holds, when that frame came).
A Texture 3D TOP writes the next slot on every cook and says nothing of where it is (dev/probes/texture3d.py), so
frames finds the newest slot by its stamp, walks back while the stamps follow on, and lists the input's distinct
frames newest first; scan and slit look a moment up in that list (src/past.glsl). Slots never written, left from a
pause or from before History changed fail the walk and never show.

The network, left to right:
  history  source -> pics; optical_flow() -> lk4 -> flows; clock -> pace -> stamp (+ stamp_fb) -> stamps;
           stamps + stamp -> frames (the input's frames, newest first)
  picture  scan (Sweep, Rings, Depth, Liquid) or slit (+ slit_fb, the film) -> view
  audio    audio_in() -> counts -> steps (Slope CHOP); steady counts the time; beat_on, bar_on, steady_on pick the flips
           asked for and drop_on the freezes -> flash_gate() -> flash_budget -> drop_kind; drop_pulse -> freeze (time
           held for Length); flip_pulse -> flip_n -> flip_parity -> flip (the map sliding end over end); beats (or
           steady ticks with nothing wired) -> beat_pulse -> beat_env, beat_n (each beat's tears); level_smooth
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
HISTORY = 2.0        # seconds kept by default
SLACK = 1.05         # the rings hold this much more than History (and 2 slots), so a full one reaches past Delay
GAP = 0.5            # a gap between cooks longer than this (s) ends the history: the output went unused
FLIP_SLIDE = 0.25    # seconds a flip takes to slide the map end over end (longer at long delays, below)
# How fast the time map may sweep time past a point, which is the delay times how fast the map moves: a sweep faster
# than the clip's own movement shows the clip's changes faster, and with them its flashes. Each limit is a setting that
# measured clean at the default Delay of 1.5 s with Flashing Off (dev/flash.py); at Delay 8 the same Drift of 1 or
# Spin of 90 added a flash or more a second on the plaza and the flowers, red ones too, and Drift 2 at 1.5 did on the
# dancer.
SPAN_GLIDE = 1.0     # the delay (Delay, loudness, a build) changes by at most this many seconds a second
DRIFT_SPAN = 1.5     # Drift x delay at most (Drift 1 at Delay 1.5)
SPIN_SPAN = 135.0    # Spin x delay at most, in degree-seconds a second (Spin 90 at Delay 1.5)
FLIP_SPAN = 6.0      # delay / a flip's slide at most: it slides over at least delay / 6 s (0.25 s at Delay 1.5)
# Slit's film spreads whatever flickers on the slit line over the strip, and the faster it runs the wider each flicker
# lands, until it fills areas: with Flashing Off, red flowers measured 1.0 flash a second at 80 pixels a second (the
# clip 1.0), 1.5 at 120, 2.0 at 160 and 4.0 at 1000; the dancer 2.0 from 250 up.
SPEED_MAX = 120.0    # pixels a second at 720 high, loudness included
TEAR = 0.15          # seconds a beat's tears stay open
TEAR_DEPTH = 0.8     # how much further back a tear looks at Beat Kick 1 (seconds, at most; each tear between half and all)
SIZES = (('full', 'Full', 'useinput', 1), ('half', 'Half', 'half', 2), ('quarter', 'Quarter', 'quarter', 4))
FILLS = (('flow', 'Flow'), ('blend', 'Blend'), ('steps', 'Steps'))
MAPS = (('sweep', 'Sweep'), ('rings', 'Rings'), ('depth', 'Depth'), ('liquid', 'Liquid'), ('slit', 'Slit'))
FILMS = (('right', 'Right', (1, 0)), ('left', 'Left', (-1, 0)), ('down', 'Down', (0, -1)), ('up', 'Up', (0, 1)))
# After the gate, flips at least this far apart (s): Calm a little over its one second, else about 1.3 a second (a
# flip changes the whole frame, as Bent Cam's bursts do).
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


# GPU memory, measured with dev/probes/slit_memory.py (TOP.gpuMemory, 2025.33230 on the reference Mac): MB (millions
# of bytes) each second of History adds at 60 fps, the picture and its flow, by the input's height and History Size
# (from History 1, 2 and 8 s, which agree), and everything inside at the defaults at 1280 x 720. A 720-high slot
# measures 7% over width x height x 4, a 1280-high one exactly that: the rows are padded.
MEM = {'mem720': 263, 'mem720h': 68, 'mem720q': 18, 'mem1280': 439, 'mem1280h': 112, 'mem1280q': 30, 'memdef': 546}
MEM_TEXT = {k: '{:d}'.format(v) for k, v in MEM.items()}
README = src('readme.txt').format(v=VERSION, steady=STEADY, hist=HISTORY, tear=TEAR, glide=SPAN_GLIDE, speedmax=SPEED_MAX,
                                  **MEM_TEXT)
comp, page, source = new_effect(
    'slit_scan', 'Slit-Scan',
    'Slit-Scan {}: each part of the picture from its own moment (sweeps, rings, depth, liquid, a slit with film), '
    'filled in along the movement between frames, on the music.'.format(VERSION),
    README, tags=('slit-scan', 'time-displacement', 'audio-reactive'), audio=True, flashing=True, depth=True,
    # A slow pan through a forest (TouchDesigner's own sample): the whole frame moves, so every map shows.
    sample="app.samplesFolder + '/Map/Nature/Movie.5.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
MAP = "me.par.Map"
p = menu(page, 'Map', 'Map', MAPS, 'sweep',
         'Which moment each part of the picture comes from. With Sweep the delay grows across the picture toward '
         'Angle, and with Rings outward from the center. Depth takes it from input 3 (or the brightness), so nearer '
         'parts are now and farther ones lag. Liquid takes it from a drifting noise. Slit is strip photography, one '
         'line of the picture laid down on moving film.')
p.startSection = True
custom(page, 'Float', 'Delay', 'Delay', 1.5,
       'How far back the most delayed part of the picture lies, in seconds (at most History; while the history '
       'fills, less). It glides to a new value at up to {:g} s a second, so time never sweeps past too fast.'.format(
           SPAN_GLIDE), 0, 8, True).enableExpr = MAP + " != 'slit'"
custom(page, 'Float', 'Angle', 'Angle', 270.0,
       "Where Sweep's past lies, in degrees counterclockwise from the right. The default, 270, puts it at the "
       'bottom, so the top is now and each row down is a moment older.', 0, 360, True).enableExpr = MAP + " == 'sweep'"
custom(page, 'Float', 'Spin', 'Spin', 0.0,
       "How fast Sweep's Angle turns, in degrees a second, like turning a slice through the video. At delays over "
       "{:g} s it turns more slowly, so time never sweeps past faster than it does at 90 and Delay {:g} s (faster, the "
       "picture's own changes came fast enough to flash).".format(SPIN_SPAN / 90, SPIN_SPAN / 90), -90, 90,
       True).enableExpr = MAP + " == 'sweep'"
custom(page, 'Float', 'Centerx', 'Center X', 0.5,
       "Where the rings' center is across the picture, from 0 at the left to 1 at the right.", 0, 1,
       True).enableExpr = MAP + " == 'rings'"
custom(page, 'Float', 'Centery', 'Center Y', 0.5,
       "Where the rings' center is up the picture, from 0 at the bottom to 1 at the top.", 0, 1,
       True).enableExpr = MAP + " == 'rings'"
custom(page, 'Float', 'Scale', 'Scale', 2.0, "How many of Liquid's swirls fit the picture's height.", 0.5, 8,
       True).enableExpr = MAP + " == 'liquid'"
custom(page, 'Float', 'Drift', 'Drift', 0.2,
       "How fast Liquid's noise changes, 0-1. At delays over {:g} s it changes more slowly, so time never sweeps past "
       "faster than it does at Drift 1 and Delay {:g} s (faster, the picture's own changes came fast enough to "
       "flash).".format(DRIFT_SPAN, DRIFT_SPAN), 0, 1,
       True).enableExpr = MAP + " == 'liquid'"
menu(page, 'Film', 'Film', [(n, l) for n, l, _ in FILMS], 'right',
     "Which way Slit's film runs past the slit. With Right the slit is a vertical line and the strip lies to its "
     'right.').enableExpr = MAP + " == 'slit'"
custom(page, 'Float', 'Position', 'Position', 0.5,
       'Where the slit is, 0-1 across the picture in the direction of Film, with the live picture on one side and '
       'the strip on the other. At 0 the whole picture is strip.', 0, 1, True).enableExpr = MAP + " == 'slit'"
custom(page, 'Float', 'Speed', 'Speed', 80.0,
       "How fast Slit's film runs, in pixels a second at 720 high (it scales with the picture). Slower squeezes "
       'more time into the strip. It stops at {:g}, louder music included: faster, whatever flickers on the slit line '
       'came out wide enough to flash.'.format(SPEED_MAX), 10, SPEED_MAX, True).enableExpr = MAP + " == 'slit'"
custom(page, 'Int', 'Bands', 'Bands', 0,
       'Cut the map into this many steps of time, each its own moment, with hard edges between. At 0 it is smooth.', 0, 32,
       True).enableExpr = MAP + " != 'slit'"
custom(page, 'Toggle', 'Reverse', 'Reverse', False,
       'Turn the map end over end, so what lagged most is now and what was now lags most. Slit runs its film the '
       'other way.')
p = custom(page, 'Float', 'History', 'History', HISTORY,
           'How many seconds of the input are kept on the GPU, every frame the project makes (60 a second at 60 fps). '
           'At 1280 x 720 each second takes {mem720} MB at Full History Size, and at 1280 x 1280 {mem1280} MB. '
           'Changing it starts the history again.'.format(**MEM_TEXT), 0.5, 8, True)
p.startSection = True
menu(page, 'Histsize', 'History Size', [(n, l) for n, l, *_ in SIZES], 'full',
     'The resolution the history is kept at. Half takes a quarter of the memory ({mem720h} MB a second at '
     '1280 x 720) and Quarter a sixteenth ({mem720q} MB), and the past looks softer. The newest moment always comes '
     'from the input itself. Changing it starts the history again.'.format(**MEM_TEXT))
menu(page, 'Fill', 'Between Frames', FILLS, 'flow',
     "How the moments between the input's frames are filled in. Flow moves the frames either side along the "
     'movement between them, smooth even from a 24 fps video. Blend mixes them, which doubles moving edges. Steps '
     'shows the frame that was showing, in bands of whole frames.')
p = menu(page, 'Flips', 'Flips', (('beats', 'On Beats'), ('bars', 'On Bars'), ('steady', 'Steady'), ('off', 'Off')),
         'bars',
         "When the map flips end over end, sliding over a quarter second. On Bars flips on the one of each of "
         "input 2's bars and On Beats on its beats (with nothing wired, every {s:g} s). Steady flips every {s:g} s, "
         "and Off never. A flip changes the whole picture, so it is a flash, and Flashing limits how often they "
         "come. Slit doesn't flip, since its film would lose the strip.".format(s=STEADY))
p.startSection = True
p.enableExpr = MAP + " != 'slit'"
custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'How hard each beat tears the picture, 0-1. For {:g} s a few thin slivers of rows open onto a moment up to '
       '{:g} s further back, and in Slit they land on the film and ride away with it. Flashing Off stops '
       'them.'.format(TEAR, TEAR_DEPTH), 0, 1, True)
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much louder music on input 2 reaches further back, 0-1. In Slit it runs the film faster.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a build reaches further back as it rises, and a drop freezes time for "
       "Length seconds (Fosfora's drop detection is experimental).")
custom(page, 'Float', 'Length', 'Length', 0.5, 'How long a drop freezes time, in seconds.', 0.1, 1.5,
       True).enableExpr = 'me.par.Moments'

# ---- Audio (input 2): flips, freezes, tears -------------------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -200, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count drop_count')
steady = mk(comp, constantCHOP, 'steady', -200, -500, comment='Counts {:g} s periods, for Steady flips.'.format(STEADY),
            const0name='steady_count', const0value=Expr('int(absTime.seconds / {})'.format(STEADY)))
both = mk(comp, mergeCHOP, 'all_counts', 0, -400, [counts, steady], 'Every count a flip or freeze may follow.')
steps = mk(comp, slopeCHOP, 'steps', 200, -400, [both], 'Above 0 on the frame a count goes up.', timeslice=True)
WIRED = "op('audio')['source'].eval() > 0"
asks = []
for i, (name, chan, when, what) in enumerate((
        ('beat_on', 'beat_count', "parent().par.Flips == 'beats' and " + WIRED, 'beats, when Flips is On Beats'),
        ('bar_on', 'bar_count', "parent().par.Flips == 'bars' and " + WIRED, 'bars, when Flips is On Bars'),
        ('steady_on', 'steady_count',
         "parent().par.Flips == 'steady' or (parent().par.Flips in ('beats', 'bars') and not " + WIRED + ")",
         'the steady clock, when Flips is Steady (or On Beats or On Bars with nothing on input 2)'),
        ('drop_on', 'drop_count', 'parent().par.Moments', 'drops (Song Moments: a freeze)'))):
    pick = mk(comp, selectCHOP, name + '_step', 400, -250 - 150 * i, [steps], 'Steps of {}.'.format(chan), channames=chan)
    asks.append(mk(comp, mathCHOP, name, 600, -250 - 150 * i, [pick], 'Flips on {}.'.format(what) if i < 3 else
                   'Freezes on {}.'.format(what), gain=Expr('1 if ({}) else 0'.format(when))))
ask = mk(comp, mergeCHOP, 'flip_asks', 800, -450, asks, 'Every flip and freeze asked for.')
ask_any = mk(comp, mathCHOP, 'flip_any', 1000, -450, [ask], 'One channel: any flip or freeze.', chanop='max')
gate = flash_gate(comp, ask_any, 1200, -450)
budget = mk(comp, triggerCHOP, 'flash_budget', 1600, -450, [gate],
            'After the gate: flips and freezes {calm} s apart at Calm, {other} s otherwise, so the total stays well '
            'under WCAG.'.format(**FLASH_SPACING),
            retrigger=Expr("{calm} if parent().par.Flashing == 'calm' else {other}".format(**FLASH_SPACING)),
            retriggerunit='seconds', attack=0, peak=1, peaklen=0, decay=0, sustain=0, release=0)
drop_step = mk(comp, selectCHOP, 'drop_now', 1600, -650, [asks[3]], 'A drop asking for a freeze.')
drop_env = mk(comp, triggerCHOP, 'drop_env', 1800, -650, [drop_step], 'How recent a drop is (fades over 0.3 s).',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
drop_kind = mk(comp, holdCHOP, 'drop_kind', 2000, -600, [drop_env, budget],
               "1 when what passed the gate was a drop's: a freeze, not a flip.")
drop_pulse = mk(comp, mathCHOP, 'drop_pulse', 2200, -600, [budget, drop_kind], 'A freeze passing the gate.',
                chopop='mul')
flip_pulse = mk(comp, mathCHOP, 'flip_pulse', 2200, -450, [budget, drop_pulse], 'A flip passing the gate.',
                chopop='sub')
flip_n = mk(comp, countCHOP, 'flip_n', 2400, -450, [flip_pulse], 'Flips so far.')
flip_parity = mk(comp, limitCHOP, 'flip_parity', 2600, -450, [flip_n], 'Flipped (1) or not (0): flips so far, odd or even.',
                 type='loop', min=0, max=2)
FLIP_RATE = Expr("min({}, {} / max(op('span')[0], 0.01))".format(1 / FLIP_SLIDE, FLIP_SPAN))
flip = mk(comp, lagCHOP, 'flip', 2800, -450, [flip_parity],
          'How far the map is flipped: slides 0 to 1 (or back) over {:g} s, longer at delays over {:g} s.'.format(
              FLIP_SLIDE, FLIP_SLIDE * FLIP_SPAN), lag1=0, lag2=0, clamp=True, slope1=FLIP_RATE, slope2=FLIP_RATE)
freeze = mk(comp, triggerCHOP, 'freeze', 2400, -650, [drop_pulse],
            'Seconds time has been frozen, rising from 0 to Length, then back to 0 at once.',
            attack=par('Length'), ashape='linear', peak=par('Length'), peaklen=0, decay=0, sustain=0, release=0)

tick = mk(comp, mathCHOP, 'steady_tick', 800, -100, [asks[2].inputs[0]], 'Steady ticks, only while input 2 is empty.',
          gain=Expr('0 if ' + WIRED + ' else 1'))
beat_in = mk(comp, mergeCHOP, 'beat_in', 1000, -150, [asks[0].inputs[0], tick], 'Beats, or steady ticks.')
beat_pick = mk(comp, mathCHOP, 'beat_pulse', 1200, -150, [beat_in], "One channel: a beat, for its tears.", chanop='max')
beat_env = mk(comp, triggerCHOP, 'beat_env', 1400, -150, [beat_pick],
              'Falls from 1 to 0 over the {:g} s after a beat: its tears stay open while it is above 0.'.format(TEAR),
              attack=0, peak=1, peaklen=0, decay=TEAR, sustain=0, release=0)
beat_n = mk(comp, countCHOP, 'beat_n', 1400, -50, [beat_pick], "Beats so far: where each beat's tears fall.")
level_pick = mk(comp, selectCHOP, 'level_pick', 1200, 0, [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', 1400, 0, [level_pick],
           'Loudness eased over half a second, so the delay swells and fades instead of jittering.', width=0.5)
LOUD = ("(parent().par.Loudness * 1.5 * (op('level_smooth')[0] - 0.6) if {} else 0)".format(WIRED))
BUILD = "(op('audio')['build'] if parent().par.Moments else 0)"
span_to = mk(comp, constantCHOP, 'span_to', 1600, 0, comment='The delay asked for: Delay, with loudness and a build.',
             const0name='span', const0value=Expr('parent().par.Delay * max(0.2, 1 + {}) * (1 + {})'.format(LOUD, BUILD)))
span = mk(comp, lagCHOP, 'span', 1800, 0, [span_to],
          'The delay, gliding to what is asked at up to {:g} s a second, so time never sweeps past faster.'.format(
              SPAN_GLIDE), lag1=0, lag2=0, clamp=True, slope1=SPAN_GLIDE, slope2=SPAN_GLIDE)
SPAN_NOW = "max(op('span')[0], 0.01)"
spin_rate = mk(comp, constantCHOP, 'spin_rate', 1600, 150,
               comment='How fast Sweep turns: Spin, slowed at long delays.', const0name='spin',
               const0value=Expr('max(-{l}, min({l}, parent().par.Spin))'.format(l='{} / {}'.format(SPIN_SPAN, SPAN_NOW))))
turned = mk(comp, speedCHOP, 'turned', 1800, 150, [spin_rate], 'How far Sweep has turned (degrees).',
            limittype='loop', min=0, max=360)
drift_rate = mk(comp, constantCHOP, 'drift_rate', 1600, 300,
                comment="How fast Liquid's noise moves: Drift, slowed at long delays.", const0name='drift',
                const0value=Expr('min(parent().par.Drift, {} / {})'.format(DRIFT_SPAN, SPAN_NOW)))
drifted = mk(comp, speedCHOP, 'drifted', 1800, 300, [drift_rate],
             "How far Liquid's noise has moved (it repeats every 256).", limittype='loop', min=0, max=256)

# ---- The history ----------------------------------------------------------------------------------
SLOTS = 'int(math.ceil(parent().par.History * project.cookRate * {})) + 2'.format(SLACK)
SIZE = 'parent().par.Histsize.menuIndex'
mo = optical_flow(comp, _ROOT, source, x=-400, y=650)
start = mk(comp, constantTOP, 'start', -400, 1450, comment='Nothing: where the one-pixel states start.',
           outputresolution='custom', resolutionw=2, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
pace_fb = mk(comp, feedbackTOP, 'pace_fb', -200, 1450, [start], "pace's last frame.", top='pace')
pace = glsl(comp, 'pace', 0, 1450, [mo['clock'], pace_fb], lib_glsl(_ROOT, 'pace.glsl'),
            'One pixel: when the last new input frame came.', res=(1, 1), fmt='rgba32float', uP=(clock_seconds(), 0.25))
stamp_fb = mk(comp, feedbackTOP, 'stamp_fb', 200, 1600, [start], "stamp's last frame.", top='stamp')
stamp = glsl(comp, 'stamp', 200, 1450, [pace, stamp_fb], src('stamp.glsl'),
             "This cook's stamp: which cook, which input frame, when it came, whether at a cut.", res=(2, 1),
             fmt='rgba32float', uS=(clock_seconds(),))


def ring(name, x, y, top, fmt, comment, res=None):
    t = mk(comp, texture3dTOP, name, x, y, [top], comment, type='texture2darray', cachesize=Expr(SLOTS), format=fmt)
    if res:
        setpars(t, outputresolution=Expr(res))
    return t


SIZE_MENU = "{}[{}]".format([s[2] for s in SIZES], SIZE)
pics = ring('pics', 400, 300, source, 'rgba8fixed',
            'The history: the last History seconds of the input, one slot a frame, at History Size.', res=SIZE_MENU)
flows = ring('flows', 400, 650, mo['lk4'], 'rg16float',
             "Each slot's optical flow: the movement since the input frame before (a quarter of pics' size).",
             res=SIZE_MENU)
stamps = ring('stamps', 400, 1450, stamp, 'rgba32float', "Each slot's stamp.")
frames = glsl(comp, 'frames', 600, 1450, [stamp, stamps], src('frames.glsl'),
              "The input's frames, newest first: each one's slot, how long ago it came, whether at a cut.",
              res=(64, 2), fmt='rgba32float', uF=(CLOCK, GAP))
setpars(frames, resolutionw=Expr(SLOTS))
depth = depth_in(comp)

# ---- The picture ----------------------------------------------------------------------------------
past = lib_glsl(_ROOT, 'common.glsl') + src('past.glsl')
BEATING = "parent().par.Flashing != 'off'"
TEARS = (Expr("{} * parent().par.Kick if {} and op('beat_env')[0] > 0 else 0".format(TEAR_DEPTH, BEATING)),
         Expr("op('beat_n')[0] % 4096"))
FILL = Expr('parent().par.Fill.menuIndex')
FLIPPED = "abs((1 if parent().par.Reverse else 0) - op('flip')[0])"
ANGLE = "math.radians(parent().par.Angle + op('turned')[0])"
scan = glsl(comp, 'scan', 800, 300, [source, frames, depth, pics, flows], past + src('scan.glsl'),
            "Each pixel from its moment: the time map (Sweep, Rings, Depth, Liquid), then the history.",
            fmt='rgba8fixed',
            uMap=(Expr("min(parent().par.Map.menuIndex, 3)"), par('Bands'), Expr(FLIPPED), Expr("op('span')[0]")),
            uDir=(Expr('math.cos({})'.format(ANGLE)), Expr('math.sin({})'.format(ANGLE)), par('Centerx'), par('Centery')),
            uLiq=(par('Scale'), Expr("op('drifted')[0]")),
            uTear=TEARS, uTime=(FILL, Expr("op('freeze')[0]")))
setpars(scan, inputextenduv='hold')

FILM = "{}[parent().par.Film.menuIndex]".format([f[2] for f in FILMS])
SIGN = '(-1 if parent().par.Reverse else 1)'
SPEED = "min({}, parent().par.Speed * max(0.2, 1 + {})) / 720 * (0 if op('freeze')[0] > 0 else 1)".format(SPEED_MAX, LOUD)
slit_fb = mk(comp, feedbackTOP, 'slit_fb', 800, 0, [source], "slit's last frame: the film so far.", top='slit')
slit = glsl(comp, 'slit', 1000, 0, [source, frames, slit_fb, pics, flows],
            past + lib_glsl(_ROOT, 'red_guard.glsl') + src('slit.glsl'),
            'The Slit map, strip photography, which lays the line under the slit on film running past it.',
            fmt='rgba16float',
            uSlit=(Expr('{}[0] * {}'.format(FILM, SIGN)), Expr('{}[1] * {}'.format(FILM, SIGN)), par('Position'),
                   Expr('({}) * min(absTime.stepSeconds, 0.1)'.format(SPEED))),
            uSlit2=(Expr(SPEED), FILL), uTear=TEARS)
setpars(slit, inputextenduv='hold')
view = mk(comp, switchTOP, 'view', 1200, 150, [scan, slit], 'The map picked: scan, or slit for Slit.',
          index=Expr("1 if parent().par.Map == 'slit' else 0"))

finish_effect(comp, view, VERSION, page)
save_effect(comp, _HERE, _ROOT)
