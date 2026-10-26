"""DEV ONLY. What an effect's audio front end makes of a song: its level (0-1) percentiles and beats
and bars a second over SECONDS, read every frame, with the song as raw audio on input 2 (as
dev/record.py feeds it). TD_ARGS='particles audio=m1_ease' dev/td.sh dev/probes/level_stats.py,
then dev/td.sh --pull dev/out/level_stats/done."""
import glob
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUT = os.path.join(_ROOT, 'dev', 'out', 'level_stats')
SECONDS = 20.0
names = [a for a in TDLIB_ARGS if '=' not in a] or ['particles']
opts = dict(a.split('=', 1) for a in TDLIB_ARGS if '=' in a)
song = os.path.join(_ROOT, 'private', 'assets', 'ready', opts.get('audio', 'm1_cinematic') + '.wav')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
os.makedirs(OUT, exist_ok=True)
if os.path.exists(os.path.join(OUT, 'done')):
    os.remove(os.path.join(OUT, 'done'))
track = mk(host, audiofileinCHOP, 'track', comment='The song.', file=song, repeat='on', at=(-600, -300))
fx = host.loadTox(os.path.join(_ROOT, 'effects', names[0], names[0] + '.tox'))
fx.inputConnectors[1].connect(track)
audio = fx.op('audio')
rows = []


def tick():
    audio.cook(force=True)
    rows.append((absTime.seconds, audio['level'].eval(), audio['beat_count'].eval(), audio['bar_count'].eval()))
    if rows[-1][0] - rows[0][0] < SECONDS:
        run('args[0]()', tick, delayFrames=1)
        return
    lv = sorted(r[1] for r in rows)
    span = rows[-1][0] - rows[0][0]
    report = dict(song=os.path.basename(song), seconds=round(span, 1),
                  level_p10_50_90=[round(lv[int(len(lv) * q)], 3) for q in (0.1, 0.5, 0.9)],
                  beats_per_s=round((rows[-1][2] - rows[0][2]) / span, 2), bars_per_s=round((rows[-1][3] - rows[0][3]) / span, 2))
    with open(os.path.join(OUT, 'done'), 'w') as f:
        f.write(json.dumps(report) + '\n')
    for o in list(host.children):
        o.destroy()


run('args[0]()', tick, delayFrames=30)
print('reading', names[0], 'audio for', SECONDS, 's on', os.path.basename(song))
