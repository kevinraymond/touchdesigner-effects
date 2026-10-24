"""Build ASCII. Run from a textport: __file__ = '/path/to/build_ascii.py'; exec(open(__file__).read())

The picture as text: a grid of glyph cells. Edges found by a difference of Gaussians and a Sobel
filter (at half resolution) get the line glyph along them, | \\ - /; the rest of the picture gets a
brightness ramp of glyphs. Glyphs come from a system font drawn into an atlas at run time (Text
TOP; nothing font-related ships) or from the library's 5 x 7 bitmap font. Input 2 (optional) makes
it follow music: beats change glyphs, bars give a contrast pop through the flash gate, and
Fosfora's signal adds sections, builds and drops.
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
FONT = lib_module(_ROOT, 'font5x7')

# Glyph sets for the fill, each ordered by ink (lib/font5x7.py ramp()); digits and letters share the
# light end (. :) so dark areas read the same in every set and a set changes the brights.
SETS = (('symbols', 'Symbols', FONT['ramp']('.,:;+=*%#@')),
        ('digits', 'Digits', FONT['ramp']('.:1723469580')),
        ('letters', 'Letters', FONT['ramp']('.:ABCDEFGHIJKLMNOPQRSTUVWXYZ')))
EDGES = '|\\-/'   # the direction bins of edges.glsl, in order
CHARS = ''.join(dict.fromkeys(EDGES + ''.join(s for _, _, s in SETS)))
# The atlas: one slot per character, big enough for the largest Cell Size; each glyph drawn with its
# left edge SLOT_X and its baseline SLOT_Y from the slot's lower-left corner.
ATLAS_COLS, SLOT_W, SLOT_H, SLOT_X, SLOT_Y = 16, 48, 64, 8, 16
ATLAS_ROWS = -(-len(CHARS) // ATLAS_COLS)
CELL_MIN, CELL_MAX = 6, 48
ORANGE_BLUE, SOURCE, MONO = 'orangeblue', 'source', 'mono'

README = """ASCII {v}: the picture as text. touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/ascii.md

ASCII art draws a picture with nothing but text characters: characters with a lot of ink stand
in for bright patches and sparse ones for dim patches, so from a step back the text reads as the
picture. This effect does it live.

The picture becomes a grid of glyph cells. Where it has a clear edge, the cell gets the line
glyph that follows it ( | \\ - / ), in orange by default; everywhere else a glyph from a
brightness ramp, and cells below the black point stay empty.

USE
Drag ascii.tox into your network: it shows TouchDesigner's sample picture straight away. Wire
any TOP into input 1; the result is on output 1, at the input's size. Optionally wire audio or
beat channels into input 2 (below). Open Window shows it full size; Esc closes the window.

FONTS
System Font draws the glyphs with a font installed on your computer (Font Name; Courier New is on
Mac and Windows), rasterized at run time, so no font ships in this file. If the font is missing,
TouchDesigner substitutes Helvetica and shows a warning. Bitmap 5x7 is a pixel font drawn for this
library, the same on every computer; its cells snap to whole font pixels (9, 18, 27...).

AUDIO (input 2, optional)
Fosfora's signal is the best input: run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's
integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire
it into input 2. Then, with Fosfora Moments on: pops land on its downbeats, a new section moves
the picture to the next glyph set, a build fills in the darks and the outlines, and a drop makes
the next allowed flash reverse video (Fosfora's drop detection is experimental).
Any input: every beat moves a share of the cells to another glyph set of the same ink (Beat
Glyphs), every bar (or beat, Pop On) gives a contrast pop (Beat Pop), and loudness brings out more
outlines (Loudness). Raw audio (Audio File In, Audio Device In) gives beats from a simple kick
detector (experimental: it can add or miss beats) and a bar every 4 beats; TouchDesigner's
audioAnalysis gives beats from its kick or onset channels. Nothing wired: no beats, and the
effect still draws the picture.

FLASHING
The pops and the drop are flashes; they share one gate that follows the Flashing parameter: Off
never flashes, Calm (the default) at most once a second, Up to 3 per second is the WCAG 2.3.1
limit. Glyph swaps keep the ink, so they don't flash.

INSIDE
source -> prep (luminance, half size) -> blur_fine, blur_wide -> edges (difference of Gaussians,
Sobel direction) -> cells (one texel per cell: mean color, winning edge direction) -> render ->
out_top. avg, peak, stats_prev and stats set the automatic white point; atlas_glyphs and atlas
draw the system font; cell and grid size the cells. Input 2 goes through audio (lib audio_in);
moments_* turn its counts into pulses, flash_limit and flash gate the pops and drops, and pop_env,
drop_env and beat_env shape them.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new ascii.tox from
https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's
External .tox at a downloaded copy).
""".format(v=VERSION)


def shader(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [n for n, _ in items]
    p.menuLabels = [lb for _, lb in items]
    p.default = p.val = default
    return p


def glyph_tables():
    """The GLSL constants render.glsl's GLYPHS line stands for: glyph numbers are indices into CHARS
    (the atlas slot), BITMAP maps them to the 5 x 7 font."""
    idx = CHARS.index
    flat = [idx(c) for _, _, s in SETS for c in s]
    starts = [sum(len(s) for _, _, s in SETS[:i]) for i in range(len(SETS))]
    lines = [
        '// Glyph numbers index CHARS = {!r}, the atlas slots in order.'.format(CHARS),
        '#define ATLAS_COLS {}'.format(ATLAS_COLS), '#define ATLAS_ROWS {}'.format(ATLAS_ROWS),
        '#define SLOT_W {}'.format(SLOT_W), '#define SLOT_H {}'.format(SLOT_H),
        '#define SLOT_X {}'.format(SLOT_X), '#define SLOT_Y {}'.format(SLOT_Y),
        '#define SETS_N {}'.format(len(SETS)),
        'const int BITMAP[{}] = int[]({});'.format(len(CHARS), ', '.join(str(FONT['index'](c)) for c in CHARS)),
        'const int EDGE[4] = int[]({});   // | \\ - /'.format(', '.join(str(idx(c)) for c in EDGES)),
        'const int SETS[{}] = int[]({});'.format(len(flat), ', '.join(map(str, flat))),
        'const int SET_START[{}] = int[]({});'.format(len(SETS), ', '.join(map(str, starts))),
        'const int SET_LEN[{}] = int[]({});'.format(len(SETS), ', '.join(str(len(s)) for _, _, s in SETS)),
    ]
    for name, _, s in SETS:
        lines.append('// {}: {}'.format(name, s))
    return '\n'.join(lines) + '\n' + FONT['glsl_font']()


comp, page, source = new_effect(
    'ascii', 'ASCII', 'ASCII {}: the picture as text; glyphs follow its edges, beats change them.'.format(VERSION),
    README, tags=('ascii', 'text', 'glyphs', 'audio-reactive'), audio=True, flashing=True)
P = 'parent().par.'

# ---- Parameters -----------------------------------------------------------------------------------
font = menu(page, 'Font', 'Font', (('system', 'System Font'), ('bitmap', 'Bitmap 5x7')), 'system',
            'System Font: glyphs drawn with a font installed on this computer (Font Name), rasterized at '
            'run time. Bitmap 5x7: a pixel font drawn for this library, the same on every computer.')
font.startSection = True
custom(page, 'Str', 'Fontname', 'Font Name', 'Courier New',
       'The system font, by name; a monospaced one keeps glyphs centered. Courier New is on Mac and '
       'Windows; Menlo, Consolas and Andale Mono work too.').enableExpr = "me.par.Font == 'system'"
custom(page, 'Int', 'Cellsize', 'Cell Size', 18,
       'Height of a glyph cell in pixels; the width follows (about 0.55 of it). Bitmap 5x7 snaps to '
       'whole font pixels: 9, 18, 27...', CELL_MIN, CELL_MAX, True)
menu(page, 'Glyphs', 'Glyphs', [(n, lb) for n, lb, _ in SETS], 'symbols',
     'The glyphs for brightness: symbols ( . , : ; + = * % # @ ), digits or letters. Every set runs from '
     'light to heavy ink, so changing it keeps the picture.')
custom(page, 'Float', 'Edges', 'Edges', 0.5,
       'How readily outlines become line glyphs ( | \\ - / ) that follow them. 0: none, only the '
       'brightness ramp.', 0, 1, True)

color = menu(page, 'Color', 'Color', ((ORANGE_BLUE, 'Orange and Blue'), (SOURCE, 'Source'), (MONO, 'Mono')),
             ORANGE_BLUE, 'Orange and Blue: outlines orange, fill blue turning pale in the brights. Source: '
             "each glyph in its cell's color. Mono: every glyph in Ink. Brightness always follows the picture.")
color.startSection = True
ink = page.appendRGB('Ink', label='Ink')
for p, v in zip(ink, (1.0, 0.72, 0.42)):
    p.default = p.val = v
    p.normMin, p.normMax = 0, 1
    p.help = 'The glyph color when Color is Mono.'
    p.enableExpr = "me.par.Color == 'mono'"
custom(page, 'Float', 'Blackpoint', 'Black Point', 0.06,
       'Cells darker than this stay empty. Raise it to clear noise out of dark footage.', 0, 0.5, True)
custom(page, 'Float', 'Gamma', 'Gamma', 0.8,
       'Below 1 brings up the midtones (more, heavier glyphs in dim areas); above 1 pushes them down.',
       0.25, 3, True)
custom(page, 'Toggle', 'Autolevels', 'Auto Levels', True,
       'Stretch dim pictures so their brightest parts reach the heaviest glyphs. It eases over half a '
       'second, so a sudden highlight never makes the picture jump.')
custom(page, 'Float', 'Backdrop', 'Backdrop', 0.0,
       'How much of the picture, dimmed, shows behind the glyphs. 0: a dark ground.', 0, 1, True)

pop = custom(page, 'Float', 'Beatpop', 'Beat Pop', 0.5,
             'A contrast jump on every bar (or beat, Pop On) from input 2. It is a flash, so the '
             'Flashing parameter limits how often it comes; 0 turns it off. From raw audio, beats come '
             'from a simple kick detector (experimental: it can add or miss beats).', 0, 1, True)
pop.startSection = True
menu(page, 'Popon', 'Pop On', (('bars', 'Bars'), ('beats', 'Beats')), 'bars',
     'Pop on every bar (Fosfora\'s downbeats, else every 4 beats) or every beat. Beats can come faster '
     'than Flashing allows (120 BPM is two a second); Calm lets at most one a second through.'
     ).enableExpr = 'me.par.Beatpop > 0'
custom(page, 'Float', 'Beatglyphs', 'Beat Glyphs', 0.3,
       'Share of the cells that switch to another glyph set of the same ink on every beat, settling back '
       'over 0.3 s (no flash). 1 swaps the whole set.', 0, 1, True)
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much the music\'s loudness brings out more outlines.', 0, 1, True)
custom(page, 'Toggle', 'Fosfora', 'Fosfora Moments', True,
       "Extra moments from Fosfora's signal on input 2 (github.com/kevinraymond/fosfora): a new section "
       'switches the glyph set, a build fills in the darks and outlines, a drop gives one reverse-video '
       'flash (drop detection is experimental in Fosfora). Other inputs have none of these.')

# ---- Cell geometry ---------------------------------------------------------------------------------
BITMAP = P + "Font == 'bitmap'"
SCALE = 'max(1, round({}Cellsize / 9))'.format(P)
WIDTH = 'max(4, round({}Cellsize * 0.55))'.format(P)
cell = mk(comp, constantCHOP, 'cell', -400, 350, comment='Cell width and height, font size, bitmap font scale.')
grid = mk(comp, constantCHOP, 'grid', -200, 350, comment='Columns and rows of cells, and the grid origin '
          '(centered on the picture).')
for chop, chans in ((cell, (('w', '6 * {s} if {b} else {w}'.format(s=SCALE, b=BITMAP, w=WIDTH)),
                            ('h', '9 * {s} if {b} else {p}Cellsize.eval()'.format(s=SCALE, b=BITMAP, p=P)),
                            ('fs', 'max(4, round(min({p}Cellsize / 1.12, {w} / 0.6)))'.format(p=P, w=WIDTH)),
                            ('s', SCALE))),
                    (grid, (('cols', "math.ceil(op('source').width / op('cell')['w'].eval())"),
                            ('rows', "math.ceil(op('source').height / op('cell')['h'].eval())"),
                            ('ox', "(op('source').width - me.par.const0value.eval() * op('cell')['w'].eval()) // 2"),
                            ('oy', "(op('source').height - me.par.const1value.eval() * op('cell')['h'].eval()) // 2")))):
    chop.seq.const.numBlocks = len(chans)
    for i, (name, expr) in enumerate(chans):
        getattr(chop.par, 'const{}name'.format(i)).val = name
        getattr(chop.par, 'const{}value'.format(i)).expr = expr
CELL = (Expr("op('cell')['w']"), Expr("op('cell')['h']"), Expr("op('grid')['ox']"), Expr("op('grid')['oy']"))

# ---- Edges, at half resolution ------------------------------------------------------------------------
prep = glsl(comp, 'prep', -400, 0, [source], shader('prep.glsl'), 'Luminance at half size, for the edge pass.',
            fmt='mono16float')
prep.par.outputresolution = 'half'
blur_fine = mk(comp, blurTOP, 'blur_fine', -200, 100, [prep], 'The luminance blurred a little (difference of '
               'Gaussians, narrow).', size=2, extend='hold')
blur_wide = mk(comp, blurTOP, 'blur_wide', -200, -100, [prep], 'The luminance blurred more (difference of '
               'Gaussians, wide).', size=5, extend='hold')
edges = glsl(comp, 'edges', 0, 0, [blur_fine, blur_wide], shader('edges.glsl'),
             'Edges and their direction (difference of Gaussians, Sobel), at half size.', fmt='rg8fixed',
             uThresh=Expr('0.008 * 2 ** ((0.5 - {}Edges) * 3)'.format(P)))
edges.par.inputextenduv = 'hold'
cells = glsl(comp, 'cells', 200, 0, [source, edges], shader('cells.glsl'),
             'One texel per cell: its mean color and winning edge direction.', fmt='rgba32float',
             res=(1, 1), uCell=CELL)
cells.par.resolutionw.expr = "int(op('grid')['cols'])"
cells.par.resolutionh.expr = "int(op('grid')['rows'])"

# ---- Automatic levels --------------------------------------------------------------------------------
avg = mk(comp, analyzeTOP, 'avg', 400, 250, [cells], 'Mean cell color (automatic levels).',
         op='average', analyzechannel='independent', format='rgba32float')
peak = mk(comp, analyzeTOP, 'peak', 400, 150, [cells], 'Brightest cell (automatic levels).',
          op='maximum', analyzechannel='luminance', format='rgba32float')
prev = mk(comp, feedbackTOP, 'stats_prev', 400, 350, [avg], "The white point's previous value.", top='stats')
stats = glsl(comp, 'stats', 600, 250, [avg, peak, prev], shader('stats.glsl'),
             'Automatic white point, eased over time.', res=(1, 1), fmt='rgba32float',
             uEase=(Expr('absTime.stepSeconds'), 0.5))

# ---- The system font's atlas --------------------------------------------------------------------------
table = mk(comp, tableDAT, 'atlas_glyphs', 200, 500, comment='Where atlas draws each glyph: x is its left edge, '
           'y its baseline, one slot per glyph.')
table.clear()
table.appendRow(['x', 'y', 'text'])
for i, ch in enumerate(CHARS):
    table.appendRow([i % ATLAS_COLS * SLOT_W + SLOT_X, (ATLAS_ROWS - 1 - i // ATLAS_COLS) * SLOT_H + SLOT_Y, ch])
atlas = mk(comp, textTOP, 'atlas', 400, 500, comment='The glyphs, drawn with the system font at the cell size.',
           text='', specdat='atlas_glyphs', font=Expr(P + 'Fontname'), typeface='Bold', fontsizexunit='pixels',
           fontsizex=Expr("op('cell')['fs']"), keepfontratio=True, outputresolution='custom',
           resolutionw=ATLAS_COLS * SLOT_W, resolutionh=ATLAS_ROWS * SLOT_H)
if hasattr(atlas.par, 'legacyparsing'):
    atlas.par.legacyparsing = False

# ---- Audio: counts become pulses; every flash goes through the gate ----------------------------------------
audio = audio_in(comp, _ROOT, x=-400, y=-350)
counts = (('pop', "'bar_count' if {}Popon == 'bars' else 'beat_count'".format(P), 'The count the contrast pop '
           'follows: bars or beats (Pop On).'),
          ('drop', 'drop_count', "Fosfora's drop count."),
          ('beat', 'beat_count', 'The beat count: glyphs change on every beat.'))
picks = [mk(comp, selectCHOP, 'moments_' + name, -200, -350 - 100 * i, [audio], text,
            channames=Expr(chan) if 'Popon' in chan else chan, renamefrom='*', renameto=name)
         for i, (name, chan, text) in enumerate(counts)]
moments = mk(comp, mergeCHOP, 'moments', 0, -450, picks, 'The three counts.')
lagged = mk(comp, lagCHOP, 'moments_lag', 200, -500, [moments], 'The counts, lagged a little.',
            lag1=0.15, lag2=0.15, lagunit='seconds')
new = mk(comp, mathCHOP, 'moments_new', 400, -450, [moments, lagged], 'Near 1 just after a count steps up.',
         chopop='sub')
gains = mk(comp, constantCHOP, 'moments_on', 400, -600, comment='Which pulses count: the pop while Beat Pop is '
           'above 0, the drop while Fosfora Moments is on, every beat.')
gains.seq.const.numBlocks = 3
setpars(gains, const0name='pop', const0value=Expr('1 if {}Beatpop > 0 else 0'.format(P)),
        const1name='drop', const1value=Expr('1 if {}Fosfora else 0'.format(P)), const2name='beat', const2value=1)
picked = mk(comp, mathCHOP, 'moments_pick', 600, -450, [new, gains], 'Pulses that count.', chopop='mul')
pulses = mk(comp, triggerCHOP, 'moments_pulse', 800, -450, [picked], 'A clean 0/1 pulse per new count.',
            threshup=0.5, attack=0, peak=1, decay=0, sustain=1, release=0)
flashes = mk(comp, selectCHOP, 'moments_flash', 1000, -400, [pulses], 'The pulses that flash: pops and drops.',
             channames='pop drop')
either = mk(comp, mathCHOP, 'moments_any', 1200, -400, [flashes], 'A pop or a drop: one flash either way.',
            chanop='max')
flash = flash_gate(comp, either, 1400, -400)
pop_env = mk(comp, triggerCHOP, 'pop_env', 1800, -400, [flash], "The flash's shape: up at once, down over "
             '0.4 s.', attack=0, peak=1, peaklen=0.05, decay=0.4, dshape='easeout', sustain=0)
drop_pulse = mk(comp, selectCHOP, 'drop_pulse', 1000, -550, [pulses], 'A new drop.', channames='drop')
drop_env = mk(comp, triggerCHOP, 'drop_env', 1200, -550, [drop_pulse], 'Near a drop, a flash is reverse video.',
              attack=0, peak=1, peaklen=0.6, decay=0.2, sustain=0)
beat_pulse = mk(comp, selectCHOP, 'beat_pulse', 1000, -700, [pulses], 'A new beat.', channames='beat')
beat_env = mk(comp, triggerCHOP, 'beat_env', 1200, -700, [beat_pulse], 'Glyphs changed by a beat settle back '
              'over 0.3 s.', attack=0, peak=1, peaklen=0.05, decay=0.3, dshape='linear', sustain=0)
build = mk(comp, selectCHOP, 'build', 200, -800, [audio], "Fosfora's build, 0..1.", channames='build')
build_lag = mk(comp, lagCHOP, 'build_lag', 400, -800, [build], 'The build, easing out after a drop.',
               lag1=0.3, lag2=1.5, lagunit='seconds')
level = mk(comp, selectCHOP, 'level', 200, -900, [audio], 'Loudness, 0..1.', channames='level')
level_lag = mk(comp, lagCHOP, 'level_lag', 400, -900, [level], 'Loudness, smoothed (up in 0.4 s, down in 1 s).',
               lag1=0.4, lag2=1.0, lagunit='seconds')

# ---- Render --------------------------------------------------------------------------------------------
render = glsl(
    comp, 'render', 600, 0, [cells, atlas, stats], shader('render.glsl').replace('//@GLYPHS', glyph_tables()),
    'A glyph in every cell: lines along edges, a brightness ramp elsewhere, colored.', fmt='rgba8fixed',
    res=(1, 1),
    uCell=CELL,
    uFont=(Expr('1 if {} else 0'.format(BITMAP)), Expr("op('cell')['s'] if {} else op('cell')['fs']".format(BITMAP))),
    uTone=(Expr(P + 'Blackpoint'), Expr(P + 'Gamma'), Expr(P + 'Autolevels'), Expr(P + 'Backdrop')),
    uEdge=(Expr('0.09 * 2 ** ((0.5 - {}Edges) * 2.5)'.format(P)), 0.35, Expr('1 if {}Edges > 0 else 0'.format(P)),
           Expr(P + 'Loudness')),
    uLook=(Expr(P + 'Color.menuIndex'), Expr(P + 'Inkr'), Expr(P + 'Inkg'), Expr(P + 'Inkb')),
    uGlyphs=(Expr("{p}Glyphs.menuIndex + (op('audio')['section_count'] if {p}Fosfora else 0)".format(p=P)),
             Expr("op('audio')['beat_count']"), Expr("op('beat_env')[0] * {}Beatglyphs".format(P))),
    uAudio=(Expr("op('pop_env')[0] * {}Beatpop".format(P)), Expr("op('pop_env')[0] * op('drop_env')[0]"),
            Expr("op('build_lag')[0] * {}Fosfora".format(P)), Expr("op('level_lag')[0]")))
render.par.resolutionw.expr = "op('source').width"
render.par.resolutionh.expr = "op('source').height"

finish_effect(comp, render, VERSION, page)
save_effect(comp, _HERE, _ROOT)
