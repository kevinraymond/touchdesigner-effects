"""Build the Showreel bundle. Run from a textport: __file__ = '/path/to/build_showreel.py'; exec(open(__file__).read())

Every effect in effects/ (each effects/<n>/<n>.tox as built, embedded unchanged) behind one View
menu: Grid (the input and every effect side by side, named), Cycle (one at a time, moving on every
few bars) or one effect by name. It finds the effects itself, so a new effect needs only a rebuild
of this; until then tests/check_tox.py fails (embeds_all in the manifest), as it does when an
effect is rebuilt and this isn't.

The network, left to right:
  input      the standard shell: source (input 1, or the sample movie), in2_audio and in3_top, whose
             depth (lib depth_in: input 3, else input 1's brightness) feeds the effects that take one
  effects    every effect's COMP, fed the inputs it takes, its output through a Null TOP (fx_<name>)
  views      grid.glsl tiles the input and every effect with their names; view (a Switch TOP,
             which cooks only the input it shows) picks Grid, Cycle's effect or the one chosen;
             label.glsl names the effect showing
  cycle      audio_in() -> audio and a clock -> cycle (a Script CHOP, src/cycle.py): how many
             times Cycle has moved on, on the bars or the clock, never within 2 s of the last
             move; the view reads it only while View is Cycle, so none of it cooks otherwise
"""
import glob
import hashlib
import math
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# Shown while nothing is wired: the dancer, the library's own footage (CC BY 4.0, 5 s, 1.3 MB), and
# her depth map (Depth Anything 3 Base, 0.9 MB) for the effects that take input 3, carried in the
# component's Virtual File System and read by a path relative to it, so they play wherever the .tox
# is loaded. TouchDesigner's sample movies barely move (Blob Track and Datamosh need motion) and
# have no depth. The only media inside any of the library's .tox files; no sound.
CLIP, CLIP_DEPTH = 'dancer.mp4', 'dancer_depth.mp4'
SAMPLE = "'vfs:' + parent().path + ':{}'".format(CLIP)
# Both clips are 81 frames at 16 fps. They show the frame the clock picks rather than play on their
# own, so they stay in step whichever of them cooks: a movie playing by itself starts when something
# first pulls it, and the depth only cooks while an effect that uses it is showing.
CLIP_SECONDS = 81 / 16
IN_STEP = dict(playmode='specify', indexunit='seconds', index=Expr('absTime.seconds % {:g}'.format(CLIP_SECONDS)))
GRID_W, GRID_H = 1280, 720
# Cycle's bar while input 2 gives none, and the least time between two of its moves (src/cycle.py
# keeps them; these are for the help and the README).
SECONDS_A_BAR, MIN_GAP = 2.0, 2.0


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


# Every built effect, in name order: effects/<n>/<n>.tox with its manifest beside it.
EFFECTS = []
for d in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', ''))):
    name = os.path.basename(os.path.dirname(d))
    tox = os.path.join(d, name + '.tox')
    if os.path.isfile(tox) and os.path.isfile(os.path.join(d, name + '.json')):
        EFFECTS.append((name, tox))
if not EFFECTS:
    raise RuntimeError('no built effects in {}'.format(os.path.join(_ROOT, 'effects')))

comp, page, source = new_effect(
    'showreel', 'Showreel',
    'Showreel {}: every effect in the library ({}) in one component; View picks a grid of them all, '
    'a cycle through them, or one.'.format(VERSION, ', '.join(n for n, _ in EFFECTS)),
    'Filled in once the effects are loaded.', tags=('showreel', 'bundle'), audio=True, flashing=True,
    sample=SAMPLE, depth=True)
comp.vfs.addFile(os.path.join(_HERE, 'src', CLIP))
comp.vfs.addFile(os.path.join(_HERE, 'src', CLIP_DEPTH))
comp.op('sample').comment = 'Shown until a TOP is wired into input 1: the dancer clip inside this component.'
setpars(comp.op('sample'), **IN_STEP)
# Input 3's stand-in: the dancer's depth while she is showing, else black: no depth, so each effect
# falls back to its own way of working without (Particles: what moves).
guess = mk(comp, constantTOP, 'no_depth', -1000, -1000, comment="Black: no depth, when input 1 is wired but input 3 is not.",
           outputresolution='custom', resolutionw=320, resolutionh=180, colorr=0, colorg=0, colorb=0, alpha=1)
sample_depth = mk(comp, moviefileinTOP, 'sample_depth', -1000, -1150,
                  comment="The dancer's depth map inside this component, in step with the dancer clip.",
                  file=Expr("'vfs:' + parent().path + ':{}'".format(CLIP_DEPTH)), **IN_STEP)
stand_in = mk(comp, switchTOP, 'depth_stand_in', -800, -1050, [guess, sample_depth],
              "The dancer's depth while the dancer clip shows (input 1 unwired), else no depth (black).",
              index=Expr('0 if parent().inputConnectors[0].connections else 1'))
depth = depth_in(comp, stand_in, x=-600, y=-850)
depth.comment = 'Input 3 (depth or mask) when it is wired, else the stand-in: for the effects that take one.'
audio = audio_in(comp, _ROOT, -800, -550)
audio.comment = "Input 2's bars, for Cycle (read only while View is Cycle, so it cooks only then)."
clock = mk(comp, constantCHOP, 'clock', -800, -700, comment='The time, so cycle cooks every frame while used.',
           const0name='seconds', const0value=Expr('absTime.seconds'))
cycle = mk(comp, scriptCHOP, 'cycle', -600, -600, [audio, clock],
           'How many times Cycle has moved on: every Every bars, or seconds with no bars; never within '
           '{:g} s of the last move (src/cycle.py).'.format(MIN_GAP))
docked(cycle, '_callbacks', src('cycle.py'), "Cycle's callbacks: when to move on to the next effect.")

# ---- The effects --------------------------------------------------------------------------------
fxs, embeds = [], {}
for i, (name, path) in enumerate(EFFECTS):
    if comp.op(name) is not None or comp.op('fx_' + name) is not None:
        raise RuntimeError('effect name {} collides with an operator of the showreel'.format(name))
    fx = comp.loadTox(path)
    if fx.name != name:
        raise RuntimeError('{} loaded as {}, not {}'.format(path, fx.name, name))
    fx.nodeX, fx.nodeY = -250, 300 - 450 * i
    fx.inputConnectors[0].connect(source)
    if len(fx.inputConnectors) > 1:
        fx.inputConnectors[1].connect(comp.op('in2_audio'))
    if len(fx.inputConnectors) > 2:
        fx.inputConnectors[2].connect(depth)
    # Its node viewer would cook it whenever this network is open on screen.
    fx.viewer = False
    if hasattr(fx.par, 'Flashing'):
        fx.par.Flashing.expr = 'parent().par.Flashing'
    with open(path, 'rb') as f:
        embeds[name] = hashlib.sha256(f.read()).hexdigest()
    null = mk(comp, nullTOP, 'fx_' + name, 150, fx.nodeY, comment="{}'s picture, for grid and view.".format(name))
    null.inputConnectors[0].connect(fx.outputConnectors[0])
    fxs.append((fx, null, fx.customPages[0].name))

# ---- Names in the library's font: INPUT, then each effect's title -------------------------------
font = lib_module(_ROOT, 'font5x7')
names = ['INPUT'] + [title.upper() for _, _, title in fxs]
for n in names:
    for ch in n:
        font['index'](ch)  # a character the font lacks fails here, not as a blank in the picture
at = [sum(len(n) for n in names[:k]) for k in range(len(names))]
names_head = ('#define N_TILES {}\n'.format(len(names)) + font['glsl_font']()
              + font['glsl_ints']('NAMES', ''.join(names))
              + 'const int NAME_AT[{0}] = int[]({1});\nconst int NAME_LEN[{0}] = int[]({2});\n'.format(
                  len(names), ', '.join(map(str, at)), ', '.join(str(len(n)) for n in names))
              + src('names.glsl'))
cols = math.ceil(math.sqrt(len(names)))
rows = math.ceil(len(names) / cols)
# tile(t, uv) and tileRes(t) read input t through constant indices (a sampler can't be picked
# by a variable).
tiles_head = '#define COLS {}\n#define ROWS {}\n'.format(cols, rows)
tiles_head += 'vec2 tileRes(int t) {\n' + ''.join(
    '    if (t == {0}) return uTD2DInfos[{0}].res.zw;\n'.format(k) for k in range(len(names))) + '    return vec2(1.0);\n}\n'
tiles_head += 'vec4 tile(int t, vec2 uv) {\n' + ''.join(
    '    if (t == {0}) return texture(sTD2DInputs[{0}], uv);\n'.format(k) for k in range(len(names))) + '    return vec4(0.0);\n}\n'

# ---- Views --------------------------------------------------------------------------------------
view_menu = custom(page, 'Menu', 'View', 'View', None,
                   'What to show. Grid: the input and every effect side by side, each named (every effect '
                   'runs). Cycle: one effect at a time, moving on every Every bars of input 2 (a bar is {:g} s '
                   'while no bars arrive), never within {:g} s of the last move. Or one effect by name. Only '
                   'the effects showing run.'.format(SECONDS_A_BAR, MIN_GAP))
view_menu.menuNames = ['grid', 'cycle'] + [fx.name for fx, _, _ in fxs]
view_menu.menuLabels = ['Grid', 'Cycle'] + [title for _, _, title in fxs]
view_menu.default = view_menu.val = 'grid'
every = custom(page, 'Int', 'Every', 'Every', 4,
               "Cycle's pace: how many bars of input 2's music each effect shows for.", 1, 64, True)
every.enableExpr = "me.par.View == 'cycle'"
custom(page, 'Toggle', 'Labels', 'Labels', True, "Name each effect on the picture, in the library's pixel font.")

grid = glsl(comp, 'grid', 450, 300, [source] + [null for _, null, _ in fxs], names_head + tiles_head + src('grid.glsl'),
            'Grid: the input and every effect side by side ({} x {}), each named.'.format(cols, rows),
            res=(GRID_W, GRID_H), uLook=(par('Labels'),))
# Grid is input 0; effect k (from 1) is View's item k + 1; Cycle steps through them, reading the
# cycle CHOP (and so cooking it and the audio) only while it is chosen.
VIEW_INDEX = ("0 if parent().par.View == 'grid' else parent().par.View.menuIndex - 1 if parent().par.View != 'cycle' "
              "else 1 + int(op('cycle')['step'].eval()) % {}").format(len(fxs))
view = mk(comp, switchTOP, 'view', 650, 0, [grid] + [null for _, null, _ in fxs],
          'What View shows: Grid, the effect Cycle has reached, or the one chosen (only that input cooks).',
          index=Expr(VIEW_INDEX))
label = glsl(comp, 'label', 850, 0, [view], names_head + src('label.glsl'),
             'Names the effect showing, bottom left (Labels); Grid names its own cells.',
             uLabel=(Expr("op('view').par.index.eval()"), par('Labels')))
finish_effect(comp, label, VERSION, page)
comp.op('out_top').nodeX = 1050
comp.op('window').nodeX = 1050
comp.op('README').text = src('readme.txt').format(v=VERSION, effects='\n'.join(
    '  {} ({})'.format(title, fx.name) for fx, _, title in fxs))

path, manifest = save_tox(comp, _HERE, comp.name, {
    'version': VERSION,
    'sources_sha256': digest(_ROOT, component_sources(_ROOT, _HERE)),
    'embeds': embeds,
    'embeds_all': True,
})
print('built', comp.path, 'version', VERSION, 'in', app.build, 'with', ', '.join(sorted(embeds)), '->', path)
