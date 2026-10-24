# Script CHOP callbacks for an effect's audio input (lib/tox_build.py audio_in() puts this text
# in the Script CHOP's docked callbacks DAT). Whatever is wired into input 2 becomes the same
# channels, which the rest of the effect reads:
#
#   beat           1 on the frame a beat arrives, else 0
#   beat_count     beats so far (for logic, watch the counts: a one-frame pulse can be missed)
#   bar_count      bars so far: Fosfora's downbeats, else one every 4 beats (a guess at 4/4)
#   beat_phase     0..1 through the current beat: Fosfora's, else timed from the last beats
#   level          0..1, how loud right now
#   build          0..1, how far into a build (a riser): Fosfora only, else 0
#   drop_count     drop-like moments so far: Fosfora only (experimental there), else 0
#   section_count  section changes so far: Fosfora only, else 0
#   source         0 nothing, 1 raw audio, 2 analysis channels, 3 Fosfora's signal
#
# Input 2 may carry:
#   Fosfora's signal (fosfora_signal.tox, github.com/kevinraymond/fosfora): every channel above
#     comes from it, by name;
#   raw audio (an Audio File In or Audio Device In CHOP, at an audio rate): the loudness of the
#     low band (LOW_HZ, the kick and bass) over the last WINDOW seconds, from an FFT, drives level,
#     and a beat is a jump in it above its recent average;
#   other analysis channels, found by name, first match wins: beats from beat_count or the
#     rising edge of beat, kick or onset (TouchDesigner's audioAnalysis and Essentia rhythm
#     CHOPs); level from energy, level, low, bass or rms;
#   nothing: level 0 and no beats, and the effect still works.
# Timing is judged in seconds, so dropped frames don't change it. State lives in _state, by
# operator id: not in storage, so nothing of a run is saved into the .tox.

# Each count: the output, then the input channels it follows, first match wins: a running count
# (Fosfora's), else a pulse whose rising edges are counted.
COUNTS = (
    ('beat_count', ('beat_count',), ('beat', 'kick', 'onset')),
    ('bar_count', ('bar_count',), ('downbeat',)),
    ('drop_count', ('drop_count',), ('drop',)),
    ('section_count', ('boundary_count',), ('boundary',)),
)
LEVEL = ('energy', 'level', 'low', 'bass', 'rms')
FOSFORA = 'bar_phase'  # a channel only Fosfora's signal has
BEATS_PER_BAR = 4      # for bar_count when the input has no bars
MIN_GAP = 0.2          # seconds between two detected beats in raw audio (at most 300 a minute)
JUMP = 1.5             # a beat: the low band at least this many times its recent average
PEAK_FALL = 4.0        # seconds for the raw level's running peak to fall by half
LOW_HZ = (30.0, 150.0) # the band raw audio's beats and level come from
WINDOW = 0.04          # seconds of raw audio each measure of the low band looks at
RAW_SAMPLES = 32       # samples a cook at or above which input 2 is raw audio
PHASE_BEATS = 4        # beat_phase keeps cycling this many beats past the last one, then rests at 0

_state = {}


def _low_band(rate, samples, s):
    """Raw audio's low-band loudness: the RMS magnitude of the FFT bins in LOW_HZ over the last
    WINDOW seconds, kept across cooks so a short slice still sees a full window."""
    import numpy as np
    mono = samples.mean(axis=0) if samples.ndim == 2 and samples.shape[1] else np.zeros(0)
    n = max(int(rate * WINDOW), 64)
    buf = np.concatenate([s.get('buf', np.zeros(n)), mono])[-n:]
    s['buf'] = buf
    spectrum = np.abs(np.fft.rfft(buf * np.hanning(n))) / n
    freqs = np.fft.rfftfreq(n, 1.0 / rate)
    band = spectrum[(freqs >= LOW_HZ[0]) & (freqs <= LOW_HZ[1])]
    return float(np.sqrt(np.mean(band ** 2))) if band.size else 0.0


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


def _value(inp, name, default=0.0):
    return min(max(float(inp[name][-1]), 0.0), 1.0) if name else default


def onCook(scriptOp):
    now = absTime.seconds
    s = _state.get(scriptOp.id)
    if s is None:
        s = _state[scriptOp.id] = dict(
            counts={out: 0 for out, _, _ in COUNTS}, prev={out: None for out, _, _ in COUNTS},
            pulse={out: 0.0 for out, _, _ in COUNTS}, last=None, avg=0.0, peak=1e-4, level=0.0,
            last_beat=-1e9, interval=0.5)
    dt = 0.0 if s['last'] is None else min(max(now - s['last'], 0.0), 0.5)
    s['last'] = now
    steps = {out: 0 for out, _, _ in COUNTS}
    source, phase, build, has_bars = 0, None, 0.0, False
    inp = scriptOp.inputs[0] if scriptOp.inputs else None
    if inp is not None and inp.numChans:
        samples = inp.numpyArray()
        # Raw audio arrives as a slice of hundreds of samples a frame, analysis channels as one or
        # two. Telling them apart by count, not by inp.rate, matters: reading .rate makes
        # TouchDesigner cook in2_audio every frame from then on, used or not (2025.33230,
        # dev/probes/in_chop_cook.py), so it is read only for raw audio.
        if samples.shape[1] >= RAW_SAMPLES:
            source = 1
            x = _low_band(inp.rate, samples, s)
            s['peak'] = max(x, s['peak'] * 0.5 ** (dt / PEAK_FALL), 1e-4)
            if x > s['avg'] * JUMP and x > 0.1 * s['peak'] and now - s['last_beat'] >= MIN_GAP:
                steps['beat_count'] = 1
            s['avg'] += (x - s['avg']) * min(dt / 0.4, 1.0)
            target = x / s['peak']
        else:
            names = [c.name for c in inp.chans()]
            source = 3 if FOSFORA in names else 2
            for out, counts, pulses in COUNTS:
                counted = _first(names, counts)
                pulsed = None if counted else _first(names, pulses)
                if counted:
                    c = inp[counted][-1]
                    steps[out] = 1 if s['prev'][out] is not None and c > s['prev'][out] else 0
                    s['prev'][out] = c
                elif pulsed:
                    p = inp[pulsed][-1]
                    steps[out] = 1 if p >= 0.5 > s['pulse'][out] else 0
                    s['pulse'][out] = p
                if out == 'bar_count':
                    has_bars = bool(counted or pulsed)
            phase = _value(inp, _first(names, ('beat_phase',)), None)
            build = _value(inp, _first(names, ('build',)))
            target = _value(inp, _first(names, LEVEL))
        s['level'] += (target - s['level']) * min(dt / 0.08, 1.0)
    else:
        s['level'] = 0.0

    beat = steps['beat_count']
    if beat:
        gap = now - s['last_beat']
        if 0.25 <= gap <= 2.0:
            s['interval'] += (gap - s['interval']) * 0.3
        s['last_beat'] = now
    if not has_bars and beat and (s['counts']['beat_count'] + 1) % BEATS_PER_BAR == 0:
        steps['bar_count'] = 1
    for out in steps:
        s['counts'][out] += steps[out]
    if phase is None:
        since = (now - s['last_beat']) / s['interval']
        phase = since % 1.0 if since < PHASE_BEATS else 0.0

    scriptOp.clear()
    scriptOp.numSamples = 1
    values = [('beat', beat), ('beat_count', s['counts']['beat_count']), ('bar_count', s['counts']['bar_count']),
              ('beat_phase', phase), ('level', s['level']), ('build', build),
              ('drop_count', s['counts']['drop_count']), ('section_count', s['counts']['section_count']),
              ('source', source)]
    for name, value in values:
        scriptOp.appendChan(name)[0] = value
    return
