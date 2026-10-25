"""DEV ONLY. How much the music moves each effect's picture, from dev/reaction.py's recordings:

    uv run --with numpy dev/reaction_report.py dev/out/reaction            # every effect recorded there
    uv run --with numpy dev/reaction_report.py dev/out/reaction ascii glitch

For each effect, from its take with the song (song) and its take without audio (none), at the beats
and bars the effect heard in the song take:

  change    how much of the picture changes from one frame to the next: the mean, over every pixel,
            of its largest channel change, in percent of full scale, per 1/60 s
  beat      change in the BEAT s after a beat over change in the BEAT s before it: 1.0 is nothing
            on the beat; the none take at the same times is the control (the clip's own moves)
  extra     change in the BEAT s after a beat minus that before it, song take: the beat's reaction
            in the same units as change, so a lift on a picture that barely changes shows as small
  profile   change by time since the last beat, in BIN s steps, over the take's mean: where the
            beat's reaction sits and how fast it fades
  bar       change in the BEAT s after a bar over that after the other beats: what a bar adds
  away      how far the picture is from the clip: the mean, over the 64 x 36 cells, of the largest
            channel difference of their mean colors, in percent, none and song takes; then that in
            the AWAY s after a bar over the AWAY s before it (an effect that holds or smears the
            picture on a bar, rather than changing it, shows here)
  loud      correlation of loudness (the song take's level, over LOUD_SMOOTH s) with the picture's
            mean brightness and with its change over the same window; and the brightness from the
            quietest third of the frames to the loudest
"""

import os
import sys

import numpy as np

BEAT = 0.2
AWAY = 0.5
BIN = 0.05
BINS = 10
LOUD_SMOOTH = 0.5
FRAME = 1 / 60


def load(path):
    z = np.load(path)
    rows = dict(zip([str(c) for c in z['chans']], z['rows'].T))
    out = z['out'].astype(np.float32)
    dt = np.diff(rows['t'], prepend=rows['t'][0] - FRAME)
    # per 1/60 s, so a dropped frame doesn't count double; the first frame's change is against
    # the settle's last frame, which is fine
    change = out[:, :, :, 3].mean(axis=(1, 2)) * 100 * FRAME / np.maximum(dt, FRAME / 4)
    luma = (out[:, :, :, :3] @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)).mean(axis=(1, 2)) * 100
    away = np.abs(out[:, :, :, :3] - z['inp'][:, :, :, :3].astype(np.float32)).max(axis=3).mean(axis=(1, 2)) * 100
    return dict(rows, change=change, luma=luma, away=away, song=str(z['song']))


def steps(t, count):
    return t[1:][np.diff(count) > 0]


def window(t, x, times, lo, hi):
    vals = [x[(t >= b + lo) & (t < b + hi)] for b in times]
    vals = [v.mean() for v in vals if len(v)]
    return float(np.mean(vals)) if vals else float('nan')


def lift(t, x, times):
    return window(t, x, times, 0, BEAT) / max(window(t, x, times, -BEAT, 0), 1e-6)


def profile(t, x, beats):
    since = np.full(len(t), np.inf)
    for b in beats:
        s = t - b
        since = np.where((s >= 0) & (s < since), s, since)
    mean = max(float(np.mean(x)), 1e-6)
    return [float(x[(since >= i * BIN) & (since < (i + 1) * BIN)].mean()) / mean
            if np.any((since >= i * BIN) & (since < (i + 1) * BIN)) else float('nan') for i in range(BINS)]


def smooth(t, x, seconds):
    n = max(int(round(seconds / FRAME)), 1)
    return np.convolve(x, np.ones(n) / n, mode='same')


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 1e-9 and np.std(b) > 1e-9 else float('nan')


def report(song, none):
    t = song['t']
    beats = steps(t, song['beat_count'])
    bars = steps(t, song['bar_count'])
    others = np.array([b for b in beats if not np.any(np.abs(bars - b) < 0.02)])
    span = t[-1] - t[0]
    level = smooth(t, song['level'], LOUD_SMOOTH)
    loud_change = smooth(t, song['change'], LOUD_SMOOTH)
    order = np.argsort(level)
    third = len(order) // 3
    tn = none['t']
    return dict(
        song=song['song'], seconds=span, beats=len(beats), bars=len(bars),
        level=np.percentile(song['level'], [10, 50, 90]),
        change=(float(np.mean(none['change'])), float(np.mean(song['change']))),
        beat=(lift(tn, none['change'], beats), lift(t, song['change'], beats)),
        extra=window(t, song['change'], beats, 0, BEAT) - window(t, song['change'], beats, -BEAT, 0),
        away=(float(np.mean(none['away'])), float(np.mean(song['away'])),
              window(t, song['away'], bars, 0, AWAY) / max(window(t, song['away'], bars, -AWAY, 0), 1e-6)),
        bar=window(t, song['change'], bars, 0, BEAT) / max(window(t, song['change'], others, 0, BEAT), 1e-6),
        profile=profile(t, song['change'], beats),
        loud=(corr(level, song['luma']), corr(level, loud_change),
              float(song['luma'][order[:third]].mean()), float(song['luma'][order[-third:]].mean())))


def bar_chart(values):
    marks = ' .:-=+*#%@'
    return ''.join(marks[min(int(v / 0.5), len(marks) - 1)] if v == v else '?' for v in values)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else 'dev/out/reaction'
    names = sys.argv[2:] or sorted(f[:-len('_song.npz')] for f in os.listdir(folder) if f.endswith('_song.npz'))
    results = {}
    for name in names:
        song, none = (os.path.join(folder, '{}_{}.npz'.format(name, k)) for k in ('song', 'none'))
        if not (os.path.exists(song) and os.path.exists(none)):
            print('{}: no song and none takes in {}'.format(name, folder))
            continue
        results[name] = report(load(song), load(none))
    if not results:
        return
    first = next(iter(results.values()))
    print('{}: {:.1f} s, {} beats, {} bars as the effects heard it; level p10/50/90 {}'.format(
        first['song'], first['seconds'], first['beats'], first['bars'],
        ' / '.join('{:.2f}'.format(v) for v in first['level'])))
    print()
    head = '{:<12} {:>13}  {:>13} {:>6}  {:<10} {:>5}  {:>19}  {:>15}  {:>13}'
    print(head.format('', 'change %', 'beat lift', 'beat', 'profile', 'bar', 'away %', 'loud r', 'luma'))
    print(head.format('effect', 'none -> song', 'none -> song', 'extra', '0-0.5 s', 'lift', 'none -> song  bar',
                      'luma / change', 'quiet -> loud'))
    for name, r in results.items():
        print('{:<12} {:>5.2f} -> {:<5.2f}  {:>5.2f} -> {:<5.2f} {:>+6.2f}  {:<10} {:>5.2f}  {:>5.1f} -> {:<5.1f} {:>5.2f}'
              '  {:>+6.2f} / {:<+6.2f}  {:>5.1f} -> {:<5.1f}'.format(
                  name, r['change'][0], r['change'][1], r['beat'][0], r['beat'][1], r['extra'], bar_chart(r['profile']),
                  r['bar'], r['away'][0], r['away'][1], r['away'][2], r['loud'][0], r['loud'][1], r['loud'][2],
                  r['loud'][3]))
    print()
    print('profile: change by time since the last beat over the take\'s mean, one mark per {:g} s: '
          '" ." under 1, ":" 1-1.5, "-" 1.5-2, "=" 2-2.5, ... "@" 4.5 and up'.format(BIN))


main()
