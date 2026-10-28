"""Build Scan Processor. Run from a textport: __file__ = '/path/to/build_scan_processor.py'; exec(open(__file__).read())

The picture shown on a television whose raster the music bends, after the scan processors of 1969-73: Paik and Abe's
Wobbulator (extra yokes driven by audio), Harrison's Scanimate (each line twisted, bent and rippled by an analog
computer, then colorized) and, for the beam's sweep along a line, Chowning's frequency modulation. The picture is
scanned in Lines lines and the beam draws each where the yokes put it, as a Gaussian spot, so the light piles up where
lines bunch and the dark shows where they spread. The yokes follow seven signal generators, one a band of lib
audio_in(), each a sine of its own number of cycles down the frame (the sub bass's a bow), its level the band's: the
song's own waveform laid along the raster read as scratchy noise on every line (board #4744). Each beat strikes the
raster through the flash gate; with nothing on input 2 the generators wander at Idle's level and Idle strikes every 2 s.

dev/protos/scan_processor/offline.py tried it first on the clips with a song.

The network, left to right:
  picture  source -> scan (the raster, from yokes) -> show (colors, the red guard) -> out
  yokes    phase_size -> phase (the generators' phases, phase_fb) -> yokes (each line's push, drop, twist or phase)
  audio    audio_in() -> bands -> bands_now (over a second) -> bands_usual (the last 4 s); counts -> steps and
           idle_count -> idle_steps -> strike_ask -> flash_gate() -> strike_env (a strike ringing down), strikes (their
           count, for the side); levels (each generator's level, the strike) -> drive (the low, middle and high bands,
           Scanimate's bend, FM's beta), read by phase, yokes, scan and show
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
SCANS = (('wobbulator', 'Wobbulator'), ('scanimate', 'Scanimate'), ('fm', 'FM'))
COLORS = (('picture', 'Picture'), ('colorizer', 'Colorizer'))
# A generator's level is its band smoothed over SLOW s times NOW, plus RISE x how far that sits above the band's usual
# level (its average over USUAL s), at most 1. A strike rings down over RING s.
SLOW, USUAL, NOW, RISE, RING = 1.0, 4.0, 0.6, 1.0, 0.35
IDLE = 2.0            # Idle: a strike every 2 s while nothing is on input 2, and the generators wandering
DOWN, REACH = 0.06, 1.5   # yokes.glsl's vertical yoke and its cap, which scan.glsl searches
PLEATS = 7.0          # FM: pleats across the picture
BETA = (0.5, 1.2, 0.3, 0.85)   # FM's index: Amount x (BETA[0] + BETA[1] x the bands' mean) + Beat Kick x BETA[2] x the
                               # strike, at most BETA[3] so the beam never runs backward (it folds at 1)
BEND = 0.3           # Scanimate: the bend at the sides at Amount 1 and the middle bands full, a share of the height
PERF = '1.0'          # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


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
    'scan_processor', 'Scan Processor',
    'Scan Processor {}: the picture shown on a television whose raster the music bends, as the Wobbulator and '
    'Scanimate bent theirs.'.format(VERSION),
    README, tags=('scan-processor', 'wobbulator', 'scanimate', 'raster', 'video-synth', 'audio-reactive'), audio=True,
    flashing=True, sample="app.samplesFolder + '/Map/Nature/Movie.1.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Scan', 'Scan', SCANS, 'wobbulator',
     'Which scan processor bends the raster. Wobbulator (Paik and Abe, 1970) pushes each line sideways and up or '
     'down with the music, so the picture ripples and lines bunch into bright bands. Scanimate (Harrison, 1969) '
     'turns the lines about the middle like a ribbon, twisting with the low bands, bending with the middle ones and '
     'rippling with the high ones. FM (after Chowning, 1973) speeds and slows the beam along each line, so the '
     'picture gathers into glowing pleats.')
custom(page, 'Float', 'Amount', 'Amount', 0.5, 'How far the music bends the raster, 0-1.', 0, 1, True)
custom(page, 'Float', 'Speed', 'Speed', 1.0,
       "How fast the signal generators' stripes creep up and down the screen, 0-2, faster while their bands are loud. "
       '0 holds them still.', 0, 2, True)
custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'How hard each beat on input 2 strikes the raster, 0-1: the Wobbulator bows it, Scanimate twists it, FM deepens '
       'its pleats. Each strike goes the other way from the last and rings down over a third of a second, as often as '
       'Flashing allows.', 0, 1, True)
custom(page, 'Float', 'Idle', 'Idle', 0.5,
       'With nothing on input 2, the signal generators wander at this level and the raster is struck every 2 seconds, '
       'so you can see what the music would do, 0-1. 0 rests.', 0, 1, True)
p = custom(page, 'Int', 'Lines', 'Lines', 240,
           'How many lines the beam draws down the picture, 60-720, whatever its size. Fewer shows the raster more.',
           60, 720, True)
p.startSection = True
custom(page, 'Float', 'Beam', 'Beam', 0.7,
       "How wide the beam's spot is, as a share of the space between lines, 0.2-1: thin lines with dark gaps between "
       'them, up to lines that touch.', 0.2, 1, True)
menu(page, 'Colors', 'Colors', COLORS, 'picture',
     "Picture keeps the picture's own colors. Colorizer gives each band of brightness a color, dark blue through teal, "
     'gray and orange to gold, twice over from dark to light, each pixel keeping its brightness, as the scan '
     'processors colored their black and white pictures. The bands slide through the tones with the low bands and '
     'slowly over time.').startSection = True

# ---- Audio (input 2): the generators' levels from the bands, a strike on each beat ------------------
section('audio', "Audio (input 2): the signal generators' levels from the music's bands, a strike on each beat")
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
                comment='Idle: a count that goes up every {:g} s while nothing is on input 2.'.format(IDLE),
                const0name='idle', const0value=Expr('int(absTime.seconds / {:g}) % 1024 if parent().par.Idle > 0 and '
                                                    'not {} else 0'.format(IDLE, WIRED)))
idle_steps = mk(comp, slopeCHOP, 'idle_steps', [idle_count], 'Above 0 on the frame Idle strikes.', timeslice=True)
strike_ask = mk(comp, mathCHOP, 'strike_ask', [steps, idle_steps], 'A beat or an idle strike asking to strike.',
                chopop='max')
flash = flash_gate(comp, strike_ask)
strike_env = mk(comp, triggerCHOP, 'strike_env', [flash], 'A strike: up at once, ringing down over {:g} s.'.format(RING),
                attack=0, peak=1, decay=RING, sustain=0, release=0)
strikes = mk(comp, countCHOP, 'strikes', [flash], 'The strikes so far: odd ones go one way, even ones the other.')
LEVEL = ("min({now} * op('bands_now')[{k}] + {rise} * max(op('bands_now')[{k}] - op('bands_usual')[{k}], 0), 1) if "
         "{wired} else parent().par.Idle * (0.5 + 0.5 * math.sin(absTime.seconds * 6.2832 / {period} + {k}))")
levels = [LEVEL.format(now=NOW, rise=RISE, wired=WIRED, k=k, period=5 + 2 * k) for k in range(7)]
idle_kick = "(1 if {} else parent().par.Idle)".format(WIRED)
lv = mk(comp, constantCHOP, 'levels', comment="Each signal generator's level (l0, the sub bass's, to l6) and the strike "
        '(signed: each goes the other way from the last; ringing down).')
lv.seq.const.numBlocks = 8
for k, text in enumerate(levels + ["op('strike_env')[0] * (1 - 2 * (int(op('strikes')[0]) % 2)) * " + idle_kick]):
    setpars(lv, **{'const{}name'.format(k): 'l{}'.format(k) if k < 7 else 'strike', 'const{}value'.format(k): Expr(text)})
L = "op('levels')['l{}']"
drive = mk(comp, constantCHOP, 'drive', comment="What Scanimate and FM read from the levels: the low, middle and high "
           "bands, Scanimate's bend and FM's beta.")
items = [
    ('low', '({} + {}) / 2'.format(L.format(0), L.format(1))),
    ('mid', '({} + {} + {}) / 3'.format(L.format(2), L.format(3), L.format(4))),
    ('high', '({} + {}) / 2'.format(L.format(5), L.format(6))),
    ('bend', '{} * parent().par.Amount * ({} + {} + {}) / 3 * math.sin(absTime.seconds * 0.23 % (2 * math.pi) + '
             '1)'.format(BEND, L.format(2), L.format(3), L.format(4))),
    ('beta', 'min(parent().par.Amount * ({} + {} * ({}) / 7) + parent().par.Kick * {} * abs(op(\'levels\')'
             '[\'strike\']), {})'.format(BETA[0], BETA[1], ' + '.join(L.format(k) for k in range(7)), BETA[2],
                                         BETA[3])),
]
drive.seq.const.numBlocks = len(items)
for k, (name, text) in enumerate(items):
    setpars(drive, **{'const{}name'.format(k): name, 'const{}value'.format(k): Expr(text)})


def chan(name, of='levels'):
    return Expr("op('{}')['{}']".format(of, name))


W0 = (chan('l0'), chan('l1'), chan('l2'), chan('l3'))
W1 = (chan('l4'), chan('l5'), chan('l6'), chan('strike'))

# ---- The yokes ----------------------------------------------------------------------------------
section('yokes', "The yokes: seven signal generators, one a band, and what they do to each line of the raster",
        lane='yokes')
phase_size = mk(comp, constantTOP, 'phase_size', comment='Seven pixels, one a signal generator: the size of phase.',
                outputresolution='custom', resolutionw=7, resolutionh=1, format='rgba32float', colorr=0, colorg=0,
                colorb=0, alpha=1)
phase_fb = mk(comp, feedbackTOP, 'phase_fb', [phase_size], "phase's last frame.", top='phase')
phase = glsl(comp, 'phase', [phase_size, phase_fb], src('phase.glsl'),
             "The signal generators' phases, each creeping at its own rate, faster while its band is loud.",
             fmt='rgba32float', uW0=W0, uW1=W1, uD=(Expr('min(absTime.stepSeconds, 0.1)'), par('Speed')))
yokes = glsl(comp, 'yokes', [phase], src('yokes.glsl'),
             "What the yokes do to each line: its push sideways and drop (Wobbulator), its twist and ripple "
             "(Scanimate) or its pleats' phase (FM), one pixel a line.", fmt='rgba32float',
             uW0=W0, uW1=W1, uM=(Expr('parent().par.Scan.menuIndex'), par('Amount'), par('Kick'), clock_seconds()),
             uS=(chan('low', 'drive'), chan('mid', 'drive'), chan('high', 'drive'), 0))
setpars(yokes, outputresolution='custom', resolutionw=par('Lines'), resolutionh=1)

# ---- The raster ---------------------------------------------------------------------------------
section('raster', 'The raster: the picture drawn line by line where the yokes put each line, then colored',
        lane='picture')
scan = glsl(comp, 'scan', [source, yokes], src('scan.glsl'),
            'The raster: each line the picture averaged over its rows, drawn as the beam\'s spot where yokes puts it, '
            'the light adding up where lines bunch.',
            uR=(par('Lines'), par('Beam'), Expr('parent().par.Scan.menuIndex'),
                Expr("{} * {} * parent().par.Amount * parent().par.Lines if parent().par.Scan == 'wobbulator' else "
                     "0".format(DOWN, REACH))),
            uB=(chan('bend', 'drive'), chan('beta', 'drive'), PLEATS, 0))
setpars(scan, inputextenduv='hold')
show = glsl(comp, 'show', [scan], lib_glsl(_ROOT, 'red_guard.glsl') + src('show.glsl'),
            "The raster's colors (the picture's own, or the colorizer's), every pixel through the red guard.",
            uC=(Expr('parent().par.Colors.menuIndex'),
                Expr("(0.15 * op('drive')['low'] + 0.05 * (absTime.seconds % 20)) % 1"), 0, 0))

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
