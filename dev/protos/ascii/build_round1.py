"""DEV ONLY. ASCII round-1 prototypes: builds every variant into TDLIB_PARENT/r1 (replacing it)
and leaves it not cooking; shoot_round1.py captures them.

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/build_round1.py

Variants (all 1280 x 720, read from one shared input picker):
  a_atlas   Text TOP atlas (a system font, rasterized at run time), luminance ramp, one ink color
  b_edges   DoG + Sobel edge glyphs | \\ - / drawn as strokes in GLSL, fill ramp under them
  c_color   bitmap font defined in GLSL, the source's color per cell
  d_rain    falling glyph trails over the picture as a dim ramp, with glow
  e_beat    bitmap font; beats from an Audio File In CHOP swap glyph sets and lift contrast
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_HERE, 'font5x7.py')).read(), 'font5x7.py', 'exec'), globals())

W, H = 1280, 720
ORANGE, BLUE, PAPER = (1.0, 0.58, 0.16), (0.30, 0.56, 1.0), (0.02, 0.025, 0.04)
INPUTS = [('tree', 'Map/Nature/Movie.3.mp4'), ('grass', 'Map/Nature/Movie.2.mp4'),
          ('butterfly', 'Map/Butterfly5.tif'), ('count', 'Map/Count.mov'), ('jellybeans', 'Map/Jellybeans.1.jpg')]


def menu(par, *keys):
    for k in keys:
        for n in par.menuNames:
            if k in n:
                par.val = n
                return
    raise RuntimeError('{} has none of {}: {}'.format(par.name, keys, list(par.menuNames)))


def uniforms(g, values):
    g.seq.vec.numBlocks = max(len(values), 1)
    for i, (name, v) in enumerate(values.items()):
        getattr(g.par, 'vec{}name'.format(i)).val = name
        for axis, x in zip('xyzw', v if isinstance(v, (tuple, list)) else (v,)):
            p = getattr(g.par, 'vec{}value{}'.format(i, axis))
            if isinstance(x, Expr):
                p.expr = x.text
            else:
                p.val = x


def shader(name, extra=''):
    text = open(os.path.join(_HERE, name)).read()
    text = text.replace('//@LEVELS', open(os.path.join(_HERE, 'levels.glsl')).read())
    return text.replace('//@FONT', glsl_font() + extra)


def glsl(host, name, x, y, inputs, pixel, comment, res=None, fmt=None, **u):
    g = mk(host, glslTOP, name, x, y, (), comment)
    # mk() wires through inputConnectors[i]; a new GLSL TOP has 3 and they don't grow within one
    # Python call (2025.33230, probe_inputs.py), so a 4th input fails. setInputs() takes them all.
    g.setInputs(list(inputs))
    docked(g, '_pixel', pixel, comment)
    if res:
        g.par.outputresolution = 'custom'
        g.par.resolutionw, g.par.resolutionh = res
    if fmt:
        g.par.format = fmt
    g.par.inputextenduv = 'hold'
    uniforms(g, u)
    return g


def grid(cell):
    return (-(-W // int(cell[0])), -(-H // int(cell[1])))


host = op(TDLIB_PARENT)
if host.op('r1'):
    host.op('r1').destroy()
r = host.create(baseCOMP, 'r1')
r.comment = 'DEV ONLY: ASCII round-1 prototypes (dev/protos/ascii/build_round1.py).'

# ---- shared input picker -------------------------------------------------------------------
movies = [mk(r, moviefileinTOP, 'in_' + n, -1600, -150 * i, comment='Test input: ' + f,
             file=Expr("app.samplesFolder + '/{}'".format(f))) for i, (n, f) in enumerate(INPUTS)]
pick = mk(r, switchTOP, 'pick', -1400, 0, movies, comment='Which test input; shoot_round1.py steps it.', index=0)
frame = mk(r, fitTOP, 'frame', -1200, 0, [pick], comment='Every input filled to 1280 x 720.',
           outputresolution='custom', resolutionw=W, resolutionh=H)
menu(frame.par.fit, 'outside', 'fill')

# ---- shared cells and automatic levels --------------------------------------------------------
SCALE = 2
F_CELL = (6 * SCALE, 9 * SCALE)
f_cells = glsl(r, 'f_cells', -1000, -500, [frame], shader('cells.glsl'), 'Mean color per 12 x 18 cell (C, D, E).',
               res=grid(F_CELL), fmt='rgba16float', uCell=F_CELL)
f_avg = mk(r, analyzeTOP, 'f_avg', -800, -450, [f_cells], comment='Mean cell luminance (auto levels).')
menu(f_avg.par.op, 'average')
f_max = mk(r, analyzeTOP, 'f_max', -800, -600, [f_cells], comment='Brightest cell (auto levels).')
menu(f_max.par.op, 'maximum')
f_stats = glsl(r, 'f_stats', -600, -500, [f_avg, f_max], shader('stats.glsl'), 'Automatic white point.',
               res=(1, 1), fmt='rgba16float')
STATS = [f_stats]

# ---- A: Text TOP atlas -----------------------------------------------------------------------
A_RAMP, A_CELL, A_SIZE = ' .:-=+*#%@', (10, 20), 16
# A Specification DAT ignores the Text TOP's alignment: each x, y is the glyph's left edge on its
# baseline (2025.33230, probe_atlas.py). Monospaced fonts advance about 0.6 em, so center on that.
tab = mk(r, tableDAT, 'a_glyphs', -1000, 400, comment='Where a_atlas draws each glyph: one slot per glyph.')
tab.clear()
tab.appendRow(['x', 'y', 'text'])
for i, ch in enumerate(A_RAMP):
    tab.appendRow([round(i * A_CELL[0] + (A_CELL[0] - 0.6 * A_SIZE) / 2, 2), round(A_CELL[1] * 0.25), ch])
atlas = mk(r, textTOP, 'a_atlas', -800, 400, comment='The glyph atlas, drawn with a system font at cell size.',
           text='', specdat='a_glyphs', font='Courier New', typeface='Bold', fontsizexunit='pixels',
           fontsizex=A_SIZE, keepfontratio=True, outputresolution='custom',
           resolutionw=A_CELL[0] * len(A_RAMP), resolutionh=A_CELL[1])
a_cells = glsl(r, 'a_cells', -800, 200, [frame], shader('cells.glsl'), 'Mean color and luminance per cell.',
               res=grid(A_CELL), fmt='rgba16float', uCell=A_CELL)
a = glsl(r, 'a_render', -600, 200, [a_cells, atlas] + STATS, shader('a_render.glsl'), 'A: atlas glyphs, one ink.',
         res=(W, H), uCell=A_CELL, uLevels=(0.04, 0.8, 1.0), uAuto=1, uInk=ORANGE, uPaper=(0.03, 0.02, 0.01),
         uCount=len(A_RAMP))
a.par.inputfiltertype = 'nearest'

# ---- B: edges --------------------------------------------------------------------------------
B_CELL = (10, 18)
mono = mk(r, monochromeTOP, 'b_mono', -1000, -200, [frame], comment='Luminance.')
blur1 = mk(r, blurTOP, 'b_blur1', -800, -150, [mono], comment='Narrow Gaussian.', size=4)
blur2 = mk(r, blurTOP, 'b_blur2', -800, -300, [mono], comment='Wide Gaussian.', size=10)
edge = glsl(r, 'b_edge', -600, -200, [blur1, blur2], shader('b_edge.glsl'), 'DoG edges + Sobel direction.',
            fmt='rgba16float', uTau=1.0, uEdge=0.008)
b_cells = glsl(r, 'b_cells', -400, -200, [edge], shader('b_cells.glsl'), 'Per-cell direction vote.',
               res=grid(B_CELL), fmt='rgba16float', uCell=B_CELL)
b = glsl(r, 'b_render', -200, -200, [b_cells] + STATS, shader('b_render.glsl'), 'B: stroke glyphs.', res=(W, H),
         uCell=B_CELL, uLevels=(0.04, 0.8, 1.0), uAuto=1, uMinEdge=0.09, uWidth=0.9, uEdgeInk=ORANGE, uFillInk=BLUE,
         uPaper=PAPER)

# ---- C: source color, bitmap font ------------------------------------------------------------
C_RAMP = ramp(' .-:;+=o*%$#@')
c = glsl(r, 'c_render', -600, -500, [f_cells] + STATS, shader('c_render.glsl', glsl_ints('RAMP', C_RAMP)),
         'C: bitmap glyphs in source color.', res=(W, H), uScale=SCALE, uLevels=(0.03, 0.85, 0.9), uAuto=1, uPaperMix=0.18)

# ---- D: rain ---------------------------------------------------------------------------------
D_RAMP = ramp(' .:-=+*#%@')
D_RAIN = '0123456789ABCDEFHKLMNPRTXZ<>*+=$%#@'
d0 = glsl(r, 'd_render', -600, -700, [f_cells] + STATS,
          shader('d_render.glsl', glsl_ints('RAMP', D_RAMP) + glsl_ints('RAIN', D_RAIN)),
          'D: rain over a dim ramp.', res=(W, H), uScale=SCALE, uTime=Expr('absTime.seconds'),
          uLevels=(0.03, 0.85, 1.0), uAuto=1, uHead=(1.0, 0.86, 0.62), uTrail=ORANGE, uBack=(0.22, 0.42, 0.85))
d_blur = mk(r, blurTOP, 'd_blur', -400, -800, [d0], comment='Glow.', size=8)
d = glsl(r, 'd_glow', -200, -700, [d0, d_blur], shader('d_glow.glsl'), 'D: add the glow.', uGlow=0.7)

# ---- E: audio --------------------------------------------------------------------------------
au = mk(r, audiofileinCHOP, 'e_audio', -1000, -1000, comment='The sample WAV, looping (not played out).',
        file=Expr("app.samplesFolder + '/Audio/SonarBlackie666.wav'"))
low = mk(r, audiofilterCHOP, 'e_low', -850, -1000, [au], comment='Kick band.', filter='lowpass',
         units='frequency', cutofffrequency=150)
rms = mk(r, analyzeCHOP, 'e_rms', -700, -1000, [low], comment='Level this frame.', function='rmspower')
slow = mk(r, lagCHOP, 'e_slow', -700, -1150, [rms], comment='Recent average level.', lag1=0.8, lag2=0.8)
ratio = mk(r, mathCHOP, 'e_ratio', -550, -1050, [rms, slow], comment='Level over its recent average.')
menu(ratio.par.chopop, 'div')
trig = mk(r, triggerCHOP, 'e_trig', -400, -1050, [ratio], comment='Beat envelope; re-trigger delay = Calm interval.',
          threshold=True, threshup=1.35, retrigger=FLASH_INTERVAL['calm'], attack=0, decay=0.45, sustain=0, peak=1)
count = mk(r, countCHOP, 'e_count', -250, -1050, [trig], comment='Beats so far: picks the glyph set.')
SETS = [ramp(' .:-=+*%#@'), ramp(' 0123456789'), ramp(' ABCDEFGHIJKLMNOPQRSTUVWXYZ')]
starts = [sum(len(s) for s in SETS[:i]) for i in range(3)]
e_extra = (glsl_ints('SETS', ''.join(SETS)) + 'const int SET_START[3] = int[]({});\n'.format(', '.join(map(str, starts)))
           + 'const int SET_LEN[3] = int[]({});\n'.format(', '.join(str(len(s)) for s in SETS)))
e = glsl(r, 'e_render', -600, -900, [f_cells] + STATS, shader('e_render.glsl', e_extra), 'E: beat-driven glyph sets.',
         res=(W, H), uScale=SCALE, uLevels=(0.03, 0.85, 1.0), uAuto=1, uBeat=Expr("op('e_trig')[0]"),
         uSet=Expr("op('e_count')[0]"), uLow=BLUE, uHigh=ORANGE, uPaper=PAPER)
# Dev only: E held at the peak of a beat on the letter set, to show what a beat does in a still.
e_peak = glsl(r, 'e_peak', -600, -1200, [f_cells] + STATS, shader('e_render.glsl', e_extra), 'E at a beat peak.',
              res=(W, H), uScale=SCALE, uLevels=(0.03, 0.85, 1.0), uAuto=1, uBeat=1, uSet=2, uLow=BLUE,
              uHigh=ORANGE, uPaper=PAPER)

r.allowCooking = False
print('built', r.path, [o.name for o in (a, b, c, d, e)])
print('ramps C', repr(''.join(C_RAMP)), 'D', repr(''.join(D_RAMP)), 'E', [''.join(s) for s in SETS])
