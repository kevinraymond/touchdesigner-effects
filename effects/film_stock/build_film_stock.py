"""Build Film Stock. Run from a textport: __file__ = '/path/to/build_film_stock.py'; exec(open(__file__).read())

The picture shot on film and printed, modeled from the film rather than laid over the top. Each frame is held at the
film's frame rate and weaves in the gate; its light, through the stock's own softness, exposes the layers of the
emulsion by their characteristic curves, and bright light bounces off the base into the red layer (halation). The
density of each layer is grain: the Boolean model of stochastic geometry (Newson, Delon and Galerne 2017), simulated,
not summarized: for each pixel and layer the number of developed grains is drawn from its Poisson law and, once the
grains are big enough to see, each grain is drawn where it falls. The grain's size on the film comes from Kodak's
published rms granularity by Nutting's formula, and on screen from the Gauge (how many micrometers of film one pixel
holds), so Super 8 is grainier, softer and wanders further than 35 mm, as it does. The negative is read a little soft
and printed on a steep print curve (or the reversal shown as it is), with the dyes' impurities and the stock's
character; the lamp flickers, dirt and scratches land on the print, and the red guard covers every pixel. Day for
Night is Thompson, Shirley and Ferwerda's night look. On the music, beats kick the film in the gate and drops splice
the reel, both through the flash gate; louder passages push the grain; section changes show a cue mark.

The task's paper (Zhang, Wang, Tian and Pappas, TOG 2023) derives the model's statistics and synthesizes noise with
them; that method is Northwestern's US 12,705,810 (private/patents/film_stock.md), so it is not used: nothing here
derives a variance or scales noise.

The network, left to right:
  picture  source -> hold (held at the film's frame rate, read back through hold_fb) -> cadence (it or the source) ->
           gate (weave, kicks, splices; linear light, Exposure) -> night_src, night_fine, night_wide -> night (Day for
           Night) -> scene (it or the gate's picture) -> glare -> halo (the light that halates) ; negative (the layers'
           density as grain) -> print (the print or the reversal, the dyes, the stock's character) -> show (flicker,
           dirt, the cue mark, the red guard) -> out
  audio    audio_in() -> counts -> steps; beat_on, drop_on -> flash gate -> flash_budget -> kick_env (a kick),
           drop_env + drop_kind -> splice_env (a splice); section steps -> cue; level_pick -> level_smooth (the push);
           film_frame (the film's frame number) and clock
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# The stocks. curve: gamma (density per log10 exposure), dmin, density range, and where a mid gray sits (stops below
# the curve's middle, negative for a reversal). grain: each layer's mean grain radius in micrometers (one value for
# black and white) from the published granularity by Nutting's formula (0.0364 mm x sigma_D), and the log-normal
# spread of the radii. look: layers (1 or 3), reversal (0 or 1), resolving power (lines a millimeter, where its MTF is
# about 10%), and how much it halates (1: no anti-halation layer at all). dyes: the dyes' impurity (0-1) and the
# stock's saturation. shadow and high: tints in log10 light in the shadows and the highlights.
STOCKS = (
    dict(name='neg500t', label='Color Negative 500T', curve=(0.6, 0.2, 2.2, 3.0), grain=(0.40, 0.40, 0.73, 0.4),
         look=(3, 0, 70, 0.25), dyes=(0.3, 1.0), shadow=(-0.01, 0.0, 0.015), high=(0.01, 0.004, -0.01)),
    dict(name='neg50d', label='Color Negative 50D', curve=(0.6, 0.2, 2.2, 3.0), grain=(0.28, 0.28, 0.5, 0.3),
         look=(3, 0, 110, 0.25), dyes=(0.3, 1.05), shadow=(0.0, 0.0, 0.01), high=(0.005, 0.005, 0.0)),
    dict(name='vintage', label='Vintage Color Negative', curve=(0.62, 0.25, 2.0, 2.8), grain=(0.55, 0.55, 0.9, 0.5),
         look=(3, 0, 55, 0.6), dyes=(0.6, 0.85), shadow=(0.02, 0.01, -0.02), high=(0.01, 0.0, -0.02)),
    dict(name='reversal', label='Color Reversal', curve=(1.7, 0.1, 3.2, -1.86), grain=(0.35, 0.35, 0.5, 0.3),
         look=(3, 1, 90, 0.35), dyes=(0.5, 1.25), shadow=(0.0, -0.01, 0.01), high=(0.01, 0.0, -0.01)),
    dict(name='bw400', label='Black and White 400', curve=(0.65, 0.25, 2.3, 3.0), grain=(0.62, 0.62, 0.62, 0.45),
         look=(1, 0, 100, 0.4), dyes=(0.0, 1.0), shadow=(0.0, 0.0, 0.0), high=(0.0, 0.0, 0.0)),
    dict(name='bw100', label='Black and White 100', curve=(0.7, 0.2, 2.3, 3.0), grain=(0.29, 0.29, 0.29, 0.3),
         look=(1, 0, 200, 0.4), dyes=(0.0, 1.0), shadow=(0.0, 0.0, 0.0), high=(0.0, 0.0, 0.0)),
)
# The film's frame: its height in micrometers for each Gauge (SMPTE camera apertures: 35 mm 22.05 x 16.03 mm, 16 mm
# 10.26 x 7.49 mm, Super 8 5.79 x 4.01 mm) and how far the halo spreads at 720 high, at an eighth of the size, as a
# Blur TOP size (sigma about 0.21 of the size): the base is about 125 micrometers thick, the ring a little wider.
GAUGES = (('g35', '35 mm', 16030, 5.3), ('g16', '16 mm', 7490, 11.3), ('s8', 'Super 8', 4010, 21.0))
RATES = (('source', 'Source'), ('fps24', '24 fps'), ('fps18', '18 fps (Super 8)'), ('fps16', '16 fps (silent 16 mm)'))
SWITCH = 0.4         # grains are drawn one by one from this radius in pixels up
SCAN_SIGMA = 0.8     # the scanner's softness on the negative, in pixels (its color twice that)
KICK_FADE = 0.3      # a kick settles over this many seconds
SPLICE_S = 0.2       # a splice's roll settles over this many seconds
CUE_S = 0.17         # the cue mark shows this long (4 frames at 24)
FLASH_SPACING = {'calm': 1.1, 'other': 0.55}   # after the gate, as VHS + CRT: about 2 a second at Up to 3
PERF = '2.3'         # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


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


def stock_table():
    """The stocks as GLSL constants for negative.glsl and print.glsl."""
    out = '#define STOCKS {}\n'.format(len(STOCKS))
    for key, name in (('curve', 'STOCK_CURVE'), ('grain', 'STOCK_GRAIN'), ('look', 'STOCK_LOOK'), ('dyes', 'STOCK_DYES'),
                      ('shadow', 'STOCK_SHADOW'), ('high', 'STOCK_HIGH')):
        rows = [tuple(s[key]) + (0,) * (4 - len(s[key])) for s in STOCKS]
        out += 'const vec4 {}[{}] = vec4[{}](\n    {});\n'.format(
            name, len(rows), len(rows), ',\n    '.join('vec4({})'.format(', '.join('{:.5f}'.format(x) for x in r))
                                                      for r in rows))
    return out


README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'film_stock', 'Film Stock',
    'Film Stock {}: the picture shot on film and printed, modeled from the film: grain simulated grain by grain from '
    'the stock\'s granularity, weave, halation, flicker, dirt, a 24 fps cadence, day for night; beats kick the film in '
    'the gate.'.format(VERSION),
    README, tags=('film', 'grain', 'analog', 'audio-reactive'), audio=True, flashing=True, sample=SAMPLE_MOVIE)

# ---- Parameters -------------------------------------------------------------------------------
p = menu(page, 'Stock', 'Stock', [(s['name'], s['label']) for s in STOCKS], 'neg500t',
         'The film. Color Negative 500T: a modern tungsten negative, fine grain, warm skin. Color Negative 50D: the '
         'finest and sharpest, a daylight negative. Vintage Color Negative: a 1970s negative, coarser, softer, warmer, '
         'more halation, tamer colors. Color Reversal: a slide film, contrasty and saturated. Black and White 400: a '
         'classic fast panchromatic negative. Black and White 100: a modern tabular-grain negative, very fine.')
p.startSection = True
menu(page, 'Gauge', 'Gauge', [(n, l) for n, l, *_ in GAUGES], 'g16',
     "The film's size: 35 mm, 16 mm or Super 8. A smaller frame is blown up further, so its grain is bigger on screen, "
     'its picture softer, its weave wider and its halation broader.')
custom(page, 'Float', 'Exposure', 'Exposure', 0.0, 'Stops over (+) or under (-) exposed.', -3, 3, True)
custom(page, 'Float', 'Contrast', 'Contrast', 1.0, "The print's contrast, 0.5-1.5 (1: a cinema print's).", 0.5, 1.5, True)
custom(page, 'Float', 'Saturation', 'Saturation', 1.0, "The colors' saturation, 0-2, on top of the stock's own.", 0, 2,
       True)
p = custom(page, 'Float', 'Grain', 'Grain', 1.0,
           "The grain's size, as a multiple of the stock's own (1: as measured on the real film; 0: none).", 0, 3, True)
p.startSection = True
custom(page, 'Float', 'Halation', 'Halation', 0.3,
       'How much light bounces off the back of the film into the red layer around bright things, 0-1, a red glow. '
       "Each stock's anti-halation backing scales it; 1 is a film without one.", 0, 1, True)
custom(page, 'Float', 'Weave', 'Weave', 0.4,
       'How far the film wanders in the gate, 0-1: a slow drift and a jitter frame to frame, a few micrometers on the '
       'film, so further on screen for a smaller Gauge.', 0, 1, True)
custom(page, 'Float', 'Flicker', 'Flicker', 0.3,
       "How much the projector's light breathes and varies frame to frame, 0-1: never more than 5% of the light.", 0, 1,
       True)
custom(page, 'Float', 'Dirt', 'Dirt', 0.2,
       'How much dust, hair and how many scratches the print carries, 0-1: specks and hairs come and go each frame, '
       'scratches run for a second or two.', 0, 1, True)
menu(page, 'Framerate', 'Frame Rate', RATES, 'fps24',
     'Hold each frame as film does: 24 a second, 18 (Super 8), 16 (silent 16 mm), or follow the source as it comes. '
     'The grain, weave and flicker change once a film frame either way.')
p = custom(page, 'Float', 'Night', 'Day for Night', 0.0,
           'Turn the scene into a night scene, 0-1, as cinematographers shot night by day: dim, blue, the colors gone '
           'but for what is lit, fine detail lost without looking blurred.', 0, 1, True)
p.startSection = True
p = custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
           'How far each beat on input 2 kicks the film in the gate (a jump down, settling back), 0-1. Flashing limits '
           'how often.', 0, 1, True)
p.startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5, 'How much louder music on input 2 pushes the grain coarser, 0-1.',
       0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a drop splices the reel (the frame line rolls through and the picture "
       "settles) and a section change shows a cue mark (Fosfora's drop detection is experimental).")

# ---- Audio (input 2) -----------------------------------------------------------------------------
section('audio', 'Audio (input 2): beats kick the film, drops splice it, sections cue the reel, loudness pushes the grain')
audio = audio_in(comp, _ROOT)
WIRED = "op('audio')['source'].eval() > 0"
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count section_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beat_step = mk(comp, selectCHOP, 'beat_step', [steps], 'Steps of beat_count.', channames='beat_count')
beat_on = mk(comp, mathCHOP, 'beat_on', [beat_step], 'Kicks asked for: every beat, when Beat Kick is above 0.',
             gain=Expr('1 if parent().par.Kick > 0 else 0'))
drop_step = mk(comp, selectCHOP, 'drop_step', [steps], 'Steps of drop_count.', channames='drop_count')
drop_on = mk(comp, mathCHOP, 'drop_on', [drop_step], 'Splices asked for: every drop, with Song Moments on.',
             gain=Expr('1 if parent().par.Moments else 0'))
asks = mk(comp, mergeCHOP, 'asks', [beat_on, drop_on], 'Every kick or splice asked for.')
ask_any = mk(comp, mathCHOP, 'ask_any', [asks], 'One channel: any of them.', chanop='max')
section('flash', 'Flashing: kicks and splices no closer together than it allows', lane='audio')
gate = flash_gate(comp, ask_any)
budget = mk(comp, triggerCHOP, 'flash_budget', [gate],
            'After the gate: {calm} s apart at Calm, {other} s otherwise, so the total stays well under '
            'WCAG.'.format(**FLASH_SPACING),
            retrigger=Expr("{calm} if parent().par.Flashing == 'calm' else {other}".format(**FLASH_SPACING)),
            retriggerunit='seconds', attack=0, peak=1, peaklen=0, decay=0, sustain=0, release=0)
section('events', "What the music does: a kick's jump, a splice's roll, the cue mark", lane='audio')
kick_env = mk(comp, triggerCHOP, 'kick_env', [budget], 'A kick: the film jumps at once and settles over {:g} s.'.format(KICK_FADE),
              attack=0, peak=1, peaklen=0, decay=KICK_FADE, sustain=0, release=0)
drop_env = mk(comp, triggerCHOP, 'drop_env', [drop_on], 'How recent a drop is (fades over 0.3 s).',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
drop_kind = mk(comp, holdCHOP, 'drop_kind', [drop_env, budget], "1 when the event that passed the gate was a drop's.")
splice_env = mk(comp, triggerCHOP, 'splice_env', [budget], 'A splice: the roll, settling over {:g} s.'.format(SPLICE_S),
                attack=0, peak=1, peaklen=0, decay=SPLICE_S, sustain=0, release=0)
section_step = mk(comp, selectCHOP, 'section_step', [steps], 'Steps of section_count.', channames='section_count')
cue = mk(comp, triggerCHOP, 'cue', [section_step], 'The cue mark, shown for {:g} s on each section change.'.format(CUE_S),
         attack=0, peak=1, peaklen=CUE_S, decay=0, sustain=0, release=0)
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick], 'Loudness eased over a second: the push.', width=1.0)
film_frame = mk(comp, constantCHOP, 'film_frame',
                comment="The film's frame number, counted in Python (exact): the frame rate's ticks, or every frame at "
                        'Source.',
                const0name='frame',
                const0value=Expr("(absTime.frame if parent().par.Framerate == 'source' else int(absTime.seconds * "
                                 "{'fps24': 24, 'fps18': 18, 'fps16': 16}[parent().par.Framerate.eval()])) % 65536"))
PUSH = "max(0.5, 1 + parent().par.Loudness * 2 * (op('level_smooth')[0] - 0.5)) if {} else 1".format(WIRED)
UF = (Expr("op('film_frame')[0]"), clock_seconds(), Expr('parent().par.Grain * ({})'.format(PUSH)),
      Expr('{}[parent().par.Gauge.menuIndex]'.format(tuple(g[2] for g in GAUGES))))
common = lib_glsl(_ROOT, 'common.glsl') + src('common.glsl')
KICK = "parent().par.Kick * op('kick_env')[0] if parent().par.Flashing != 'off' else 0"
SPLICE = "op('splice_env')[0] if op('drop_kind')[0] > 0.5 and parent().par.Moments and parent().par.Flashing != 'off' else 0"

# ---- Picture ----------------------------------------------------------------------------------
section('cadence', "The frame rate: each frame held as long as film holds it")
still = mk(comp, constantTOP, 'still', comment='Nothing: where the Feedback TOP starts.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
hold_fb = mk(comp, feedbackTOP, 'hold_fb', [still], "hold's last frame.", top='hold')
hold = glsl(comp, 'hold', [source, hold_fb], common + src('hold.glsl'),
            "The frame held until the film's frame number changes (its number in alpha).", fmt='rgba16float', uF=UF)
cadence = mk(comp, switchTOP, 'cadence', [source, hold], 'The source as it comes, or held at Frame Rate; only that one cooks.',
             index=Expr("0 if parent().par.Framerate == 'source' else 1"))
section('gate', 'The gate: the film weaves, a beat kicks it, a splice rolls it; linear light')
gate_top = glsl(comp, 'gate', [cadence], common + src('gate.glsl'),
                'The picture where the film sits in the gate (weave, kicks, splices), in linear light with Exposure.',
                fmt='rgba16float', uF=UF, uW=(par('Weave'), Expr(KICK), Expr(SPLICE), par('Exposure')))
section('night', 'Day for Night: the scene as the rods see it, blurred, its remaining edges sharpened')
night_src = glsl(comp, 'night_src', [gate_top], common + src('night_src.glsl'),
                 'The night color at half size: the scotopic luminance, bluish and dim; what is bright keeps its color '
                 '(alpha).', fmt='rgba16float', uF=UF)
night_src.par.outputresolution = 'half'
night_fine = mk(comp, blurTOP, 'night_fine', [night_src], 'The night color blurred, the fine detail gone.',
                type='gaussian', size=5)
night_wide = mk(comp, blurTOP, 'night_wide', [night_src], 'And blurred wider, with a triangle filter.',
                type='bartlette', size=7)
night = glsl(comp, 'night', [gate_top, night_src, night_fine, night_wide], common + src('night.glsl'),
             'The night scene: the edges left between the blurs sharpened, mixed against the day by Day for Night.',
             fmt='rgba16float', uF=UF, uN=(par('Night'),))
scene = mk(comp, switchTOP, 'scene', [gate_top, night], "The gate's picture, or the night scene when Day for Night is above 0.",
           index=Expr('1 if parent().par.Night > 0 else 0'))
section('halation', 'Halation: the light over white, spread as far as the base is thick')
glare = glsl(comp, 'glare', [scene], common + src('glare.glsl'),
             'The light over white at an eighth of the size.', fmt='rgba16float', uF=UF)
glare.par.outputresolution = 'eighth'
halo = mk(comp, blurTOP, 'halo', [glare], 'Spread as far as the base reflects it (wider for a smaller Gauge).',
          type='gaussian', size=Expr('{}[parent().par.Gauge.menuIndex]'.format(tuple(g[3] for g in GAUGES))))
section('film', "The film: each layer's density as grain, read a little soft and printed")
negative = glsl(comp, 'negative', [scene, halo], common + stock_table() + src('negative.glsl'),
                "The negative: each layer's density from its curve, made of grains drawn from the Poisson law (or one "
                'by one when big), as transmittance.',
                fmt='rgba16float', uF=UF, uS=(Expr('parent().par.Stock.menuIndex'), par('Halation'), 0, SWITCH))
printed = glsl(comp, 'print', [negative], common + stock_table() + src('print.glsl'),
               "The print (or the reversal): the scanner's softness, the print's curve, the dyes' impurities, the "
               "stock's tints, Contrast and Saturation; linear light.",
               fmt='rgba16float', uF=UF,
               uP=(Expr('parent().par.Stock.menuIndex'), par('Contrast'), par('Saturation'), SCAN_SIGMA))
section('screen', 'The screen: flicker, dirt and scratches, the cue mark, the red guard')
show = glsl(comp, 'show', [printed], lib_glsl(_ROOT, 'red_guard.glsl') + common + src('show.glsl'),
            'The picture: the flicker, dust and hairs, scratches, the cue mark, every pixel through the red guard, sRGB.',
            uF=UF, uD=(par('Flicker'), par('Dirt'), Expr("op('cue')[0] if parent().par.Moments else 0"), 0))
for g in (gate_top, night, negative, printed, show, night_src, glare):
    setpars(g, inputextenduv='hold')

finish_effect(comp, show, VERSION, page)
save_effect(comp, _HERE, _ROOT)
