"""Build Point Cloud. Run from a textport: __file__ = '/path/to/build_point_cloud.py'; exec(open(__file__).read())

The picture as a cloud of points in 3D: every point of a grid placed at its depth (input 3, or the
picture's brightness) and drawn in its color. From the camera's starting place the cloud is the
picture; as the camera sways round it, the depth shows. Music on input 2 moves it: loudness swells
the dots, each beat deepens the cloud, each bar swings the camera; Fosfora's build scatters the
points and its drop blows them apart.

The network, left to right:
  depth      depth (input 3, or input 1's brightness) -> near (the grid's size, as nearness, by Depth
             Type: lib depth_near.glsl) -> pos (each point in 3D). depth_stats: does input 3 carry any
             depth (near_tiny)? If not, near_pick hands pos input 1's brightness instead. Points From The Subject or Nearer
             Than: near_small -> find (lib depth_find.glsl) -> keep (a Switch TOP: white keeps all,
             and find cooks only when it is in use)
  middle     pivot_in -> pivot_avg (an Analyze TOP) -> pivot (eased; pivot_fb is its last frame): what
             the cloud turns around, kept on the GPU
  drawing    geo instances a square at every pixel of pos; dot_mat's shaders place, turn, move and
             color each. cam stays where the picture fills the frame. render draws Points and Glow;
             Surface draws splat_depth (depth only, a little farther back), then splat_sum (a Render
             Pass TOP adding up colors and weights over that depth, splat_mat) and splat_norm divides;
             look picks one
  audio      audio_in() -> counts -> steps (Slope CHOP) -> beat_env (the swell) and drop_env (the
             burst); level_lag (the dots' size), bar -> bar_lag (the camera's angle for each bar),
             build_lag (the scatter)
"""
import math
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.2'
# Detail: rows of points (columns follow the picture's shape), at most 640 x 360 = 230,400 points.
ROWS = (180, 270, 360)
# Depth Type's Stand Out search runs on a small copy of the depth, as in Particles: it reads a whole
# row per pixel.
MW, MH = 320, 180
# With nothing on input 3, input 1's brightness stands in for the depth The Subject and Nearer Than
# search, and brightness isn't depth: below BRIGHT_FAR it never counts, whatever Far Limit says (as in
# Particles, whose builder has the measurements).
BRIGHT_FAR = 0.5
# Whether input 3 carries any depth is judged on a copy this small (each pixel averages 4 x 4 samples).
TINY = (80, 45)
# The camera: its vertical field of view, and so its distance to the picture plane where the
# picture fills the frame (the plane is one unit tall).
FOV = 40.0
D0 = 0.5 / math.tan(math.radians(FOV / 2))
# Smoothing (pos.glsl): nearness differences up to about SMOOTH (a few 8-bit steps) are smoothed
# over, within SMOOTH_STEPS grid steps per 180 rows; a next point EDGE (a share of its distance)
# nearer or farther lies across an edge.
SMOOTH, SMOOTH_STEPS, EDGE = 0.03, 3, 0.05
# A Glow dot is this many times a Points dot; a Surface splat spans this many grid steps.
GLOW_SIZE, SPLAT_SIZE = 2.5, 2.5
# The pivot settles on the kept points' middle over about this many seconds.
PIVOT_EASE = 1.0
# Sway at 1: the camera swings this far (degrees) round and up and down, by itself.
SWAY_TURN, SWAY_TILT = 25.0, 8.0
# A beat at Beat Swell 1: the cloud gets SWELL_DEEP deeper and the dots SWELL_POP bigger, both
# gone BEAT_TIME seconds later.
SWELL_DEEP, SWELL_POP, BEAT_TIME = 0.45, 0.3, 0.3
# Loudness (0-1 from audio_in, median about 0.6 on raw audio) scales the dots by
# 1 + LEVEL_GAIN x (loudness - LEVEL_MID) at Loudness 1: a fifth smaller in quiet passages, a
# quarter bigger in the loudest.
LEVEL_MID, LEVEL_GAIN = 0.6, 0.8
# Each bar at Bar Moves 1 the camera turns to BAR_TURN x sin(bar x 2.4) degrees (a new angle each
# bar), easing there over BAR_EASE seconds.
BAR_TURN, BAR_EASE = 30.0, 0.8
# A drop: the cloud flies apart in DROP_ATTACK seconds and settles back over DROP_TIME.
DROP_ATTACK, DROP_TIME = 0.08, 1.2
# Surface is one solid, high-contrast skin, so the same moves change more of the frame's light: with
# the moves above it measured 3.5 flashes a second under dev/flash.py's stress beat (WCAG allows 3).
# It gets SURFACE_MOVES of the swell and the burst, and glides to each bar's angle over
# SURFACE_BAR_EASE seconds.
SURFACE_MOVES, SURFACE_BAR_EASE = 0.5, 1.6
DT = Expr('absTime.stepSeconds')
ROWS_EXPR = '[{}][parent().par.Detail.menuIndex]'.format(', '.join(map(str, ROWS)))
ASPECT = Expr("op('source').width / max(1, op('source').height)")


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


def choices(p, names, labels, default):
    p.menuNames, p.menuLabels = names, labels
    p.default = p.val = default
    return p


README = src('readme.txt').format(v=VERSION, n=ROWS[-1] * ROWS[-1] * 16 // 9)
comp, page, source = new_effect(
    'point_cloud', 'Point Cloud',
    'Point Cloud {}: the picture as a cloud of points at its depth (input 3, or brightness), seen from a '
    'swaying camera; the music swells, deepens and swings it.'.format(VERSION),
    README, tags=('point-cloud', 'depth', '3d', 'audio-reactive'), audio=True, depth=True,
    # A white birch among dark leaves (TouchDesigner's own sample): read as depth, its bright trunk
    # stands out in front of the leaves.
    sample="app.samplesFolder + '/Map/Nature/Movie.5.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
choices(custom(page, 'Menu', 'Look', 'Look', None,
               'Points: solid dots, the nearest in front. Glow: soft dots added up, glowing where they crowd. '
               'Surface: soft splats that blend into one skin, the picture wrapped over the depth.'),
        ['points', 'glow', 'surface'], ['Points', 'Glow', 'Surface'], 'points')
pfrom = choices(custom(page, 'Menu', 'Pointsfrom', 'Points From', None,
                       'Which points make the cloud. Everything. The Subject: what is nearer than Far Limit and '
                       'than what lies to its left and right, which leaves out floors and walls. Nearer Than Far '
                       'Limit: everything nearer, for a mask or a camera that sees no floor.'),
                ['everything', 'standout', 'nearer'], ['Everything', 'The Subject (Stand Out)', 'Nearer Than Far Limit'],
                'everything')
pfrom.startSection = True
custom(page, 'Float', 'Standout', 'Stand Out', 0.1,
       'For The Subject: how much nearer than what lies to its left and right something must be to count, '
       '0-1 of the depth range.', 0, 0.3, True).enableExpr = "me.par.Pointsfrom == 'standout'"
custom(page, 'Float', 'Far', 'Far Limit', 0.15,
       'For The Subject and Nearer Than: anything farther than this is left out, 0 (farthest) to 1 (nearest). '
       'Brightness standing in for depth (nothing on input 3) counts only above {:g}, or above Far Limit when '
       'that is higher.'.format(BRIGHT_FAR), 0, 1, True).enableExpr = "me.par.Pointsfrom != 'everything'"
choices(custom(page, 'Menu', 'Depthtype', 'Depth Type', None,
               'What input 3 holds. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance '
               '0-1: the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left '
               'out). Distance in Meters: the Kinect Azure TOP, scaled by Max Distance.'),
        ['nearness', 'distance', 'meters'],
        ['Brighter Is Nearer', 'Distance 0-1 (RealSense, Kinect)', 'Distance in Meters (Kinect Azure)'], 'nearness')
custom(page, 'Float', 'Maxdist', 'Max Distance', 4.0,
       'For Distance in Meters: how far away, in meters, counts as the far end of the depth.',
       0.5, 15, True).enableExpr = "me.par.Depthtype == 'meters'"

custom(page, 'Float', 'Depth', 'Depth', 1.5,
       'How deep the cloud is: the farthest points lie this many times farther than the nearest, plus one. 0 '
       'is flat.', 0, 4, True).startSection = True
choices(custom(page, 'Menu', 'Detail', 'Detail', None,
               'How many points: 180, 270 or 360 rows of them, as many columns as the picture is wide.'),
        ['coarse', 'medium', 'fine'], ['Coarse (180 Rows)', 'Medium (270 Rows)', 'Fine (360 Rows)'], 'fine')
custom(page, 'Float', 'Size', 'Size', 0.8,
       'For Points and Glow: how big a dot is, in steps between points (1: dots touch, seen from the start).',
       0.2, 3, True).enableExpr = "me.par.Look != 'surface'"
choices(custom(page, 'Menu', 'Color', 'Color', None,
               "The points' color: the picture's, by depth (orange near, blue far), or white."),
        ['picture', 'depth', 'white'], ['Picture', 'Depth (Orange Near, Blue Far)', 'White'], 'picture')
custom(page, 'Float', 'Brightness', 'Brightness', 1.0, 'How bright the points are.', 0, 3, True)

custom(page, 'Float', 'Turn', 'Turn', 0.0,
       'Where the camera looks from, round the cloud, in degrees: 0 straight on, as the picture was taken.',
       -90, 90, True).startSection = True
custom(page, 'Float', 'Tilt', 'Tilt', 0.0, 'Where the camera looks from, above (more) or below (less), in degrees.',
       -45, 45, True)
custom(page, 'Float', 'Distance', 'Distance', 1.0,
       'How near the camera is to the middle of the cloud: 1 where the picture fills the frame, less nearer.',
       0.2, 2, True)
custom(page, 'Float', 'Sway', 'Sway', 0.5,
       'How far the camera swings round the cloud by itself (at 1, {:g} degrees each way); 0 holds it still.'
       .format(SWAY_TURN), 0, 2, True)
custom(page, 'Float', 'Swaytime', 'Sway Time', 12, 'Seconds for one swing of the camera.', 2, 60, True)

custom(page, 'Float', 'Loudness', 'Loudness', 0.5,
       'How much the loudness of input 2 grows and shrinks the dots; 0 for a steady size.',
       0, 1, True).startSection = True
custom(page, 'Float', 'Swell', 'Beat Swell', 0.5,
       'On each beat of input 2, the cloud gets deeper for a moment and the dots pop; 0 for neither.', 0, 1, True)
custom(page, 'Float', 'Barmoves', 'Bar Moves', 0.5,
       'On each bar of input 2 (every 4 beats when it has no bars), the camera swings to a new angle; 0 keeps '
       'it where Turn and Sway put it.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a build scatters the points as it rises, and a drop blows the cloud "
       "apart, after which it settles back (Fosfora's drop detection is experimental).")

# ---- Audio (input 2) ---------------------------------------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -400, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count drop_count')
steps = mk(comp, slopeCHOP, 'steps', -200, -350, [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beat_step = mk(comp, selectCHOP, 'beat_step', 0, -300, [steps], 'A beat.', channames='beat_count')
beat_env = mk(comp, triggerCHOP, 'beat_env', 200, -300, [beat_step],
              "A beat's swell: 1 at the beat, none {:g} s later.".format(BEAT_TIME),
              attack=0, peak=1, peaklen=0, decay=BEAT_TIME, dshape='linear', sustain=0, release=0)
drop_step = mk(comp, selectCHOP, 'drop_step', 0, -450, [steps], 'A drop.', channames='drop_count')
drop_env = mk(comp, triggerCHOP, 'drop_env', 200, -450, [drop_step],
              "A drop's burst: out in {:g} s, settled back {:g} s later.".format(DROP_ATTACK, DROP_TIME),
              attack=DROP_ATTACK, peak=1, peaklen=0, decay=DROP_TIME, dshape='linear', sustain=0, release=0)
build = mk(comp, selectCHOP, 'build', 0, -600, [audio], "Fosfora's build, 0..1.", channames='build')
build_lag = mk(comp, lagCHOP, 'build_lag', 200, -600, [build], 'The build, easing out after a drop.',
               lag1=0.5, lag2=2.0, lagunit='seconds')
level = mk(comp, selectCHOP, 'level', 0, -750, [audio], 'Loudness, 0..1.', channames='level')
level_lag = mk(comp, lagCHOP, 'level_lag', 200, -750, [level], 'Loudness, smoothed (up in 0.1 s, down in 0.8 s).',
               lag1=0.1, lag2=0.8, lagunit='seconds')
bar = mk(comp, constantCHOP, 'bar', 0, -900, comment="The camera's angle for this bar (degrees).",
         const0name='turn', const0value=Expr("math.sin(op('audio')['bar_count'] * 2.4) * {} * parent().par.Barmoves"
                                             .format(BAR_TURN)))
BAR_GLIDE = Expr("{} if parent().par.Look == 'surface' else {}".format(SURFACE_BAR_EASE, BAR_EASE))
bar_lag = mk(comp, lagCHOP, 'bar_lag', 200, -900, [bar],
             'The camera easing to its new angle over {:g} s ({:g} s for Surface).'.format(BAR_EASE, SURFACE_BAR_EASE),
             lag1=BAR_GLIDE, lag2=BAR_GLIDE, lagunit='seconds')

# ---- The points ----------------------------------------------------------------------------------
depth = depth_in(comp, x=-600, y=-1100)
grid_w = Expr("max(1, int(round({} * op('source').width / max(1, op('source').height))))".format(ROWS_EXPR))
near = glsl(comp, 'near', -400, -1100, [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
            'The depth at the grid size (Detail), as nearness; Depth Type flips distance (black: no reading).',
            fmt='rgba16float', uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
setpars(near, outputresolution='custom', resolutionw=grid_w, resolutionh=Expr(ROWS_EXPR))
near_small = glsl(comp, 'near_small', -400, -1300, [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
                  'The depth, {} x {}, for finding the subject.'.format(MW, MH), res=(MW, MH), fmt='rgba16float',
                  uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
find = glsl(comp, 'find', -200, -1300, [near_small], lib_glsl(_ROOT, 'depth_find.glsl'),
            'The subject: nearer than Far Limit and (The Subject) than what lies left and right of it.',
            res=(MW, MH), fmt='rgba16float',
            uFind=(Expr("1 if parent().par.Pointsfrom == 'nearer' else 0"), par('Standout'),
                   Expr('parent().par.Far.eval() if parent().inputConnectors[2].connections else '
                        'max(parent().par.Far.eval(), {:g})'.format(BRIGHT_FAR))))
keep_all = mk(comp, constantTOP, 'keep_all', -200, -1450, comment='White: every point stays (Points From Everything).',
              outputresolution='custom', resolutionw=1, resolutionh=1, colorr=1, colorg=1, colorb=1, alpha=1)
keep = mk(comp, switchTOP, 'keep', 0, -1300, [keep_all, find],
          'Which points stay: all, or the subject (find cooks only then: a Switch TOP cooks only what it shows).',
          index=Expr("0 if parent().par.Pointsfrom == 'everything' else 1"))
near_tiny = glsl(comp, 'near_tiny', -600, -800, [depth], lib_glsl(_ROOT, 'depth_near.glsl'),
                 'The depth, {} x {}, as nearness: enough to tell whether input 3 carries any.'.format(*TINY),
                 res=TINY, fmt='rgba16float', uNear=(Expr('parent().par.Depthtype.menuIndex'), par('Maxdist')))
depth_stats = mk(comp, analyzeTOP, 'depth_stats', -400, -800, [near_tiny],
                 'The nearest reading in the depth: none (black) means input 3 carries no depth.',
                 op='maximum', analyzechannel='independent', format='rgba16float')
near_pick = glsl(comp, 'near_pick', -200, -950, [near, source, depth_stats], src('near_pick.glsl'),
                 "The depth pos reads: input 3's when it carries any, else input 1's brightness.", fmt='rgba16float')
JITTER = Expr("0 if parent().par.Look == 'surface' else 1")
pos = glsl(comp, 'pos', -200, -1100, [near_pick, keep], src('pos.glsl'),
           'Every point in 3D: on its ray from the camera, as far as its depth says (smoothed, edges put to a side).',
           fmt='rgba32float',
           uGeo=(ASPECT, par('Depth'), Expr("1 if parent().par.Depthtype != 'nearness' else 0"), JITTER),
           uSmooth=(SMOOTH, Expr('round({} * {} / {})'.format(SMOOTH_STEPS, ROWS_EXPR, ROWS[0])), EDGE),
           uCam=(D0,))
setpars(pos, outputresolution='custom', resolutionw=grid_w, resolutionh=Expr(ROWS_EXPR))

# ---- The cloud's middle --------------------------------------------------------------------------
pivot_in = glsl(comp, 'pivot_in', 0, -950, [pos], src('pivot_in.glsl'), 'The kept points (and 1), for their average.',
                fmt='rgba32float')
pivot_avg = mk(comp, analyzeTOP, 'pivot_avg', 200, -950, [pivot_in], "pivot_in's average: the kept points' middle.",
               op='average', analyzechannel='independent', format='rgba32float')
pivot_start = mk(comp, constantTOP, 'pivot_start', 200, -800, comment="pivot's starting state: no middle yet.",
                 outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba32float',
                 colorr=0, colorg=0, colorb=0, alpha=0)
pivot_fb = mk(comp, feedbackTOP, 'pivot_fb', 400, -800, [pivot_start], "pivot's last frame.", top='pivot')
pivot = glsl(comp, 'pivot', 400, -950, [pivot_avg, pivot_fb], src('pivot.glsl'),
             'What the cloud turns around: its middle, eased over {:g} s.'.format(PIVOT_EASE),
             res=(1, 1), fmt='rgba32float', uPivot=(DT, PIVOT_EASE))

# ---- Drawing -------------------------------------------------------------------------------------
GAINS = ("(1 + parent().par.Loudness * {} * (op('level_lag')[0] - {}) if op('audio')['source'] > 0 else 1)"
         " * (1 + parent().par.Swell * {} * op('beat_env')[0])".format(LEVEL_GAIN, LEVEL_MID, SWELL_POP))
TURN = Expr("math.radians(parent().par.Turn + parent().par.Sway * {} * math.sin(2 * math.pi * absTime.seconds"
            " / parent().par.Swaytime) + op('bar_lag')[0])".format(SWAY_TURN))
TILT = Expr("math.radians(parent().par.Tilt + parent().par.Sway * {} * math.sin(2 * math.pi * absTime.seconds"
            " / (1.37 * parent().par.Swaytime)))".format(SWAY_TILT))


def moves(calm=1):
    """dot_vertex.glsl's uMove: the beat's swell, the build's scatter, the drop's burst, the time;
    calm scales the swell and the burst."""
    return (Expr("parent().par.Swell * {} * op('beat_env')[0]".format(SWELL_DEEP * calm)),
            Expr("op('build_lag')[0] * parent().par.Moments"),
            Expr("op('drop_env')[0] * parent().par.Moments * {}".format(calm)), Expr('absTime.seconds'))


COLOR = Expr('parent().par.Color.menuIndex')


def dot_mat(name, y, comment, size, pass_, calm=1):
    """A GLSL MAT with the dot shaders (each MAT fills its own docked DATs, so the three carry the
    same text), reading pos, the picture and the pivot."""
    mat = mk(comp, glslMAT, name, 800, y, comment=comment)
    docked(mat, '_vertex', src('dot_vertex.glsl'), 'Places, turns, moves and colors each dot (dot_vertex.glsl).')
    docked(mat, '_pixel', src('dot_pixel.glsl'), 'Draws a dot: solid, soft or a splat (dot_pixel.glsl).')
    mat.seq.sampler.numBlocks = 3
    setpars(mat, sampler0name='sPos', sampler0top='pos', sampler1name='sColor', sampler1top='source',
            sampler2name='sPivot', sampler2top='pivot')
    uniforms(mat, uDot=(size, Expr('1 / {}'.format(ROWS_EXPR)), EDGE, JITTER),
             uView=(TURN, TILT, par('Distance'), D0), uMove=moves(calm), uLook=(COLOR, par('Brightness'), pass_, par('Depth')),
             uGain=(Expr(GAINS),))
    return mat


GLOW = "parent().par.Look == 'glow'"
dots = dot_mat('dot_mat', -150, 'Points and Glow: solid dots in front of each other, or soft ones added up.',
               Expr("parent().par.Size * ({} if {} else 1)".format(GLOW_SIZE, GLOW)),
               Expr('parent().par.Look.menuIndex'))
setpars(dots, blending=Expr(GLOW), srcblend='one', destblend='one', depthtest=Expr('not ' + GLOW),
        depthwriting=Expr('not ' + GLOW))
dot_mat('splat_depth_mat', -300, "Surface's depth pass: each splat's middle, a little farther back.",
        SPLAT_SIZE, 3, SURFACE_MOVES)
splats = dot_mat('splat_mat', -450, "Surface's splats: color x weight and weight, added up where they pass the depth.",
                 SPLAT_SIZE, 2, SURFACE_MOVES)
setpars(splats, blending=True, srcblend='one', destblend='one', srcblenda='one', destblenda='one', depthtest=True,
        depthwriting=False, premultrgbbyalpha=False)

geo = mk(comp, geometryCOMP, 'geo', 600, -150, comment="A square at every point: instancing, one per pixel of pos.",
         instancing=True, instancecountmode='oplength', instanceop='pos', instancetx='r', instancety='g',
         instancetz='b', material='dot_mat')
for o in list(geo.children):             # a new Geometry COMP holds a torus
    o.destroy()
quad = mk(geo, rectangleSOP, 'quad', 0, 0, comment='A square one unit across: dot_mat sizes and places each one.',
          sizex=1, sizey=1)
quad.render = quad.display = True
cam = mk(comp, cameraCOMP, 'cam', 600, 0, comment='Where the picture fills the frame ({:g} degrees high); the cloud '
         'turns, not the camera.'.format(FOV), projection='perspective', viewanglemethod='vertfov', fov=FOV,
         tz=D0, near=0.01, far=100)
# A new Camera COMP holds a File In POP (its own picture in the viewer); nothing here draws it.
for o in list(cam.children):
    o.destroy()
SIZE = dict(outputresolution='custom', resolutionw=Expr("op('source').width"), resolutionh=Expr("op('source').height"))
render = mk(comp, renderTOP, 'render', 1000, -150, comment='Points and Glow, at the picture size.',
            camera='cam', geometry='geo', lights='', bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=1, **SIZE)
# A Render Pass TOP draws into its input's buffers, so the float the sums need is set here.
splat_depth = mk(comp, renderTOP, 'splat_depth', 1000, -300, comment="Surface: the splats' depth only, a little "
                 'farther back than they are.', camera='cam', geometry='geo', lights='', overridemat='splat_depth_mat',
                 drawdepthonly=True, format='rgba16float', bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=0, **SIZE)
splat_sum = mk(comp, renderpassTOP, 'splat_sum', 1200, -300, [splat_depth],
               "Surface: the splats' colors and weights added up where they pass splat_depth's depth.",
               camera='cam', geometry='geo', lights='', cleardepth=False, clearcolor=True, overridemat='splat_mat',
               bgcolorr=0, bgcolorg=0, bgcolorb=0, bgcolora=0)
splat_norm = glsl(comp, 'splat_norm', 1400, -300, [splat_sum], src('splat_norm.glsl'),
                  'Surface: color divided by weight, the splats blended into one skin.')
look = mk(comp, switchTOP, 'look', 1600, -150, [render, splat_norm], 'The Look: Points and Glow, or Surface.',
          index=Expr("1 if parent().par.Look == 'surface' else 0"))

finish_effect(comp, look, VERSION, page)
save_effect(comp, _HERE, _ROOT)
