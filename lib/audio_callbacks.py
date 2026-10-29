# Script CHOP callbacks for an effect's audio input (lib/tox_build.py audio_in() puts this text
# in the Script CHOP's docked callbacks DAT). Whatever is wired into input 2 becomes the same
# channels, which the rest of the effect reads:
#
#   beat           1 on the frame a beat arrives, else 0
#   beat_count     beats so far (for logic, watch the counts: a one-frame pulse can be missed)
#   bar_count      bars so far: Fosfora's downbeats, else one every 4 beats (a guess at 4/4)
#   beat_phase     0..1 through the current beat: Fosfora's, else timed from the last beats
#   beat_period    seconds a beat lasts: Fosfora's bpm (or another input's bpm or tempo channel), else raw
#                  audio's beat clock, else the gaps between the last beats; 0.5 (120 BPM) until there are beats
#   level          0..1, how loud right now
#   build          0..1, how far into a build (a riser): Fosfora only, else 0
#   drop_count     drop-like moments so far: Fosfora only (experimental there), else 0
#   section_count  section changes so far: Fosfora only, else 0
#   source         0 nothing, 1 raw audio, 2 analysis channels, 3 Fosfora's signal
#   sub_bass, bass, low_mid, mid, upper_mid, presence, brilliance
#                  0..1, how much is in each band of the sound right now, lowest to highest: Fosfora's
#                  seven-way split (BANDS), each over its own recent peak, so each band uses the whole range
#
# Input 2 may carry:
#   Fosfora's signal (fosfora_signal.tox, github.com/kevinraymond/fosfora): every channel above
#     comes from it, by name, and level from its bass (its energy barely moves with the music); the
#     bands from its feature bus (fosfora --signal --feat-bus: feat_sub_bass ... feat_brilliance), else
#     from its bass, melody and drums (bass for the lowest two, melody for the middle, drums for the top);
#   raw audio (an Audio File In or Audio Device In CHOP, at an audio rate): the loudness of the
#     low band (LOW_HZ, the kick and bass) over the last WINDOW seconds, from an FFT, drives level,
#     and a kick is a jump in it above its recent average. Once the kicks keep to a tempo, a beat
#     clock locks to their grid: beats come on the grid (a missed kick is filled in, a kick between
#     beats is left out) and a bar is every 4 of them; while unlocked, every kick is a beat; the bands
#     from FFTs of the last BAND_WINDOWS samples (the long one for the lowest three bands, the short one,
#     which follows a hi-hat closely, for the rest);
#   other analysis channels, found by name, first match wins: beats from beat_count or the
#     rising edge of beat, kick or onset (TouchDesigner's audioAnalysis and Essentia rhythm
#     CHOPs); level from energy, level, low, bass or rms; the bands by their own names, else from low,
#     mid and high (audioAnalysis: low for the lowest two, mid for the middle three, high for the top),
#     else all from the level;
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
TEMPO = ('bpm', 'tempo')   # beats a minute, when the input carries it (Fosfora's signal does)
FOSFORA = 'bar_phase'  # a channel only Fosfora's signal has
FOSFORA_LEVEL = ('bass', 'energy')  # its energy sits near 0.9 through a song; bass swells with each beat
BEATS_PER_BAR = 4      # for bar_count when the input has no bars
MIN_GAP = 0.2          # seconds between two kicks detected in raw audio (at most 300 a minute)
JUMP = 1.5             # a kick: the low band at least this many times its recent average
PEAK_FALL = 4.0        # seconds for the raw level's running peak to fall by half
LOW_HZ = (30.0, 150.0) # the band raw audio's beats and level come from
WINDOW = 0.04          # seconds of raw audio each measure of the low band looks at
# The bands, Fosfora's seven-way split (its AUDIO-FEATURES.md): each one's lowest frequency, the last band up to
# BAND_EDGES[-1]. Raw audio measures the lowest three over the long window (BAND_WINDOWS[0] samples, about 90 ms)
# and the rest over the short one.
BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')
BAND_EDGES = (20.0, 60.0, 250.0, 500.0, 2000.0, 4000.0, 6000.0, 16000.0)
BAND_WINDOWS = (4096, 1024)
FOSFORA_BANDS = ('bass', 'bass', 'bass melody', 'melody', 'melody', 'drums', 'drums')
ANALYSIS_BANDS = ('low', 'low', 'mid', 'mid', 'mid', 'high', 'high')
RAW_SAMPLES = 32       # samples a cook at or above which input 2 is raw audio
PHASE_BEATS = 4        # beat_phase keeps cycling this many beats past the last one, then rests at 0
# Raw audio's beat clock: once the kicks found keep to a tempo, beats come from a clock on their grid,
# so a missed kick is filled in, a kick between beats is left out, and a bar is every 4 of its beats.
TEMPO_SPAN = 8.0       # seconds of kicks the tempo and the grid are judged from
PERIODS = (0.33, 0.75) # seconds a beat may last: 80 to 180 BPM
ON_GRID = 0.15         # a kick within this share of a beat from the grid is on it
LOCK = 4               # kicks on one grid, within TEMPO_SPAN, that start the clock...
AGREE = 0.6            # ...when at least this share of those kicks are on it
KEEP = (8, 3)          # the clock stops when of its last KEEP[0] beats, at most KEEP[1] had a kick, while
                       # kicks kept coming (as many as those beats): the kicks keep another grid
FREEWHEEL = 8          # beats the clock keeps going after the last kick on its grid

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


def _bands(rate, samples, s):
    """Raw audio's bands: the RMS magnitude of each band's FFT bins, the lowest three over the last
    BAND_WINDOWS[0] samples and the rest over the last BAND_WINDOWS[1], kept across cooks."""
    import numpy as np
    mono = samples.mean(axis=0) if samples.ndim == 2 and samples.shape[1] else np.zeros(0)
    buf = np.concatenate([s.get('bbuf', np.zeros(BAND_WINDOWS[0])), mono])[-BAND_WINDOWS[0]:]
    s['bbuf'] = buf
    out = []
    for n, bands in ((BAND_WINDOWS[0], range(0, 3)), (BAND_WINDOWS[1], range(3, 7))):
        spectrum = np.abs(np.fft.rfft(buf[-n:] * np.hanning(n))) / n
        freqs = np.fft.rfftfreq(n, 1.0 / rate)
        for b in bands:
            bins = spectrum[(freqs >= BAND_EDGES[b]) & (freqs < BAND_EDGES[b + 1])]
            out.append(float(np.sqrt(np.mean(bins ** 2))) if bins.size else 0.0)
    return out


def _period(kicks, prev):
    """The beat length the kicks keep to: each gap between two kicks votes for the periods it is one
    to four of, nearer multiples louder; 120 BPM and the current period are favored a little, so the
    clock doesn't jump between a tempo and its half or double."""
    import numpy as np
    o = np.array(kicks)
    gaps = (o[None, :] - o[:, None])[np.triu_indices(len(o), 1)]
    p = np.arange(PERIODS[0], PERIODS[1], 0.004)[:, None]
    k = np.round(gaps[None, :] / p)
    err = (gaps[None, :] / np.maximum(k, 1) - p) / p
    votes = np.where((k >= 1) & (k <= 4), np.exp(-0.5 * (err / 0.025) ** 2) / np.maximum(k, 1), 0).sum(axis=1)
    p = p[:, 0]
    votes *= np.exp(-0.5 * np.log2(p / 0.5) ** 2)
    if prev:
        votes *= 1 + np.exp(-0.5 * ((p - prev) / (0.02 * prev)) ** 2)
    return float(p[np.argmax(votes)])


def _fit(hits, period):
    """The grid through the kicks on it, (index, time) pairs: time = origin + period x index, by least
    squares (the period alone when the kicks span too few beats to say)."""
    import numpy as np
    n, t = np.array(hits, dtype=float).T
    if n.max() - n.min() >= 4:
        period, origin = np.polyfit(n, t, 1)
    else:
        origin = float(np.mean(t - period * n))
    return float(origin), float(min(max(period, PERIODS[0]), PERIODS[1]))


def _clock(s, now, dt, kick):
    """Raw audio's beat clock, one cook of dt seconds: returns (beat, bar). Locked, beats come on the
    grid (at a kick on the grid just before the beat is due, or when it is due); unlocked, at every
    kick, with a bar every BEATS_PER_BAR of them."""
    s['kicks'] = [k for k in s['kicks'] if now - k <= TEMPO_SPAN] + ([now] if kick else [])
    c = s['clock']
    if c is not None and kick:
        span = KEEP[0] * c['period']
        hit = {n for n, t in c['hits'] if c['next'] - n <= KEEP[0]}
        if sum(now - k <= span for k in s['kicks']) >= KEEP[0] and len(hit) <= KEEP[1]:
            s['clock'] = c = None  # the kicks keep another grid: find it again
            s['grid'] = None
    if c is None:
        if not kick:
            return 0, 0
        beat, bar = 1, int((s['counts']['beat_count'] + 1) % BEATS_PER_BAR == 0)
        if len(s['kicks']) >= LOCK:
            period = _period(s['kicks'], s['grid'][1] if s['grid'] else None)
            hits = [(round((k - now) / period), k) for k in s['kicks']
                    if abs((k - now) / period - round((k - now) / period)) <= ON_GRID]
            if len({n for n, _ in hits}) >= LOCK and len(hits) >= AGREE * len(s['kicks']):
                shift = 0
                g = s['grid']
                at = (now - g[0]) / g[1] if g else 0.0
                if g and abs(g[1] / period - 1) < 0.03 and abs(at - round(at)) <= ON_GRID:
                    shift = round(at)  # the old grid again: keep its count, and so its bars
                hits = [(n + shift, k) for n, k in hits]
                origin, period = _fit(hits, period)
                s['clock'] = c = dict(origin=origin, period=period, hits=hits, next=shift + 1, last=shift)
                bar = int(shift % BEATS_PER_BAR == 0)
        return beat, bar
    beat = 0
    if kick:
        n = round((now - c['origin']) / c['period'])
        if abs(now - c['origin'] - n * c['period']) <= ON_GRID * c['period']:
            c['hits'] = [h for h in c['hits'] if now - h[1] <= TEMPO_SPAN] + [(n, now)]
            c['last'] = max(c['last'], n)
            c['origin'], c['period'] = _fit(c['hits'], c['period'])
            if n == c['next']:
                beat = 1
    due = c['origin'] + c['period'] * c['next']
    if not beat and now >= due - dt / 2:
        if c['next'] - c['last'] > FREEWHEEL:
            s['grid'] = (c['origin'], c['period'])
            s['clock'] = None
            return 0, 0
        beat = 1
    if not beat:
        return 0, 0
    n = c['next']
    c['next'] = max(n + 1, int((now - c['origin']) / c['period']) + 1)
    return 1, int(n % BEATS_PER_BAR == 0)


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
            last_beat=-1e9, interval=0.5, kicks=[], clock=None, grid=None, last_kick=-1e9,
            bands=[0.0] * len(BANDS), band_peaks=[1e-4] * len(BANDS))
    dt = 0.0 if s['last'] is None else min(max(now - s['last'], 0.0), 0.5)
    s['last'] = now
    steps = {out: 0 for out, _, _ in COUNTS}
    source, phase, build, has_bars, raw_bar, bpm = 0, None, 0.0, False, 0, 0.0
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
            kick = x > s['avg'] * JUMP and x > 0.1 * s['peak'] and now - s['last_kick'] >= MIN_GAP
            if kick:
                s['last_kick'] = now
            steps['beat_count'], raw_bar = _clock(s, now, dt, kick)
            has_bars = True
            s['avg'] += (x - s['avg']) * min(dt / 0.4, 1.0)
            target = x / s['peak']
            band_targets = []
            for b, e in enumerate(_bands(inp.rate, samples, s)):
                s['band_peaks'][b] = max(e, s['band_peaks'][b] * 0.5 ** (dt / PEAK_FALL), 1e-4)
                band_targets.append(e / s['band_peaks'][b])
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
            tempo = _first(names, TEMPO)
            bpm = float(inp[tempo][-1]) if tempo else 0.0
            build = _value(inp, _first(names, ('build',)))
            target = _value(inp, _first(names, FOSFORA_LEVEL if source == 3 else LEVEL))
            band_targets = []
            for b, band in enumerate(BANDS):
                own = _first(names, ('feat_' + band, band))
                proxy = (FOSFORA_BANDS if source == 3 else ANALYSIS_BANDS)[b].split()
                found = [n for n in proxy if n in names]
                band_targets.append(_value(inp, own) if own else
                                    sum(_value(inp, n) for n in found) / len(found) if found else target)
        s['level'] += (target - s['level']) * min(dt / 0.08, 1.0)
        for b, t in enumerate(band_targets):
            s['bands'][b] += (t - s['bands'][b]) * min(dt / 0.08, 1.0)
    else:
        s['level'] = 0.0
        s['bands'] = [0.0] * len(BANDS)

    beat = steps['beat_count']
    if beat:
        gap = now - s['last_beat']
        if 0.25 <= gap <= 2.0:
            s['interval'] += (gap - s['interval']) * 0.3
        s['last_beat'] = now
    if source == 1:
        steps['bar_count'] = raw_bar
        if s['clock'] is not None:
            s['interval'] = s['clock']['period']
    elif not has_bars and beat and (s['counts']['beat_count'] + 1) % BEATS_PER_BAR == 0:
        steps['bar_count'] = 1
    for out in steps:
        s['counts'][out] += steps[out]
    if phase is None:
        since = (now - s['last_beat']) / s['interval']
        phase = since % 1.0 if since < PHASE_BEATS else 0.0
    period = min(max(60.0 / bpm, 0.2), 2.0) if bpm > 0 else s['interval']

    scriptOp.clear()
    scriptOp.numSamples = 1
    values = [('beat', beat), ('beat_count', s['counts']['beat_count']), ('bar_count', s['counts']['bar_count']),
              ('beat_phase', phase), ('level', s['level']), ('build', build),
              ('drop_count', s['counts']['drop_count']), ('section_count', s['counts']['section_count']),
              ('source', source)] + list(zip(BANDS, s['bands'])) + [('beat_period', period)]
    for name, value in values:
        scriptOp.appendChan(name)[0] = value
    return
