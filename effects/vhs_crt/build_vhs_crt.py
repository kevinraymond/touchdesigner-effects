"""Build VHS + CRT. Run from a textport: __file__ = '/path/to/build_vhs_crt.py'; exec(open(__file__).read())

The picture as a VHS tape played into a CRT television shows it, modeled as the signal goes rather than laid
over the top: the deck's time base wobbles each line sideways; its luma and chroma channels lowpass and
sharpen the picture (causal filters, so colors bleed to the right) and add their noise, specks, dropouts and
mistracking; the composite cable and the TV's decoder add dots and rainbows; the tube draws each line with
a beam that widens as it brightens, through a phosphor mask, and the glass glows around the light. Or another
screen shows it: an LCD (slow crystal, smearing; tones that shift with the viewing angle), a plasma panel (grays
made of pulses, false contours on moving gradients) or e-ink (a few updates a second, ghosts, a full refresh on
each burst). On the music the heads lose tracking for a moment, and a drop slips the picture down a third of a
frame; on e-ink, each of those is a full refresh instead.

The network, left to right:
  picture  source -> line_in (each line read where the deck's time base puts it, as YIQ) -> tape (the deck's
           filters, noise, specks, dropouts, mistracking) -> deck (its steep output filter) -> signal
           (composite, S-Video or RGB into the TV)
           -> glow_src -> glow (the light the glass spreads) -> screen (beams, mask, glow, curvature)
  screens  lcd_state (the crystal, read back through lcd_fb) -> lcd; lib optical_flow() and flow_speed() (the
           picture's motion) -> plasma; eink_state (read back through eink_fb) -> eink; shown picks one by
           Screen (only that one cooks); still is where every Feedback TOP starts
  audio    audio_in() -> counts -> steps (Slope CHOP); steady counts the time; beat_on, bar_on, steady_on,
           drop_on pick the bursts asked for -> flash_gate() -> flash_budget -> burst (the heads mistracking,
           held for Length), burst_count (the seed), drop_kind (a drop's burst: the picture slips), refresh
           (e-ink's full refresh, which takes a burst's place);
           beats (or steady ticks with nothing wired) -> beat_pulse -> beat_env: the time base kicks
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.2.0'
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
SCREENS = (('crt', 'CRT'), ('lcd', 'LCD'), ('plasma', 'Plasma'), ('eink', 'E-Ink'), ('none', 'None'))
SUBFIELDS = (('binary', '8 (Binary)'), ('redundant', '12 (Redundant)'))
INK_MODES = (('gray16', '16 Grays'), ('gray4', '4 Grays'), ('fast', 'Fast'))
# E-ink's full refresh, in seconds: to black, held there, back to the picture. One dark flash, through the gate.
REFRESH = (0.12, 0.12, 0.3)
DT = Expr('min(absTime.stepSeconds, 0.05)')


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
TAPE_ON = 'me.par.Tape'
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
p = menu(page, 'Screen', 'Screen', SCREENS, 'crt',
         'What shows the picture. CRT: a tube (scanlines, the phosphor mask, glow, a curved face). LCD: liquid '
         'crystal, slow to change, so moving things smear, its tones shifting with the angle it is seen from. '
         'Plasma: cells of glowing gas that make each gray from pulses, so moving gradients break into false bands. '
         'E-Ink: paper-like grays updating a few times a second, leaving ghosts, cleared by a full refresh (a black '
         'flash) on each burst. None: the signal, flat.')
p.startSection = True
CRT = "me.par.Screen == 'crt'"
p = menu(page, 'Mask', 'Mask', MASKS, 'aperture',
         'The pattern of the CRT\'s red, green and blue phosphors. Aperture Grille: fine stripes (Trinitron). Slot '
         'Mask: stripes broken into staggered slots (most TVs). Shadow Mask: dot triads (older sets, monitors).')
p.enableExpr = CRT
p = custom(page, 'Float', 'Masksize', 'Mask Size', 3.0,
           "Width of one red-green-blue triad of the CRT's mask, or of one pixel of the LCD or plasma panel, in "
           'pixels at 720 high (scales with the picture).', 2, 8, True)
p.enableExpr = "(me.par.Screen == 'crt' and me.par.Mask != 'none') or me.par.Screen in ('lcd', 'plasma')"
p = custom(page, 'Float', 'Scanlines', 'Scanlines', 0.6,
           'How much the CRT\'s lines stand apart, 0-1: dark lines thin with black between them, bright lines '
           'wide enough to touch, as a CRT\'s beam grows with its brightness.', 0, 1, True)
p.enableExpr = CRT
p = custom(page, 'Float', 'Curvature', 'Curvature', 0.3,
           'How much the CRT\'s glass bows, 0-1, with rounded corners and darker edges. 0: flat.', 0, 1, True)
p.enableExpr = CRT
p = custom(page, 'Float', 'Glow', 'Glow', 0.3,
           "Light spreading in the glass around bright parts (halation), 0-1: the CRT's, or the plasma panel's "
           'front glass.', 0, 1, True)
p.enableExpr = "me.par.Screen in ('crt', 'plasma')"
p = custom(page, 'Float', 'Response', 'Response', 0.5,
           "How slowly the LCD's crystal follows, 0-1: 0 a later panel, 1 an early one. Moving things leave trails, "
           'longest where cells turn lighter (behind dark things moving over light ones), since a cell turns to '
           'let light through more slowly than to block it.', 0, 1, True)
p.enableExpr = "me.par.Screen == 'lcd'"
p = custom(page, 'Float', 'Angle', 'Viewing Angle', 0.0,
           'Where the LCD is seen from, -1 (well below) to 1 (well above). From above the picture washes out; from '
           'below it darkens and its light tones invert. At 0 the top is seen a little from below and the bottom '
           'from above, as on an old laptop.', -1, 1, True)
p.enableExpr = "me.par.Screen == 'lcd'"
p = menu(page, 'Subfields', 'Sub-Fields', SUBFIELDS, 'binary',
         'How the plasma panel makes each gray: lighting a cell for some of a frame\'s pulses. 8 (Binary): pulses '
         'of 1, 2, 4 ... 128, as early panels did: where a gradient moves, the eye adds pulses from different grays '
         'and sees false bands (dynamic false contours). 12 (Redundant): seven pulses of 32 for the upper grays, as '
         'later panels did: fainter bands.')
p.enableExpr = "me.par.Screen == 'plasma'"
p = menu(page, 'Inkmode', 'Ink Mode', INK_MODES, 'gray4',
         'How the e-ink panel updates, after E Ink\'s own modes. 16 Grays: about twice a second. 4 Grays: about '
         'three times a second. Fast: black and white, dithered, about eight times a second, a little less contrast.')
p.enableExpr = "me.par.Screen == 'eink'"
p = custom(page, 'Float', 'Ghosting', 'Ghosting', 0.5,
           'How much of what the e-ink panel showed stays behind after each update, 0-1. Where a pixel then holds '
           'still, its ghost stays, so ghosts pile up until a full refresh (each burst) clears them.', 0, 1, True)
p.enableExpr = "me.par.Screen == 'eink'"
p = menu(page, 'Bursts', 'Bursts', (('beats', 'On Beats'), ('bars', 'On Bars'), ('steady', 'Steady'), ('off', 'Off')),
         'bars',
         "When the heads lose tracking for a moment: a big torn band full of streaks (on e-ink, a full refresh "
         "instead: black and back, the ghosts cleared). On Bars (the one of each bar) or On Beats: input 2's (with "
         "nothing wired, every {s:g} s). Steady: every {s:g} s. Off: never. Every burst is a flash, so Flashing "
         "limits how often they come.".format(s=STEADY))
p.startSection = True
custom(page, 'Float', 'Length', 'Length', 0.3, 'How long a burst lasts, in seconds.', 0.1, 1.0, True).enableExpr = \
    "me.par.Bursts != 'off'"
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a build throws the tracking off further as it rises, and a drop slips "
       "the picture down for a moment, as a TV losing vertical hold (on e-ink, a full refresh; Fosfora's drop "
       "detection is experimental).")

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
refresh = mk(comp, triggerCHOP, 'refresh', 1800, -200, [budget],
             "E-ink's full refresh, a burst's place on e-ink: to black over {} s, held {} s, back over {} s.".format(
                 *REFRESH),
             attack=REFRESH[0], peak=1, peaklen=REFRESH[1], decay=REFRESH[2], sustain=0, release=0)

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
# On e-ink a burst is a full refresh instead, so the tape neither bursts nor slips there.
INK = "parent().par.Screen == 'eink'"
SLIPPED = ("{} if not {} and op('burst')[0] > 0.5 and op('drop_kind')[0] > 0.5 and parent().par.Moments "
           "else 0").format(SLIP, INK)
KICK = "op('beat_env')[0] if parent().par.Flashing != 'off' and parent().par.Bursts != 'off' else 0"
TAPE = dict(
    uT=(Expr('absTime.seconds'), par('Lines'), Expr(KICK), Expr(SLIPPED)),
    uTape=(par('Tape'), par('Wear'),
           Expr("min(1, parent().par.Tracking + (0.5 * op('audio')['build'] if parent().par.Moments else 0))"),
           par('Headswitch')),
    uBurst=(Expr("0 if {} else op('burst')[0]".format(INK)), Expr("op('burst_count')[0]"),
            Expr("op('audio')['level']")))
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
              'The tube: each line a beam that widens as it brightens, the phosphor mask, the glow, the curved face '
              '(Screen CRT); the signal, flat (None).',
              uScr=(Expr("1 if parent().par.Screen == 'crt' else 0"), Expr('parent().par.Mask.menuIndex'),
                    par('Masksize'), par('Scanlines')),
              uScr2=(par('Lines'), par('Curvature'), par('Glow')))

# ---- The other screens ---------------------------------------------------------------------------
panel = src('panel.glsl')
still = mk(comp, constantTOP, 'still', 400, 450, comment='Nothing: where every Feedback TOP starts.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
lcd_fb = mk(comp, feedbackTOP, 'lcd_fb', 600, 600, [still], "lcd_state's last frame.", top='lcd_state')
lcd_state = glsl(comp, 'lcd_state', 600, 450, [source, signal, lcd_fb], panel + src('lcd_state.glsl'),
                 "The LCD's crystal: each cell turning toward the signal over milliseconds, more slowly to lighter.",
                 fmt='rgba16float', uLcd=(par('Masksize'), par('Response'), DT))
lcd = glsl(comp, 'lcd', 800, 450, [source, lcd_state], src('red_guard.glsl') + panel + src('lcd.glsl'),
           "The LCD's face: the cells in their black matrix, the backlight, the tones the viewing angle shifts.",
           uLcd=(par('Masksize'), 0, 0, par('Angle')))
mo = optical_flow(comp, _ROOT, source, x=0, y=800)
pace, motion = flow_speed(comp, _ROOT, mo, still, x=800, y=800)
plasma = glsl(comp, 'plasma', 1000, 800, [source, signal, glow, motion],
              src('red_guard.glsl') + panel + src('plasma.glsl'),
              "The plasma panel: grays made of a frame's pulses, read along the eye's path (false contours), the "
              "phosphors' afterglow, the cells, the glass's glow.",
              uPl=(par('Masksize'), Expr('parent().par.Subfields.menuIndex'), par('Glow'),
                   Expr('int(absTime.seconds * 60) % 4096')))
# E-ink's updates, counted in Python (double precision): which one this is (mod 1024) and how far through it.
WAVE = "(0.45, 0.29, 0.12)[parent().par.Inkmode.menuIndex]"
INK_PARS = dict(uInk=(Expr('int(absTime.seconds / {}) % 1024'.format(WAVE)), Expr('absTime.seconds / {} % 1'.format(WAVE)),
                      Expr('parent().par.Inkmode.menuIndex'), par('Ghosting')),
                uInk2=(Expr("op('refresh')[0]"),))
eink_fb = mk(comp, feedbackTOP, 'eink_fb', 1000, 600, [still], "eink_state's last frame.", top='eink_state')
eink_state = glsl(comp, 'eink_state', 1000, 450, [source, signal, eink_fb], panel + src('eink_state.glsl'),
                  'The e-ink panel: the gray each pixel is driven to a few times a second, and the ghosts it leaves.',
                  fmt='rgba16float', **INK_PARS)
eink = glsl(comp, 'eink', 1200, 450, [source, eink_state], lib_glsl(_ROOT, 'common.glsl') + src('eink.glsl'),
            "The e-ink panel's face: ink and paper grays, each update easing in, the full refresh.", **INK_PARS)
shown = mk(comp, switchTOP, 'shown', 1000, 150, [screen, lcd, plasma, eink],
           'The screen Screen picks (None is the flat signal, from screen): only that one cooks.',
           index=Expr("{'lcd': 1, 'plasma': 2, 'eink': 3}.get(parent().par.Screen.eval(), 0)"))

finish_effect(comp, shown, VERSION, page)
save_effect(comp, _HERE, _ROOT)
