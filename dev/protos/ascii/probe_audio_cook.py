"""DEV ONLY. With input 2 unwired and nothing downstream, audio_in()'s audio_low (Audio Filter CHOP,
time sliced) and audio_rms cook every frame inside a loaded ascii.tox, pulled through the Script
CHOP's second input though the Script CHOP itself doesn't cook (cutting that wire or bypassing
audio_low stops it). Does turning audio_low's Time Slice off while input 2 is unwired stop it, and
does raw audio still give beats once input 2 is wired? Short; destroys what it made.

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/probe_audio_cook.py
    TD_PARENT=/tdlib_dev_ascii dev/td.sh --pull dev/out/ascii/pass2/audio_done
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
OUT = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'pass2')
TOX = os.path.join(_ROOT, 'effects', 'ascii', 'ascii.tox')
os.makedirs(OUT, exist_ok=True)
for f in ('audio.txt', 'audio_done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
WIRED = '1 if parent().inputConnectors[1].connections else 0'


def load(name, fix):
    c = host.loadTox(TOX)
    c.name = name
    c.viewer = False
    if fix:
        c.op('audio_low').par.timeslice.expr = WIRED
    return c


cases = {'as_loaded': load('t_as_loaded', False), 'timeslice_follows_wiring': load('t_fixed', True)}
raw = load('t_raw', True)
music = host.create(audiofileinCHOP, 't_music')
music.par.file.expr = "app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'"
NAMES = ('in2_audio', 'audio_low', 'audio_rms', 'audio')
start = {}
state = {'n': 0}
lines = []


def tick():
    state['n'] += 1
    n = state['n']
    if n == 30:
        start.update({(k, nm): c.op(nm).totalCooks for k, c in cases.items() for nm in NAMES})
    if n == 90:
        for k, c in cases.items():
            lines.append('unwired {}: {}'.format(k, ', '.join(
                '{} {}'.format(nm, c.op(nm).totalCooks - start[(k, nm)]) for nm in NAMES)))
            lines.append('   audio_low timeslice {} '.format(c.op('audio_low').par.timeslice.eval()))
        raw.inputConnectors[1].connect(music)
    if 90 < n <= 300:
        raw.op('audio').cook()   # something uses the effect: its audio CHOP cooks every frame
    if n == 100:
        start['raw'] = raw.op('audio')['beat_count'].eval()
    if n < 300:
        run('args[0]()', tick, delayFrames=1)
        return
    a = raw.op('audio')
    lines.append('wired to the sample MP3 (raw audio): audio_low timeslice {}, source {:.0f}, {:.0f} beats in 200 '
                 'frames, level {:.2f}'.format(raw.op('audio_low').par.timeslice.eval(), a['source'].eval(),
                                               a['beat_count'].eval() - start['raw'], a['level'].eval()))
    raw.inputConnectors[1].disconnect()
    for c in list(cases.values()) + [raw, music]:
        c.destroy()
    open(os.path.join(OUT, 'audio.txt'), 'w').write('cooks in 60 frames, nothing downstream\n' + '\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'audio_done'), 'w').write('audio.txt\n')


tick()
print('probing')
