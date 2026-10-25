"""Build Datamosh (datamosh-style). Run from a textport:
__file__ = '/path/to/touchdesigner-effects/effects/datamosh/build_datamosh.py'; exec(open(__file__).read())

The picture is a small decoder fed back into itself: each new input frame moves it by the
motion this effect estimates (Smear: Lucas-Kanade optical flow; Blocks: 16 px block matching)
and adds part of the residual. Cuts, beats, builds and Hold withhold the keyframe; recovery and
keyframes fade. src/mosh.glsl says how; the README below says what a user sees.
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.2.1'
# Unwired, the effect cuts every SAMPLE_CUT seconds between two of TouchDesigner's sample pictures,
# since datamosh needs a cut to show: grass swaying in front of a colorful building, and jellybeans
# under a slow drift, turn and zoom (whole-picture motion for the old shot to be dragged by).
MOVIE = "app.samplesFolder + '/Map/Nature/Movie.2.mp4'"
STILL = "app.samplesFolder + '/Map/Jellybeans.1.jpg'"
SAMPLE_CUT = 6
BLOCK = 16            # macroblock size in input pixels (Blocks)
NEW_FRAME = 2e-5      # mean |luma change| at 1/8 that makes a new input frame
CUT_FLOOR = 0.02      # never call a smaller change a cut...
CUT_RATIO = 4.0       # ...and only one this many times the running mean of the changes between frames...
CUT_GAP = 0.25        # ...and no sooner than this many seconds after the last one
SKIP_HOLD = 0.2       # seconds a skipped keyframe holds fully...
SKIP_RELEASE = 0.35   # ...and lets go over
SKIP_PUSH = 1.5       # during a skip the held motion pushes this much further (1 + SKIP_PUSH x the skip)
# A beat's surge at Beat Surge 1: corrections stop, the motion pushes 1 + SURGE_PUSH times as far and
# the whole picture blooms, zooming out from the middle at up to BLOOM a second, all easing off over
# SURGE_TIME seconds; as it fades the picture catches up with the input at up to CATCH a second, so it
# blooms on the beat and comes back.
SURGE_PUSH, SURGE_TIME, BLOOM, CATCH = 2.0, 0.35, 4.0, 10.0
P = 'parent().par.'


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


SUMMARY = ('Datamosh {}: datamosh-style smear. The picture is pushed around by its own motion while '
           'keyframes are withheld at cuts, beats and builds, then fades back.').format(VERSION)
README = '''Datamosh {version}: a datamosh-style effect (touchdesigner-effects, MIT).
{docs}

WHAT IT DOES
Datamoshing is a glitch-art technique: a compressed video stores a full picture (a keyframe)
only now and then and, in between, mostly how the picture moves. Delete the keyframe at a cut
and the new shot's motion moves the old shot's picture, so the old shot smears and melts into
the new one until the next keyframe.

This effect imitates that look live. It does not edit a real codec stream (no I-frames are
removed from a file). It estimates the
motion itself on the GPU and runs its own small "decoder", from which it withholds corrections.

Wire a TOP into input 1; until you do, it cuts between two of TouchDesigner's sample pictures
every {cut} seconds, so there is a cut to mosh. Moving pictures and hard cuts mosh best. A clip
slower than the project (16 fps in a 60 fps project) is fine: the picture moves only when the
input brings a new frame. Open Window shows it in its own window (Full Screen fills a display);
Esc closes it.

MODES
  Smear   optical flow per pixel (Lucas-Kanade, in this effect's own shader): liquid smears.
  Blocks  one motion vector per 16 px block, as a codec finds them, a coarse residual, frozen
          blocks, and keyframes that sweep across in block columns.

PARAMETERS (first page; Alt+hover shows each one's help)
  Mode, Mosh, Motion, Recovery, Chroma, Frozen Blocks, Hold: how much it smears and how.
  Mosh Cuts, Keyframe, Fade, Skip Keyframe: what happens at a cut, or when you ask.
  Beat Surge, Skip On, Level, Song Structure: what input 2 does.
  Flashing, Open Window, Full Screen, Display: flashes and the full-size window.

INPUT 2 (optional): audio or beat channels
  Any audio (an Audio File In or Audio Device In CHOP) or analysis channels: a beat blooms the
  picture, smearing it out from the middle, and it catches up (Beat Surge; as often as Flashing
  allows); every bar (or beat) skips a keyframe, the held motion blooming further (Skip On); and
  loudness adds to Mosh (Level).
  Fosfora's signal (fosfora_signal.tox, https://github.com/kevinraymond/fosfora) adds the
  song's shape (Song Structure): through a build the keyframes are withheld and the mosh grows,
  the drop brings a keyframe that fades it clean (Fosfora marks drops as experimental), and a
  new section brings a keyframe. Bars follow Fosfora's downbeats.
  Nothing wired: no surges and no skips; the effect still moshes the input's cuts and its own Mosh.

FLASHING
  Keyframes, skipped keyframes and a beat's bloom change the whole picture, so they count as
  flashes. Flashing Off lets none through: no blooms or skips on beats, no keyframes from Fosfora's
  drops and sections, and the Keyframe and Skip Keyframe pulses do nothing. Calm, the default,
  allows at most one of each a second (a bloom about every other beat at dance tempos); Up to 3
  per second is the WCAG 2.3.1 limit (a bloom on every beat up to 180 BPM). Even then nothing
  cuts: keyframes fade over Fade, skips smear, a bloom eases out and back, recovery fades, and a
  cut in the input is held. The limits were measured on the output (docs page, Accessibility).

EXPERIMENTAL
  Cut detection is a heuristic (a change several times the usual one between frames): it can
  miss a soft cut, or take a sudden change of light in the input for one. Mosh Cuts turns it off.
  Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo:
  it can still add or miss beats, and which beat starts a bar is a guess.

INSIDE
  GLSL TOPs do the work: luma at 1/2, 1/4 and 1/8 (lum2, lum4, lum8), the new-frame and cut test
  (change, clock), optical flow (lk8, lk4), block matching (bm_*), the motion field (motion) and
  the decoder (mosh), each stateful one fed back into itself through a Feedback TOP. CHOPs turn
  input 2's counts into skips and keyframes, limit them in flash_limit and flash, and shape them
  (beat_env, skip_env, key_env). Per frame, Python runs only in the audio input's Script CHOP and in
  parameter expressions.

CREDITS
- Datamoshing is the glitch art of deleting a compressed video's keyframes, so one shot's motion
  drags the last shot's pixels. This is datamosh-style: it models what a decoder does with missing
  keyframes, with no codec.
- Smear: Lucas-Kanade optical flow, written from B. D. Lucas and T. Kanade, "An Iterative Image
  Registration Technique with an Application to Stereo Vision" (1981).
- Blocks: block matching as a video encoder does it, a full search refined to a quarter pixel as in
  H.264. olegchomp's tdx-datamosh (tdx-rnd), read during the survey, models macroblocks too; none
  of its code was used (it states no license).
- Resampling: a Catmull-Rom bicubic (Catmull and Rom, 1974), clamped to its neighbors.
- Dice: Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
- Read during the survey, not used: VARIMOSH, the Palette's opticalFlow (its license keeps it out
  of a shared .tox).
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness;
  the beat clock takes its tempo from the gaps between kicks, each voting for the beat lengths it
  is a whole multiple of: inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic
  Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001).
  Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else is written for this library. MIT.

UPDATING
  Dragging a .tox in embeds a copy, so a new release doesn't reach it on its own. To update,
  delete this copy and drag in the new datamosh.tox from
  {download}
  or point the COMP's External .tox at a downloaded file.

Built by effects/datamosh/build_datamosh.py; the .tox is generated, never edited by hand.
'''.format(version=VERSION, cut=SAMPLE_CUT, docs=DOCS_URL.format('datamosh'), download=DOWNLOAD_URL.format('datamosh'))


def menu(page, name, label, items, default, help_text):
    p = custom(page, 'Menu', name, label, None, help_text)
    p.menuNames = [n for n, _ in items]
    p.menuLabels = [lab for _, lab in items]
    p.default = p.val = default
    return p


comp, page, source = new_effect('datamosh', 'Datamosh-style', SUMMARY, README,
                                tags=('datamosh', 'glitch', 'feedback', 'audio-reactive'),
                                audio=True, flashing=True, sample=MOVIE)

# Unwired, a cut every SAMPLE_CUT seconds between the sample movie and a moving still.
T = 'absTime.seconds'
still = mk(comp, moviefileinTOP, 'sample2', -1000, -150, comment='The second sample picture (unwired only).',
           file=Expr(STILL))
drift = mk(comp, transformTOP, 'sample2_drift', -1000, -300, [still],
           'The still drifting, turning and zooming slowly, so it moves the old shot after a cut.',
           tx=Expr('0.05 * math.sin({} * 0.7)'.format(T)), ty=Expr('0.03 * math.sin({} * 0.5)'.format(T)),
           rotate=Expr('8 * math.sin({} * 0.4)'.format(T)), sx=Expr('1.3 + 0.1 * math.sin({} * 0.6)'.format(T)),
           sy=Expr('1.3 + 0.1 * math.sin({} * 0.6)'.format(T)), extend='mirror', outputresolution='custom',
           resolutionw=1280, resolutionh=720, fillmode='outside')
samples = mk(comp, switchTOP, 'samples', -600, -200, [comp.op('sample'), drift],
             'Unwired: cuts between the two sample pictures every {} seconds.'.format(SAMPLE_CUT),
             index=Expr('int({} / {}) % 2'.format(T, SAMPLE_CUT)), outputresolution='custom', resolutionw=1280,
             resolutionh=720)
source.inputConnectors[1].connect(samples)

# ---- Parameters ------------------------------------------------------------------------------
menu(page, 'Mode', 'Mode', (('smear', 'Smear'), ('blocks', 'Blocks')), 'smear',
     'How the picture moves. Smear: optical flow per pixel, liquid. Blocks: one motion vector per 16 px '
     'block, as a codec finds them, with a coarse residual and frozen blocks.')
custom(page, 'Float', 'Mosh', 'Mosh', 0.5,
       'How much of each new frame\'s correction the picture leaves out. 0: every correction arrives, so it moshes '
       'only at cuts, skips, Hold or with Motion away from 1; 1: the motion alone moves it and only Recovery brings '
       'it back.', 0, 1, True)
custom(page, 'Float', 'Motion', 'Motion', 1.2,
       'How far each frame\'s motion pushes the picture. Above 1 it runs ahead of the movement and smears; '
       'below 1 it lags behind.', 0, 3, True).clampMax = False
custom(page, 'Float', 'Recovery', 'Recovery', 3.0,
       'Seconds the picture takes to fade back to the input after a mosh. Longer keeps smears around.',
       0.25, 10, True).clampMax = False
custom(page, 'Float', 'Chroma', 'Chroma', 0.0,
       'Lets color smear apart from brightness: at 1 brightness follows the input and only color moshes.',
       0, 1, True)
frozen = custom(page, 'Float', 'Frozen', 'Frozen Blocks', 0.03,
                'Blocks only: the share of blocks that miss each update and stay where they were (more during a '
                'skipped keyframe).', 0, 1, True)
frozen.enableExpr = "me.par.Mode == 'blocks'"
custom(page, 'Toggle', 'Hold', 'Hold', False,
       'Freeze the motion and keep applying it, with no corrections: what was moving keeps flowing the same way '
       '(the "bloom" mosh) and what was still stays put, until Hold is off; then it recovers.')
cuts = custom(page, 'Toggle', 'Moshcuts', 'Mosh Cuts', True,
              'At a cut in the input, drop the keyframe: the new shot\'s motion pushes the old picture around '
              'until it recovers. Off: cuts pass through. Cut detection is a heuristic (experimental).')
cuts.startSection = True
custom(page, 'Pulse', 'Keyframe', 'Keyframe',  None,
       'Send a keyframe: the picture fades back to the input over Fade (Blocks: in a sweep of block columns). '
       'Counts as a flash: limited by Flashing, none when it is Off.')
custom(page, 'Float', 'Fade', 'Fade', 1.0, 'Seconds a keyframe takes to fade the picture back to the input.',
       0.25, 5, True).clampMax = False
custom(page, 'Pulse', 'Skip', 'Skip Keyframe', None,
       'Skip a keyframe now: for about half a second the motion holds and no corrections arrive, so the picture '
       'smears along its last movement, then recovers. Counts as a flash: limited by Flashing, none when Off.')
skipon = menu(page, 'Skipon', 'Skip On', (('off', 'Off'), ('beats', 'Every Beat'), ('bars', 'Every Bar')), 'bars',
              'Which pulse on input 2 skips a keyframe (as Skip Keyframe does): every beat, every bar (Fosfora\'s '
              'downbeats, else every 4th beat), or none. Limited by Flashing: Calm allows one a second. Beats '
              'found in raw audio are experimental: they can be added or missed, and which beat starts a bar is '
              'a guess.')
skipon.startSection = True
custom(page, 'Float', 'Surge', 'Beat Surge', 0.5,
       'On each beat of input 2 the picture blooms: for a moment no corrections arrive, it zooms out from the '
       'middle and its motion runs further ahead, then it catches up with the input. It changes the whole '
       'picture, so it counts as a flash: Calm allows one a second (about every other beat), Up to 3 per '
       'second every beat at dance tempos, Off none. 0 turns it off.', 0, 1, True)
custom(page, 'Float', 'Level', 'Level', 0.3, 'How much loudness on input 2 adds to Mosh: louder passages smear more.',
       0, 1, True)
custom(page, 'Toggle', 'Songstruct', 'Song Structure', True,
       'With Fosfora\'s signal on input 2: a build withholds keyframes so the mosh grows, the drop brings a '
       'keyframe that fades it clean (Fosfora\'s drops are experimental), a new section brings one too. '
       'Other inputs carry no song structure, so this does nothing with them.')

# ---- Events: input 2 and the pulses become skips and keyframes, limited by Flashing ---------------
audio = audio_in(comp, _ROOT, x=-600, y=-450)
counts = mk(comp, selectCHOP, 'counts', 0, -450, [audio], 'Input 2\'s counts: beats, bars, drops, sections.',
            channames='beat_count bar_count drop_count section_count')
steps = mk(comp, logicCHOP, 'steps', 200, -450, [counts], '1 on the frame a count goes up.', convert='valchange')
skip_audio = mk(comp, selectCHOP, 'skip_audio', 400, -400, [steps], 'The beat or bar that skips a keyframe (Skip On).',
                channames=Expr("'beat_count' if parent().par.Skipon == 'beats' else 'bar_count'"),
                renamefrom='*', renameto='skip')
skip_on = mk(comp, mathCHOP, 'skip_on', 600, -400, [skip_audio], 'Nothing when Skip On is Off.',
             gain=Expr("0 if parent().par.Skipon == 'off' else 1"))
key_audio = mk(comp, selectCHOP, 'key_audio', 400, -550, [steps], "Fosfora's drops and section changes.",
               channames='drop_count section_count')
key_on = mk(comp, mathCHOP, 'key_on', 600, -550, [key_audio], 'Either one, when Song Structure is on.',
            chanop='max', gain=Expr(P + 'Songstruct'))
key_named = mk(comp, renameCHOP, 'key_named', 800, -550, [key_on], 'Named key.', renamefrom='*', renameto='key')
pulse = dict(attack=0, peak=1, peaklen=0, decay=0, sustain=1, release=0)
skip_pulse = mk(comp, triggerCHOP, 'skip_pulse', 400, -700, comment='Skip Keyframe (pulsed by pulses).',
                channame='skip', **pulse)
key_pulse = mk(comp, triggerCHOP, 'key_pulse', 400, -850, comment='Keyframe (pulsed by pulses).',
               channame='key', **pulse)
skip_any = mk(comp, mathCHOP, 'skip_any', 800, -700, [skip_on, skip_pulse], 'A skip from input 2 or the pulse.',
              chopop='max')
key_any = mk(comp, mathCHOP, 'key_any', 1000, -700, [key_named, key_pulse], 'A keyframe from input 2 or the pulse.',
             chopop='max')
surge_on = mk(comp, selectCHOP, 'surge_on', 1000, -300, [steps], "A beat: its surge (a bloom of the whole picture, so a "
              'flash too).', channames='beat_count', renamefrom='*', renameto='surge')
events = mk(comp, mergeCHOP, 'events', 1200, -550, [skip_any, key_any, surge_on],
            'Skips, keyframes and surges, before the limit.')
flash = flash_gate(comp, events, 1400, -550)
skip_sel = mk(comp, selectCHOP, 'skip_sel', 1800, -450, [flash], 'Skips that passed the limit.', channames='skip')
mk(comp, triggerCHOP, 'skip_env', 2000, -450, [skip_sel],
   'A skip\'s envelope: holds, then lets go. mosh and motion read it.', attack=0, attackunit='seconds', peak=1,
   peaklen=SKIP_HOLD, peaklenunit='seconds', decay=SKIP_RELEASE, decayunit='seconds', dshape='easeout', sustain=0,
   release=0, multitrigger='restart')
beat_sel = mk(comp, selectCHOP, 'beat_sel', 1800, -300, [flash], 'Surges that passed the limit.', channames='surge')
mk(comp, triggerCHOP, 'beat_env', 2000, -300, [beat_sel],
   "A beat's surge: 1 at the beat, gone {:g} s later. mosh reads it.".format(SURGE_TIME), attack=0, peak=1,
   peaklen=0, decay=SURGE_TIME, decayunit='seconds', dshape='easeout', sustain=0, release=0)
key_sel = mk(comp, selectCHOP, 'key_sel', 1800, -600, [flash], 'Keyframes that passed the limit.', channames='key')
mk(comp, triggerCHOP, 'key_env', 2000, -600, [key_sel], "A keyframe's progress, 0 to 1 over Fade. mosh reads it.",
   attack=Expr(P + 'Fade'), attackunit='seconds', ashape='linear', peak=1, peaklen=0, decay=0, sustain=0, release=0,
   multitrigger='restart')
pulses = mk(comp, parameterexecuteDAT, 'pulses', -600, 250, comment='Keyframe and Skip Keyframe pulse their Trigger CHOPs.')
pulses.text = ('def onPulse(par):\n'
               "    if par.name == 'Keyframe':\n"
               "        op('key_pulse').par.trigger.pulse()\n"
               "    elif par.name == 'Skip':\n"
               "        op('skip_pulse').par.trigger.pulse()\n")
setpars(pulses, op='..', pars='Keyframe Skip', onpulse=True, valuechange=False)

# ---- Analysis: new frames, cuts, motion -----------------------------------------------------------
# The luma pyramid, the new-frame and cut test, and the optical flow (Smear): lib optical_flow().
mo = optical_flow(comp, _ROOT, source, levels=(8, 4, 2), new_frame=NEW_FRAME, cut=(CUT_FLOOR, CUT_RATIO, CUT_GAP))
lum = {k: mo['lum{}'.format(k)] for k in (8, 4, 2)}
prevlum = {k: mo['lum{}p'.format(k)] for k in (8, 4, 2)}
clock, lk4 = mo['clock'], mo['lk4']
# Block matching: every size follows an input through the resolution menu (no expression reads another
# operator's size: after a first cook, that kept the unwired sample movie cooking while nothing used the effect).
R_COARSE, R_FINE = 6, 2
sad_c = glsl(comp, 'bm_sad_c', 0, 450, [lum[4], prevlum[4], lum[4]], src('bm_sad.glsl'),
             'Block costs at 1/4, every offset within 24 px: one 16 x 16 tile per block (Blocks).', fmt='rgba32float',
             uP=(R_COARSE, BLOCK // 4, 0, BLOCK))
setpars(sad_c, outputresolution='4x')
min_c = glsl(comp, 'bm_min_c', 200, 450, [lum[4], sad_c, source], src('bm_min.glsl'),
             'The best coarse offset, one pixel per block (Blocks).', fmt='rgba32float',
             uP=(R_COARSE, 0.004, 0, 4), uQ=(BLOCK, 1))
setpars(min_c, outputresolution='quarter')
sad_f = glsl(comp, 'bm_sad_f', 0, 300, [lum[2], prevlum[2], min_c], src('bm_sad.glsl'),
             'Block costs at 1/2 around the coarse offset, within 2 px: one 8 x 8 tile per block (Blocks).',
             fmt='rgba32float', uP=(R_FINE, BLOCK // 2, 1, BLOCK // 2))
min_f = glsl(comp, 'bm_min_f', 200, 300, [lum[4], sad_f, source], src('bm_min.glsl'),
             'Block vectors to a quarter pixel, at 1/4 size like the flow (Blocks).', fmt='rgba32float',
             uP=(R_FINE, 0.004, 1, 2), uQ=(BLOCK // 2, BLOCK // 4))
motion_in = mk(comp, switchTOP, 'motion_in', 400, 500, [lk4, min_f], 'Flow or block vectors; only the chosen one cooks.',
               index=Expr(P + 'Mode.menuIndex'))
motion_fb = mk(comp, feedbackTOP, 'motion_fb', 400, 650, [motion_in], 'The last motion field.', top='motion')
motion = glsl(comp, 'motion', 600, 500, [motion_in, motion_fb, clock], src('motion.glsl'),
              'The motion the decoder applies; held between new frames, at cuts, on Hold and skips.',
              fmt='rgba32float',
              uM=(Expr(P + 'Mode.menuIndex'), Expr(P + 'Hold'), Expr("op('skip_env')['skip']"), 0.25),
              uM2=(0.65,))

# ---- The decoder ------------------------------------------------------------------------------
prev = mk(comp, cacheTOP, 'prev', -200, -150, [source], 'The previous input frame: what the residual is measured '
          'against.', cachesize=2, outputindex=-1)
mosh_fb = mk(comp, feedbackTOP, 'mosh_fb', 200, 150, [source], 'The picture last frame.', top='mosh')
mosh = glsl(comp, 'mosh', 600, 0, [source, mosh_fb, prev, motion, clock],
            lib_glsl(_ROOT, 'common.glsl') + src('mosh.glsl'),
            'The decoder: moves its own picture by the motion, adds part of the residual, fades back.',
            fmt='rgba16float',
            uP1=(Expr(P + 'Mode.menuIndex'), Expr(P + 'Mosh'), Expr(P + 'Motion'), Expr(P + 'Recovery')),
            uP2=(Expr(P + 'Chroma'), Expr(P + 'Hold'), Expr(P + 'Frozen'), Expr(P + 'Moshcuts')),
            uP3=(Expr(P + 'Fade'), Expr(P + 'Level'), Expr(P + 'Songstruct'), BLOCK),
            uBeat=(Expr("op('beat_env')[0]"), Expr(P + 'Surge')),
            uPush=(SURGE_PUSH, BLOOM, CATCH, SKIP_PUSH),
            uAud=(Expr("op('audio')['level']"), Expr("op('audio')['build']"), Expr("op('skip_env')['skip']"),
                  Expr("op('key_env')['key']")),
            uT=(clock_seconds(), Expr('absTime.stepSeconds')))

finish_effect(comp, mosh, VERSION, page)
save_effect(comp, _HERE, _ROOT)
