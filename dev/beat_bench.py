"""DEV ONLY. lib/audio_callbacks.py outside TouchDesigner: feed it a song as raw audio, a cook's
worth at a time, and score the beats and bars it makes against the song's own beat grid:

    uv run --with numpy dev/beat_bench.py                          # every private/assets/ready/m1*.wav
    uv run --with numpy dev/beat_bench.py m1x_ease_from_drop --seconds 30 --show 8
    uv run --with numpy dev/beat_bench.py --selftest     # the clock on a made-up kick track (below)

Each cook gets the samples since the last one at FPS frames a second, as an Audio File In CHOP gives
them (an absTime and a scriptOp stand in for TouchDesigner's). The reference grid comes from the whole
song at once, which a live detector can't do: an onset envelope (the rise of each band's log
magnitude, summed) and a dynamic-programming beat tracker over it (Ellis, 'Beat Tracking by Dynamic
Programming', J. New Music Research 2007), at the tempo the envelope's autocorrelation favors (or a known one, TEMPO).

Per song: the tempo; hits (a beat within HIT s of a grid beat), misses (grid beats with none), extras
(beats near no grid beat), judged against the grid moved by the beats' median lag behind it (reported:
a detector lags the onsets by about the same each time), and the hits' median distance from it (jitter); how evenly bars come (each gap between
bars over four grid beats: 1.0 is every 4 beats; the spread says how far off they wander); and level's
percentiles. --show prints the first beats beside the grid's.

--selftest makes a kick track whose grid is known, SELFTEST_BPM with every 5th kick left out and an
extra kick a quarter beat after every 3rd, and fails unless, from SELFTEST_LOCK s on, at least 95% of
its beats are found, at most 5% of the beats are extras and bars come every 4 beats (dev/td.sh-free:
run it after changing lib/audio_callbacks.py; the callbacks before the beat clock fail it).
"""

import argparse
import glob
import os
import types
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READY = os.path.join(ROOT, 'private', 'assets', 'ready')
FPS = 60
HIT = 0.07
HOP = 512
SELFTEST_BPM, SELFTEST_SECONDS, SELFTEST_LOCK = 128.0, 24.0, 6.0
# Songs whose envelope favors another tempo than their beat: m1_cinematic's triplet feel makes 86 and
# 172 BPM fit as well as its beat, 114.8, which Fosfora held over the whole song (dev/song_test.py).
TEMPO = {'m1_cinematic': 114.8}


def load(path, seconds=None):
    with wave.open(path) as w:
        rate, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        if seconds:
            n = min(n, int(seconds * rate))
        x = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, ch).T.astype(np.float32) / 32768
    return rate, x


def grid(rate, x, bpm=None):
    """The song's beat times: onset envelope, tempo from its autocorrelation (weighted toward 120
    BPM, or within 5% of bpm when given), then the dynamic-programming tracker."""
    mono = x.mean(axis=0)
    n_fft = 2048
    frames = np.lib.stride_tricks.sliding_window_view(mono, n_fft)[::HOP] * np.hanning(n_fft)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    freqs = np.fft.rfftfreq(n_fft, 1 / rate)
    # log-spaced bands, each at least one bin wide (the lowest would otherwise hold none)
    cuts = np.unique(np.searchsorted(freqs, np.geomspace(30, 8000, 25)))
    bands = np.stack([mag[:, a:b].mean(axis=1) for a, b in zip(cuts, cuts[1:])], axis=1)
    logb = np.log1p(100 * bands)
    env = np.maximum(np.diff(logb, axis=0), 0).sum(axis=1)
    env = np.concatenate([[0], env])
    env -= np.convolve(env, np.ones(16) / 16, mode='same')
    env = np.maximum(env, 0)
    env /= env.std() + 1e-9
    fr = rate / HOP
    lags = np.arange(int(fr * 60 / 200), int(fr * 60 / 70))
    ac = np.array([np.dot(env[:-l], env[l:]) for l in lags])
    weight = np.exp(-0.5 * (np.log2(60 * fr / lags / 120) / 1.0) ** 2)
    if bpm:
        weight = (np.abs(60 * fr / lags / bpm - 1) < 0.05).astype(float)
    period = lags[np.argmax(ac * weight)]
    # Ellis 2007: score(t) = env(t) + max over earlier beats of score - alpha * log(gap / period)^2
    alpha = 100.0
    score = env.copy()
    back = np.full(len(env), -1)
    for t in range(len(env)):
        lo, hi = t - 2 * period, t - period // 2
        if hi <= 0:
            continue
        prev = np.arange(max(lo, 0), hi)
        cand = score[prev] - alpha * np.log((t - prev) / period) ** 2
        k = np.argmax(cand)
        score[t] = env[t] + cand[k]
        back[t] = prev[k]
    t = int(np.argmax(score[-2 * period:])) + len(env) - 2 * period
    beats = []
    while t >= 0:
        beats.append(t)
        t = back[t]
    times = (np.array(beats[::-1]) * HOP + n_fft / 2) / rate
    return times, 60 * fr / period


def run_callbacks(rate, x, path=os.path.join(ROOT, 'lib', 'audio_callbacks.py')):
    """Cook the callbacks FPS times a second on raw audio; return per-frame t, beat, bar_count,
    level, beat_phase."""
    clock = types.SimpleNamespace(seconds=0.0)
    ns = {'absTime': clock, 'CookLevel': types.SimpleNamespace(WHEN_USED=1)}
    exec(compile(open(path).read(), path, 'exec'), ns)
    chans = {}

    class Chan:
        def __init__(self, name):
            self.name = name
            self.v = 0.0

        def __setitem__(self, i, v):
            self.v = v

    class Inp:
        numChans = x.shape[0]

        def __init__(self):
            self.slice = x[:, :0]

        def numpyArray(self):
            return self.slice

        def chans(self):
            return [Chan('chan1'), Chan('chan2')]

    inp = Inp()
    inp.rate = rate

    class Op:
        id = 1
        inputs = [inp]
        numSamples = 1

        def clear(self):
            chans.clear()

        def appendChan(self, name):
            chans[name] = Chan(name)
            return chans[name]

    op = Op()
    per = rate / FPS
    rows = []
    for f in range(int(x.shape[1] / per)):
        clock.seconds = (f + 1) / FPS
        inp.slice = x[:, int(f * per):int((f + 1) * per)]
        ns['onCook'](op)
        rows.append((clock.seconds, chans['beat'].v, chans['bar_count'].v, chans['level'].v, chans['beat_phase'].v))
    return np.array(rows)


def score(ref, rows, start=1.0):
    t, beat, bars = rows[:, 0], rows[:, 1], rows[:, 2]
    # A cook reports a beat at the end of its slice: the beat happened up to one frame earlier.
    found = t[beat > 0.5] - 0.5 / FPS
    ref = ref[(ref > start) & (ref < t[-1] - 0.5)]  # the detector needs a moment to start
    found_in = found[(found > start - HIT) & (found < t[-1] - 0.5 + HIT)]
    # A detector lags the onsets by about the same each time (its window, the kick's rise): judge the
    # beats against the grid moved by their median lag, and report the lag on its own.
    diffs = np.array([found_in[np.argmin(np.abs(found_in - r))] - r for r in ref]) if len(found_in) else np.zeros(0)
    lag = float(np.median(diffs[np.abs(diffs) < 0.15])) if np.any(np.abs(diffs) < 0.15) else 0.0
    ref = ref + lag
    near = np.array([np.min(np.abs(found_in - r)) if len(found_in) else 1e9 for r in ref])
    hits = int(np.sum(near <= HIT))
    used = np.array([np.min(np.abs(ref - b)) <= HIT for b in found_in]) if len(ref) else np.zeros(0, bool)
    errs = [found_in[np.argmin(np.abs(found_in - r))] - r for r in ref if np.min(np.abs(found_in - r)) <= HIT] \
        if len(found_in) else []
    bar_t = t[1:][np.diff(bars) > 0] - 0.5 / FPS
    beat_gap = np.median(np.diff(ref))
    gaps = np.diff(bar_t[bar_t > start]) / (4 * beat_gap)
    return dict(ref=len(ref), hits=hits, misses=len(ref) - hits, extras=int(np.sum(~used)), lag=lag,
                err=float(np.median(np.abs(errs))) if errs else float('nan'),
                bars=gaps, level=np.percentile(rows[:, 3], [10, 50, 90]), found=found)


def kick_track(rate=44100):
    """SELFTEST_SECONDS of kicks (a falling 60 Hz thump) at SELFTEST_BPM over quiet noise: every 5th
    left out, an extra a quarter beat after every 3rd. Returns the audio and the grid."""
    period = 60 / SELFTEST_BPM
    n = int(SELFTEST_SECONDS * rate)
    x = np.random.default_rng(1).normal(0, 0.003, n).astype(np.float32)
    k = np.arange(int(0.12 * rate)) / rate
    thump = (np.sin(2 * np.pi * 60 * k) * np.exp(-k / 0.04)).astype(np.float32) * 0.8
    beats = np.arange(0.5, SELFTEST_SECONDS - 0.5, period)
    for i, b in enumerate(beats):
        for at in ([b] if i % 5 != 4 else []) + ([b + period / 4] if i % 3 == 2 else []):
            j = int(at * rate)
            x[j:j + len(thump)] += thump[:n - j]
    return rate, np.stack([x, x]), beats


def selftest(callbacks):
    rate, x, ref = kick_track()
    s = score(ref, run_callbacks(rate, x, callbacks), start=SELFTEST_LOCK)
    g = s['bars']
    found = s['hits'] / max(s['ref'], 1)
    extra = s['extras'] / max(s['hits'] + s['extras'], 1)
    bars = len(g) > 2 and np.all(np.abs(g - 1) < 0.05)
    ok = found >= 0.95 and extra <= 0.05 and bars
    print('{} beat clock on {:g} BPM kicks, every 5th missing, an extra after every 3rd: {:.0f}% found, {:.0f}% '
          'extra, bars every {} x 4 beats (want >= 95%, <= 5%, every 1.00)'.format(
              'ok  ' if ok else 'FAIL', SELFTEST_BPM, 100 * found, 100 * extra,
              ' '.join('{:.2f}'.format(v) for v in g[:8]) or 'none'))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('songs', nargs='*')
    ap.add_argument('--seconds', type=float, default=None)
    ap.add_argument('--show', type=int, default=0)
    ap.add_argument('--callbacks', default=os.path.join(ROOT, 'lib', 'audio_callbacks.py'))
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(0 if selftest(a.callbacks) else 1)
    songs = a.songs or sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(READY, 'm1*.wav')))
    for name in songs:
        rate, x = load(os.path.join(READY, name + '.wav'), a.seconds)
        ref, bpm = grid(rate, x, TEMPO.get(name))
        rows = run_callbacks(rate, x, a.callbacks)
        s = score(ref, rows)
        g = s['bars']
        print('{:<20} {:5.1f} BPM  {:4d} beats: {:4d} hit {:4d} missed {:4d} extra ({:3.0f}% / {:3.0f}%), lag {:+3.0f} ms, jitter {:2.0f} ms;'
              ' bars every {:.2f} x 4 beats (p10-p90 {:.2f}-{:.2f}); level p10/50/90 {}'.format(
                  name, bpm, s['ref'], s['hits'], s['misses'], s['extras'], 100 * s['hits'] / max(s['ref'], 1),
                  100 * s['extras'] / max(s['hits'] + s['extras'], 1), 1000 * s['lag'], 1000 * s['err'],
                  np.median(g) if len(g) else float('nan'), *(np.percentile(g, [10, 90]) if len(g) else (np.nan, np.nan)),
                  ' / '.join('{:.2f}'.format(v) for v in s['level'])))
        if a.show:
            print('   grid :', ' '.join('{:.2f}'.format(v) for v in ref[(ref > 1)][:a.show]))
            print('   beats:', ' '.join('{:.2f}'.format(v) for v in s['found'][s['found'] > 1][:a.show]))


main()
