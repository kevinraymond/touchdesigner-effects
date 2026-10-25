"""Build VHS + CRT. Run from a textport: __file__ = '/path/to/build_vhs_crt.py'; exec(open(__file__).read())

The picture as a VHS tape played into a CRT television shows it, modeled as the signal goes rather than laid
over the top: the deck's time base wobbles each line sideways; its luma and chroma channels lowpass and
sharpen the picture (causal filters, so colors bleed to the right) and add their noise, specks, dropouts and
mistracking; the composite cable and the TV's decoder add dots and rainbows; the tube draws each line with
a beam that widens as it brightens, through a phosphor mask, and the glass glows around the light. On the
music the heads lose tracking for a moment, and a drop slips the picture down a third of a frame.

The network, left to right:
  picture  source -> line_in (each line read where the deck's time base puts it, as YIQ) -> tape (the deck's
           filters, noise, specks, dropouts, mistracking) -> deck (its steep output filter) -> signal
           (composite, S-Video or RGB into the TV)
           -> glow_src -> glow (the light the glass spreads) -> screen (beams, mask, glow, curvature)
  audio    audio_in() -> counts -> steps (Slope CHOP); steady counts the time; beat_on, bar_on, steady_on,
           drop_on pick the bursts asked for -> flash_gate() -> flash_budget -> burst (the heads mistracking,
           held for Length), burst_count (the seed), drop_kind (a drop's burst: the picture slips);
           beats (or steady ticks with nothing wired) -> beat_pulse -> beat_env: the time base kicks
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# The tape's raster: this many samples a line, whatever the picture's size (each a fraction of the width;
# the shaders turn the deck's bandwidths into samples from the picture's aspect).
RASTER_W = 1280
# Tape Speed: luma and chroma bandwidths (MHz, 3 dB down) and how far the chroma lands right of the luma
# (picture heights, at Wear 0.5). VHS keeps about 240 lines of luma and about 40 of chroma across a picture
# height at SP; the slower speeds less.
SPEEDS = (('sp', 'SP', 3.4, 0.5, 0.004), ('lp', 'LP', 2.8, 0.45, 0.005), ('ep', 'EP', 2.2, 0.4, 0.006))
SHARPEN = 0.8        # playback sharpening: the luma's difference from its own blur, added back this many times
STEADY = 2.5         # bursts this many seconds apart for Steady, and for On Beats or On Bars with nothing wired
SLIP = 0.35          # a drop slips the picture this much of a frame down, for Length, then it snaps back
GLOW_SIZE = 9        # the glow's blur, in pixels at an eighth of the size (72 at full size)
# After the gate, bursts at least this far apart (s), as in Glitch: Calm a little over its one second, else
# about 2 a second, leaving headroom under WCAG's 3 for what the picture does by itself.
FLASH_SPACING = {'calm': 1.1, 'other': 0.55}
SIGNALS = (('composite', 'Composite'), ('svideo', 'S-Video'), ('rgb', 'RGB'))
MASKS = (('aperture', 'Aperture Grille'), ('slot', 'Slot Mask'), ('shadow', 'Shadow Mask'), ('none', 'None'))


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [n for n, _ in items]
    p.menuLabels = [label for _, label in items]
    p.default = p.val = default
    return p


README = src('readme.txt').format(v=VERSION, steady=STEADY)
comp, page, source = new_effect(
    'vhs_crt', 'VHS + CRT',
    'VHS + CRT {}: the picture played off a worn VHS tape into a CRT television, modeled as the signal goes: '
    'bleeding color, noise, tracking, head switching, composite dots, scanlines, phosphor mask and glow.'.format(VERSION),
    README, tags=('vhs', 'crt', 'analog', 'audio-reactive'), audio=True, flashing=True, sample=SAMPLE_MOVIE)

# ---- Parameters -------------------------------------------------------------------------------
TAPE_ON, SCREEN_ON = 'me.par.Tape', 'me.par.Screen'
p = custom(page, 'Toggle', 'Tape', 'Tape', True,
           'Play the picture off a VHS tape: soft, bleeding color, noise, a wobbly time base. Off: straight '
           'into the TV.')
p.startSection = True
p = menu(page, 'Speed', 'Tape Speed', [(n, l) for n, l, *_ in SPEEDS], 'sp',
         'SP is the best a VHS tape gets; LP and EP fit more on a tape and keep less detail, so the picture '
         'is softer and the colors bleed further.')
p.enableExpr = TAPE_ON
p = custom(page, 'Float', 'Wear', 'Wear', 0.4,
           'How worn the tape and the deck are, 0-1: grain, color noise, white specks, dropouts, the hue '
           'wandering, lines wobbling sideways and the top of the frame bending.', 0, 1, True)
p.enableExpr = TAPE_ON
p = custom(page, 'Float', 'Tracking', 'Tracking', 0.2,
           'How far off the tracking is, 0-1: a band where the heads read between the tracks, torn sideways '
           'and full of white streaks, crawls up the picture. 0: none.', 0, 1, True)
p.enableExpr = TAPE_ON
p = custom(page, 'Toggle', 'Headswitch', 'Head Switching', True,
           'The last lines at the bottom pushed sideways, with a line of noise above them, where the deck '
           'switches from one head to the other.')
p.enableExpr = TAPE_ON
p = menu(page, 'Signal', 'Signal', SIGNALS, 'composite',
         'How the picture reaches the TV. Composite: brightness and color on one wire, so colored edges '
         'show dots and fine detail turns into rainbows. S-Video: on two wires, no dots. RGB: as it is.')
p.startSection = True
custom(page, 'Int', 'Lines', 'Lines', 240,
       'How many lines the picture has, top to bottom, on tape and on the screen. 240: one field of NTSC, '
       'as old consoles drew it.', 120, 576, True)
p = custom(page, 'Toggle', 'Screen', 'Screen', True,
           'Show it on a CRT: scanlines, the phosphor mask, glow and a curved face. Off: the signal, flat.')
p.startSection = True
p = menu(page, 'Mask', 'Mask', MASKS, 'aperture',
         'The pattern of red, green and blue phosphors. Aperture Grille: fine stripes (Trinitron). Slot Mask: '
         'stripes broken into staggered slots (most TVs). Shadow Mask: dot triads (older sets, monitors).')
p.enableExpr = SCREEN_ON
p = custom(page, 'Float', 'Masksize', 'Mask Size', 3.0,
           'Width of one red-green-blue triad, in pixels at 720 high (scales with the picture).', 2, 8, True)
p.enableExpr = SCREEN_ON + " and me.par.Mask != 'none'"
p = custom(page, 'Float', 'Scanlines', 'Scanlines', 0.6,
           'How much the lines stand apart, 0-1: dark lines thin with black between them, bright lines '
           'wide enough to touch, as a CRT\'s beam grows with its brightness.', 0, 1, True)
p.enableExpr = SCREEN_ON
p = custom(page, 'Float', 'Curvature', 'Curvature', 0.3,
           'How much the glass bows, 0-1, with rounded corners and darker edges. 0: flat.', 0, 1, True)
p.enableExpr = SCREEN_ON
p = custom(page, 'Float', 'Glow', 'Glow', 0.3, 'Light spreading in the glass around bright parts (halation), 0-1.',
           0, 1, True)
p.enableExpr = SCREEN_ON
p = menu(page, 'Bursts', 'Bursts', (('beats', 'On Beats'), ('bars', 'On Bars'), ('steady', 'Steady'), ('off', 'Off')),
         'bars',
         "When the heads lose tracking for a moment: a big torn band full of streaks. On Bars (the one of each "
         "bar) or On Beats: input 2's (with nothing wired, every {s:g} s). Steady: every {s:g} s. Off: never. "
         "Every burst is a flash, so Flashing limits how often they come.".format(s=STEADY))
p.startSection = True
custom(page, 'Float', 'Length', 'Length', 0.3, 'How long a burst lasts, in seconds.', 0.1, 1.0, True).enableExpr = \
    "me.par.Bursts != 'off'"
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a build throws the tracking off further as it rises, and a drop slips "
       "the picture down for a moment, as a TV losing vertical hold (Fosfora's drop detection is experimental).")

# ---- Audio (input 2) and the bursts -------------------------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -200, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count drop_count')
steady = mk(comp, constantCHOP, 'steady', -200, -500, comment='Counts {:g} s periods, for Steady bursts.'.format(STEADY),
            const0name='steady_count', const0value=Expr('int(absTime.seconds / {})'.format(STEADY)))
both = mk(comp, mergeCHOP, 'all_counts', 0, -400, [counts, steady], 'Every count a burst may follow.')
steps = mk(comp, slopeCHOP, 'steps', 200, -400, [both], 'Above 0 on the frame a count goes up.', timeslice=True)
WIRED = "op('audio')['source'].eval() > 0"
asks = []
for i, (name, chan, when, what) in enumerate((
        ('beat_on', 'beat_count', "parent().par.Bursts == 'beats' and " + WIRED, 'beats, when Bursts is On Beats'),
        ('bar_on', 'bar_count', "parent().par.Bursts == 'bars' and " + WIRED, 'bars, when Bursts is On Bars'),
        ('steady_on', 'steady_count',
         "parent().par.Bursts == 'steady' or (parent().par.Bursts in ('beats', 'bars') and not " + WIRED + ")",
         'the steady clock, when Bursts is Steady (or On Beats or On Bars with nothing on input 2)'),
        ('drop_on', 'drop_count', "parent().par.Moments and parent().par.Bursts != 'off'", 'drops (Song Moments)'))):
    pick = mk(comp, selectCHOP, name + '_step', 400, -250 - 150 * i, [steps], 'Steps of {}.'.format(chan), channames=chan)
    asks.append(mk(comp, mathCHOP, name, 600, -250 - 150 * i, [pick], 'Bursts on {}.'.format(what),
                   gain=Expr('1 if ({}) else 0'.format(when))))
ask = mk(comp, mergeCHOP, 'burst_asks', 800, -450, asks, 'Every burst asked for.')
ask_any = mk(comp, mathCHOP, 'burst_any', 1000, -450, [ask], 'One channel: any burst.', chanop='max')
gate = flash_gate(comp, ask_any, 1200, -450)
budget = mk(comp, triggerCHOP, 'flash_budget', 1600, -450, [gate],
            'After the gate: bursts {calm} s apart at Calm, {other} s otherwise, so the total stays well under '
            'WCAG.'.format(**FLASH_SPACING),
            retrigger=Expr("{calm} if parent().par.Flashing == 'calm' else {other}".format(**FLASH_SPACING)),
            retriggerunit='seconds', attack=0, peak=1, peaklen=0, decay=0, sustain=0, release=0)
burst = mk(comp, triggerCHOP, 'burst', 1800, -350, [budget],
           'A burst: 1 for Length seconds, then gone over 0.15 s.',
           attack=0, peak=1, peaklen=par('Length'), decay=0.15, sustain=0, release=0)
burst_count = mk(comp, countCHOP, 'burst_count', 1800, -500, [budget], "Bursts so far: each burst's seed.")
drop_step = mk(comp, selectCHOP, 'drop_now', 1600, -650, [asks[3]], 'A drop asking for a burst.')
drop_env = mk(comp, triggerCHOP, 'drop_env', 1800, -650, [drop_step], 'How recent a drop is (fades over 0.3 s).',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
drop_kind = mk(comp, holdCHOP, 'drop_kind', 2000, -600, [drop_env, budget],
               "1 when the burst that passed was a drop's: it slips the picture.")

tick = mk(comp, mathCHOP, 'steady_tick', 800, -100, [asks[2].inputs[0]], 'Steady ticks, only while input 2 is empty.',
          gain=Expr('0 if ' + WIRED + ' else 1'))
beat_in = mk(comp, mergeCHOP, 'beat_in', 1000, -150, [asks[0].inputs[0], tick], 'Beats, or steady ticks.')
beat_pick = mk(comp, mathCHOP, 'beat_pulse', 1200, -150, [beat_in], 'One channel: a beat, for the time base kick.',
               chanop='max')
beat_env = mk(comp, triggerCHOP, 'beat_env', 1400, -150, [beat_pick], 'Falls from 1 to 0 over the 0.3 s after a beat.',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)

# ---- Picture ----------------------------------------------------------------------------------
# A drop's slip: the whole of it at once and back at once, so each part of the picture changes once and back
# (one flash); a roll sweeping the picture past every point made several.
SLIPPED = ("{} if op('burst')[0] > 0.5 and op('drop_kind')[0] > 0.5 and parent().par.Moments else 0").format(SLIP)
KICK = "op('beat_env')[0] if parent().par.Flashing != 'off' and parent().par.Bursts != 'off' else 0"
TAPE = dict(
    uT=(Expr('absTime.seconds'), par('Lines'), Expr(KICK), Expr(SLIPPED)),
    uTape=(par('Tape'), par('Wear'),
           Expr("min(1, parent().par.Tracking + (0.5 * op('audio')['build'] if parent().par.Moments else 0))"),
           par('Headswitch')),
    uBurst=(Expr("op('burst')[0]"), Expr("op('burst_count')[0]"), Expr("op('audio')['level']")))
common = lib_glsl(_ROOT, 'common.glsl') + src('common.glsl')
line_in = glsl(comp, 'line_in', -400, 150, [source], common + src('line_in.glsl'),
               "Each line of the picture where the deck's time base puts it, as YIQ.", res=(RASTER_W, 240),
               fmt='rgba16float', uMode=Expr('parent().par.Signal.menuIndex'), **TAPE)
tape = glsl(comp, 'tape', -200, 150, [line_in, source], common + src('tape.glsl'),
            "The deck: its luma and chroma filters, noise, specks, dropouts, mistracking.", res=(RASTER_W, 240),
            fmt='rgba16float', uSpeed=tuple(Expr('{}[parent().par.Speed.menuIndex]'.format(tuple(s[k] for s in SPEEDS)))
                                             for k in (2, 3, 4)) + (SHARPEN,), **TAPE)
deck = glsl(comp, 'deck', 0, 150, [tape, source], src('deck.glsl'),
            "The deck's steep output filter on the luma (3 MHz): keeps tape noise out of the color subcarrier.",
            res=(RASTER_W, 240), fmt='rgba16float', uDeck=par('Tape'))
signal = glsl(comp, 'signal', 200, 150, [deck, source], src('red_guard.glsl') + src('signal.glsl'),
              'Into the TV: composite (dots, rainbows), S-Video or RGB, back to RGB.', res=(RASTER_W, 240),
              fmt='rgba16float', uSig=(Expr('parent().par.Signal.menuIndex'), 0, par('Lines')))
for o in (line_in, tape, deck, signal):
    o.par.resolutionh.expr = 'parent().par.Lines'
glow_src = glsl(comp, 'glow_src', 200, 0, [source, signal], src('glow.glsl'),
                'The signal at an eighth of the size, in linear light, for the glow.', fmt='rgba16float')
glow_src.par.outputresolution = 'eighth'
glow = mk(comp, blurTOP, 'glow', 400, 0, [glow_src], 'The light the glass spreads around bright parts.',
          type='gaussian', size=GLOW_SIZE)
screen = glsl(comp, 'screen', 600, 150, [source, signal, glow], src('red_guard.glsl') + src('screen.glsl'),
              'The tube: each line a beam that widens as it brightens, the phosphor mask, the glow, the curved face.',
              uScr=(par('Screen'), Expr('parent().par.Mask.menuIndex'), par('Masksize'), par('Scanlines')),
              uScr2=(par('Lines'), par('Curvature'), par('Glow')))

finish_effect(comp, screen, VERSION, page)
save_effect(comp, _HERE, _ROOT)
