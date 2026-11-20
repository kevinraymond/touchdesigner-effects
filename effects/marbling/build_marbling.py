"""Build Marbling. Run from a textport: __file__ = '/path/to/build_marbling.py'; exec(open(__file__).read())

The live picture floated on the size of a marbler's tray: inks dropped on the beats push it aside, and combs drawn on
the bars pull it into the classic patterns (gel-git, nonpareil, bouquet), each tool relaxing a few bars later so the
picture comes back. Every tool is one of the closed-form, area-keeping maps of S. Lu, A. Jaffer, X. Jin, H. Zhao and
X. Mao, "Mathematical Marbling" (IEEE CG&A 32(6), 2012), and the picture is read through all of them undone at once,
afresh at every pixel each frame (the paper's second raster method, after K. Sims, 1992).

dev/protos/marbling/offline.py tried it first on the clips (board #4848): combs pulling a third of the frame left
nothing of the dancer, a pull of about a tenth combs her into feathers and keeps her; drops a fifteenth of the frame
across read as inks at a glance. Nothing is carried from frame to frame: the tools' list is the state (patents:
private notes; README CREDITS, Not used).

The network, left to right:
  picture  source -> marble (the picture through the tools undone, the inks, the subject kept clear)
  tray     tray (the tools, a Script CHOP: drops on beats, strokes on bars) -> ta, tb, tc (its fields four at a time, the
           shaders' uniform arrays) -> ink (+ ink_fb: each drop's color, taken from the picture when it fell)
  audio    audio_in() -> idle (a beat every 0.5 s while nothing is on input 2)
  depth    input 3 (depth_in()) -> near (nearness at a quarter size) -> find (what stands out, or the mask)
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
INKS = (('picture', 'Picture'), ('ebru', 'Ebru'))
PATTERNS = (('stone', 'Stone'), ('gelgit', 'Gel-Git'), ('nonpareil', 'Nonpareil'), ('bouquet', 'Bouquet'))
DROP_EVERY = (('beat', 'Every Beat'), ('other', 'Every Other Beat'), ('bar', 'Every Bar'))
INPUT3 = (('depth', 'Depth Map'), ('mask', 'Mask'))
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))
N = 64                 # tools at once (tray.py's N, the shaders' N)
DROP_R = 0.14          # a drop's radius at Drop Size 1 and full loudness, in frame heights
PULL = 0.24            # a comb's pull at Comb 1, in frame heights (the paper's alpha)
SHARP = 0.015          # how sharply a pull falls off from its tine, in frame heights (the paper's lambda)
IDLE = 0.5             # tray.py's IDLE: a beat every 0.5 s with nothing on input 2
# Depth: what stands out (lib depth_find.glsl) by STAND_OUT of the depth range from what lies left and right, nearer
# than a Far Limit that Sensitivity sets: FAR[0] at 0 to FAR[1] at 1 (on a log scale), as in Fluid, Frost and Ferrofluid.
STAND_OUT, FAR = 0.1, (0.5, 0.05)
WIRED3 = 'parent().inputConnectors[2].connections'


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu_index(name):
    return Expr('parent().par.{}.menuIndex'.format(name))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


README = src('readme.txt').format(v=VERSION)
comp, page, source = new_effect(
    'marbling', 'Marbling',
    'Marbling {}: the live picture floated on a marbler\'s tray, inks dropped on the beats and combed into the '
    'classic patterns on the bars, from the paper.'.format(VERSION),
    README, tags=('marbling', 'ebru', 'warp', 'pattern', 'audio-reactive'),
    audio=True, depth=True, sample=SAMPLE_MOVIE)

# ---- Parameters -------------------------------------------------------------------------------
menu(page, 'Inks', 'Inks', INKS, 'picture',
     "Picture: each drop is the picture's own color where it falls, taken the moment it falls. Ebru: traditional "
     'marbling pigments, indigo, ochre, rose, off-white, umber and sea green, in turn.').startSection = True
menu(page, 'Pattern', 'Pattern', PATTERNS, 'bouquet',
     'How far each tray is combed, a stroke a bar over four bars. Stone: drops only. Gel-Git: a comb drawn across '
     'and back. Nonpareil: then a fine comb at right angles. Bouquet: then a comb drawn along a wave.')
custom(page, 'Float', 'Dropsize', 'Drop Size', 0.5, 'How big the drops are, 0-1. At 0 no drops fall.', 0, 1, True)
custom(page, 'Float', 'Comb', 'Comb', 0.5,
       'How hard the combs pull, 0-1. Past about 0.6 the picture is combed past knowing; at 0 the combs leave it be.',
       0, 1, True)
custom(page, 'Float', 'Spacing', 'Tine Spacing', 0.5,
       "How far apart the combs' tines are, 0-1 (a tenth to a half of the frame's height; the nonpareil's are a "
       'quarter of that). It applies to the next strokes.', 0, 1, True)
custom(page, 'Float', 'Hold', 'Hold', 4.0,
       'How many bars a drop or a stroke holds before it relaxes. It applies to the next ones.', 1, 16, True)
custom(page, 'Float', 'Relax', 'Relax', 2.0,
       'How many bars a drop or a stroke takes to relax, so the picture comes back. It applies to the next ones.',
       0.5, 8, True)
custom(page, 'Pulse', 'Reset', 'Reset', None, 'Clear the tray: every drop and stroke is gone at once.')
custom(page, 'Toggle', 'Keep', 'Keep Subject', True,
       'What stands out in front in the depth map on input 3 (or what is inside the mask) stays the live picture, '
       'clear of the inks and the combs. With nothing on input 3 the whole picture is marbled.').startSection = True
menu(page, 'Input3', 'Input 3 Holds', INPUT3, 'depth',
     'Depth Map: what stands in front of its surroundings is kept clear (floors and walls drop out). Mask: what is '
     'inside the mask (white inside) is.')
custom(page, 'Float', 'Sense', 'Sensitivity', 0.5,
       'How easily something in the depth map counts as standing out (farther counts as well), or how gray a mask '
       'counts as inside.', 0, 1, True)
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"
menu(page, 'Dropevery', 'Drops', DROP_EVERY, 'beat',
     'Which beats of input 2 drop ink: every beat, every other beat or the first of each bar, at most 3 a second. '
     'Bars draw the strokes, at most one every 2 seconds. With nothing on input 2 the tray keeps 120 BPM by itself.'
     ).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.6,
       'How much the loudness of input 2 sizes the drops, 0-1: at 1 a quiet beat drops a speck and a loud one a big '
       'drop.', 0, 1, True)

# ---- Audio (input 2) ------------------------------------------------------------------------------
section('audio', 'Audio (input 2): beats drop ink, bars draw the strokes; a clock stands in with nothing wired')
audio = audio_in(comp, _ROOT)
idle = mk(comp, constantCHOP, 'idle',
          comment='A count that goes up every {:g} s while nothing is on input 2: the beats then.'.format(IDLE),
          const0name='idle', const0value=Expr("int(absTime.seconds / {:g}) % 4096 if op('audio')['source'] == 0 "
                                              "else 0".format(IDLE)))

# ---- The tray -------------------------------------------------------------------------------------
section('tray', "The tray: the drops and strokes on the size now, and each drop's ink", lane='tray')
tray = mk(comp, scriptCHOP, 'tray', [audio, idle],
          'The tools on the tray, newest first: a drop on each beat, a stroke on each bar in the classic order, each '
          'held for Hold bars and relaxed over Relax.')
docked(tray, '_callbacks', src('tray.py'), 'Keeps the tray: drops, strokes, when each was made and how long it lasts.')
# The shaders take the tools as three uniform arrays of vec4 (a GLSL TOP's Arrays page: a CHOP's first four channels are
# an element's x, y, z and w, a sample an element; dev/probes/glsl_arrays.py), so the tray's fields go four at a time.
groups = []
for key, chans, what in (('ta', 'kind t0 rise hold', 'what each tool is and its timing'),
                         ('tb', 'relax a b c', 'its relaxing and its first three numbers'),
                         ('tc', 'd e serial', 'its last two numbers and its drop number')):
    groups.append(mk(comp, selectCHOP, key, [tray], "The tools' {}, for the shaders.".format(what), channames=chans))


def tool_arrays(g):
    g.seq.array.numBlocks = 3
    for i, (o, kind) in enumerate(zip(groups, ('vec4', 'vec4', 'vec3'))):
        setpars(g, **{'array{}name'.format(i): 'uT' + o.name[1], 'array{}type'.format(i): kind,
                      'array{}chop'.format(i): o.name, 'array{}arraytype'.format(i): 'uniformarray'})


clear = mk(comp, constantTOP, 'clear', comment='No inks yet (alpha 0): where the ink ring starts.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
ink_fb = mk(comp, feedbackTOP, 'ink_fb', [clear], 'The inks last frame.', top='ink')
ink = glsl(comp, 'ink', [source, ink_fb], src('ink.glsl'),
           "Each drop's ink: the picture's color where it fell, taken the moment it fell, kept while it lasts.",
           res=(N, 1), fmt='rgba32float')
setpars(ink, inputfiltertype='mipmap')
tool_arrays(ink)
reset = mk(comp, parameterexecuteDAT, 'reset', comment='Reset: the tray starts clean.')
reset.text = ('def onPulse(par):\n'
              "    if par.name == 'Reset':\n"
              "        t = op('tray')\n"
              "        t.store('reset', t.fetch('reset', 0) + 1)\n")
setpars(reset, op='..', pars='Reset', onpulse=True, valuechange=False)

# ---- Depth (input 3) ------------------------------------------------------------------------------
section('depth', 'Depth or a mask (input 3): what stands out stays clear of the marbling')
depth = depth_in(comp)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness. Depth Type flips distance (black is no reading).',
            fmt='rgba16float', uNear=(menu_index('Depthtype'), par('Maxdist')))
setpars(near, outputresolution='quarter')
find = glsl(comp, 'find', [near], lib_glsl(_ROOT, 'depth_find.glsl'),
            'What stands in front of what lies left and right of it (Depth Map), or inside the mask (Mask), nearer '
            'than a limit (Sensitivity).', fmt='rgba16float',
            uFind=(Expr("1 if parent().par.Input3 == 'mask' else 0"), STAND_OUT,
                   Expr("{0} * ({1} / {0}) ** parent().par.Sense if parent().par.Input3 == 'depth' else "
                        "0.95 - 0.9 * parent().par.Sense".format(FAR[0], FAR[1]))))

# ---- The marbling ---------------------------------------------------------------------------------
section('marble', 'The marbling: the picture read through every tool undone, the inks, the subject kept clear')
marble = glsl(comp, 'marble', [source, ink, find], src('marble.glsl'),
              'The picture floated on the tray: each pixel undoes the tools newest first, landing in an ink or on '
              'the picture; four samples a pixel.',
              uM=(clock_seconds(), Expr('{} * parent().par.Dropsize'.format(DROP_R)),
                  Expr('{} * parent().par.Comb'.format(PULL)), SHARP),
              uK=(menu_index('Inks'), Expr('1 if parent().par.Keep and {} else 0'.format(WIRED3))))
tool_arrays(marble)
for g in (ink, marble):
    setpars(g, inputextenduv='hold')

finish_effect(comp, marble, VERSION, page)
save_effect(comp, _HERE, _ROOT)
