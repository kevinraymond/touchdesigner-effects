"""Build Glitch. Run from a textport: __file__ = '/path/to/build_glitch.py'; exec(open(__file__).read())

Digital corruption on the music. Every beat tears a few thin slivers of rows and glitches a few
blocks, too small an area to be a flash, so they skip the gate (none with Flashing or Bursts Off);
on the one of each bar (Bursts) a big burst: blocks shift, freeze, smear or lose their colors and
rows tear, from one seed per burst so the damage holds still while it lasts. Every burst is a
flash, so all go through flash_gate(). The RGB split stays, kicking on each beat.

The network, left to right:
  picture    source -> hold (the picture from before the burst: a Feedback TOP that follows the
             input between bursts and holds during one) -> glitch (the damage and the split)
  audio      audio_in() -> counts -> steps (Slope CHOP); steady counts the time; beat_on, bar_on,
             steady_on, drop_on pick the bursts asked for -> flash_gate() -> flash_budget ->
             burst (held for Length), burst_count (the seed), drop_kind (a drop's burst); beats
             (or steady ticks with nothing wired) -> beat_pulse -> beat_env, beat_n: the small
             glitches
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.2'
# Steady bursts, and On Beats or On Bars with nothing on input 2, come this many seconds apart.
STEADY = 1.6
# After the gate, bursts at least this far apart (s): Calm a little over its one second, so frame
# jitter can't fit a third swing into any one second; otherwise about 2 a second, leaving headroom
# under WCAG's 3 for what the picture does by itself (as Blob Track does).
FLASH_SPACING = {'calm': 1.1, 'other': 0.55}


def src(name):
    return open(os.path.join(_HERE, 'src', name)).read()


def par(name):
    return Expr('parent().par.{}'.format(name))


README = src('readme.txt').format(v=VERSION, steady=STEADY)
comp, page, source = new_effect(
    'glitch', 'Glitch',
    'Glitch {}: digital corruption in short bursts (blocks shift, freeze, smear, rows tear) on the beat, '
    'with an RGB split.'.format(VERSION),
    README, tags=('glitch', 'audio-reactive'), audio=True, flashing=True,
    # Grass in the wind (TouchDesigner's own sample): motion, so frozen blocks show.
    sample="app.samplesFolder + '/Map/Nature/Movie.2.mp4'")

# ---- Parameters -------------------------------------------------------------------------------
bursts = custom(page, 'Menu', 'Bursts', 'Bursts', None,
                'When a big burst comes. On Bars (on the one of each bar) or On Beats: input 2\'s (with '
                'nothing wired, every {:g} s). Steady: every {:g} s. Off: none. Every burst is a flash, so '
                'Flashing limits how often they come; every beat also glitches a few single blocks, too small '
                'to count as flashes (none with Flashing or Bursts Off).'.format(STEADY, STEADY))
bursts.menuNames = ['beats', 'bars', 'steady', 'off']
bursts.menuLabels = ['On Beats', 'On Bars', 'Steady', 'Off']
bursts.default = bursts.val = 'bars'
custom(page, 'Float', 'Amount', 'Amount', 0.5, 'How much of the picture a burst breaks, 0-1.', 0, 1, True)
custom(page, 'Float', 'Length', 'Length', 0.15, 'How long a burst lasts, in seconds.', 0.05, 0.5, True)
custom(page, 'Int', 'Blocksize', 'Block Size', 32,
       'Size of the blocks a burst breaks, in pixels at 720 high (scales with the picture).', 8, 128, True)
look = custom(page, 'Toggle', 'Blocks', 'Blocks', True,
              'In a burst, blocks shift to another part of the picture, freeze, smear or lose their colors.')
look.startSection = True
custom(page, 'Toggle', 'Tears', 'Tears', True, 'In a burst, bands of rows slip sideways, as if the signal lost sync.')
custom(page, 'Float', 'Split', 'RGB Split', 0.2,
       'How far red and blue drift apart, always (wider in a burst and with loudness on input 2), 0-1.', 0, 1, True)
custom(page, 'Toggle', 'Moments', 'Song Moments', True,
       "With Fosfora's signal on input 2: a build breaks more of the picture as it rises, and a drop breaks "
       "all of it once (Fosfora's drop detection is experimental).")

# ---- Audio (input 2) and the bursts -------------------------------------------------------------
section('audio', 'Audio (input 2): beats, bars, drops or a steady clock ask for bursts')
audio = audio_in(comp, _ROOT)
counts = mk(comp, selectCHOP, 'counts', [audio], 'The running counts: watched, not the one-frame beat.',
            channames='beat_count bar_count drop_count')
steady = mk(comp, constantCHOP, 'steady', comment='Counts {:g} s periods, for Steady bursts.'.format(STEADY),
            const0name='steady_count', const0value=Expr('int(absTime.seconds / {})'.format(STEADY)))
both = mk(comp, mergeCHOP, 'all_counts', [counts, steady], 'Every count a burst may follow.')
steps = mk(comp, slopeCHOP, 'steps', [both], 'Above 0 on the frame a count goes up.', timeslice=True)
WIRED = "op('audio')['source'].eval() > 0"
asks = []
for i, (name, chan, when, what) in enumerate((
        ('beat_on', 'beat_count', "parent().par.Bursts == 'beats' and " + WIRED, 'beats, when Bursts is On Beats'),
        ('bar_on', 'bar_count', "parent().par.Bursts == 'bars' and " + WIRED, 'bars, when Bursts is On Bars'),
        ('steady_on', 'steady_count',
         "parent().par.Bursts == 'steady' or (parent().par.Bursts in ('beats', 'bars') and not " + WIRED + ")",
         'the steady clock, when Bursts is Steady (or On Beats or On Bars with nothing on input 2)'),
        ('drop_on', 'drop_count', "parent().par.Moments and parent().par.Bursts != 'off'", 'drops (Song Moments)'))):
    pick = mk(comp, selectCHOP, name + '_step', [steps], 'Steps of {}.'.format(chan), channames=chan)
    asks.append(mk(comp, mathCHOP, name, [pick], 'Bursts on {}.'.format(what),
                   gain=Expr('1 if ({}) else 0'.format(when))))
ask = mk(comp, mergeCHOP, 'burst_asks', asks, 'Every burst asked for.')
ask_any = mk(comp, mathCHOP, 'burst_any', [ask], 'One channel: any burst.', chanop='max')
section('flash', 'Flashing: bursts no closer together than it allows', lane='audio')
gate = flash_gate(comp, ask_any)
budget = mk(comp, triggerCHOP, 'flash_budget', [gate],
            'After the gate: bursts {calm} s apart at Calm, {other} s otherwise, so the total stays well under '
            'WCAG.'.format(**FLASH_SPACING),
            retrigger=Expr("{calm} if parent().par.Flashing == 'calm' else {other}".format(**FLASH_SPACING)),
            retriggerunit='seconds', attack=0, peak=1, peaklen=0, decay=0, sustain=0, release=0)
section('bursts', "Bursts: each held for Length, numbered for its seed, a drop's marked", lane='audio')
burst = mk(comp, triggerCHOP, 'burst', [budget], 'A burst: 1 for Length seconds, then 0 at once.',
           attack=0, peak=1, peaklen=par('Length'), decay=0, sustain=0, release=0)
burst_count = mk(comp, countCHOP, 'burst_count', [budget], "Bursts so far: each burst's seed.")
drop_step = mk(comp, selectCHOP, 'drop_now', [asks[3]], 'A drop asking for a burst.')
drop_env = mk(comp, triggerCHOP, 'drop_env', [drop_step], 'How recent a drop is (fades over 0.3 s).',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
drop_kind = mk(comp, holdCHOP, 'drop_kind', [drop_env, budget],
               "1 when the burst that passed was a drop's: it breaks the whole picture.")

section('beats', 'Small glitches: every beat tears a few rows and blocks', lane='audio')
BURST = (Expr("op('burst')[0]"), Expr("op('burst_count')[0]"), Expr("op('drop_kind')[0]"), Expr("op('audio')['build']"))
# Every beat (or the steady clock with nothing on input 2): a few single blocks and a kick of the
# split, too small an area to be a flash, so they skip the gate; none with Flashing or Bursts Off.
tick = mk(comp, mathCHOP, 'steady_tick', [asks[2].inputs[0]], 'Steady ticks, only while input 2 is empty.',
          gain=Expr('0 if ' + WIRED + ' else 1'))
beat_in = mk(comp, mergeCHOP, 'beat_in', [asks[0].inputs[0], tick], 'Beats, or steady ticks.')
beat_pick = mk(comp, mathCHOP, 'beat_pulse', [beat_in], 'One channel: a beat, for the small glitches.',
               chanop='max')
beat_env = mk(comp, triggerCHOP, 'beat_env', [beat_pick], 'Falls from 1 to 0 over the 0.3 s after a beat.',
              attack=0, peak=1, peaklen=0, decay=0.3, sustain=0, release=0)
beat_n = mk(comp, countCHOP, 'beat_n', [beat_pick], "Beats so far: each beat's seed.")
BEAT = (Expr("op('beat_env')[0]"), Expr("op('beat_n')[0]"),
        Expr("1 if parent().par.Flashing != 'off' and parent().par.Bursts != 'off' else 0"))

# ---- Picture ----------------------------------------------------------------------------------
section('glitch', 'The glitch: the picture held through a burst, then broken')
hold_fb = mk(comp, feedbackTOP, 'hold_fb', [source], "hold's previous frame.", top='hold')
hold = glsl(comp, 'hold', [source, hold_fb], src('hold.glsl'),
            'The picture from just before the burst: follows the input between bursts, holds during one.',
            uBurst=BURST)
glitch = glsl(comp, 'glitch', [source, hold], src('glitch.glsl'),
              "The burst's damage (blocks, tears) and the RGB split, in one pass.",
              uBurst=BURST, uLook=(par('Amount'), par('Blocksize'), par('Split'), Expr("op('audio')['level']")),
              uOn=(par('Blocks'), par('Tears'), par('Moments')), uBeat=BEAT)

finish_effect(comp, glitch, VERSION, page)
save_effect(comp, _HERE, _ROOT)
