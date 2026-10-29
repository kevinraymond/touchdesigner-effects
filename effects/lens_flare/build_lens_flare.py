"""Build Lens Flare. Run from a textport: __file__ = '/path/to/build_lens_flare.py'; exec(open(__file__).read())

The picture's bright lights throw the ghosts a real lens would, after Lee and Eisemann, "Practical Real-Time Lens-Flare
Rendering" (EGSR 2013). A ghost is light that reflects twice inside the lens, off one surface and back off another,
and reaches the sensor where it shouldn't. In paraxial (first-order) optics every step of a ray through the lens is a
2 x 2 matrix, so each ghost of a lens is a handful of numbers: where it lands as a multiple of the light's offset from
the middle, how big the iris's image is there, where the front element cuts it, how bright it is, and how much its two
surfaces reflect in each color. optics.py works them out from the lens's prescription (lenses.py: camera lenses from
expired patents) when the effect is built, into one table per lens; each frame the effect finds the picture's lights
and draws every ghost of every light, and each light's starburst (the iris's diffraction, Hullin et al. 2011).

dev/protos/lens_flare/offline.py tried it first on the clips (board #4733).

The network, left to right:
  picture    source -> look (the picture with the flare added in linear light) -> out
  lights     source -> bright (each pixel's light past Threshold, a quarter size) -> tiles (summed in 32 px tiles,
             eased; tiles_fb) -> lights (a compute shader: the brightest tiles gathered into up to Lights lights)
  lens       lens_heliar, lens_sonnar, lens_topogon, lens_phone (each lens's ghosts) -> ghost_table (the one Lens
             picks) -> ghost_chop -> ghost_tex (the table as a texture)
  starburst  aperture (the iris) -> dft_rows -> dft (its Fourier transform, squared) -> burst (summed over the spectrum)
  flare      ghost_mat on ghost_geo (an instance per light and ghost), burst_mat on burst_geo (one per light) ->
             render (cam looks at them; the shaders place everything themselves) -> flare (eased; flare_fb)
  audio      audio_in() -> counts -> steps -> flash_gate() -> kick; level -> level_now -> level_usual
"""
import os
import re

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# Lights: tiles of 32 x 32 pixels, TILES across and down (enough for 1280), eased over EASE s; tiles whose middles lie
# within MERGE (picture units: half diagonals) of a light's brightest tile join it; energies E become S ln(1 + E / S).
TILES, EASE, MERGE, MAX_LIGHTS, S = 40, 0.2, 0.15, 16, 0.001
# The flare drawn is eased over FLARE_EASE s (ease.glsl).
FLARE_EASE = 0.1
# The starburst: the iris's transform on N x N, ZOOM frequency steps a pixel at 550 nm, brightness to the power TONE.
N, ZOOM, TONE, DUST = 256, 1.0, 0.3, 0.5
# The ghosts' gain at Amount 1: a light's ghosts carry GAIN times its energy (a lens's share, normalized per coating, is
# under 1%; the clipped picture holds a light's brightness back by far more).
GAIN = 150.0
# Beats: the flare up by KICK x Beat Kick, falling over KICK_FALL s. Loudness: up by SWELL x Swell x how far the level,
# over SLOW s, is above its average over USUAL s.
KICK, KICK_FALL = 1.5, 0.4
SWELL, SLOW, USUAL = 2.0, 1.0, 4.0
COATING_LABELS = {'bare': 'Uncoated', 'single': 'Single Coated', 'multi': 'Multicoated'}
PERF = '1.4'           # GPU ms a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def shader(name):
    return src('common.glsl') + src(name)


def module(name):
    """A src/ Python file as a namespace (read fresh each build: TouchDesigner's Python would cache an import)."""
    ns = {'__name__': name}
    exec(compile(src(name + '.py'), name + '.py', 'exec'), ns)
    return ns


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


optics = module('optics')
LENSES = module('lenses')['LENSES']
COATINGS = optics['COATINGS']
COLUMNS = (['i', 'j'] + ['{}_{}'.format(q, ch) for q in ('c', 'rho', 'clipc', 'clipr', 'bright') for ch in 'rgb'] +
           ['refl_{}_{}'.format(k, ch) for k in COATINGS for ch in 'rgb'] + ['norm_' + k for k in COATINGS] +
           ['fnumber'])
# The vertex shader reads the table's rows by number: they must be these columns.
_ROWS = dict(re.findall(r'#define ROW_(\w+) (\d+)', src('ghost_vertex.glsl')))
for _row, _column in (('C', 'c_r'), ('RHO', 'rho_r'), ('CLIPC', 'clipc_r'), ('CLIPR', 'clipr_r'),
                      ('BRIGHT', 'bright_r'), ('REFL', 'refl_bare_r'), ('NORM', 'norm_bare'), ('FNUMBER', 'fnumber')):
    if int(_ROWS[_row]) != COLUMNS.index(_column):
        raise RuntimeError('ghost_vertex.glsl reads ROW_{} at {}, but the table has {} at {}'.format(
            _row, _ROWS[_row], _column, COLUMNS.index(_column)))


def ghost_rows(spec):
    """The lens's ghosts as the table's rows, at its own f-number, each coating normalized to the same total."""
    table = optics['ghosts'](spec)
    norms = [1.0 / optics['power'](table, k) for k in COATINGS]
    rows = []
    for g in table:
        rows.append([g['i'], g['j']] + g['c'] + g['rho'] + g['clip_c'] + g['clip_r'] + g['bright'] +
                    [x for k in COATINGS for x in g['refl'][k]] + norms + [spec['fnumber']])
    return rows


README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'lens_flare', 'Lens Flare',
    "Lens Flare {}: the picture's bright lights throw the ghosts a real lens would, worked out from the lens's "
    'design.'.format(VERSION),
    README, tags=('lens-flare', 'optics', 'light', 'audio-reactive'), audio=True, flashing=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.3.mp4'")   # the sun through branches: the one sample with a light

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Lens', 'Lens', [(k, v['label']) for k, v in LENSES.items()], 'heliar',
     "Which lens the flare comes from: real camera lenses from their patents. Each throws its own ghosts, in its own "
     'places and sizes.').startSection = True
menu(page, 'Coating', 'Coating', [(k, COATING_LABELS[k]) for k in COATINGS], 'single',
     "The lens's anti-reflection coating, which colors its ghosts. Uncoated lenses (before the 1940s) give pale, "
     'colorless ghosts, a single coating (from the 1940s) pale violet ones, a modern multicoating ghosts in deeper '
     'colors. Each is shown about as strong; real uncoated lenses flare far more.')
custom(page, 'Float', 'Aperture', 'Aperture', 8.0,
       'The f-number, 1.4-22. Stopped down (a bigger number) the ghosts get smaller, crisper and brighter; wide open '
       "they spread into veils. A lens can't open wider than its design: f/3.5 for the Heliar, f/1.5 the Sonnar, f/4.5 "
       'the Topogon, f/4 the phone camera.', 1.4, 22, True)
custom(page, 'Int', 'Blades', 'Blades', 6,
       "How many blades the iris has, 3-12. The ghosts take the iris's shape, and the starburst has that many "
       'spikes (twice as many for an odd number).', 3, 12, True).startSection = True
custom(page, 'Float', 'Roundness', 'Roundness', 0.15,
       "How rounded the iris's blades are, 0-1. At 1 the iris is a circle: round ghosts and no spikes.", 0, 1, True)
custom(page, 'Float', 'Angle', 'Blade Angle', 15.0, 'How far the iris is turned, in degrees.', 0, 360)
custom(page, 'Float', 'Amount', 'Amount', 1.0,
       'How strong the ghosts are, 0-4.', 0, 4, True).startSection = True
custom(page, 'Float', 'Starburst', 'Starburst', 1.0,
       "How strong each light's starburst is, 0-4: the spikes diffraction draws around a bright light.", 0, 4, True)
custom(page, 'Float', 'Burstsize', 'Starburst Size', 0.5,
       "How wide a starburst is, 0.05-1: at 1 as wide as half the picture's diagonal.", 0.05, 1, True)
custom(page, 'Float', 'Threshold', 'Threshold', 0.85,
       'How bright a part of the picture must be to count as a light, 0.5-0.99. Lower it for a picture without '
       'clipped highlights.', 0.5, 0.99, True).startSection = True
custom(page, 'Int', 'Lights', 'Lights', 6,
       'How many lights may flare at once, 1-16: the brightest ones. Fewer costs less.', 1, MAX_LIGHTS, True)
menu(page, 'Show', 'Show', (('picture', 'Picture and Flare'), ('flare', 'Flare Only')), 'picture',
     'The picture with its flare, or the flare alone over black, to add onto something else.').startSection = True
custom(page, 'Float', 'Kick', 'Beat Kick', 0.5,
       'On each beat on input 2 the flare flares up and settles, 0-1, as often as Flashing allows.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Swell', 'Swell', 0.5,
       'How much the music getting louder than usual strengthens the flare, 0-1. It follows the loudness over a '
       'second.', 0, 1, True)

# ---- Audio (input 2): the flare up on each beat, stronger with the loudness ----------------------------
section('audio', 'Audio (input 2): the flare flares up on each beat and grows with the loudness')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
flash = flash_gate(comp, steps)
mk(comp, triggerCHOP, 'kick', [flash], 'The flare up after a beat the gate let through, falling over {:g} s.'.format(
    KICK_FALL), attack=0, peak=1, decay=KICK_FALL, sustain=0, release=0)
level = mk(comp, selectCHOP, 'level', [audio], 'How loud the music is now.', channames='level')
level_now = mk(comp, filterCHOP, 'level_now', [level], 'The loudness smoothed over {:g} s.'.format(SLOW), width=SLOW)
mk(comp, filterCHOP, 'level_usual', [level_now], 'The usual loudness: its average over the last {:g} s.'.format(USUAL),
   type='box', width=USUAL)
WIRED = "op('audio')['source'].eval() > 0"
BOOST = ("(1 + {} * parent().par.Kick * op('kick')[0] + {} * parent().par.Swell * max(op('level_now')[0] - "
         "op('level_usual')[0], 0) if {} else 1)").format(KICK, SWELL, WIRED)

# ---- The lights -----------------------------------------------------------------------------------------
section('lights', "The lights: the picture's light past Threshold, summed in tiles, gathered into the brightest few",
        lane='lights')
empty = mk(comp, constantTOP, 'empty', comment='Nothing yet: what tiles_fb and flare_fb start from.', outputresolution='custom',
           resolutionw=1, resolutionh=1, format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
bright = glsl(comp, 'bright', [source], shader('bright.glsl'),
              "Each pixel's light past Threshold, a quarter size: its color times how far past, squared.",
              fmt='rgba16float', uBright=(par('Threshold'),))
setpars(bright, outputresolution='quarter')
tiles_fb = mk(comp, feedbackTOP, 'tiles_fb', [empty], "tiles' last frame.", top='tiles')
tiles = glsl(comp, 'tiles', [bright, tiles_fb], shader('tiles.glsl'),
             "The light summed in tiles of 32 x 32 pixels: each tile's energy, where it lies and its color, eased over "
             '{:g} s.'.format(EASE), res=(2 * TILES, TILES), fmt='rgba32float',
             uTiles=(TILES, Expr('1 - math.exp(-min(absTime.stepSeconds, 0.1) / {})'.format(EASE))))
lights = mk(comp, glslTOP, 'lights', [tiles],
            'The lights: the brightest tile and every tile near it, then the next, up to Lights; each one\'s place, '
            'energy, spread and color. A compute shader, one workgroup.', mode='compute', autodispatchsize=False,
            dispatchsizex=1, dispatchsizey=1, dispatchsizez=1, outputresolution='custom', resolutionw=MAX_LIGHTS,
            resolutionh=2, format='rgba32float')
docked(lights, '_compute', shader('lights.glsl'), 'The lights, a compute shader: 512 invocations sharing the tiles, '
       'each step added up in shared memory.')
uniforms(lights, uLights=(par('Lights'), MERGE, TILES, S))

# ---- The lens --------------------------------------------------------------------------------------------
section('lens', "The lens: its ghosts, worked out from its prescription when the effect was built", lane='lens')
tables = []
for key, spec in LENSES.items():
    t = mk(comp, tableDAT, 'lens_' + key,
           comment="{}'s ghosts, one row each (optics.py, from its patent's prescription at f/{:g}): which surfaces "
                   'reflect, then per color where it lands, how big, the front element\'s cut, how bright, how much '
                   'each coating reflects.'.format(spec['label'], spec['fnumber']))
    t.clear()
    t.appendRow(COLUMNS)
    for row in ghost_rows(spec):
        t.appendRow(['{:.7g}'.format(v) for v in row])
    tables.append(t)
table = mk(comp, switchDAT, 'ghost_table', tables, 'The ghosts of the lens Lens picks.',
           index=Expr('parent().par.Lens.menuIndex'))
chop = mk(comp, dattoCHOP, 'ghost_chop', comment='The ghost table as channels, one a column.', dat='ghost_table',
          output='chanpercol', firstrow='names', firstcolumn='values')
# Its row and column filters default to expressions of me.inputCell, which only exists while it cooks; the whole table
# goes through, so they are unused.
for p in (chop.par.rowexpr, chop.par.colexpr):
    p.expr = ''
    p.mode = ParMode.CONSTANT
ghost_tex = mk(comp, choptoTOP, 'ghost_tex', comment='The ghost table as a 32-bit texture: a row per column, a pixel '
               'per ghost.', chop='ghost_chop', dataformat='r')
setpars(ghost_tex, format='r32float')

# ---- The starburst ----------------------------------------------------------------------------------------
section('starburst', "The starburst: the iris's diffraction, summed over the spectrum; cooks only when the iris changes",
        lane='starburst')
IRIS = (par('Blades'), Expr('math.radians(parent().par.Angle)'), par('Roundness'), DUST)
aperture = glsl(comp, 'aperture', [], shader('aperture.glsl'), 'The iris, with specks of dust.', res=(N, N),
                fmt='r32float', uIris=IRIS)
dft_rows = glsl(comp, 'dft_rows', [aperture], src('dft_rows.glsl'), "The iris's Fourier transform along its rows.",
                res=(N, N), fmt='rgba32float')
dft = glsl(comp, 'dft', [dft_rows], src('dft.glsl'),
           "The transform along the columns, squared: the iris's diffraction at one wavelength.", res=(N, N),
           fmt='r32float')
burst = glsl(comp, 'burst', [dft], src('common.glsl') + lib_glsl(_ROOT, 'spectrum.glsl') + src('burst.glsl'),
             'The starburst: the diffraction summed over 24 wavelengths, each scaled by its length.', res=(N, N),
             fmt='rgba16float', uBurst=(ZOOM, TONE))
setpars(burst, inputfiltertype='linear')

# ---- The flare ---------------------------------------------------------------------------------------------
section('flare', 'The flare: every ghost of every light and their starbursts, added up', lane='flare')
RES = (Expr("op('source').width"), Expr("op('source').height"))
ghost_mat = mk(comp, glslMAT, 'ghost_mat', comment='A ghost: placed, sized and colored by its shaders, added onto '
               'what is drawn.', blending=True, srcblend='one', destblend='one', depthtest=False, depthwriting=False)
docked(ghost_mat, '_vertex', shader('ghost_vertex.glsl'), "A ghost's place, size and light, from the light and the "
       'ghost table.')
docked(ghost_mat, '_pixel', shader('ghost_pixel.glsl'), "A ghost's light at each pixel: the iris's shape cut by the "
       "front element's circle, per color.")
ghost_mat.seq.sampler.numBlocks = 2
setpars(ghost_mat, sampler0name='sLights', sampler0top='lights', sampler1name='sGhosts', sampler1top='ghost_tex')
uniforms(ghost_mat, uRes=RES + (Expr("op('ghost_tex').width"), par('Lights')),
         uLens=(par('Aperture'), Expr('parent().par.Coating.menuIndex'), Expr('{} * parent().par.Amount * '.format(GAIN) + BOOST)),
         uIris=IRIS)
burst_mat = mk(comp, glslMAT, 'burst_mat', comment='A starburst on its light, added onto what is drawn.',
               blending=True, srcblend='one', destblend='one', depthtest=False, depthwriting=False)
docked(burst_mat, '_vertex', src('burst_vertex.glsl'), "A starburst's square on its light, as bright as the light.")
docked(burst_mat, '_pixel', src('burst_pixel.glsl'), 'The starburst texture in the light\'s color.')
burst_mat.seq.sampler.numBlocks = 2
setpars(burst_mat, sampler0name='sLights', sampler0top='lights', sampler1name='sBurst', sampler1top='burst')
uniforms(burst_mat, uRes=RES, uBurst=(Expr('parent().par.Starburst * ' + BOOST), par('Burstsize')))


def instanced(name, mat, count, comment):
    geo = mk(comp, geometryCOMP, name, comment=comment, instancing=True, instancecountmode='manual',
             numinstances=count, material=mat)
    for o in list(geo.children):             # a new Geometry COMP holds a torus
        o.destroy()
    quad = mk(geo, rectangleSOP, 'quad', comment='One square, which the material moves and sizes for each instance.',
              sizex=1, sizey=1, texture='face', at=(0, 0))
    quad.render = quad.display = True
    return geo


instanced('ghost_geo', 'ghost_mat', Expr("parent().par.Lights * op('ghost_tex').width"),
          'A square for every ghost of every light (Lights x the lens\'s ghosts), placed by ghost_mat.')
instanced('burst_geo', 'burst_mat', par('Lights'), 'A square for each light\'s starburst, placed by burst_mat.')
cam = mk(comp, cameraCOMP, 'cam', comment='The Render TOP needs a camera; the shaders place everything themselves.',
         projection='ortho', tz=5)
# A new Camera COMP holds a File In POP (its own picture in the viewer); nothing here draws it.
for o in list(cam.children):
    o.destroy()
render = mk(comp, renderTOP, 'render', comment='The flare: every ghost and starburst, added up in linear light, at half '
            'size and not antialiased (the shaders soften every edge; 4x antialiasing at full size cost 7 ms).', camera='cam',
            geometry='ghost_geo burst_geo', lights='', bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=0, antialias='aa1',
            format='rgba16float', outputresolution='custom', resolutionw=Expr("max(1, op('source').width // 2)"),
            resolutionh=Expr("max(1, op('source').height // 2)"))

flare_fb = mk(comp, feedbackTOP, 'flare_fb', [empty], "flare's last frame.", top='flare')
flare = glsl(comp, 'flare', [render, flare_fb], src('ease.glsl'),
             'The flare eased over {:g} s, so ghosts whose lights wobble don\'t flicker.'.format(FLARE_EASE),
             fmt='rgba16float', uEase=(Expr('1 - math.exp(-min(absTime.stepSeconds, 0.1) / {})'.format(FLARE_EASE)),))

# ---- The picture -------------------------------------------------------------------------------------------
section('look', 'The picture with its flare', lane='picture')
look = glsl(comp, 'look', [source, flare], shader('look.glsl'),
            'The flare added to the picture in linear light, as a lens adds it (or over black: Show).',
            uLook=(Expr("1 if parent().par.Show == 'picture' else 0"),))

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
