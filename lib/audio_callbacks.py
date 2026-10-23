# Script CHOP callbacks for an effect's audio input (lib/tox_build.py audio_in() puts this text
# in the Script CHOP's docked callbacks DAT). Whatever is wired into input 2 becomes the same
# three channels, which the rest of the effect reads:
#
#   beat        1 on the frame a beat arrives, else 0
#   beat_count  beats so far (watch this one for logic: a one-frame pulse can be missed)
#   level       0..1, how loud right now
#   source      0 nothing wired, 1 raw audio, 2 analysis channels
#
# Input 2 may carry:
#   raw audio (an Audio File In or Audio Device In CHOP, at an audio rate): the effect's own
#     low-band level (input 2 of this CHOP: low-pass then RMS, done by operators) drives level,
#     and a beat is a jump in it above its recent average;
#   analysis channels, found by name, first match wins:
#     beats from beat_count (Fosfora), or the rising edge of beat, kick or onset (Fosfora,
#     TouchDesigner's audioAnalysis and Essentia rhythm CHOPs);
#     level from energy, level, low, bass or rms;
#   nothing: level 0 and no beats, and the effect still works.
# Timing is judged in seconds, so dropped frames don't change it. State lives in _state, by
# operator id: not in storage, so nothing of a run is saved into the .tox.

BEAT_COUNT = ('beat_count',)
BEAT_PULSE = ('beat', 'kick', 'onset')
LEVEL = ('energy', 'level', 'low', 'bass', 'rms')
MIN_GAP = 0.2          # seconds between two detected beats in raw audio (at most 300 a minute)
JUMP = 1.5             # a beat: the low band at least this many times its recent average
PEAK_FALL = 4.0        # seconds for the raw level's running peak to fall by half

_state = {}


def onSetupParameters(scriptOp):
    return


def onPulse(par):
    return


def onGetCookLevel(scriptOp):
    return CookLevel.WHEN_USED


def _first(names, wanted):
    for w in wanted:
        if w in names:
            return w
    return None


def onCook(scriptOp):
    now = absTime.seconds
    s = _state.setdefault(scriptOp.id, dict(count=0, last=None, prev_pulse=0.0, prev_count=None,
                                           avg=0.0, peak=1e-4, level=0.0, last_beat=-1e9))
    dt = 0.0 if s['last'] is None else min(max(now - s['last'], 0.0), 0.5)
    s['last'] = now
    beat, source = 0, 0
    inp = scriptOp.inputs[0] if scriptOp.inputs else None
    if inp is not None and inp.numChans:
        if inp.rate >= 1000:
            source = 1
            low = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
            x = float(low[0][-1]) if low is not None and low.numChans else 0.0
            s['peak'] = max(x, s['peak'] * 0.5 ** (dt / PEAK_FALL), 1e-4)
            if x > s['avg'] * JUMP and x > 0.1 * s['peak'] and now - s['last_beat'] >= MIN_GAP:
                beat, s['last_beat'] = 1, now
            s['avg'] += (x - s['avg']) * min(dt / 0.4, 1.0)
            target = x / s['peak']
        else:
            source = 2
            names = [c.name for c in inp.chans()]
            counted = _first(names, BEAT_COUNT)
            pulsed = _first(names, BEAT_PULSE)
            if counted:
                c = inp[counted][-1]
                if s['prev_count'] is not None and c > s['prev_count']:
                    beat = 1
                s['prev_count'] = c
            elif pulsed:
                p = inp[pulsed][-1]
                beat = 1 if p >= 0.5 > s['prev_pulse'] else 0
                s['prev_pulse'] = p
            lev = _first(names, LEVEL)
            target = min(max(float(inp[lev][-1]), 0.0), 1.0) if lev else 0.0
        s['level'] += (target - s['level']) * min(dt / 0.08, 1.0)
    else:
        s['level'] = 0.0
    s['count'] += beat
    scriptOp.clear()
    scriptOp.numSamples = 1
    for name, value in (('beat', beat), ('beat_count', s['count']), ('level', s['level']), ('source', source)):
        scriptOp.appendChan(name)[0] = value
    return
