"""Build Motion Magnify. Run from a textport: __file__ = '/path/to/build_motion_magnify.py'; exec(open(__file__).read())

The live picture's movements made larger: a sway, a nod or a dancer's bounce drawn several times as big, while what
stands still stays put. It is Lagrangian, after Liu, Torralba, Freeman, Durand and Adelson ("Motion Magnification",
SIGGRAPH 2005): the picture's motion is measured (lib optical_flow() and flow_speed(), Lucas-Kanade) and the picture is
moved further along it. A displacement field travels with the content (semi-Lagrangian, as Pencil's strokes do),
adding up each frame's motion and leaking back to 0, so it says how far each part is from where it rests; the field is
eased, spread over its neighbors, made larger, held back where it would fold the picture over itself, and the picture
is taken from that far back.

The Eulerian methods (Wu et al. 2012, Wadhwa et al. 2013 and 2014), which filter the picture's pixels over time instead,
are patented in the US by MIT until 2032-2035 (private/patents/motion-magnify.md), so nothing here filters a pixel's
value over time and adds it back, and there is no color (pulse) mode.

The network, left to right:
  picture  source -> warp (the picture taken from its displacement) -> out
  motion   optical_flow() (lum8, lum4, change, clock, lk8, lk4) -> flow_speed() (pace, motion) -> move (the displacement
           and its easing; move_fb) -> spread_h, spread_v -> stretch (made larger, and how much it stretches) -> guard
           (held from folding) -> moved (nothing while Amount is 0, so the motion doesn't cook)
  audio    audio_in() -> counts -> steps -> beat_now -> kick_env (each beat's push); beat_rate (the
           tempo, for Follow Tempo); drop_now -> drop_env; level_pick -> level_smooth (loudness)
  depth    input 3 (depth_in()) -> near
"""
import math
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
# The movements kept are those that go back and forth about Timing times a second: the displacement leaks back to 0
# with a corner at half that (LEAK) and is eased with a corner at twice it (EASE), a band two octaves wide.
LEAK, EASE = 0.5, 2.0
SPREAD = 12.0        # the displacement spread over 12 pixels at 720 high (Smoothness 1)
FOLD, REACH = 0.6, 12.0   # the warp stretches at most 0.6 pixels per pixel, a stretch counted 12 pixels around (at 720)
DEAD = 0.03          # flow_speed()'s dead zone, cells a frame: small, so a slow sway counts (Pencil's)
TEMPO_SPAN = 4.0     # the tempo is the beats of the last 4 s
# The music: Loudness 1 makes the movement up to LOUD larger when loud (smaller when quiet); Beat Kick 1 makes it up to
# KICK larger for a moment on a beat; a build up to BUILD larger as it rises, a drop DROP larger for Length s.
LOUD, KICK, BUILD, DROP = 0.5, 1.0, 0.5, 1.0
DEPTH_TYPES = (('nearness', 'Brighter Is Nearer'), ('distance', 'Distance 0-1 (RealSense, Kinect)'),
               ('meters', 'Distance in Meters (Kinect Azure)'))


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


README = src('readme.txt').format(v=VERSION)
comp, page, source = new_effect(
    'motion_magnify', 'Motion Magnify',
    "Motion Magnify {}: the live picture's movements made larger, a sway, a nod or a bounce drawn several times as "
    'big.'.format(VERSION),
    README, tags=('motion-magnify', 'motion', 'optical-flow', 'warp', 'audio-reactive'), audio=True, depth=True,
    sample="app.samplesFolder + '/Map/Nature/Movie.2.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
custom(page, 'Float', 'Amount', 'Amount', 3.0,
       'How much further things move, 0-10: at 3 a movement is drawn 4 times as large; 0 shows the picture as it '
       'is.', 0, 10, True).startSection = True
custom(page, 'Float', 'Timing', 'Timing', 1.0,
       'Which movements grow, by how often they go back and forth, in Hz: 0.5 a slow sway or a breath, 1 a nod, 2-3 '
       'a bounce. Much slower movements (a steady walk) and much faster ones (a shake, noise) grow less.', 0.25, 4,
       True)
custom(page, 'Toggle', 'Tempo', 'Follow Tempo', False,
       'With beats on input 2, Timing follows the music: one back and forth every two beats (1 Hz at 120 BPM), as a '
       'dancer steps one way on a beat and back on the next.')
custom(page, 'Float', 'Smoothness', 'Smoothness', 1.0,
       'How large the areas that move together are, 0.25-4: lower lets small details move on their own (and tear '
       'more where they part), higher moves whole areas as one.', 0.25, 4, True)
p = custom(page, 'Float', 'Depthfocus', 'Depth Focus', 0.5,
           'With a depth map or mask on input 3: how much the movement grows only near the camera (or inside the '
           'mask), 0-1. At 1 far things (or what lies outside the mask) stay as they are. Nothing changes without '
           'input 3.', 0, 1, True)
p.startSection = True
menu(page, 'Depthtype', 'Depth Type', DEPTH_TYPES, 'nearness',
     'What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits '
     'the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance '
     'in Meters suits the Kinect Azure TOP, scaled by Max Distance.')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.', 0.5, 15,
       True).enableExpr = "me.par.Depthtype == 'meters'"
custom(page, 'Float', 'Beatkick', 'Beat Kick', 0.5,
       'How much larger the movement grows for a moment on each beat of input 2, 0-1: at 1 twice as large, easing '
       'back over 0.4 s.', 0, 1, True).startSection = True
custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much larger the movement grows when music on input 2 is loud (and smaller when quiet), 0-1. It eases '
       'over half a second.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2, a build makes the movement grow as it rises, and a drop makes it twice as "
       "large for Length seconds (Fosfora's drop detection is experimental).")
custom(page, 'Float', 'Length', 'Length', 1.0, 'How long a drop makes the movement larger, in seconds.', 0.2, 3,
       True).enableExpr = 'me.par.Moments'

# ---- Audio (input 2): pushes on the beats, the tempo, the loudness ---------------------------------
section('audio', 'Audio (input 2): a push on each beat, the tempo, the movement larger when loud')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beat_now = mk(comp, selectCHOP, 'beat_now', [steps], 'A beat arriving.', channames='beat_count')
kick_env = mk(comp, triggerCHOP, 'kick_env', [beat_now], "A beat's push: up at once, back over 0.4 s.",
              attack=0, peak=1, decay=0.4, sustain=0, release=0)
beat_rate = mk(comp, filterCHOP, 'beat_rate', [beat_now],
               'Beats a second: the beats of the last {:g} s, for Follow Tempo.'.format(TEMPO_SPAN),
               type='box', width=TEMPO_SPAN)
drop_now = mk(comp, selectCHOP, 'drop_now', [steps], 'A drop arriving (Fosfora, experimental).',
              channames='drop_count')
drop_env = mk(comp, triggerCHOP, 'drop_env', [drop_now],
              "A drop's larger movement: up in 0.3 s, held for Length, back over 0.8 s.",
              attack=0.3, peak=1, peaklen=par('Length'), decay=0.8, sustain=0, release=0)
level_pick = mk(comp, selectCHOP, 'level_pick', [audio], 'How loud it is now.', channames='level')
level = mk(comp, filterCHOP, 'level_smooth', [level_pick],
           'Loudness eased over half a second, so the movement swells and falls instead of jittering.', width=0.5)
WIRED = "op('audio')['source'].eval() > 0"
PRESS = "(parent().par.Loudness * 2 * (op('level_smooth')[0] - 0.5) if {} else 0)".format(WIRED)
TIMES = ("parent().par.Amount * (1 + {loud} * {press}) * (1 + {kick} * parent().par.Beatkick * op('kick_env')[0]) "
         "* (1 + ({build} * op('audio')['build'] + {drop} * op('drop_env')[0] if parent().par.Moments else 0))").format(
    loud=LOUD, press=PRESS, kick=KICK, build=BUILD, drop=DROP)
# Timing, or half the beat rate with Follow Tempo while beats come at 60 BPM or more.
CENTER = ("(op('beat_rate')[0] / 2 if parent().par.Tempo and op('beat_rate')[0] > 1 "
          'else parent().par.Timing)')

# ---- Depth (input 3): the movement grows near the camera -------------------------------------------
section('depth', 'Depth or a mask (input 3): the movement grows near the camera, or inside the mask')
flat = mk(comp, constantTOP, 'depth_none', comment='Near everywhere: with nothing on input 3 everything grows.',
          outputresolution='custom', resolutionw=1, resolutionh=1, colorr=1, colorg=1, colorb=1, alpha=1)
depth = depth_in(comp, fallback=flat)
near = glsl(comp, 'near', [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'Input 3 at a quarter size, as nearness; Depth Type flips distance (black is no reading).', fmt='rgba16float',
            uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='quarter')

# ---- The motion and the displacement --------------------------------------------------------------
section('motion', "Motion: the picture's movement, measured (optical flow)", lane='motion')
still = mk(comp, constantTOP, 'still', comment='Nothing, and still: where the motion and the displacement start.',
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
mo = optical_flow(comp, _ROOT, source)
pace, motion = flow_speed(comp, _ROOT, mo, still, dead=DEAD)
section('displacement', 'The displacement: how far each part is from where it rests, made larger', lane='motion')
move_fb = mk(comp, feedbackTOP, 'move_fb', [still], "move's last frame.", top='move')
STEP = Expr('min(absTime.stepSeconds, 0.1)')
move = glsl(comp, 'move', [motion, move_fb, pace], src('move.glsl'),
            'How far each part of the picture is from where it rests: carried with the content, leaking back to 0, '
            'eased.', fmt='rgba32float',
            uM=(STEP, Expr('{:.6f} / {}'.format(1 / (2 * math.pi * LEAK), CENTER)),
                Expr('{:.6f} / {}'.format(1 / (2 * math.pi * EASE), CENTER))))
spread_h = glsl(comp, 'spread_h', [move], src('spread.glsl'), 'The displacement spread across.', fmt='rg32float',
                uS=(1, 0, Expr('{} * parent().par.Smoothness'.format(SPREAD))))
spread_v = glsl(comp, 'spread_v', [spread_h], src('spread.glsl'), 'The displacement spread down.', fmt='rg32float',
                uS=(0, 1, Expr('{} * parent().par.Smoothness'.format(SPREAD))))
stretch = glsl(comp, 'stretch', [spread_v, near], src('stretch.glsl'),
               'The displacement made larger (Amount, the music, Depth Focus), and how much it would stretch the picture.',
               fmt='rgba32float',
               uA=(Expr(TIMES), Expr('parent().par.Depthfocus if parent().inputConnectors[2].connections else 0')))
guard = glsl(comp, 'guard', [stretch], src('guard.glsl'),
             'The fold guard: the displacement held back wherever it would fold the picture over itself.',
             fmt='rgba32float', uG=(FOLD, REACH))
moved = mk(comp, switchTOP, 'moved', [still, guard],
           "The displacement to move the picture by; nothing while Amount is 0, so the motion doesn't cook.",
           index=Expr('1 if parent().par.Amount > 0 else 0'))
for o in (move, spread_h, spread_v, stretch, guard):
    setpars(o, inputextenduv='hold')

# ---- The picture, moved further ----------------------------------------------------------------------
section('warp', 'The picture moved further: each part taken from its displacement')
warp = glsl(comp, 'warp', [source, moved], lib_glsl(_ROOT, 'red_guard.glsl') + src('warp.glsl'),
            'The picture, each part moved its displacement further from where it rests; every red kept short of '
            "WCAG's saturated-red line.")
setpars(warp, inputextenduv='hold')

finish_effect(comp, warp, VERSION, page)
save_effect(comp, _HERE, _ROOT)
