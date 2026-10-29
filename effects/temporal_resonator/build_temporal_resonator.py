"""Build Temporal Resonator. Run from a textport: __file__ = '/path/to/build_temporal_resonator.py'; exec(open(__file__).read())

Every pixel a plucked string, after Karplus and Strong (1983) with Jaffe and Smith's extensions: a delay line a beat long
whose output is averaged and fed back, so whatever moves comes round again on the next beat, and the next, fainter and
softer each time, as a string's tone repeats every period and loses its highs first. The pluck is what differs from the
background (a running approximate median, so someone walking through leaves no trace), fed in for the beat after each
beat of input 2 (or all the time), and the echoes are added behind whatever stands out now. A negative loop gain
(Alternating) inverts every trip round, so the echoes alternate between the picture's difference and its opposite.

dev/protos/temporal_resonator/offline.py tried it first on the clips with a song (board #4717): a running average for
the background left the subject in it, and its echoes came back as dark copies where she had stood.

The network, left to right:
  picture  source -> background (+ background_fb) -> string (the strings: buffer 0 their state, through state ->
           string_fb into the ring; buffer 1 the echo, through echo) -> show (the echoes behind the live picture) -> out
  ring     optical_flow() (levels 8, no flow: only its clock, for cuts) -> stamp (+ stamp_fb); string_fb -> states,
           stamp_fb -> stamps (rings a cook late, in step); stamp + stamps -> taps (where the delay line is read)
  depth    input 3 (depth_in(), else no_depth) -> near -> find (what stands in front), read by string
  audio    audio_in() -> beat (the beat's length) -> delay_to -> delay (gliding); phase (through the beat) and
           level_smooth -> pluck (how hard the string is plucked now)
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.1'
MODES = (('same', 'Same'), ('alternating', 'Alternating'))
LENGTHS = (('half', '1/2 Beat', 0.5), ('beat', '1 Beat', 1.0), ('two', '2 Beats', 2.0))
PLUCKS = (('beats', 'On Beats'), ('always', 'Always'))
BEAT = (0.3, 1.0)     # the beat's length is folded into this range by doubling or halving (s): 60 to 200 BPM as is
GLIDE = 0.25          # the delay changes by at most this many seconds a second, so the echoes never jump in time
ATTACK = 0.1          # a pluck rises over this share of the beat, then fades by the next
FLOOR = 0.5           # and never below this, so a picture that moves all over doesn't pulse with the beat
ALWAYS = 0.65         # Always plucks this hard, about On Beats' average over a beat (at 1 the dancer's echoes flashed)
SPREAD = 0.12         # Softness 1 averages the loop over this many seconds either side of the delay
BLUR = 3.0            # and over this many pixels of the ring around each pixel
MEDIAN = 0.6          # the background moves toward the picture by at most this much a second
STAND_OUT, NEAR = 0.1, 0.2   # input 3: what stands out (lib depth_find.glsl) by this much of the depth range from what
                             # lies left and right, and is nearer than this, is in front of the echoes
GAP = 0.5             # a pause between cooks longer than this (s) starts the string again: the output went unused
SLACK = 1.05          # the rings hold this much more than the longest delay (and 3 slots)
PERF = '1.6'          # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)
MEM = {'membeat': 160, 'memhalf': 99, 'memtwo': 284}   # MB of GPU memory at 1280 x 720, 60 fps, by Length (TOP.gpuMemory)


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


README = src('readme.txt').format(v=VERSION, perf=PERF, lo=60 / BEAT[1], hi=60 / BEAT[0], **MEM)
comp, page, source = new_effect(
    'temporal_resonator', 'Temporal Resonator',
    'Temporal Resonator {}: every pixel a plucked string tuned to the beat, so whatever moves comes round again on the '
    'next beats, fainter and softer each time.'.format(VERSION),
    README, tags=('temporal-resonator', 'karplus-strong', 'echo', 'time', 'audio-reactive'), audio=True, depth=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.2.mp4'")   # grass swaying in front of a building: it rings

# ---- Parameters -------------------------------------------------------------------------------
LENGTH = '{}[parent().par.Length.menuIndex]'.format([l[2] for l in LENGTHS])
menu(page, 'Mode', 'Mode', MODES, 'same',
     'Same: each echo is like the moment it repeats, fainter each beat. Alternating inverts the string every trip '
     'round, as a pipe closed at one end reflects a wave, so the echoes alternate between a shadow and a light: '
     'a bright figure comes back dark on the next beat, then bright on the one after.')
menu(page, 'Length', 'Length', [(n, l) for n, l, _ in LENGTHS], 'beat',
     "How long the string is, in beats of input 2 (with nothing wired, of Tempo): how far apart the echoes come. "
     'Beats slower than {:g} or faster than {:g} a minute count double or half. Changing it starts the strings '
     'again.'.format(60 / BEAT[1], 60 / BEAT[0]))
custom(page, 'Float', 'Sustain', 'Sustain', 10.0,
       'How many beats the echoes last, until they have faded to a tenth: a short pluck at 2, a long ring at 30.',
       1, 30, True)
custom(page, 'Float', 'Strength', 'Strength', 1.5, 'How bright the echoes show, 0-3.', 0, 3, True)
custom(page, 'Float', 'Softness', 'Softness', 0.5,
       'How much softer each echo comes back than the last, 0-1, in time and across the picture, as a string loses its '
       'high harmonics first: at 0 every echo is as sharp as the moment, at 1 they soon blur into a haze.', 0, 1, True)
custom(page, 'Float', 'Threshold', 'Threshold', 0.06,
       'How far a pixel must differ from the background (what has stood still for a while) to pluck its string and '
       'to stand in front of the echoes, 0-0.5. Higher leaves drifting smoke and noise out.', 0, 0.5, True)
p = menu(page, 'Pluck', 'Plucks', PLUCKS, 'beats',
         'On Beats plucks the strings on each beat of input 2 (with nothing wired, of Tempo), rising at once and falling '
         'to half by the next beat, so what moves on the beat rings loudest. Always plucks them evenly all the time.')
p.startSection = True
custom(page, 'Float', 'Tempo', 'Tempo', 120.0,
       'The beat with nothing on input 2, in beats a minute: how long the string is and, On Beats, when it is plucked.',
       40, 240, True)
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much harder louder music on input 2 plucks the strings, 0-1.', 0, 1, True)
p = menu(page, 'Depthtype', 'Depth Type',
         (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
          ('meters', 'Distance in Meters (Kinect Azure)')), 'nearness',
         'What input 3 holds, a depth map or a mask: whatever stands in front of its surroundings there stays in front '
         'of the echoes, even standing still. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance '
         '0-1: the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). '
         'Distance in Meters: the Kinect Azure TOP, scaled by Max Distance. With nothing on input 3, only what differs '
         'from the background stands in front.')
p.startSection = True
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"

# ---- Audio (input 2): the beat's length and where each beat plucks ---------------------------------
section('audio', "Audio (input 2): the beat's length, where in the beat it is, how loud")
audio = audio_in(comp, _ROOT)
WIRED = "op('audio')['source'].eval() > 0"
PERIOD = "(op('audio')['beat_period'].eval() if {} else 60 / parent().par.Tempo)".format(WIRED)
FOLD = ('p if {lo} <= p <= {hi} else p / 2 ** math.ceil(math.log2(p / {hi})) if p > {hi} else '
        'p * 2 ** math.ceil(math.log2({lo} / p))').format(lo=BEAT[0], hi=BEAT[1])
beat = mk(comp, constantCHOP, 'beat', comment="The beat's length (s): input 2's, else Tempo's, doubled or halved into "
          '{:g} to {:g} s.'.format(*BEAT), const0name='period',
          const0value=Expr('(lambda p: {})({})'.format(FOLD, PERIOD)))
delay_to = mk(comp, constantCHOP, 'delay_to', comment="The string's length asked for: Length beats (s).",
              const0name='delay', const0value=Expr("{} * op('beat')[0]".format(LENGTH)))
delay = mk(comp, lagCHOP, 'delay', [delay_to],
           "The string's length, gliding to what is asked at up to {:g} s a second, so the echoes never jump in "
           'time.'.format(GLIDE), lag1=0, lag2=0, clamp=True, slope1=GLIDE, slope2=GLIDE)
phase = mk(comp, constantCHOP, 'phase', comment="Where in the beat it is, 0-1: input 2's, else Tempo's.",
           const0name='phase',
           const0value=Expr("op('audio')['beat_phase'].eval() if {} else absTime.seconds * parent().par.Tempo / 60 "
                            "% 1".format(WIRED)))
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick],
           'Loudness eased over half a second, so the plucks swell and fade with the music.', width=0.5)
LOUD = "(max(0.3, 1 + parent().par.Loudness * 1.5 * (op('level_smooth')[0] - 0.6)) if {} else 1)".format(WIRED)
ENV = "({f} + {g} * min(op('phase')[0] / {a}, 1) * (1 - op('phase')[0]))".format(f=FLOOR, g=1 - FLOOR, a=ATTACK)
pluck = mk(comp, constantCHOP, 'pluck', comment='How hard the strings are plucked now: On Beats, rising over a tenth of '
           'the beat and fading by the next to half; Always, evenly at about their average; louder music harder.',
           const0name='pluck',
           const0value=Expr("({} if parent().par.Pluck == 'always' else {}) * {}".format(ALWAYS, ENV, LOUD)))

# ---- The delay line ---------------------------------------------------------------------------------
section('ring', "The delay line: the strings' state a cook at a time, kept in a ring with stamps", lane='ring')
mo = optical_flow(comp, _ROOT, source, levels=(8,), flow=False)
start = mk(comp, constantTOP, 'start', comment='Nothing: where the stamp starts.', outputresolution='custom',
           resolutionw=2, resolutionh=1, format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
stamp_fb = mk(comp, feedbackTOP, 'stamp_fb', [start], "stamp's last frame: the last cook's stamp.", top='stamp')
stamp = glsl(comp, 'stamp', [mo['clock'], stamp_fb], src('stamp.glsl'),
             "This cook's stamp: which cook, when, whether the strings start again (first cook, a pause, a cut).",
             res=(2, 1), fmt='rgba32float', uS=(clock_seconds(), GAP, CLOCK))
SLOTS = 'int(math.ceil(({} * {} + {}) * project.cookRate * {})) + 3'.format(LENGTH, BEAT[1], SPREAD, SLACK)

# ---- Depth or a mask (input 3) ----------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): what stands in front of the echoes')
none = mk(comp, constantTOP, 'no_depth', comment='Nothing: with nothing on input 3, nothing stands in front by depth.',
          outputresolution='custom', resolutionw=8, resolutionh=8, colorr=0, colorg=0, colorb=0, alpha=1)
depth = depth_in(comp, none)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at an eighth size, as nearness; Depth Type flips distance (black: no reading).', fmt='rgba16float',
            uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='eighth')   # find scans each pixel's row: at a quarter size it cost 0.45 ms
find = glsl(comp, 'find', [near], lib_glsl(_ROOT, 'depth_find.glsl'),
            'In the depth: what stands in front of what lies left and right of it, nearer than {:g}.'.format(NEAR),
            fmt='rgba16float', uFind=(0, STAND_OUT, NEAR))

# ---- The strings --------------------------------------------------------------------------------
section('strings', 'The strings: what differs from the background, plucked, fed back a beat late, softer each time',
        lane='picture')
background_fb = mk(comp, feedbackTOP, 'background_fb', [source], "background's last frame.", top='background')
background = glsl(comp, 'background', [source, background_fb, stamp], src('background.glsl'),
                  "The background: the picture's running median at half size, what isn't moving.", fmt='rgba16float',
                  uB=MEDIAN)
setpars(background, outputresolution='half')
string_fb = mk(comp, feedbackTOP, 'string_fb', [background], "The strings' state from the last cook.", top='state')
states = mk(comp, texture3dTOP, 'states', [string_fb],
            "The delay line: the strings' state, one slot a cook, a beat (Length) and a little more of them.",
            type='texture2darray', cachesize=Expr(SLOTS), format='rgba16float')
stamps = mk(comp, texture3dTOP, 'stamps', [stamp_fb], "Each slot's stamp, written in step with states.",
            type='texture2darray', cachesize=Expr(SLOTS), format='rgba32float')
taps = glsl(comp, 'taps', [stamp, stamps], src('taps.glsl'),
            'Where the delay line is read: the delay and a little either side, each between two slots.', res=(3, 1),
            fmt='rgba32float',
            uT=(Expr("op('delay')[0]"), Expr('{} * parent().par.Softness'.format(SPREAD)), GAP, CLOCK))
GAIN = "(-1 if parent().par.Mode == 'alternating' else 1) * 0.1 ** ({} / parent().par.Sustain)".format(LENGTH)
string = glsl(comp, 'string', [source, background, taps, stamp, find, states], src('string.glsl'),
              "The strings: each pixel's pluck plus what comes back round the delay line, averaged and scaled by the "
              "loop's gain; and the echo, with what stands out now.", fmt='rgba16float',
              uS=(Expr(GAIN), Expr("op('pluck')[0]"), Expr('{} * parent().par.Softness'.format(BLUR)), par('Threshold')))
setpars(string, outputresolution='half', numcolorbufs=2)
state = mk(comp, renderselectTOP, 'state', comment="string's buffer 0: the strings' state, into the delay line.",
           top='string', bufferindex=0)
echo = mk(comp, renderselectTOP, 'echo', comment="string's buffer 1: the echo, and what stands out now.",
          top='string', bufferindex=1)
show = glsl(comp, 'show', [source, echo], lib_glsl(_ROOT, 'red_guard.glsl') + src('show.glsl'),
            'The picture with the echoes added behind whatever stands out now, every pixel through the red guard.',
            fmt='rgba8fixed',
            uE=par('Strength'))

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
