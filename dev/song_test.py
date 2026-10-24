"""DEV ONLY. Inside TouchDesigner: what input 2 makes of a song, over the whole song. It puts the song
in /tdlib_demo/track and starts it, then records for the song's length what Fosfora's signal says
(beats, bars, tempo, builds, drops, section changes, energy) and what the effects' own detector
(lib/audio_callbacks.py, in a copy under TDLIB_PARENT reading the track) makes of the raw audio:

    TD_ARGS=m1_cinematic dev/td.sh dev/song_test.py     # private/assets/ready/<name>.wav
    (play the same song where Fosfora listens, at the same moment)
    TD_WAIT=330 dev/td.sh --pull dev/out/song_test/done
    cat dev/out/song_test/report.txt

Fosfora hears whatever its machine plays, not TouchDesigner's speaker unless that is the machine
it listens to, so play the song there as this starts. The track stays on the song afterwards
(silent until /tdlib_demo/speaker is Active), and the detector's copy is removed.
"""

import os
import wave

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
OUT = os.path.join(_HERE, 'out', 'song_test')
NAME = (globals().get('TDLIB_ARGS') or ['m1_cinematic'])[0]
SONG = os.path.join(_ROOT, 'private', 'assets', 'ready', NAME + '.wav')
STEP = 10  # seconds a report row covers
FOSFORA = ('online', 'bpm', 'beat_count', 'bar_count', 'build', 'drop_count', 'boundary_count', 'energy')

os.makedirs(OUT, exist_ok=True)
for f in ('report.txt', 'samples.csv', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
with wave.open(SONG) as w:
    seconds = w.getnframes() / w.getframerate()
demo = op('/tdlib_demo')
track, signal = demo.op('track'), demo.op('fosfora_signal/out_signal')
track.par.file = SONG
track.par.cuepulse.pulse()

# The effects' detector on the raw track, as an effect would have it with Beat on Song.
root = op(TDLIB_PARENT) or op('/').create(baseCOMP, TDLIB_PARENT.strip('/'))
box = root.op('song_test') or root.create(baseCOMP, 'song_test')
for o in box.children:
    o.destroy()
raw = box.create(selectCHOP, 'raw')
raw.par.chop = track.path
detector = box.create(scriptCHOP, 'detector')
(callbacks,) = [d for d in detector.docked if d.isDAT and d.name.endswith('_callbacks')]
callbacks.text = open(os.path.join(_ROOT, 'lib', 'audio_callbacks.py')).read()
detector.inputConnectors[0].connect(raw)

rows = []
state = dict(start=absTime.seconds, n=0)


def read():
    names = [c.name for c in signal.chans()] if signal is not None else []
    f = {n: (signal[n].eval() if n in names else 0.0) for n in FOSFORA}
    beats, level = detector['beat_count'], detector['level']  # None until its first cook
    return f, beats.eval() if beats is not None else 0.0, level.eval() if level is not None else 0.0


def tick():
    t = absTime.seconds - state['start']
    f, beats, level = read()
    rows.append((t, f, beats, level))
    state['n'] += 1
    if t < seconds + 1:
        run('args[0]()', tick, delayFrames=1)
        return
    report(t)


def report(t):
    with open(os.path.join(OUT, 'samples.csv'), 'w') as out:
        out.write('t,' + ','.join(FOSFORA) + ',raw_beat_count,raw_level\n')
        for r_t, f, beats, level in rows:
            out.write('{:.3f},{},{:.0f},{:.3f}\n'.format(r_t, ','.join('{:.4f}'.format(f[n]) for n in FOSFORA),
                                                       beats, level))
    first = rows[0]
    lines = ['{}: {:.1f} s recorded, {} frames ({:.0f} fps)'.format(NAME, t, state['n'], state['n'] / t),
             'Fosfora online at start {:.0f}; counts below are steps within each row'.format(first[1]['online']),
             '',
             '  time   energy  bpm    beats bars  build  drops sections | raw beats  raw level']
    prev = first
    for t0 in range(0, int(t), STEP):
        span = [r for r in rows if t0 <= r[0] < t0 + STEP]
        if not span:
            continue
        last = span[-1]
        step = {n: last[1][n] - prev[1][n] for n in ('beat_count', 'bar_count', 'drop_count', 'boundary_count')}
        lines.append('  {}:{:02d}  {:6.3f}  {:5.1f}  {:5.0f} {:4.0f}  {:5.2f}  {:5.0f} {:8.0f} | {:9.0f}  {:9.2f}'.format(
            t0 // 60, t0 % 60, sum(r[1]['energy'] for r in span) / len(span), last[1]['bpm'],
            step['beat_count'], step['bar_count'], max(r[1]['build'] for r in span), step['drop_count'],
            step['boundary_count'], last[2] - prev[2], sum(r[3] for r in span) / len(span)))
        prev = last
    events = {'drops': [], 'sections': []}
    for a, b in zip(rows, rows[1:]):
        if b[1]['drop_count'] > a[1]['drop_count']:
            events['drops'].append(b[0])
        if b[1]['boundary_count'] > a[1]['boundary_count']:
            events['sections'].append(b[0])
    for k, ts in events.items():
        lines.append('{}: {}'.format(k, ', '.join('{}:{:04.1f}'.format(int(x // 60), x % 60) for x in ts) or 'none'))
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    box.destroy()
    open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')


tick()
print('{}: track on {}, recording {:.0f} s; Fosfora online {:.0f}'.format(
    NAME, os.path.basename(SONG), seconds + 1, read()[0]['online']))
