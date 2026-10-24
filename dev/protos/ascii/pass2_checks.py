"""DEV ONLY. ASCII pass 2: review checks that need TouchDesigner (effects/ascii/review.md). Loads
effects/ascii/ascii.tox into TDLIB_PARENT as a drag-in would, then:

  C5  nothing inside cooks while the output is unused: node viewer off, nothing downstream; every
      child's cookAbsFrame over 60 frames, (a) unwired, (b) wired to a playing clip and a beat CHOP
      that something else keeps cooking, then (c) a positive control: out_top pulled every frame.
  P6  enableExpr grays out Font Name, Ink and Pop On when they don't apply.
  C4  the Trigger CHOPs' lengths are in seconds.
  and what a font name that isn't installed does to the atlas.

Short (about 4 s); destroys everything it made and leaves nothing cooking.

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/pass2_checks.py
    TD_PARENT=/tdlib_dev_ascii dev/td.sh --pull dev/out/ascii/pass2/done
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
OUT = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'pass2')
CLIP = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'ascii', 'ascii.tox'))
fx.viewer = False
lines = []

# P6 and C4 and the font, on a second copy so the C5 copy stays as dragged in
twin = host.copy(fx, name='ascii_twin')
twin.viewer = False
for setting, par in ((('Font', 'system'), 'Fontname'), (('Font', 'bitmap'), 'Fontname'), (('Color', 'orangeblue'), 'Ink'),
                     (('Color', 'mono'), 'Ink'), (('Beatpop', 0.5), 'Popon'), (('Beatpop', 0.0), 'Popon')):
    setattr(twin.par, setting[0], setting[1])
    p = getattr(twin.par, par if par != 'Ink' else 'Inkr')
    lines.append('P6 {}={!r}: {} enabled {}'.format(setting[0], setting[1], p.name, p.enable))
for name in ('moments_pulse', 'pop_env', 'drop_env', 'beat_env', 'flash_limit'):
    t = twin.op(name)
    units = {p.name: p.eval() for p in t.pars() if p.name.endswith('unit')}
    lines.append('C4 {} units {}'.format(name, units))
for name in ('moments_lag', 'build_lag', 'level_lag'):
    lines.append('C4 {} lagunit {}'.format(name, twin.op(name).par.lagunit.eval()))
twin.par.Fontname = 'No Such Font 123'
twin.op('atlas').cook(force=True)
lines.append('font missing: atlas errors {!r} warnings {!r}, atlas mean {:.3f}'.format(
    twin.op('atlas').errors(), twin.op('atlas').warnings(),
    sum(twin.op('atlas').sample(x=x, y=y)[0] for x in range(0, 768, 3) for y in range(0, 192, 3)) / (256 * 64)))
twin.destroy()

clip = host.create(moviefileinTOP, 't_clip')
clip.par.file = CLIP
beat = host.create(lfoCHOP, 't_beat')
beat.par.wavetype = 'square'
beat.par.frequency = 2
children = [o for o in fx.findChildren() if o.isTOP or o.isCHOP or o.isDAT or o.isCOMP]


def snap():
    return {o.path: o.cookAbsFrame for o in children}


state = {'phase': 'a', 'n': 0, 'start': None}


def advanced(start):
    now = snap()
    return sorted(p.rsplit('/', 1)[-1] for p in now if now[p] != start[p])


def finish():
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
                 'b': 'wired to a playing clip and a beat, viewer off, nothing downstream',
                 'c': 'control: out_top pulled every frame'}[s['phase']]
        lines.append('C5 {}: {} of {} children cooked in 60 frames{}'.format(
            label, len(moved), len(children), (': ' + ', '.join(
                '{} ({} cooks, {:.3f} ms cpu last)'.format(m, fx.op(m).totalCooks, fx.op(m).cpuCookTime) for m in moved))
            if moved and len(moved) < 5 else ((': ' + ', '.join(moved)) if moved else '')))
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
