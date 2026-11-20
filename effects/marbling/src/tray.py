# Marbling (touchdesigner-effects, MIT): the tray. Script CHOP callbacks that keep the list of tools now on the size
# (a marbler's bath): an ink drop on each beat of input 2 and a comb stroke on each bar, in the classic order (gel-git
# across, gel-git back, nonpareil, bouquet), each tool rising as it is made, holding for some bars and relaxing to
# nothing, so the picture comes back. The tools are the whole of the marbling: the shaders undo them at every pixel
# each frame (S. Lu, A. Jaffer, X. Jin, H. Zhao and X. Mao, "Mathematical Marbling", IEEE CG&A 32(6), 2012), and
# nothing else carries from frame to frame.
#
# Out: one sample per tool, newest first, N in all (the rest kind 0), one channel per field, in this order (the
# shaders take them four at a time as uniform arrays):
#   kind    0 none, 1 drop, 2 comb, 3 wave (a bouquet's comb is drawn along a wave: a comb and a wave together)
#   t0      when it was made, on the shaders' clock (absTime.seconds wrapped every CLOCK seconds)
#   rise    seconds it takes to spread (a drop) or to be drawn (a stroke)
#   hold    seconds from when it was made until it starts to relax
#   relax   seconds it takes to relax
#   a..e    a drop: a, b its center (0-1 across and up the picture), c its size for the loudness when it fell
#           (times Drop Size in the shader). A comb: a, b the direction it is drawn in, c its tines' spacing, d their
#           offset (both in frame heights), e its pull (times Comb in the shader). A wave: a, b the direction it
#           pushes along, c its height, d its length (frame heights), e its phase
#   serial  a drop's number, from 1: its ink in the ink ring (serial mod N) and in the palette
#
# Input 1 is the effect's audio (lib audio_in()), input 2 a count that goes up every IDLE seconds while nothing is on
# input 2, which stands in for the beats then. A tray is four bars; Pattern says how many of its strokes are drawn.
# State lives in _state, by operator id, so nothing of a run is saved into the .tox. Reset (a Parameter Execute DAT)
# stores a new count in this operator's storage, and the next cook starts a clean tray.

import math

N = 64                    # tools at once (the tools texture's width); a drop waits while the tray is full
CLOCK = 16384             # the shaders' clock wraps here (lib clock_seconds())
FIELDS = ('kind', 't0', 'rise', 'hold', 'relax', 'a', 'b', 'c', 'd', 'e', 'serial')
DROP_GAP = 1.0 / 3.0      # drops at most 3 a second
STROKE_GAP = 2.0          # strokes at most one every 2 s
SPREAD = 0.25             # seconds a drop takes to spread
STROKE = (0.3, 1.0)       # a stroke is drawn over a beat, within these seconds
IDLE = 0.5                # with nothing on input 2: a beat every IDLE seconds (120 BPM), a bar every 4
WIDE = (0.1, 0.5)         # gel-git's tine spacing at Spacing 0 and 1 (frame heights); nonpareil's is a quarter
SECTION_RELAX = 1.0       # a new section (Fosfora): every tool relaxes over this many bars
R2 = 1.32471795724474602596   # the plastic number: the R2 sequence's (M. Roberts, 2018)

_state = {}


def onSetupParameters(scriptOp):
    return


def onPulse(par):
    return


def onGetCookLevel(scriptOp):
    return CookLevel.WHEN_USED


def _fresh(reset):
    return dict(reset=reset, tools=[], beat=None, bar=None, section=None, beats=0, ndrop=0, step=0, trays=0,
                last_drop=-1e9, last_stroke=-1e9)


def _relax_all(s, now, seconds):
    for t in s['tools']:
        age = now - t['made']
        t['hold'] = min(t['hold'], age)
        t['relax'] = min(t['relax'], seconds)


def _drop(s, now, par, level, period):
    # Over the tray by the R2 sequence, so each drop lands well away from the last few and they cover it evenly.
    k = s['ndrop']
    s['ndrop'] += 1
    x = (0.5 + k / R2) % 1.0
    y = 0.05 + 0.9 * ((0.5 + k / (R2 * R2)) % 1.0)
    loud = float(par.Loudness)
    size = (1.0 - loud) + loud * min(max(level, 0.0), 1.0)
    bar = 4.0 * period
    s['tools'].append(dict(kind=1, made=now, rise=SPREAD, hold=float(par.Hold) * bar, relax=float(par.Relax) * bar,
                           v=(x, y, 0.3 + 0.7 * size, 0.0, 0.0), serial=s['ndrop']))


def _stroke(s, now, par, period):
    step = s['step'] % 4
    s['step'] += 1
    if step == 0:
        s['trays'] += 1
    if step >= par.Pattern.menuIndex:
        return
    bar = 4.0 * period
    life = dict(made=now, rise=min(max(period, STROKE[0]), STROKE[1]), hold=float(par.Hold) * bar,
                relax=float(par.Relax) * bar, serial=0)
    wide = WIDE[0] + (WIDE[1] - WIDE[0]) * float(par.Spacing)
    turn = (s['trays'] % 2) * math.pi / 2     # trays take turns across and down

    def way(angle):
        return math.cos(angle), math.sin(angle)

    if step == 0:      # gel-git: a comb across the tray
        s['tools'].append(dict(kind=2, v=way(turn) + (wide, 0.0, 1.0), **life))
    elif step == 1:    # and back, its tines between the first pass's
        s['tools'].append(dict(kind=2, v=way(turn + math.pi) + (wide, wide / 2, 1.0), **life))
    elif step == 2:    # nonpareil: a fine comb at right angles
        s['tools'].append(dict(kind=2, v=way(turn - math.pi / 2) + (wide / 4, 0.0, 0.5), **life))
    else:              # bouquet: a comb drawn along a wave
        s['tools'].append(dict(kind=2, v=way(turn + math.pi / 2) + (wide, wide / 4, 0.7), **life))
        s['tools'].append(dict(kind=3, v=way(turn + math.pi / 2) + (0.3 * wide, 2.0 * wide, 0.0), **life))


def onCook(scriptOp):
    now = absTime.seconds
    par = scriptOp.parent().par
    reset = scriptOp.fetch('reset', 0, storeDefault=False)
    s = _state.get(scriptOp.id)
    if s is None or s['reset'] != reset:
        s = _state[scriptOp.id] = _fresh(reset)
    audio, idle = scriptOp.inputs[0], scriptOp.inputs[1]
    if audio['source'][0] > 0:
        beat, bar, section = audio['beat_count'][0], audio['bar_count'][0], audio['section_count'][0]
        period = max(float(audio['beat_period'][0]), 0.2)
        level = float(audio['level'][0])
    else:
        tick = int(idle['idle'][0])
        beat, bar, section, period, level = tick, tick // 4, 0, IDLE, 0.6
    # A count that changes is an event, however far it moved: a signal wired in mid-song jumps by every beat so far.
    new_beat = s['beat'] is not None and beat != s['beat']
    new_bar = s['bar'] is not None and bar != s['bar']
    if s['section'] is not None and section != s['section']:
        _relax_all(s, now, SECTION_RELAX * 4.0 * period)
        s['step'] = 0
    s['beat'], s['bar'], s['section'] = beat, bar, section
    s['tools'] = [t for t in s['tools'] if now - t['made'] < t['hold'] + t['relax']]
    if new_beat:
        s['beats'] += 1
    every = par.Dropevery.menuIndex
    due = new_bar if every == 2 else new_beat and (every == 0 or s['beats'] % 2 == 1)
    if (due and par.Dropsize > 0 and now - s['last_drop'] >= DROP_GAP and len(s['tools']) < N - 2):
        _drop(s, now, par, level, period)
        s['last_drop'] = now
    if new_bar and now - s['last_stroke'] >= STROKE_GAP and len(s['tools']) < N - 1:
        _stroke(s, now, par, period)
        s['last_stroke'] = now
    scriptOp.clear()
    scriptOp.numSamples = N
    rows = list(reversed(s['tools']))[:N]
    for f, name in enumerate(FIELDS):
        chan = scriptOp.appendChan(name)
        vals = [0.0] * N
        for i, t in enumerate(rows):
            if name == 'kind':
                vals[i] = float(t['kind'])
            elif name == 't0':
                vals[i] = t['made'] % CLOCK
            elif name in ('rise', 'hold', 'relax'):
                vals[i] = t[name]
            elif name == 'serial':
                vals[i] = float(t['serial'])
            else:
                vals[i] = t['v'][f - 5]
        chan.vals = vals
