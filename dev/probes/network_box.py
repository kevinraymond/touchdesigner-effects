# DEV ONLY probe: a Network Box made from Python (2025.33230). What is inside an Annotate COMP, can it be
# renamed, where does its extension point, does anything in it cook while the network isn't shown, and do
# the save-time checks accept an effect with one? Writes dev/out/network_box/<TDLIB_ARGS[0] or 'r1'>.txt.
import os

ROOT = os.path.expanduser('~/tdlib')
exec(compile(open(os.path.join(ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUT = os.path.join(ROOT, 'dev', 'out', 'network_box')
RUN = (TDLIB_ARGS or ['r1'])[0]
os.makedirs(OUT, exist_ok=True)
log = []
host = op(TDLIB_PARENT)
old = host.op('box_probe')
if old:
    old.destroy()
c = host.create(baseCOMP, 'box_probe')
a = mk(c, constantTOP, 'a', 0, 0, comment='Something to enclose.')
b = c.create(annotateCOMP, 'box_picture')
log.append('created as: ' + b.name)
b.name = 'box_picture'
log.append('renamed: ' + b.name)
b.par.Mode = 'networkbox'
b.par.Titletext = 'The picture'
b.par.Bodytext = 'What this part does.'
b.par.Backcolorr, b.par.Backcolorg, b.par.Backcolorb = 0.2, 0.3, 0.45
b.nodeX, b.nodeY, b.nodeWidth, b.nodeHeight = -50, -50, 400, 250
log.append('box at ({}, {}) {}x{}, mode {}'.format(b.nodeX, b.nodeY, b.nodeWidth, b.nodeHeight, b.par.Mode.eval()))
log.append('ext0object expr {!r} val {!r} eval {!r}'.format(b.par.ext0object.expr, b.par.ext0object.val,
                                                         b.par.ext0object.eval()))
log.append('op.TDAnnotate -> {}'.format(getattr(op.TDAnnotate, 'path', op.TDAnnotate)))
inside = b.findChildren()
log.append('inside the box ({}): {}'.format(len(inside), ', '.join('{} {}'.format(o.path[len(b.path) + 1:], o.OPType)
                                                                   for o in inside)))
log.append('clone {!r} externaltox {!r}'.format(b.par.clone.eval(), b.par.externaltox.eval()))
log.append('enclosedOPs: {}'.format([o.name for o in getattr(b, 'enclosedOPs', [])] if hasattr(b, 'enclosedOPs')
                                     else 'n/a ' + str([m for m in dir(b) if 'enclos' in m.lower()])))
for name, check in (('self_contained', assert_self_contained), ('no_unused_docked', assert_no_unused_docked),
                    ('readable', assert_readable), ('nc_resolution', assert_nc_resolution),
                    ('loads_clean', assert_loads_clean)):
    try:
        check(c)
        log.append(name + ': passes')
    except Exception as e:
        log.append(name + ': ' + str(e).replace('\n', ' | ')[:600])
state = {'n': 0, 'before': None}


def tick():
    state['n'] += 1
    frames = {o.path: o.cookAbsFrame for o in [b] + list(b.findChildren())}
    if state['n'] == 30:
        state['before'] = frames
    if state['n'] < 90:
        run('args[0]()', tick, delayFrames=1)
        return
    cooked = [p for p, f in frames.items() if f != state['before'][p]]
    log.append('cooked over 60 frames with the network not shown: {}'.format(cooked or 'nothing'))
    with open(os.path.join(OUT, RUN + '.txt'), 'w') as f:
        f.write('\n'.join(log) + '\n')


run('args[0]()', tick, delayFrames=1)
print('\n'.join(log))
