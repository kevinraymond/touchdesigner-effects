"""DEV ONLY. Inside TouchDesigner: every built effect running live on test footage, to look at on
the Mac itself rather than in captured frames:

    dev/td.sh dev/demo.py

It makes /tdlib_demo (once) with a looping test clip, private/assets/ready/b1_dancer.mp4 (or
TouchDesigner's sample movie when that isn't there), and a beat: Fosfora's signal while
`fosfora --signal` is sending (private/fosfora/fosfora_signal.tox, copied there from the Fosfora
repo's integrations/touchdesigner/), else TouchDesigner's sample MP3. Then it puts a copy of
every effects/<n>/<n>.tox in it, wired to both. Run it again after building
an effect: only the effects whose .tox changed are reloaded (and any whose .tox is gone are
removed), so the clip, the track and their settings stay as they are (change the clip in
/tdlib_demo/clip's File parameter). The track is
silent until Sound is turned on on the Demo page, and Sound turns itself off whenever the project
opens: TouchDesigner saves a playing speaker with the project, which then opens playing.

One effect runs at a time, so the Mac isn't running all of them at once: /tdlib_demo's Demo page
has Effect (which one the `show` viewer shows; a Switch TOP cooks only its chosen input, and the
effects' own node viewers are off), Play (the clip; off to pause it) and Beat: Auto takes
Fosfora's signal only while it is online and hearing something (Fosfora's beat clock keeps
ticking through silence and pauses, with its energy at 0), else the song; Fosfora and Song force
one. The /tdlib_demo box shows `show` too, so the top level has the picture and, one click away,
the Demo page. Pulse an effect's Open Window to see it at full size. Delete /tdlib_demo freely;
the next run makes it again.
"""

import glob
import json
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
DEMO = '/tdlib_demo'
CLIP = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')
COLUMN = 600
HEARD, HEARD_HOLD = 0.005, 3  # Fosfora's energy above HEARD within the last ~HEARD_HOLD s: it hears music


def place(o, x, y, comment):
    o.nodeX, o.nodeY = x, y
    o.comment = comment
    return o


demo = op(DEMO)
if demo is None:
    demo = place(op('/').create(baseCOMP, DEMO.strip('/')), 0, -600,
                 'DEV ONLY: tdlib effects on test footage (tdlib dev/demo.py). Delete freely.')
clip = demo.op('clip')
if clip is None:
    clip = place(demo.create(moviefileinTOP, 'clip'), -COLUMN, 0, 'The test clip every effect gets, looping.')
    clip.par.file = CLIP if os.path.exists(CLIP) else app.samplesFolder + '/Map/Nature/Movie.1.mp4'
    clip.viewer = True
try:
    stamp = os.path.getmtime(clip.par.file.eval())
except OSError:
    stamp = None
if stamp is not None and clip.fetch('mtime', None) not in (None, stamp):
    clip.par.reloadpulse.pulse()  # the file was replaced (a re-generated clip, same name)
clip.store('mtime', stamp)
track = demo.op('track')
if track is None:
    track = place(demo.create(audiofileinCHOP, 'track'), -COLUMN, -400,
                  "The beat every effect gets: TouchDesigner's sample MP3, looping.")
    track.par.file = app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'
    track.par.repeat = 'on'
SIGNAL = os.path.join(_ROOT, 'private', 'fosfora', 'fosfora_signal.tox')
signal = demo.op('fosfora_signal')
if signal is None and os.path.exists(SIGNAL):
    signal = place(demo.loadTox(SIGNAL), -2 * COLUMN, -200, "Fosfora's signal: beats, bars, builds, drops.")
beat = demo.op('beat')
if beat is not None and signal is not None and not any(i.path.startswith(signal.path) for i in beat.inputs):
    beat.destroy()  # made before the signal was there
    beat = None
if beat is None:
    beat = place(demo.create(switchCHOP, 'beat'), -COLUMN, -200,
                 "The effects' input 2: Fosfora's signal while it is online, else the track.")
    if signal is not None:
        beat.inputConnectors[0].connect(signal.outputConnectors[0])  # out_signal, its CHOP output
    beat.inputConnectors[len(beat.inputs)].connect(track)
if signal is not None and demo.op('heard') is None:
    # Fosfora's energy, rising at once and falling over HEARD_HOLD seconds: is it hearing anything?
    energy = place(demo.create(selectCHOP, 'energy'), -2 * COLUMN, -450, "Fosfora's energy (0 in silence).")
    energy.par.chop = signal.op('out_signal').path
    energy.par.channames = 'energy'
    heard = place(demo.create(lagCHOP, 'heard'), -1.5 * COLUMN, -450,
                  'Fosfora heard something lately: Beat Auto takes its signal only then.')
    heard.inputConnectors[0].connect(energy)
    heard.par.lag1, heard.par.lag2 = 0, HEARD_HOLD
speaker = demo.op('speaker')
if speaker is None:
    speaker = place(demo.create(audiodeviceoutCHOP, 'speaker'), -COLUMN, -700,
                    'Plays the track while Sound is on (Demo page).')
    speaker.inputConnectors[0].connect(track)
speaker.comment = 'Plays the track while Sound is on (Demo page).'
if demo.op('sound_off') is None:
    quiet = place(demo.create(executeDAT, 'sound_off'), -COLUMN, -850,
                  'Turns Sound off whenever the project opens, so it never opens playing.')
    quiet.text = 'def onStart():\n    parent().par.Sound = False\n    return\n'
    quiet.par.start = True

loaded = []
paths = sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox')))
names = [os.path.splitext(os.path.basename(p))[0] for p in paths]
for fx in demo.findChildren(type=COMP, depth=1):
    if fx.name not in names and fx.name != 'fosfora_signal':
        fx.destroy()
for i, (path, name) in enumerate(zip(paths, names)):
    manifest = os.path.join(os.path.dirname(path), name + '.json')
    sha = json.load(open(manifest)).get('tox_sha256') if os.path.exists(manifest) else None
    old = demo.op(name)
    if old is not None and sha is not None and old.fetch('tox_sha256', None) == sha:
        continue
    if old is not None:
        old.destroy()
    fx = demo.loadTox(path)
    fx.nodeX, fx.nodeY = i * COLUMN, 0
    fx.store('tox_sha256', sha)
    loaded.append('{} {}'.format(name, fx.par.Version.eval() if hasattr(fx.par, 'Version') else ''))
for name in names:
    fx = demo.op(name)
    fx.inputConnectors[0].connect(clip)
    if len(fx.inputConnectors) > 1:
        fx.inputConnectors[1].connect(beat)

# One effect at a time: the Demo page picks it, and only the chosen one cooks.
page = next((pg for pg in demo.customPages if pg.name == 'Demo'), None) or demo.appendCustomPage('Demo')
if not hasattr(demo.par, 'Effect'):
    page.appendMenu('Effect', label='Effect')
    page.appendToggle('Play', label='Play')
    demo.par.Play.val = False
if not hasattr(demo.par, 'Sound'):
    page.appendToggle('Sound', label='Sound')
    demo.par.Sound.val = False
if not hasattr(demo.par, 'Beat'):
    page.appendMenu('Beat', label='Beat')
    demo.par.Beat.menuNames = ['auto', 'fosfora', 'song']
    demo.par.Beat.menuLabels = ['Auto', 'Fosfora', 'Song']
    demo.par.Beat.val = 'auto'
demo.par.Effect.help = 'Which effect the show viewer shows; only that one runs.'
demo.par.Play.help = 'Play the test clip; off pauses it.'
demo.par.Sound.help = 'Play the track out loud. Turns itself off whenever the project opens.'
demo.par.Beat.help = ("The effects' input 2. Auto: Fosfora's signal while it is online and hearing "
                      "music, else the song in track. Fosfora or Song: always that one.")
# Typing a value into a parameter switches it to that constant, which cuts it off from the Demo
# page, so every run puts these links back (and says which it had to).
relinked = []


def follow(par, expr):
    if par.mode != ParMode.EXPRESSION or par.expr != expr:
        relinked.append('{} {}'.format(par.owner.name, par.label))
    par.expr = expr
    par.mode = ParMode.EXPRESSION


follow(clip.par.play, 'parent().par.Play')
follow(speaker.par.active, 'parent().par.Sound')
if signal is not None:  # beat's inputs: 0 Fosfora's signal, 1 the track
    follow(beat.par.index, (
        "0 if parent().par.Beat.eval() == 'fosfora' or (parent().par.Beat.eval() == 'auto'"
        " and op('fosfora_signal/out_signal')['online'] and op('fosfora_signal/out_signal')['online'].eval() > 0.5"
        " and op('heard')['energy'] and op('heard')['energy'].eval() > {}) else 1".format(HEARD)))
else:
    follow(beat.par.index, '0')
current = demo.par.Effect.eval()
demo.par.Effect.menuNames = ['clip'] + names
demo.par.Effect.menuLabels = ['Clip only'] + names
demo.par.Effect.val = current if current in names else 'clip'
show = demo.op('show')
if show is None:
    show = place(demo.create(switchTOP, 'show'), 0, 450, 'The effect chosen on the Demo page (only it cooks).')
    show.nodeWidth, show.nodeHeight = 480, 270
    show.viewer = True
follow(show.par.index, 'parent().par.Effect.menuIndex')
# The demo's own box shows `show` too, so from the top level one click on it gives the Demo page
# and the picture side by side. Placed clear of project1 the first time; moved by hand, it stays.
demo.par.opviewer = './show'
demo.viewer = True
if demo.nodeWidth < 480:
    demo.nodeX, demo.nodeY, demo.nodeWidth, demo.nodeHeight = 200, -500, 480, 270
# show's inputs in the Effect menu's order: clip, then each effect. Disconnecting one input of a
# multi-input operator renumbers the rest, so clear them last to first, then check.
wanted = [clip] + [demo.op(n) for n in names]
if [i.path for i in show.inputs] != [(o.outputConnectors[0].outOP or o).path for o in wanted]:
    for c in reversed(show.inputConnectors):
        c.disconnect()
    if show.inputs:
        raise RuntimeError('show still has inputs after disconnecting: {}'.format([i.path for i in show.inputs]))
    for i, o in enumerate(wanted):
        show.inputConnectors[i].connect(o.outputConnectors[0])
    relinked.append('show inputs')
for name in names:
    demo.op(name).viewer = False
    demo.op(name).allowCooking = True

if relinked:
    print('put back:', ', '.join(relinked))
print('{}: clip {}; beat from {} (Beat {}); loaded {}'.format(
    DEMO, os.path.basename(clip.par.file.eval()), 'Fosfora' if beat.par.index.eval() == 0 and signal else 'the track',
    demo.par.Beat.eval(),
    ', '.join(loaded) or 'nothing new'))
for fx in demo.findChildren(type=COMP, depth=1):
    if fx.name == 'fosfora_signal':
        continue
    problems = fx.errors(recurse=True) + fx.warnings(recurse=True)
    if problems:
        print(fx.name, 'reports:', problems)
