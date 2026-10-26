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
    g = mk(host, glslTOP, name, (), comment, at=(x, y))
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
movies = [mk(r, moviefileinTOP, 'in_' + n, comment='Test input: ' + f,
             file=Expr("app.samplesFolder + '/{}'".format(f)), at=(-1600, -150 * i)) for i, (n, f) in enumerate(INPUTS)]
pick = mk(r, switchTOP, 'pick', movies, comment='Which test input; shoot_round1.py steps it.', index=0, at=(-1400, 0))
frame = mk(r, fitTOP, 'frame', [pick], comment='Every input filled to 1280 x 720.',
           outputresolution='custom', resolutionw=W, resolutionh=H, at=(-1200, 0))
menu(frame.par.fit, 'outside', 'fill')

# ---- shared cells and automatic levels --------------------------------------------------------
SCALE = 2
F_CELL = (6 * SCALE, 9 * SCALE)
f_cells = glsl(r, 'f_cells', [frame], shader('cells.glsl'), 'Mean color per 12 x 18 cell (C, D, E).',
               res=grid(F_CELL), fmt='rgba16float', uCell=F_CELL, at=(-1000, -500))
f_avg = mk(r, analyzeTOP, 'f_avg', [f_cells], comment='Mean cell luminance (auto levels).', at=(-800, -450))
menu(f_avg.par.op, 'average')
f_max = mk(r, analyzeTOP, 'f_max', [f_cells], comment='Brightest cell (auto levels).', at=(-800, -600))
menu(f_max.par.op, 'maximum')
f_stats = glsl(r, 'f_stats', [f_avg, f_max], shader('stats.glsl'), 'Automatic white point.',
               res=(1, 1), fmt='rgba16float', at=(-600, -500))
STATS = [f_stats]

# ---- A: Text TOP atlas -----------------------------------------------------------------------
A_RAMP, A_CELL, A_SIZE = ' .:-=+*#%@', (10, 20), 16
# A Specification DAT ignores the Text TOP's alignment: each x, y is the glyph's left edge on its
# baseline (2025.33230, probe_atlas.py). Monospaced fonts advance about 0.6 em, so center on that.
tab = mk(r, tableDAT, 'a_glyphs', comment='Where a_atlas draws each glyph: one slot per glyph.', at=(-1000, 400))
tab.clear()
tab.appendRow(['x', 'y', 'text'])
for i, ch in enumerate(A_RAMP):
    tab.appendRow([round(i * A_CELL[0] + (A_CELL[0] - 0.6 * A_SIZE) / 2, 2), round(A_CELL[1] * 0.25), ch])
atlas = mk(r, textTOP, 'a_atlas', comment='The glyph atlas, drawn with a system font at cell size.',
           text='', specdat='a_glyphs', font='Courier New', typeface='Bold', fontsizexunit='pixels',
           fontsizex=A_SIZE, keepfontratio=True, outputresolution='custom',
           resolutionw=A_CELL[0] * len(A_RAMP), resolutionh=A_CELL[1], at=(-800, 400))
a_cells = glsl(r, 'a_cells', [frame], shader('cells.glsl'), 'Mean color and luminance per cell.',
               res=grid(A_CELL), fmt='rgba16float', uCell=A_CELL, at=(-800, 200))
a = glsl(r, 'a_render', [a_cells, atlas] + STATS, shader('a_render.glsl'), 'A: atlas glyphs, one ink.',
         res=(W, H), uCell=A_CELL, uLevels=(0.04, 0.8, 1.0), uAuto=1, uInk=ORANGE, uPaper=(0.03, 0.02, 0.01),
         uCount=len(A_RAMP), at=(-600, 200))
a.par.inputfiltertype = 'nearest'

# ---- B: edges --------------------------------------------------------------------------------
B_CELL = (10, 18)
mono = mk(r, monochromeTOP, 'b_mono', [frame], comment='Luminance.', at=(-1000, -200))
blur1 = mk(r, blurTOP, 'b_blur1', [mono], comment='Narrow Gaussian.', size=4, at=(-800, -150))
blur2 = mk(r, blurTOP, 'b_blur2', [mono], comment='Wide Gaussian.', size=10, at=(-800, -300))
edge = glsl(r, 'b_edge', [blur1, blur2], shader('b_edge.glsl'), 'DoG edges + Sobel direction.',
            fmt='rgba16float', uTau=1.0, uEdge=0.008, at=(-600, -200))
b_cells = glsl(r, 'b_cells', [edge], shader('b_cells.glsl'), 'Per-cell direction vote.',
               res=grid(B_CELL), fmt='rgba16float', uCell=B_CELL, at=(-400, -200))
b = glsl(r, 'b_render', [b_cells] + STATS, shader('b_render.glsl'), 'B: stroke glyphs.', res=(W, H),
         uCell=B_CELL, uLevels=(0.04, 0.8, 1.0), uAuto=1, uMinEdge=0.09, uWidth=0.9, uEdgeInk=ORANGE, uFillInk=BLUE,
         uPaper=PAPER, at=(-200, -200))

# ---- C: source color, bitmap font ------------------------------------------------------------
C_RAMP = ramp(' .-:;+=o*%$#@')
c = glsl(r, 'c_render', [f_cells] + STATS, shader('c_render.glsl', glsl_ints('RAMP', C_RAMP)),
         'C: bitmap glyphs in source color.', res=(W, H), uScale=SCALE, uLevels=(0.03, 0.85, 0.9), uAuto=1, uPaperMix=0.18, at=(-600, -500))

# ---- D: rain ---------------------------------------------------------------------------------
D_RAMP = ramp(' .:-=+*#%@')
D_RAIN = '0123456789ABCDEFHKLMNPRTXZ<>*+=$%#@'
d0 = glsl(r, 'd_render', [f_cells] + STATS,
          shader('d_render.glsl', glsl_ints('RAMP', D_RAMP) + glsl_ints('RAIN', D_RAIN)),
          'D: rain over a dim ramp.', res=(W, H), uScale=SCALE, uTime=Expr('absTime.seconds'),
          uLevels=(0.03, 0.85, 1.0), uAuto=1, uHead=(1.0, 0.86, 0.62), uTrail=ORANGE, uBack=(0.22, 0.42, 0.85), at=(-600, -700))
d_blur = mk(r, blurTOP, 'd_blur', [d0], comment='Glow.', size=8, at=(-400, -800))
d = glsl(r, 'd_glow', [d0, d_blur], shader('d_glow.glsl'), 'D: add the glow.', uGlow=0.7, at=(-200, -700))

# ---- E: audio --------------------------------------------------------------------------------
au = mk(r, audiofileinCHOP, 'e_audio', comment='The sample WAV, looping (not played out).',
        file=Expr("app.samplesFolder + '/Audio/SonarBlackie666.wav'"), at=(-1000, -1000))
low = mk(r, audiofilterCHOP, 'e_low', [au], comment='Kick band.', filter='lowpass',
         units='frequency', cutofffrequency=150, at=(-850, -1000))
rms = mk(r, analyzeCHOP, 'e_rms', [low], comment='Level this frame.', function='rmspower', at=(-700, -1000))
slow = mk(r, lagCHOP, 'e_slow', [rms], comment='Recent average level.', lag1=0.8, lag2=0.8, at=(-700, -1150))
ratio = mk(r, mathCHOP, 'e_ratio', [rms, slow], comment='Level over its recent average.', at=(-550, -1050))
menu(ratio.par.chopop, 'div')
trig = mk(r, triggerCHOP, 'e_trig', [ratio], comment='Beat envelope; re-trigger delay = Calm interval.',
          threshold=True, threshup=1.35, retrigger=FLASH_INTERVAL['calm'], attack=0, decay=0.45, sustain=0, peak=1, at=(-400, -1050))
count = mk(r, countCHOP, 'e_count', [trig], comment='Beats so far: picks the glyph set.', at=(-250, -1050))
SETS = [ramp(' .:-=+*%#@'), ramp(' 0123456789'), ramp(' ABCDEFGHIJKLMNOPQRSTUVWXYZ')]
starts = [sum(len(s) for s in SETS[:i]) for i in range(3)]
e_extra = (glsl_ints('SETS', ''.join(SETS)) + 'const int SET_START[3] = int[]({});\n'.format(', '.join(map(str, starts)))
           + 'const int SET_LEN[3] = int[]({});\n'.format(', '.join(str(len(s)) for s in SETS)))
e = glsl(r, 'e_render', [f_cells] + STATS, shader('e_render.glsl', e_extra), 'E: beat-driven glyph sets.',
         res=(W, H), uScale=SCALE, uLevels=(0.03, 0.85, 1.0), uAuto=1, uBeat=Expr("op('e_trig')[0]"),
         uSet=Expr("op('e_count')[0]"), uLow=BLUE, uHigh=ORANGE, uPaper=PAPER, at=(-600, -900))
# Dev only: E held at the peak of a beat on the letter set, to show what a beat does in a still.
e_peak = glsl(r, 'e_peak', [f_cells] + STATS, shader('e_render.glsl', e_extra), 'E at a beat peak.',
              res=(W, H), uScale=SCALE, uLevels=(0.03, 0.85, 1.0), uAuto=1, uBeat=1, uSet=2, uLow=BLUE,
              uHigh=ORANGE, uPaper=PAPER, at=(-600, -1200))

r.allowCooking = False
print('built', r.path, [o.name for o in (a, b, c, d, e)])
print('ramps C', repr(''.join(C_RAMP)), 'D', repr(''.join(D_RAMP)), 'E', [''.join(s) for s in SETS])
