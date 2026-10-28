"""Build Words. Run from a textport: __file__ = '/path/to/build_words.py'; exec(open(__file__).read())

The picture rebuilt from words. Each frame a compute shader keeps every word where it was, carried along with the
picture's motion, lets the ones that ran into an older word or out of their region fade out, and fills what is free
with new ones the way Wordle does (Feinberg 2008): one word at a time, at the biggest size it fits, at the best free
spot, never on a word already placed. Cloud packs the words into the subject, the most frequent biggest and deepest
inside it (ShapeWordle, Wang et al. 2020); Portrait fills the whole picture with the text in order, each word as big
as the picture's detail allows there. One Text TOP draws every distinct word of the text once into an atlas, with a
font on this computer, and instanced quads draw the words from it.

dev/protos/words/offline.py and video.py tried the layouts first on the clips (board #4673).

The network, left to right:
  picture  source -> render (every word, drawn by word_mat on word_geo) -> look (over the picture at Backdrop) -> out
  text     text (the built-in text) or the DAT Text names -> text_in -> words (the distinct words and where the atlas
           draws them; measure gives their sizes) -> atlas (the Text TOP) -> ink (where each word's ink lies); words
           -> vocab_cols -> vocab_chop -> vocab (a texture); order (the order the layout takes them) -> order_chop ->
           order_tex
  grid     source -> cells (8 x 8 pixels a cell, bigger past 1280: the subject, detail and brightness) -> seed (the subject's
           outline) -> jfa (each cell's nearest outline cell)
  layout   layout (a compute shader: every word's slot) <- layout_fb (its last frame)
  motion   optical_flow() and flow_speed(): the picture's motion, which the words ride
  depth    input 3 (depth_in()) -> near -> find (what stands in front) -> subject
  audio    audio_in()
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
SLOTS = 1024          # words at most (layout.glsl's workgroup: an invocation a word)
LEVELS = 8            # sizes from Smallest to Largest
HOLD = 0.15           # seconds a word may stay out of its region or on an older word before it fades out
REGION_EASE = 0.15    # seconds the subject on the grid eases over
SLEW = 1.15           # Lines' lines move at most this many lines' heights (Smallest) a second: a line's spacing
# A cell is 8 x 8 pixels, bigger for a picture past 1280 on a side: layout.glsl holds at most 160 x 160 cells.
CELL_PX = 'max(8, max(op("source").width, op("source").height) / 160)'
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right, nearer
# than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale), as in Fluid.
STAND_OUT, FAR = 0.1, (0.5, 0.05)
# A beat: every word up to PUMP_SIZE bigger and PUMP_BRIGHT brighter at Beat Pump 1, falling over PUMP_FALL s. Loudness:
# brighter by SWELL x Swell x how far the level, over SLOW s, is above its average over USUAL s (as Lens Flare).
PUMP_SIZE, PUMP_BRIGHT, PUMP_FALL = 0.25, 0.5, 0.35
SWELL, SLOW, USUAL = 1.0, 1.0, 4.0
SHAPES = (('depth', 'Depth (Input 3)'), ('mask', 'Mask (Input 3)'), ('brightness', 'Brightness'),
          ('movement', 'Movement'))
PERF = '2.4 ms (Cloud), 1.8 ms (Portrait) and 3 ms (Lines)'   # GPU a frame at 1280 x 720 on the M2 Pro (dev/perf.py, median of three runs)


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def unfiltered(o):
    """A Select DAT's or DAT to CHOP's row and column filters default to expressions of me.inputCell, which exists
    only while it cooks: evaluated anywhere else they fail. Everything here goes through by name, so they are unused."""
    for p in (o.par.rowexpr, o.par.colexpr):
        p.expr = ''
        p.mode = ParMode.CONSTANT
    return o


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


README = src('readme.txt').format(v=VERSION, perf=PERF)
comp, page, source = new_effect(
    'words', 'Words',
    'Words {}: the picture rebuilt from words, packed into its subject or filling it, each word riding its '
    'motion.'.format(VERSION),
    README, tags=('words', 'typography', 'word-cloud', 'audio-reactive'), audio=True, depth=True, flashing=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.1.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Layout', 'Layout', (('cloud', 'Cloud'), ('portrait', 'Portrait'), ('lines', 'Lines')), 'cloud',
     'How the words make the picture. Cloud: a word cloud in the shape of the subject (Shape From), the most frequent '
     'words biggest and deepest inside it. Portrait: the whole picture, the text in its order, big words where the '
     'picture is plain and small ones on its features. Lines: the text in small lines that run around the subject\'s '
     'outline, ring after ring, as in micrography (without a subject, across the picture like a page).'
     ).startSection = True
custom(page, 'DAT', 'Text', 'Text', './text',
       'The DAT holding the text (a Text DAT, or a table read cell by cell). Words are what lies between spaces. The '
       'built-in one, ./text inside this component, is the start of Walt Whitman\'s "I Sing the Body Electric". Up to '
       '1024 distinct words and the first 4096 words of the text are used.')
menu(page, 'Case', 'Case', (('written', 'As Written'), ('upper', 'Upper'), ('lower', 'Lower')), 'written',
     'The words as the text writes them, or all in capitals, or all in small letters.')
custom(page, 'Toggle', 'Skipcommon', 'Skip Common Words', True,
       'Cloud: leave out common English words (the, and, of...), as a word cloud does, so the words that matter come '
       'biggest. Portrait reads every word.').enableExpr = "me.par.Layout == 'cloud'"
custom(page, 'Str', 'Font', 'Font', 'Arial',
       'The font, by name: any installed on this computer. Arial is on Mac and Windows. A missing font falls back '
       'to TouchDesigner\'s own.')
custom(page, 'Toggle', 'Bold', 'Bold', True, 'The bold face of the font.')
custom(page, 'Float', 'Largest', 'Largest', 0.2,
       'Cloud and Portrait: how tall the biggest words may be, as a share of the picture\'s height (a line of text, '
       'letters and the space above and below them), 0.05-0.5.', 0.05, 0.5, True).enableExpr = "me.par.Layout != 'lines'"
comp.par.Largest.startSection = True
custom(page, 'Float', 'Smallest', 'Smallest', 18.0,
       'How tall the smallest words are, in pixels (a line of text), 8-64; Lines writes every word at this size. Smaller '
       'fills more closely.', 8, 64, True)
custom(page, 'Float', 'Detail', 'Detail', 0.5,
       'Portrait: how strongly the picture\'s detail makes words smaller, 0-1. At 1 even faint texture takes small '
       'words; at 0 only the strongest edges do.', 0, 1, True).enableExpr = "me.par.Layout == 'portrait'"
menu(page, 'Shapefrom', 'Shape From', SHAPES, 'depth',
     'Cloud and Lines: where the subject is. Depth: what stands in front of its surroundings in the depth map on input 3 '
     '(floors and walls drop out). Mask: what is inside the mask on input 3 (white inside). Brightness: the bright '
     'parts of the picture. Movement: what moves. With nothing on input 3, Depth and Mask take the bright '
     'parts.').startSection = True
comp.par.Shapefrom.enableExpr = "me.par.Layout != 'portrait'"
custom(page, 'Float', 'Sense', 'Sensitivity', 0.5,
       'Cloud and Lines: how easily a part counts as the subject: farther depth, a grayer mask, dimmer brightness or '
       'slower movement counts as well.', 0, 1, True).enableExpr = "me.par.Layout != 'portrait'"
menu(page, 'Depthtype', 'Depth Type',
     (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
      ('meters', 'Distance in Meters (Kinect Azure)')), 'nearness',
     'What input 3 holds. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance 0-1: the RealSense '
     'and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters: the '
     'Kinect Azure TOP, scaled by Max Distance.').enableExpr = "me.par.Shapefrom in ('depth', 'mask')"
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Shapefrom in ('depth', 'mask') and me.par.Depthtype == 'meters'"
custom(page, 'Float', 'Spread', 'Spread', 16.0,
       'Cloud: how far past the subject\'s edge the words may go, in pixels, 0-80.', 0, 80,
       True).enableExpr = "me.par.Layout == 'cloud'"
custom(page, 'Float', 'Follow', 'Follow', 1.0,
       'Cloud: how much the words ride the subject\'s movement, 0-1. At 0 they stay put and the subject moves under '
       'them. Portrait\'s words stay put; Lines\' follow their lines.', 0, 1, True).enableExpr = "me.par.Layout == 'cloud'"
comp.par.Follow.startSection = True
custom(page, 'Float', 'Fade', 'Fade', 0.4,
       'How long a word takes to appear or to go, in seconds, 0.1-2.', 0.1, 2, True)
custom(page, 'Float', 'Fill', 'Fill Speed', 600.0,
       'How many new words may appear each second, 30-1200, filling the space words leave.', 30, 1200, True)
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Clear every word and lay the picture out anew.')
custom(page, 'Float', 'Pump', 'Beat Pump', 0.5,
       'On each beat on input 2 every word swells and brightens, then settles, 0-1, as often as Flashing allows.', 0, 1,
       True).startSection = True
custom(page, 'Float', 'Swell', 'Swell', 0.5,
       'How much the music getting louder than usual brightens the words, 0-1. It follows the loudness over a second.',
       0, 1, True)
menu(page, 'Color', 'Color', (('picture', 'Picture'), ('word', 'Word'), ('white', 'White')), 'picture',
     'Picture: each letter the color of the picture under it. Word: each word one color, the picture\'s across it. '
     'White: white words.').startSection = True
custom(page, 'Float', 'Lift', 'Lift', 0.5,
       'How much the dark colors are brightened, 0-1, so words on a dark part of the picture still read. White stays '
       'white. In Cloud black words also lift toward gray, so a dark subject shows.', 0, 1, True)
custom(page, 'Float', 'Backdrop', 'Backdrop', 0.15,
       'How much of the picture shows behind the words, 0-1. At 0 the words are on black.', 0, 1, True)

# ---- The text: its words, an atlas of them, their ink and order -----------------------------------
section('text', 'The text: every distinct word drawn once into an atlas, and the order the layout takes them',
        lane='text')
text = mk(comp, textDAT, 'text', comment='The built-in text: the start of Walt Whitman\'s "I Sing the Body Electric" '
          '(1855; this text from Leaves of Grass, Project Gutenberg #1322). Text points here by default.')
text.text = src('text.txt')
text_in = unfiltered(mk(comp, selectDAT, 'text_in', comment='The DAT Text names.', dat=Expr('parent().par.Text.eval()')))
measure = mk(comp, textTOP, 'measure', comment='Measures the words at 100 pixels for words; nothing draws it.',
             text='', font=par('Font'), typeface=Expr("'Bold' if parent().par.Bold else 'Regular'"),
             fontsizexunit='pixels', fontsizex=100, outputresolution='custom', resolutionw=8, resolutionh=8)
words = mk(comp, scriptDAT, 'words', [text_in],
           'Every distinct word of the text once: where atlas draws it, its size, how often it comes, its rank.')
docked(words, '_callbacks', src('words.py'), 'Splits the text into words, measures them and packs the atlas '
       '(src/words.py).')
spec = unfiltered(mk(comp, selectDAT, 'atlas_spec', [words], 'What atlas draws: each word and where.',
                    extractcols='bynames', colnames='text x y'))
atlas = mk(comp, textTOP, 'atlas', comment='Every distinct word, drawn once with the font at the size words picked.',
           text='', specdat='atlas_spec', font=par('Font'), typeface=Expr("'Bold' if parent().par.Bold else 'Regular'"),
           fontsizexunit='pixels', fontsizex=Expr("float(op('words')[1, 'fpx'].val) if op('words')[1, 'fpx'] is not None else 64"),
           outputresolution='custom', resolutionw=1280, resolutionh=1280)
if hasattr(atlas.par, 'legacyparsing'):
    atlas.par.legacyparsing = False
cols = unfiltered(mk(comp, selectDAT, 'vocab_cols', [words], 'The words\' numbers.', extractcols='bynames',
                    colnames='x y w asc desc count rank fpx'))
vchop = mk(comp, dattoCHOP, 'vocab_chop', comment='The numbers as channels, one a column.', dat='vocab_cols',
           output='chanpercol', firstrow='names', firstcolumn='values')
unfiltered(vchop)
vocab = mk(comp, choptoTOP, 'vocab', comment='The words as a 32-bit texture: a row per number, a pixel per word.',
           chop='vocab_chop', dataformat='r')
setpars(vocab, format='r32float')
ink = mk(comp, glslTOP, 'ink', [atlas, vocab],
         "Where each word's ink lies in the atlas: a compute shader, a workgroup a word.", mode='compute',
         autodispatchsize=False, dispatchsizex=SLOTS, dispatchsizey=1, dispatchsizez=1, outputresolution='custom',
         resolutionw=SLOTS, resolutionh=1, format='rgba32float')
docked(ink, '_compute', src('ink.glsl'), "Each word's ink box in the atlas, found by its workgroup.")
order = mk(comp, scriptDAT, 'order', [text_in],
           'The words in the order the layout takes them: by rank for Cloud, as written for Portrait.')
docked(order, '_callbacks', src('words.py'), 'The same script as words; as order it lists the words in the order '
       'the layout takes them.')
ochop = mk(comp, dattoCHOP, 'order_chop', comment='The order as four channels of 1024.', dat='order',
           output='chanpercol', firstrow='names', firstcolumn='values')
unfiltered(ochop)
order_tex = mk(comp, choptoTOP, 'order_tex', comment='The order as a 32-bit texture, 1024 x 4: a word index a pixel.',
               chop='order_chop', dataformat='r')
setpars(order_tex, format='r32float')

# ---- Depth or a mask (input 3) --------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): where the subject is, for Cloud')
depth = depth_in(comp)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black: no reading).', fmt='rgba16float',
            uNear=(Expr("parent().par.Depthtype.menuIndex"), par('Maxdist')))
setpars(near, outputresolution='quarter')
find = glsl(comp, 'find', [near], lib_glsl(_ROOT, 'depth_find.glsl'),
            'In the depth: what stands in front of what lies left and right of it, nearer than a limit (Sensitivity).',
            fmt='rgba16float',
            uFind=(0, STAND_OUT, Expr('{0} * ({1} / {0}) ** parent().par.Sense'.format(FAR[0], FAR[1]))))
subject = mk(comp, switchTOP, 'subject', [find, near],
             'The subject on input 3: what stands out for Depth (find), the mask for Mask (near).',
             index=Expr("1 if parent().par.Shapefrom == 'mask' else 0"))

# ---- The picture's motion ------------------------------------------------------------------------------
section('motion', "The picture's motion, which the words ride", lane='motion')
start = mk(comp, constantTOP, 'start', comment='Nothing yet: what the Feedback TOPs start from.',
           outputresolution='custom', resolutionw=SLOTS, resolutionh=4, format='rgba32float', colorr=0, colorg=0,
           colorb=0, alpha=0)
mo = optical_flow(comp, _ROOT, source, levels=(8,))
pace, motion = flow_speed(comp, _ROOT, mo, start)
still = mk(comp, constantTOP, 'still', comment='No motion, for when nothing needs it: the optical flow then rests.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float', colorr=0, colorg=0, colorb=0,
           alpha=1)
moving = mk(comp, switchTOP, 'moving', [motion, still],
            "The picture's motion while Cloud's words ride it (Follow) or the subject is what moves (Shape From "
            'Movement), else nothing, so Portrait and Lines leave the flow resting.',
            index=Expr("0 if (parent().par.Layout == 'cloud' and parent().par.Follow > 0) or "
                       "parent().par.Shapefrom == 'movement' else 1"))

# ---- The grid ---------------------------------------------------------------------------------------
section('grid', 'The grid: the picture in cells of 8 x 8 pixels, the subject and its distance field', lane='grid')
SHAPE = Expr("parent().par.Shapefrom.menuIndex if parent().par.Shapefrom.eval() in ('brightness', 'movement') or "
             "parent().inputConnectors[2].connections else 2")
cells = glsl(comp, 'cells', [source, subject, moving], src('cells.glsl'),
             'Per cell of 8 x 8 pixels: how much of it is the subject, how much detail, how bright.', fmt='rgba32float',
             uShape=(SHAPE, par('Sense')))
setpars(cells, outputresolution='custom', resolutionw=Expr('max(1, round(op("source").width / {}))'.format(CELL_PX)),
        resolutionh=Expr('max(1, round(op("source").height / {}))'.format(CELL_PX)))
region_fb = mk(comp, feedbackTOP, 'region_fb', [start], "region's last frame.", top='region')
region = glsl(comp, 'region', [cells, region_fb], src('region.glsl'),
              'The subject steadied: smoothed over its neighbors and eased over {:g} s, so its edge doesn\'t '
              'flicker.'.format(REGION_EASE), fmt='rgba32float',
              uEase=(Expr('1 - math.exp(-min(absTime.stepSeconds, 0.1) / {})'.format(REGION_EASE)),))
seed = glsl(comp, 'seed', [region], src('seed.glsl'), "The subject's outline: cells beside a cell on its other side.",
            fmt='rgba16float')
jfa = glsl(comp, 'jfa', [seed], src('jfa.glsl'),
           "Each cell's nearest outline cell, by jump flooding: 8 passes, the step halving from 128 cells.",
           fmt='rgba16float')
setpars(jfa, npasses=8)
field_fb = mk(comp, feedbackTOP, 'field_fb', [start], "field's last frame.", top='field')
field = glsl(comp, 'field', [jfa, region, field_fb], src('field.glsl'),
             "The subject's signed distance field (cells, negative inside), smoothed: Cloud fills it deepest first, "
             "Lines' lines are its level sets, which move at most a line's spacing a second.", fmt='rgba32float',
             uSlew=(Expr('{} * parent().par.Smallest / {} * min(absTime.stepSeconds, 0.1)'.format(SLEW, CELL_PX)),))
rings = glsl(comp, 'rings', [field], src('rings.glsl'),
             "Lines' lines ready to read: the slowed field and its slope per cell, read filtered.", fmt='rgba16float')

# ---- The layout -------------------------------------------------------------------------------------
section('layout', 'The layout: every word kept, carried, retired and placed anew, a compute shader', lane='layout')
fb = mk(comp, feedbackTOP, 'layout_fb', [start], "layout's last frame.", top='layout')
layout = mk(comp, glslTOP, 'layout', [fb, region, field],
            'Every word\'s slot: kept where it was, carried by the motion, faded out when it runs into an older word '
            'or out of its region, and new words placed into what is free. One workgroup of 1024.', mode='compute',
            autodispatchsize=False, dispatchsizex=1, dispatchsizey=1, dispatchsizez=1, outputresolution='custom',
            resolutionw=SLOTS, resolutionh=4, format='rgba32float')
layout.par.tops = 'vocab ink order_tex moving rings'
docked(layout, '_compute', src('layout.glsl'), 'The layout, a compute shader (src/layout.glsl).')
STEP = 'min(absTime.stepSeconds, 0.1)'
uniforms(layout,
         uGrid=(Expr("op('source').width"), Expr("op('source').height"),
                Expr('parent().par.Layout.menuIndex'), LEVELS),
         uSize=(par('Smallest'), Expr("max(parent().par.Largest * op('source').height, parent().par.Smallest)"),
                par('Detail'), Expr('parent().par.Spread / {}'.format(CELL_PX))),
         uTime=(Expr(STEP), par('Fade'), HOLD, Expr('max(1, min(32, round(parent().par.Fill * {})))'.format(STEP))),
         uMove=(par('Follow'), 0))
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset: every word gone at once, and the picture laid out anew.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        op('layout_fb').par.resetpulse.pulse()\n")
setpars(reset, op='..', pars='Reset', onpulse=True, valuechange=False)

# ---- Drawing the words ------------------------------------------------------------------------------
section('draw', 'The words drawn: a quad each, cut from the atlas and colored by the picture', lane='draw')
RES = (Expr("op('source').width"), Expr("op('source').height"))
mat = mk(comp, glslMAT, 'word_mat', comment='A word: placed from its slot, its letters from the atlas, colored.',
         blending=True, srcblend='one', destblend='oneminussrca', depthtest=False, depthwriting=False)
docked(mat, '_vertex', src('word_vertex.glsl'), "A word's quad: its place, size and fade from its slot.")
docked(mat, '_pixel', src('word_pixel.glsl'), "A word's letters from the atlas, crisp at any size, colored.")
mat.seq.sampler.numBlocks = 4
setpars(mat, sampler0name='sState', sampler0top='layout', sampler1name='sInk', sampler1top='ink',
        sampler2name='sAtlas', sampler2top='atlas', sampler3name='sPicture', sampler3top='source')
geo = mk(comp, geometryCOMP, 'word_geo', comment='A quad for every slot (1024), placed by word_mat.',
         instancing=True, instancecountmode='manual', numinstances=SLOTS, material='word_mat')
for o in list(geo.children):             # a new Geometry COMP holds a torus
    o.destroy()
quad = mk(geo, rectangleSOP, 'quad', comment='One square, which the material moves and sizes for each word.',
          sizex=1, sizey=1, texture='face', at=(0, 0))
quad.render = quad.display = True
cam = mk(comp, cameraCOMP, 'cam', comment='The Render TOP needs a camera; the shaders place everything themselves.',
         projection='ortho', tz=5)
for o in list(cam.children):             # a new Camera COMP holds a File In POP
    o.destroy()
render = mk(comp, renderTOP, 'render', comment='Every word, over transparent black.', camera='cam',
            geometry='word_geo', lights='', bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=0, antialias='aa1',
            format='rgba8fixed', outputresolution='custom', resolutionw=RES[0], resolutionh=RES[1])

# ---- Audio (input 2) --------------------------------------------------------------------------------------
section('audio', 'Audio (input 2): the words swell on each beat and brighten as the music gets louder')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running beat count: watched, not the one-frame beat.',
            channames='beat_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a beat arrives.', timeslice=True)
flash = flash_gate(comp, steps)
mk(comp, triggerCHOP, 'pump', [flash], 'The words swollen after a beat the gate let through, settling over {:g} s.'.format(
    PUMP_FALL), attack=0, peak=1, decay=PUMP_FALL, dshape='easeout', sustain=0, release=0)
level = mk(comp, selectCHOP, 'level', [audio], 'How loud the music is now.', channames='level')
level_now = mk(comp, filterCHOP, 'level_now', [level], 'The loudness smoothed over {:g} s.'.format(SLOW), width=SLOW)
mk(comp, filterCHOP, 'level_usual', [level_now], 'The usual loudness: its average over the last {:g} s.'.format(USUAL),
   type='box', width=USUAL)
WIRED = "op('audio')['source'].eval() > 0"
PUMP = "(parent().par.Pump * op('pump')[0] if {} else 0)".format(WIRED)
SWELLING = ("(parent().par.Swell * max(op('level_now')[0] - op('level_usual')[0], 0) if {} else 0)".format(WIRED))
uniforms(mat, uRes=RES + (Expr('{} * {}'.format(PUMP_SIZE, PUMP)),),
         uLook=(Expr('parent().par.Color.menuIndex'), par('Lift'),
                Expr('{} * {} + {} * {}'.format(PUMP_BRIGHT, PUMP, SWELL, SWELLING)),
                Expr("1 if parent().par.Layout == 'cloud' else 0")))

# ---- The picture -------------------------------------------------------------------------------------------
section('look', 'The words over the picture', lane='picture')
look = glsl(comp, 'look', [source, render], src('look.glsl'), 'The words over the picture, dimmed to Backdrop.',
            uLook=(par('Backdrop'),))

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
