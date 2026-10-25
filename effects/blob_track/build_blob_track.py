"""Build Blob Track. Run from a textport: __file__ = '/path/to/build_blob_track.py'; exec(open(__file__).read())

A tracking overlay: thin boxes around what moves or shines, ID and position labels in the
library's 5 x 7 font, lines joining neighbors; audio on input 2 scrambles labels, spawns links
and fills boxes on beats, and Fosfora's signal adds bars, builds, drops and sections.

The network, left to right:
  detection  source -> small gray picture -> state (frame + slow background, Feedback TOP)
             -> mask (movement, or what stands out) -> either the Blob Track TOP on a blurred
             320 x 180 copy (its Info CHOP as a texture, filtered by bt_clean.glsl and picked by
             bt_pick.glsl) or the GPU grid
             (grid -> grid_peaks -> grid_pick), chosen by a Switch TOP so only one cooks
  boxes      track.glsl follows each blob by ID in 64 slots (Feedback TOP: glide, fade in and
             out, coast on through a short loss; match.glsl lets a box take over the blob that
             replaced its own), table.glsl packs them and finds each one's nearest neighbors
  picture    tiles.glsl lists the boxes near each 20 x 20 pixel tile; draw.glsl draws the
             picture, boxes, insides, links and labels in one pass, visiting only those
  audio      audio_in() -> counts -> Slope CHOP steps -> Trigger CHOP envelopes; fills and drops
             go through flash_gate(), then FLASH_SPACING (at most about 2 a second)
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.3'
# The tracker and the mask run on a small copy: OpenCV's contour pass and the GPU-to-CPU
# download scale with pixels (30 ms at full size on a speckly mask, under 3 ms here), and the
# Blob Track TOP's positions come back normalized anyway.
TW, TH = 320, 180
# The GPU grid's cells (32 x 32 pixels at 1280 x 720).
GW, GH = 40, 22
# Most boxes the overlay draws (Max Count's ceiling) and most blobs it reads from the Blob
# Track TOP before picking the biggest (5 rows each in a one-channel-per-row texture, which the
# Non-Commercial license caps at 1280 rows).
MAXB, MAXIN = 64, 128
WORDS = ('NODE', 'SYNC', 'SCAN', 'LOCK', 'PING', 'ECHO', 'FLUX', 'GRID', 'HALO', 'TRAK', 'BEAT', 'KICK',
         'WAVE', 'DATA', 'SEEK', 'MASS', 'IRIS', 'PEAK', 'BASS', 'LOOP', 'TONE', 'BODY', 'STEP', 'SPIN')
# The overlay must not flicker by itself (WCAG 2.3.1, measured with dev/flash.py): a blob gets a box
# only once it has lasted SHOW_AFTER seconds, a box whose blob is lost coasts on for HOLD seconds
# before it fades (so it can pick its blob up again rather than blink out and back), boxes fade in
# and out over these times, and the flashes the gate lets through are at least FLASH_SPACING
# seconds apart (Calm: a little over its one second, so frame jitter can't fit a third swing into
# any one second; otherwise at most about 2 a second, leaving headroom under WCAG's 3 for what the
# picture and the overlay do themselves).
SHOW_AFTER, HOLD, FADE_IN, FADE_OUT = 0.4, 0.5, 0.35, 0.6
# Movement's background (state.glsl) follows the picture BG_SLOW seconds behind, and BG_FAST behind
# where a pixel has stayed still for BG_STILL seconds: the floor a walker has just left stops
# standing out within about a second, not three, while the walker (never still that long) does.
BG_SLOW, BG_FAST, BG_STILL = 1.5, 0.25, 0.4
FLASH_SPACING = {'calm': 1.1, 'other': 0.55}
T = clock_seconds()
DT = Expr('absTime.stepSeconds')


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def font_head():
    """The lib font, the glyph numbers draw.glsl uses and the word list, as GLSL."""
    font = lib_module(_ROOT, 'font5x7')
    idx = font['index']
    defines = ''.join('#define G_{} {}\n'.format(name, idx(ch)) for name, ch in (
        ('SPACE', ' '), ('HASH', '#'), ('0', '0'), ('X', 'X'), ('Y', 'Y')))
    # Digits then letters must be consecutive glyphs: noiseChar() picks any of the 36.
    assert all(idx(c) == idx('0') + k for k, c in enumerate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    words = '#define NWORDS {}\n'.format(len(WORDS)) + font['glsl_ints']('WORDS', ''.join(WORDS))
    return font['glsl_font']() + defines + words


def par(name):
    return Expr('parent().par.{}'.format(name))


def menu(name):
    return Expr('parent().par.{}.menuIndex'.format(name))


README = open(os.path.join(_HERE, 'src', 'readme.txt')).read().format(v=VERSION)
comp, page, source = new_effect(
    'blob_track', 'Blob Track',
    'Blob Track {}: tracking boxes, labels and links drawn over the picture; beats scramble, spawn '
    'and fill, Fosfora adds bars, builds, drops and sections.'.format(VERSION),
    README, tags=('blob', 'tracking', 'overlay', 'audio-reactive'), audio=True, flashing=True,
    # Grass swaying (TouchDesigner's own sample): always something moving to track, unlike the
    # mist of SAMPLE_MOVIE, which drifts too little at times.
    sample="app.samplesFolder + '/Map/Nature/Movie.2.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
def menu_par(name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [n for n, _ in items]
    p.menuLabels = [lab for _, lab in items]
    p.default = p.val = default
    return p


menu_par('Detector', 'Detector', (('blobtrack', 'Blob Track TOP'), ('grid', 'GPU Grid (cheaper)')), 'blobtrack',
         "What finds the blobs. Blob Track TOP: TouchDesigner's tracker, boxes fit closely (more than 2 "
         'blobs on the Non-Commercial license needs build 2025.32820 or later). GPU Grid: cheaper, nothing '
         'read back to the CPU; boxes snap to grid cells.')
menu_par('Track', 'Track', (('motion', 'Movement'), ('contrast', 'Stand Out'), ('bright', 'Bright Areas'),
                            ('dark', 'Dark Areas')), 'motion',
         'What gets a box. Movement: what moves, light or dark (against a background that follows the '
         'picture a second or two behind; needs a still camera). Stand Out: brighter or darker than its '
         'surroundings, moving or not (works on stills). Bright Areas, Dark Areas: one of the two.')
custom(page, 'Float', 'Threshold', 'Threshold', 0.25,
       'How strongly something must move or stand out to get a box, 0-1. Raise it when everything gets one.',
       0, 1, True)
custom(page, 'Float', 'Merge', 'Merge', 0.25,
       'How far apart parts may be and still count as one blob, 0-1 (blurs the mask). Blob Track TOP only.',
       0, 1, True).enableExpr = "me.par.Detector == 'blobtrack'"
custom(page, 'Float', 'Minsize', 'Min Size', 0.03,
       "Smallest box: its longer side as a fraction of the picture's height.", 0, 1, True)
custom(page, 'Float', 'Maxsize', 'Max Size', 0.7,
       "Largest box: its longer side as a fraction of the picture's height.", 0, 2, True)
custom(page, 'Int', 'Maxcount', 'Max Count', 10,
       'Most boxes shown at once. Boxes stay with what they follow; when it is reached, new ones wait '
       'for room, the longest-lasting first.', 1, MAXB, True)
custom(page, 'Float', 'Smoothing', 'Smoothing', 0.3,
       'How calmly boxes follow what they track, 0-1: 0 jumps with every frame, 1 glides (a quarter second behind).',
       0, 1, True)

look = menu_par('Picture', 'Picture', (('gray', 'Gray'), ('original', 'Original'), ('dim', 'Dimmed')), 'gray',
                'The picture under the overlay: in gray, as it is, or dimmed so the overlay stands out.')
look.startSection = True
menu_par('Inside', 'Inside', (('none', 'None'), ('invert', 'Invert'), ('threshold', 'Threshold'), ('zoom', 'Zoom')),
         'none', 'What each box does to the picture inside it: nothing, turn it over, cut it to two '
         'tones, or magnify it 2x.')
menu_par('Labels', 'Labels', (('off', 'Off'), ('id', 'ID'), ('idpos', 'ID and Position'), ('words', 'Words')),
         'idpos', 'Text by each box: its number above (boxes are numbered as they appear), and its position '
         '(percent across and up) below when the box is tall enough; or a word.')
menu_par('Links', 'Links', (('off', 'Off'), ('nearest', 'Nearest'), ('two', 'Two Nearest')), 'two',
         'Lines from each box to its nearest neighbors.')
custom(page, 'Float', 'Linewidth', 'Line Width', 1.0,
       'Width of the boxes and links in pixels (at 720 pixels high; scales with the picture).', 1, 4, True)
custom(page, 'Int', 'Labelsize', 'Label Size', 2,
       'Size of a label font pixel in pixels (at 720 pixels high; scales with the picture).', 1, 4,
       True).enableExpr = "me.par.Labels != 'off'"
menu_par('Accent', 'Accent', (('orange', 'Orange'), ('blue', 'Blue'), ('white', 'White')), 'orange',
         'Color of the ID labels, the links a beat spawns and the Threshold inside.')

beat = custom(page, 'Toggle', 'Beatlabels', 'Scramble Labels', True,
              'On each beat (input 2), a quarter of the labels scramble and settle again. Beats from raw audio '
              'come from a kick detector and a beat clock (experimental: it can add or miss beats).')
beat.startSection = True
beat.enableExpr = "me.par.Labels != 'off'"
custom(page, 'Toggle', 'Beatlinks', 'Spawn Links', True,
       'On each beat, a quarter of the boxes reach for a random partner; the line fades over the beat.')
custom(page, 'Toggle', 'Beatfill', 'Fill Boxes', True,
       'On a beat, the inside of every box inverts for a moment. A flash: never more often than Flashing '
       'allows (Calm: once a second; at most twice a second at any setting).')
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "On each bar the labels switch between numbers and words (a bar is 4 beats when the input has no "
       "bars). With Fosfora's signal on input 2, a build adds and brightens links, a drop turns the whole "
       "picture over once (a flash, through Flashing; Fosfora's drop detection is experimental) and a new "
       'section makes every box lock on again.')

# ---- Detection --------------------------------------------------------------------------------
mono = mk(comp, monochromeTOP, 'small', -400, 300, [source], 'The picture, gray and small ({} x {}) for detection.'.format(TW, TH),
          outputresolution='custom', resolutionw=TW, resolutionh=TH)
mean = mk(comp, blurTOP, 'local_mean', -200, 450, [mono],
          'The neighborhood of each point (Stand Out compares against it), blurred at a quarter size: it is smooth anyway.',
          size=10, outputresolution='quarter')
state_fb = mk(comp, feedbackTOP, 'state_fb', -200, 150, [mono], "state's previous frame.", top='state')
state = glsl(comp, 'state', 0, 300, [mono, state_fb], src('state.glsl'),
             'The current frame and a slow background (for Movement); advances only when the picture changes.',
             res=(TW, TH), fmt='rgba32float', uClock=(DT, BG_SLOW, BG_FAST, BG_STILL))
mask = glsl(comp, 'mask', 200, 300, [state, mean], src('mask.glsl'),
            'What the detectors look for (Track): movement, or what stands out (lighter, darker), 0-1.',
            res=(TW, TH), fmt='rgba8fixed', uMask=(menu('Track'), 4.0, 6.0))

blurred = mk(comp, blurTOP, 'merge', 400, 450, [mask], 'Blurs the mask so nearby parts become one blob (Merge).',
             size=Expr('2 + 14 * parent().par.Merge'))
black = mk(comp, constantTOP, 'background', 400, 600, comment='Black: the Blob Track TOP thresholds the mask itself.',
           outputresolution='custom', resolutionw=TW, resolutionh=TH, colorr=0, colorg=0, colorb=0)
tracker = mk(comp, blobtrackTOP, 'blobs', 600, 450, [blurred, black],
             "TouchDesigner's Blob Track TOP on the mask (input 2 black: a plain threshold).",
             threshold=par('Threshold'), downloadtype='nextframe', drawblobs=False, minblobsize=0.005,
             maxblobsize=1.0, maxmovedistance=0.15, deleteoverlap=True, deleteoverlaptol=0.6,
             reviveblobs=True, revivetime=0.5, revivedistance=0.1, revivearea=0.5)
info = mk(comp, infoCHOP, 'blob_info', 800, 450, comment="The Blob Track TOP's blobs: num_blobs, then id, u, v, width, height each.",
          op='blobs')
cap = mk(comp, selectCHOP, 'blob_cap', 1000, 450, [info], 'At most {} blobs (the texture below has 5 rows per blob).'.format(MAXIN),
         channames='num_blobs blob[0-{}]:*'.format(MAXIN - 1))
data = mk(comp, choptoTOP, 'blob_data', 1200, 450, comment='The blobs as a texture, one channel per row (32-bit float).',
          chop='blob_cap', dataformat='r', format='mono32float')
# track.glsl's previous frame (bt_clean reads it too). Its input is only its starting state: blank,
# not the detector, which would make a cook loop through bt_clean.
blank = mk(comp, constantTOP, 'track_start', 1600, 0, comment="track's starting state: every slot free.",
           outputresolution='custom', resolutionw=MAXB, resolutionh=3, format='rgba32float',
           colorr=0, colorg=0, colorb=0, alpha=0)
track_fb = mk(comp, feedbackTOP, 'track_fb', 1800, 150, [blank], "track's previous frame.", top='track')
bt_clean = glsl(comp, 'bt_clean', 1400, 450, [data, source, comp.op('track_fb')], src('bt_clean.glsl'),
                'Blobs within Min Size and Max Size and not mostly inside a bigger one; boxed ones rank higher.',
                res=(MAXIN, 2), fmt='rgba32float', uPick=(par('Minsize'), par('Maxsize')))
bt_pick = glsl(comp, 'bt_pick', 1600, 450, [bt_clean], src('bt_pick.glsl'),
               'The biggest of them, as many as track has slots, as a table.',
               res=(MAXB, 2), fmt='rgba32float', uPick=(0, 0, MAXB))

grid_fb = mk(comp, feedbackTOP, 'grid_fb', 400, 150, [mask], "grid's previous frame.", top='grid')
grid = glsl(comp, 'grid', 600, 300, [mask, grid_fb], src('grid.glsl'),
            'GPU Grid: how much of each cell the mask covers, smoothed.',
            res=(GW, GH), fmt='rgba32float', uClock=(DT, 0.12))
peaks = glsl(comp, 'grid_peaks', 800, 300, [grid, source], src('grid_peaks.glsl'),
             'GPU Grid: the cells that are local peaks above Threshold, with their extents.',
             res=(GW, GH), fmt='rgba32float',
             uPeak=(Expr('0.25 * parent().par.Threshold'), par('Minsize'), par('Maxsize')))
grid_pick = glsl(comp, 'grid_pick', 1000, 300, [peaks], src('grid_pick.glsl'),
                 'GPU Grid: the strongest peaks, as many as track has slots, as the same table as bt_pick.',
                 res=(MAXB, 2), fmt='rgba32float', uPick=(0, 0, MAXB))
detector = mk(comp, switchTOP, 'detector', 1800, 300, [bt_pick, grid_pick],
              'The detector chosen (Detector); a Switch TOP cooks only the one it shows.',
              index=menu('Detector'))

match = glsl(comp, 'match', 2000, 150, [detector, track_fb, source], src('match.glsl'),
             'For each box whose blob vanished, the new blob that overlaps it or is close by (to take over).',
             res=(MAXB, 1), fmt='rgba32float')
track = glsl(comp, 'track', 2000, 300, [detector, track_fb, match], src('track.glsl'),
             'Follows each blob by its ID: boxes glide (Smoothing), show once a blob lasts, coast through a '
             'short loss, fade in and out.',
             res=(MAXB, 3), fmt='rgba32float',
             uClock=(DT, Expr('max(0.001, 0.25 * parent().par.Smoothing)'), FADE_IN, FADE_OUT),
             uShow=(SHOW_AFTER, HOLD, par('Maxcount')))
table = glsl(comp, 'table', 2200, 300, [track, source], src('table.glsl'),
             'The boxes showing, packed, each with its four nearest neighbors.',
             res=(MAXB, 3), fmt='rgba32float')

# ---- Audio (input 2) --------------------------------------------------------------------------
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', -200, -350, [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count drop_count section_count')
steps = mk(comp, slopeCHOP, 'steps', 0, -350, [counts], 'Above 0 on the frame a count goes up.', timeslice=True)
beat_step = mk(comp, selectCHOP, 'beat_step', 200, -300, [steps], 'A beat.', channames='beat_count')
envelope = dict(attack=0, peak=1, peaklen=0, sustain=0, release=0)
beat_env = mk(comp, triggerCHOP, 'beat_env', 400, -300, [beat_step],
              'Falls from 1 to 0 over the half second after a beat: scrambles and spawned links.', decay=0.45, **envelope)
bar_step = mk(comp, selectCHOP, 'bar_step', 200, -450, [steps], 'A bar.', channames='bar_count')
bar_env = mk(comp, triggerCHOP, 'bar_env', 400, -450, [bar_step],
             'Falls from 1 to 0 over the 0.3 s after a bar: the labels re-label.', decay=0.3, **envelope)
moment_step = mk(comp, selectCHOP, 'moment_step', 200, -600, [steps], 'A drop, a new section (Fosfora).',
                 channames='drop_count section_count')
moment_env = mk(comp, triggerCHOP, 'moment_env', 400, -600, [moment_step],
                'Falls from 1 to 0 over 1.5 s after a drop or a new section.', decay=1.5, **envelope)
fill_on = mk(comp, mathCHOP, 'fill_trigger', 400, -750, [beat_step], 'Beats that may fill the boxes (Fill Boxes).',
             gain=Expr('1 if parent().par.Beatfill else 0'))
drop_step = mk(comp, selectCHOP, 'drop_step', 200, -900, [steps], 'A drop.', channames='drop_count')
drop_on = mk(comp, mathCHOP, 'drop_trigger', 400, -900, [drop_step], 'Drops that may turn the picture over (Song Moments).',
             gain=Expr('1 if parent().par.Moments else 0'))
flash_in = mk(comp, mergeCHOP, 'flash_in', 600, -800, [fill_on, drop_on], 'Every flash the effect asks for.')
flash_any = mk(comp, mathCHOP, 'flash_any', 800, -800, [flash_in], 'One channel: any flash.', chanop='max')
gate = flash_gate(comp, flash_any, 1000, -800)
budget = mk(comp, triggerCHOP, 'flash_budget', 1400, -650, [gate],
            'After the gate: flashes {calm} s apart at Calm, {other} s otherwise (box fills and drops '
            'share it), so the total stays well under WCAG.'.format(**FLASH_SPACING),
            retrigger=Expr("{calm} if parent().par.Flashing == 'calm' else {other}".format(**FLASH_SPACING)),
            retriggerunit='seconds', attack=0, peak=1, peaklen=0, decay=0, sustain=0,
            release=0)
flash_env = mk(comp, triggerCHOP, 'flash_env', 1600, -800, [budget], "The flash's shape: up at once, down over 0.3 s.",
               decay=0.3, **envelope)
drop_now = mk(comp, selectCHOP, 'drop_now', 1200, -950, [moment_env], 'How recent a drop is.', channames='drop_count')
flash_kind = mk(comp, holdCHOP, 'flash_kind', 1600, -950, [drop_now, budget],
                "1 when the flash that passed the gate was a drop's: the whole picture, not the boxes.")

LOOK = dict(uLook=(par('Linewidth'), par('Labelsize'), menu('Picture'), menu('Inside')),
            uLook2=(menu('Labels'), menu('Links'), menu('Accent'), T),
            uBeat=(Expr("op('beat_env')[0]"), Expr("op('audio')['beat_count']"), Expr("op('audio')['level']"),
                   Expr("op('audio')['source']")),
            uSong=(Expr("op('bar_env')[0]"), Expr("op('audio')['bar_count']"), Expr("op('audio')['build']"),
                   Expr("op('moment_env')['section_count']")),
            uFlash=(Expr("op('flash_env')[0]"), Expr("op('flash_kind')[0]"), Expr("op('moment_env')['drop_count']"),
                    Expr("op('audio')['section_count']")),
            uOn=(par('Beatlabels'), par('Beatlinks'), par('Beatfill'), par('Moments')))
tiles = glsl(comp, 'tiles', 2400, 300, [table, source], '#define TABLE 0\n' + src('boxes.glsl') + src('tiles.glsl'),
             'Which boxes reach into each of 64 x 36 tiles, so the picture visits only those.',
             res=(64, 36), fmt='rgba32float', **LOOK)
draw = glsl(comp, 'draw', 2600, 0, [source, table, mean, tiles],
            font_head() + '#define TABLE 1\n' + src('boxes.glsl') + src('draw.glsl'),
            'The picture, boxes, insides, links and labels in one pass.', **LOOK)

finish_effect(comp, draw, VERSION, page)
comp.op('out_top').nodeX = 2800
comp.op('window').nodeX = 2800
save_effect(comp, _HERE, _ROOT)
