"""Build Bent Cam. Run from a textport: __file__ = '/path/to/build_bent_cam.py'; exec(open(__file__).read())

A circuit-bent webcam filming a screen that shows its own picture. The picture is on a screen, mixed with the
camera's last picture (Feedback); the camera films it through its lens (Zoom, Rotate, Focus), its Bayer mosaic
beating against the screen's pixels (moir\u00e9) and its sensor's noise, then its own processing (demosaicing,
gamma, Contrast, Saturation), once a camera frame. That picture goes round the loop, and out over the sensor's
bus to the bridge chip as YUYV bytes, where the wires soldered across the sensor's pins bend it: stuck and
bridged data lines (Camera, Shorts), the bytes taken late (Byte Slip), the pixel clock slipping (Clock Slips),
lines longer than the bridge counts (Sync). The bridge compresses the frame as a JPEG (Compression), and the
cable loses bits (Block Errors). The computer decodes it, scales it up and may mirror it (Mirror). On the music
a wire touches for a moment (Bursts): the bytes slip, every short connects at once, or the stream breaks from a
block to the end of the frame; a drop throws the frame's start off, so the picture jumps down a third.

The loop takes the camera's picture before the bus. A swap of brightness and color inside the loop would swap
back on the next pass, so the whole picture would strobe at the camera's frame rate, as it does in a real rig.

The network, left to right:
  loop     source + feed_fb -> screen (the picture with the camera's last picture over it, at the sensor's size)
           -> lens (Focus) -> camera (Zoom, Rotate, the screen's stripes through the Bayer mosaic, noise) -> isp
           (demosaic, gamma, Contrast, Saturation, the red guard; once a camera frame) -> feed_fb (back to screen)
  out      isp -> bus (YUYV bytes, the shorts, slips and sync) -> dct (JPEG blocks, quantized; block errors)
           -> idct (decoded) -> out (scaled up, Mirror, the red guard)
  audio    audio_in() -> counts -> steps (Slope CHOP); steady counts the time; beat_on, bar_on, steady_on, drop_on
           pick the bursts asked for -> flash_gate() -> flash_budget -> burst (held for Length), burst_count (the
           seed), drop_kind (a drop's burst: the frame jumps); beats (or steady ticks with nothing wired) ->
           beat_pulse -> beat_env, beat_n: each beat's sliver of slipped lines
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'
STEADY = 2.0         # bursts this many seconds apart for Steady, and for On Beats or On Bars with nothing wired
CAM_FPS = 30         # the camera's frame rate: the loop goes round this many times a second
# The sensor's sizes; the picture's aspect is fitted into the one picked (640 x 480 takes a 16:9 picture at 640 x 360).
SENSORS = (('s320', '320 x 240', 320, 240), ('s640', '640 x 480', 640, 480), ('s1280', '1280 x 720', 1280, 720))
SLIPS = (('none', 'None'), ('one', '1 Byte'), ('two', '2 Bytes'), ('three', '3 Bytes'))
MIRRORS = (('off', 'Off'), ('lr', 'Left-Right'), ('four', 'Four Ways'), ('kaleido', 'Kaleidoscope'))
# The loop's limits. With Zoom above 1 every movement echoes outward, and each echo passing a point is another
# light-dark swing there (the shorts' hard-edged bands make them sharp): on the flowers at Flashing Off, Feedback 0.95
# and Zoom 1.1 measured 4.5 flashes a second, 0.8 and 1.05 still added one; at these limits nothing is added, all
# the faults at 1 included (dev/flash.py, 2026-10-25). A tunnel (Zoom below 1) shrinks its echoes and stays calm.
LOOP = dict(feedback=0.85, zoom=1.03, rotate=2)
BLUR = 4.0           # the lens's blur at Focus 0, sigma in pixels of the sensor; it falls as (1 - Focus)^2
# After the gate, bursts at least this far apart (s): Calm a little over its one second, else about 1.3 a second.
# A burst changes the whole frame, each kind differently, so two of different kinds 0.55 s apart (Glitch's and VHS +
# CRT's spacing) gave bright parts of the dancer 4 flashes a second at Up to 3 with the clip's own movement.
FLASH_SPACING = {'calm': 1.1, 'other': 0.75}


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


LOT = {}
exec(compile(src('lot.py'), 'lot.py', 'exec'), LOT)


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [i[0] for i in items]
    p.menuLabels = [i[1] for i in items]
    p.default = p.val = default
    return p


# Sources stay ASCII (TouchDesigner's Python reads files as ASCII); the README DAT gets its accents here.
README = src('readme.txt').format(v=VERSION, steady=STEADY, lot=LOT['readme_table']()).replace('oire', 'oir\u00e9')
comp, page, source = new_effect(
    'bent_cam', 'Bent Cam',
    'Bent Cam {}: a circuit-bent webcam filming a screen that shows its own picture: stuck and bridged data lines, '
    'slipped bytes, broken JPEG blocks, feedback, moir\u00e9 and mirrors.'.format(VERSION),
    README, tags=('circuit-bending', 'glitch', 'feedback', 'audio-reactive'), audio=True, flashing=True,
    sample=SAMPLE_MOVIE)

# ---- Parameters -------------------------------------------------------------------------------
p = custom(page, 'Int', 'Camera', 'Camera', 8,
           'Which camera from the lot of {}. Each has its pins shorted differently: which of its data lines are '
           'stuck at 0 or 1, and which are bridged together (the README lists them).'.format(LOT['CAMERAS']),
           1, LOT['CAMERAS'], True)
p.startSection = True
custom(page, 'Float', 'Shorts', 'Shorts', 0.35,
       "How many of the camera's shorts are connected, 0-1: each sticks or bridges one of the data lines the "
       'picture travels on, so tones break into flat bands of odd colors. The one being connected touches on and '
       'off, in pieces of lines. 0: a working camera.', 0, 1, True)
menu(page, 'Byteslip', 'Byte Slip', SLIPS, 'none',
     'The bridge chip takes the bytes late. 1 Byte or 3 Bytes: it reads color as brightness and brightness as '
     'color, so dark parts turn green and light parts pink. 2 Bytes: the two colors swap, reds turning blue.')
custom(page, 'Float', 'Clockslip', 'Clock Slips', 0.2,
       'How often the pixel clock gains or loses a tick, 0-1: the bytes come a place early or late until it '
       'gains or loses one back (a quarter of the time, not until the end of the line), and that stretch of the '
       'line turns to false color. Each slip stays a moment.', 0, 1, True)
custom(page, 'Float', 'Sync', 'Sync', 0.0,
       "How far the sensor's lines are from the length the bridge expects, 0-1: the picture shears, and breaks "
       'into bands of false color where the bytes slip a place.', 0, 1, True)
p = menu(page, 'Sensor', 'Sensor', [(n, l) for n, l, *_ in SENSORS], 's640',
         "The camera's resolution, the picture's aspect fitted into it. Old webcams gave 640 x 480 or less: each "
         'of their pixels shows, and the JPEG blocks with them.')
p.startSection = True
custom(page, 'Float', 'Compress', 'Compression', 0.5,
       'How hard the camera compresses each frame (Motion JPEG), 0-1: blocks of 8 x 8 pixels and ringing around '
       'edges. 0: quality 100; 1: quality 5.', 0, 1, True)
custom(page, 'Float', 'Blockerr', 'Block Errors', 0.2,
       'How often the cable loses bits, 0-1: from a block on, up to the next restart marker (every 8 blocks), '
       'the brightness and color drift and the detail turns to stripes. Each error stays a moment.', 0, 1, True)
p = custom(page, 'Float', 'Feedback', 'Feedback', 0.5,
           "How much of the camera's own picture the screen it films shows over the input, 0-{:g}. The camera films "
           'itself filming itself: trails, and with Zoom and Rotate, tunnels and spirals. It stops at {:g}, where '
           'the echoes of movement stay within the Flashing limits.'.format(LOOP['feedback'], LOOP['feedback']),
           0, LOOP['feedback'], True)
p.startSection = True
custom(page, 'Float', 'Zoom', 'Zoom', 1.02,
       'How close the camera is to the screen: above 1 it sees part of it, so the picture grows outward on each '
       'pass round the loop ({} a second); below 1 it sees the whole screen in its black bezel, a tunnel. It stops '
       'at {:g}: faster, the echoes of anything moving sweep past each point fast enough to flash.'.format(
           CAM_FPS, LOOP['zoom']), 0.7, LOOP['zoom'], True)
custom(page, 'Float', 'Rotate', 'Rotate', 0.0,
       "How far the camera is tilted, in degrees: the picture turns this much on each pass round the loop ({} a "
       'second), so trails become spirals. It stops at {:g} either way, for the same reason as Zoom.'.format(
           CAM_FPS, LOOP['rotate']), -LOOP['rotate'], LOOP['rotate'], True)
custom(page, 'Float', 'Focus', 'Focus', 0.8,
       "How sharply the camera's lens is focused on the screen, 0-1. Sharp, it sees the screen's pixels and they "
       'beat against its own (moir\u00e9); soft, the picture blurs, more on each pass.', 0, 1, True)
custom(page, 'Float', 'Moire', 'Moir\u00e9', 0.5,
       "How much the screen's red, green and blue stripes show to the camera, 0-1: where they beat against the "
       "sensor's pixels, bands of color (moir\u00e9). Focus softens them.", 0, 1, True)
custom(page, 'Float', 'Contrast', 'Contrast', 1.1,
       'The contrast the camera adds. In the loop it builds up on every pass, so above 1 the trails turn bold '
       'and flat.', 0.5, 1.5, True)
custom(page, 'Float', 'Saturation', 'Saturation', 1.2,
       'The color the camera adds. In the loop it builds up on every pass, so above 1 the trails turn vivid '
       '(it eases off as colors grow strong, so they keep their hues).', 0, 2, True)
custom(page, 'Float', 'Noise', 'Noise', 0.3,
       "The sensor's noise, 0-1: grain that grows with the light, new on every frame.", 0, 1, True)
p = menu(page, 'Mirror', 'Mirror', MIRRORS, 'off',
         'Tile the picture, as VJ apps do with a bent camera. Left-Right: the left half mirrored onto the right. '
         'Four Ways: the top-left quarter in all four corners. Kaleidoscope: wedges mirrored around the middle.')
p.startSection = True
custom(page, 'Int', 'Segments', 'Segments', 6, "How many wedges the Kaleidoscope folds the picture into.",
       2, 16, True).enableExpr = "me.par.Mirror == 'kaleido'"
p = menu(page, 'Bursts', 'Bursts', (('beats', 'On Beats'), ('bars', 'On Bars'), ('steady', 'Steady'), ('off', 'Off')),
         'bars',
         "When a wire touches for a moment: the bytes slip, every short connects at once, or the compressed "
         "stream breaks to the end of the frame. On Bars (the one of each bar) or On Beats: input 2's (with "
         "nothing wired, every {s:g} s). Steady: every {s:g} s. Off: never. Every burst is a flash, so Flashing "
         "limits how often they come.".format(s=STEADY))
p.startSection = True
custom(page, 'Float', 'Length', 'Length', 0.3, 'How long a burst lasts, in seconds.', 0.1, 1.0, True).enableExpr = \
    "me.par.Bursts != 'off'"
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a build connects more of the shorts as it rises, and a drop throws the "
       "frame's start off for a moment, so the picture jumps down a third (Fosfora's drop detection is "
       "experimental).")

# ---- Audio (input 2) and the bursts -------------------------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -200, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count drop_count')
steady = mk(comp, constantCHOP, 'steady', -200, -500, comment='Counts {:g} s periods, for Steady bursts.'.format(STEADY),
            const0name='steady_count', const0value=Expr('int(absTime.seconds / {})'.format(STEADY)))
both = mk(comp, mergeCHOP, 'all_counts', 0, -400, [counts, steady], 'Every count a burst may follow.')
steps = mk(comp, slopeCHOP, 'steps', 200, -400, [both], 'Above 0 on the frame a count goes up.', timeslice=True)
WIRED = "op('audio')['source'].eval() > 0"
asks = []
for i, (name, chan, when, what) in enumerate((
        ('beat_on', 'beat_count', "parent().par.Bursts == 'beats' and " + WIRED, 'beats, when Bursts is On Beats'),
        ('bar_on', 'bar_count', "parent().par.Bursts == 'bars' and " + WIRED, 'bars, when Bursts is On Bars'),
        ('steady_on', 'steady_count',
         "parent().par.Bursts == 'steady' or (parent().par.Bursts in ('beats', 'bars') and not " + WIRED + ")",
         'the steady clock, when Bursts is Steady (or On Beats or On Bars with nothing on input 2)'),
        ('drop_on', 'drop_count', "parent().par.Moments and parent().par.Bursts != 'off'", 'drops (Song Moments)'))):
    pick = mk(comp, selectCHOP, name + '_step', 400, -250 - 150 * i, [steps], 'Steps of {}.'.format(chan), channames=chan)
    asks.append(mk(comp, mathCHOP, name, 600, -250 - 150 * i, [pick], 'Bursts on {}.'.format(what),
                   gain=Expr('1 if ({}) else 0'.format(when))))
ask = mk(comp, mergeCHOP, 'burst_asks', 800, -450, asks, 'Every burst asked for.')
ask_any = mk(comp, mathCHOP, 'burst_any', 1000, -450, [ask], 'One channel: any burst.', chanop='max')
gate = flash_gate(comp, ask_any, 1200, -450)
budget = mk(comp, triggerCHOP, 'flash_budget', 1600, -450, [gate],
            'After the gate: bursts {calm} s apart at Calm, {other} s otherwise, so the total stays well under '
            'WCAG.'.format(**FLASH_SPACING),
            retrigger=Expr("{calm} if parent().par.Flashing == 'calm' else {other}".format(**FLASH_SPACING)),
            retriggerunit='seconds', attack=0, peak=1, peaklen=0, decay=0, sustain=0, release=0)
burst = mk(comp, triggerCHOP, 'burst', 1800, -350, [budget], 'A burst: 1 for Length seconds, then gone.',
           attack=0, peak=1, peaklen=par('Length'), decay=0, sustain=0, release=0)
burst_count = mk(comp, countCHOP, 'burst_count', 1800, -500, [budget], "Bursts so far: each burst's seed.")
drop_step = mk(comp, selectCHOP, 'drop_now', 1600, -650, [asks[3]], 'A drop asking for a burst.')
drop_env = mk(comp, triggerCHOP, 'drop_env', 1800, -650, [drop_step], 'How recent a drop is (fades over 0.3 s).',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
drop_kind = mk(comp, holdCHOP, 'drop_kind', 2000, -600, [drop_env, budget],
               "1 when the burst that passed was a drop's: the frame jumps.")

tick = mk(comp, mathCHOP, 'steady_tick', 800, -100, [asks[2].inputs[0]], 'Steady ticks, only while input 2 is empty.',
          gain=Expr('0 if ' + WIRED + ' else 1'))
beat_in = mk(comp, mergeCHOP, 'beat_in', 1000, -150, [asks[0].inputs[0], tick], 'Beats, or steady ticks.')
beat_pick = mk(comp, mathCHOP, 'beat_pulse', 1200, -150, [beat_in], "One channel: a beat, for its sliver of slips.",
               chanop='max')
beat_env = mk(comp, triggerCHOP, 'beat_env', 1400, -150, [beat_pick], 'Falls from 1 to 0 over the 0.3 s after a beat.',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
beat_n = mk(comp, countCHOP, 'beat_n', 1400, -50, [beat_pick], "Beats so far: where each beat's sliver goes.")

# ---- The loop: the camera filming the screen -----------------------------------------------------
common = lib_glsl(_ROOT, 'common.glsl') + src('common.glsl')
guard = lib_glsl(_ROOT, 'red_guard.glsl')
still = mk(comp, constantTOP, 'still', -400, 450, comment="Nothing: where feed_fb starts, before the camera's first frame.",
           outputresolution='custom', resolutionw=1, resolutionh=1, format='rgba8fixed',
           colorr=0, colorg=0, colorb=0, alpha=0)
feed_fb = mk(comp, feedbackTOP, 'feed_fb', -200, 450, [still], "The camera's last picture (isp's).", top='isp')
screen = glsl(comp, 'screen', -400, 150, [source, feed_fb], src('screen.glsl'),
              "The screen the camera films: the picture with the camera's last picture over it (Feedback), at the "
              "sensor's size.", fmt='rgba16float', uScr=(par('Feedback'),))
SENSOR = 'parent().par.Sensor.menuIndex'
setpars(screen, outputresolution='fit',
        resolutionw=Expr('{}[{}]'.format(tuple(s[2] for s in SENSORS), SENSOR)),
        resolutionh=Expr('{}[{}]'.format(tuple(s[3] for s in SENSORS), SENSOR)))
BLUR_SIGMA = '(1 - parent().par.Focus) ** 2 * {}'.format(BLUR)
lens = mk(comp, blurTOP, 'lens', -200, 150, [screen], "The camera's lens, out of focus by 1 - Focus.",
          type='gaussian', size=Expr('max(0.01, 3 * {})'.format(BLUR_SIGMA)))
camera = glsl(comp, 'camera', 0, 150, [lens], common + src('camera.glsl'),
              "The sensor: each pixel's view of the screen (Zoom, Rotate), through its Bayer filter, the screen's "
              "stripes beating against it (moir\u00e9), the noise.", fmt='mono16float',
              uCam=(par('Zoom'), Expr('math.radians(parent().par.Rotate)'), par('Moire'),
                    Expr('parent().par.Noise')),
              uCam2=(Expr(BLUR_SIGMA), Expr('int(absTime.seconds * {}) % 4096'.format(CAM_FPS))))
NEW_FRAME = ('1 if int(absTime.seconds * {f}) % 4096 != int((absTime.seconds - absTime.stepSeconds) * {f}) % 4096 '
             'else 0').format(f=CAM_FPS)
isp = glsl(comp, 'isp', 200, 150, [camera, feed_fb], guard + src('isp.glsl'),
           "The camera's processing, once a camera frame: demosaicing, gamma, Contrast, Saturation, the red guard.",
           fmt='rgba16float', uIsp=(Expr(NEW_FRAME), par('Contrast'), par('Saturation')))

# ---- Out: the bus, the JPEG, the computer -------------------------------------------------------
KICK = "op('beat_env')[0] if parent().par.Flashing != 'off' and parent().par.Bursts != 'off' else 0"
BURST = dict(uBurst=(Expr("op('burst')[0]"), Expr("op('burst_count')[0]"),
                     Expr("op('drop_kind')[0] if parent().par.Moments else 0")))
bus = glsl(comp, 'bus', 400, 150, [isp], common + LOT['glsl_table']() + src('bus.glsl'),
           "The sensor's bus to the bridge chip, as YUYV bytes: the camera's shorts, the byte slip, the clock's "
           'slips, the lines out of sync.', fmt='rgba8fixed',
           uBus=(par('Camera'), Expr("min(1, parent().par.Shorts + (0.5 * op('audio')['build'] if parent().par.Moments "
                                     "else 0))"), Expr('parent().par.Byteslip.menuIndex'), par('Clockslip')),
           uBus2=(par('Sync'), clock_seconds(), Expr(KICK), Expr("op('beat_n')[0] % 4096")), **BURST)
dct = glsl(comp, 'dct', 600, 150, [bus], common + src('dct.glsl'),
           "The bridge's JPEG: each block's cosine coefficients, rounded to Compression's steps; the cable's block "
           'errors.', fmt='rgba16float', uJpg=(par('Compress'), par('Blockerr'), clock_seconds()), **BURST)
idct = glsl(comp, 'idct', 800, 150, [dct], common + src('idct.glsl'),
            "The computer's decoder: each pixel from its blocks' coefficients, then BT.601 back to R'G'B'.",
            fmt='rgba8fixed')
out = glsl(comp, 'out', 1000, 150, [source, idct], common + guard + src('out.glsl'),
           "The camera's picture scaled up to the input's size, mirrored (Mirror), the red guard.", fmt='rgba8fixed',
           uOut=(Expr('parent().par.Mirror.menuIndex'), par('Segments')))

finish_effect(comp, out, VERSION, page)
save_effect(comp, _HERE, _ROOT)
