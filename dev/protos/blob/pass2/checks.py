"""DEV ONLY. blob_track pass 2: review checks that need TouchDesigner (effects/blob_track/review.md).
Loads effects/blob_track/blob_track.tox into TDLIB_PARENT as a drag-in would, then:

  C5  nothing inside cooks while the output is unused: node viewer off, nothing downstream; every
      child's cookAbsFrame over 60 frames, (a) unwired, three times, (b) wired to a playing clip and
      dev/testbed.py's stress beat, which something else keeps cooking, then (c) a control: out_top
      pulled every frame.
  P6  enableExpr grays out Merge (GPU Grid), Label Size and Scramble Labels (Labels Off).
  C4  every Trigger, Lag and Slope CHOP's units; the uniforms that follow the clock.

Short (about 6 s); destroys everything it made and leaves nothing cooking.
    TD_PARENT=/tdlib_dev_blob dev/td.sh dev/protos/blob/pass2/checks.py
    dev/td.sh --pull dev/out/blob_track/pass2/done
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))
OUT = os.path.join(_ROOT, 'dev', 'out', 'blob_track', 'pass2')
CLIP = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'blob_track', 'blob_track.tox'))
fx.viewer = False
lines = []

twin = host.copy(fx, name='blob_twin')
twin.viewer = False
twin.allowCooking = False
for setting, par in ((('Detector', 'blobtrack'), 'Merge'), (('Detector', 'grid'), 'Merge'),
                     (('Labels', 'idpos'), 'Labelsize'), (('Labels', 'off'), 'Labelsize'),
                     (('Labels', 'idpos'), 'Beatlabels'), (('Labels', 'off'), 'Beatlabels')):
    setattr(twin.par, setting[0], setting[1])
    lines.append('P6 {}={!r}: {} enabled {}'.format(setting[0], setting[1], par, getattr(twin.par, par).enable))
for o in twin.findChildren(type=CHOP):
    units = {p.name: p.eval() for p in o.pars() if p.name.endswith('unit') and p.page and p.page.name != 'Common'}
    if o.OPType in ('triggerCHOP', 'lagCHOP', 'slopeCHOP'):
        lines.append('C4 {} ({}): {}{}'.format(o.name, o.OPType, units,
                                                ' timeslice {}'.format(o.par.timeslice.eval()) if hasattr(o.par, 'timeslice') else ''))
for o in twin.findChildren(type=glslTOP):
    exprs = [p.expr for p in o.pars() if p.mode == ParMode.EXPRESSION and 'absTime' in p.expr]
    if exprs:
        lines.append('C4 {} clock uniforms: {}'.format(o.name, sorted(set(exprs))))
twin.destroy()

exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
clip, beat = testbed(host, test_args([])[1])
children = [o for o in fx.findChildren() if o.isTOP or o.isCHOP or o.isDAT or o.isCOMP]


def snap():
    return {o.path: o.cookAbsFrame for o in children}


state = {'phase': 'a', 'n': 0, 'start': None}


def advanced(start):
    now = snap()
    return sorted(p.rsplit('/', 1)[-1] for p in now if now[p] != start[p])


def finish():
    clip.par.play = False
    for o in list(host.children):
        if o.valid and o.isCOMP:
            o.allowCooking = False
    for o in list(host.children):
        if o.valid:
            o.destroy()
    with open(os.path.join(OUT, 'checks.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('checks.txt\n')


def tick():
    try:
        step()
    except Exception:
        import traceback
        lines.append('ERROR in phase {} frame {}:\n{}'.format(state['phase'], state['n'], traceback.format_exc()))
        finish()


def step():
    s = state
    s['n'] += 1
    if s['phase'] in ('b', 'c'):
        clip.cook()   # upstream in use elsewhere: the clip and the beat cook every frame
        beat.cook()
    if s['phase'] == 'c':
        fx.op('out_top').cook()
    if s['n'] == 10:
        s['start'] = snap()
    if s['n'] == 70:
        moved = advanced(s['start'])
        label = {'a': 'unwired, viewer off, nothing downstream (frames 10-70 after load)',
                 'a2': 'unwired, viewer off, nothing downstream (frames 80-140 after load)',
                 'a3': 'unwired, viewer off, nothing downstream (frames 150-210 after load)',
                 'b': 'wired to a playing clip and the stress beat, viewer off, nothing downstream',
                 'c': 'control: out_top pulled every frame'}[s['phase']]
        lines.append('C5 {}: {} of {} children cooked in 60 frames{}'.format(
            label, len(moved), len(children), (': ' + ', '.join(moved[:8]) + (' ...' if len(moved) > 8 else ''))
            if moved else ''))
        nxt = {'a': 'a2', 'a2': 'a3', 'a3': 'b', 'b': 'c', 'c': None}[s['phase']]
        if nxt == 'b':
            fx.inputConnectors[0].connect(clip)
            fx.inputConnectors[1].connect(beat)
        if nxt is None:
            finish()
            return
        s['phase'], s['n'] = nxt, 0
    run('args[0]()', tick, delayFrames=1)


tick()
print('checking; results in', OUT)
