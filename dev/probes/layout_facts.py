# DEV ONLY probe: what laying out a network from Python needs (2025.33230). Does moving a GLSL TOP move the
# DATs docked to it, and does re-docking put them back? Can a pixel-mode GLSL TOP lose its _compute and _info
# DATs? How is a Network Box (Annotate COMP) made, and does it survive a .tox round trip? Changes nothing outside
# a scratch COMP. Writes dev/out/layout_facts/<TDLIB_ARGS[0] or 'r1'>.txt.
import os

ROOT = os.path.expanduser('~/tdlib')
OUT = os.path.join(ROOT, 'dev', 'out', 'layout_facts')
RUN = (globals().get('TDLIB_ARGS') or ['r1'])[0]
os.makedirs(OUT, exist_ok=True)
log = []
host = op(TDLIB_PARENT)
old = host.op('layout_facts')
if old:
    old.destroy()
c = host.create(baseCOMP, 'layout_facts')


def where(o):
    return '{} ({}, {}) {}x{}'.format(o.name, o.nodeX, o.nodeY, o.nodeWidth, o.nodeHeight)


g = c.create(glslTOP, 'g')
log.append('created: ' + where(g) + ' | ' + ', '.join(where(d) for d in g.docked))
g.nodeX, g.nodeY = 600, 300
log.append('nodeX/Y set: ' + where(g) + ' | ' + ', '.join(where(d) for d in g.docked))
for d in g.docked:
    d.dock = g
log.append('re-docked: ' + ', '.join(where(d) for d in g.docked))
log.append('showDocked: {}; dock attrs: {}'.format(getattr(g, 'showDocked', 'n/a'),
                                                   [a for a in dir(g) if 'dock' in a.lower()]))
log.append('computedat {!r} pixeldat {!r} mode {!r}'.format(g.par.computedat.eval(), g.par.pixeldat.eval(),
                                                            g.par.mode.eval()))
g.op('g_compute').destroy() if g.op('g_compute') else None
c.op('g_compute') and c.op('g_compute').destroy()
c.op('g_info') and c.op('g_info').destroy()
g.par.computedat = ''
g.cook(force=True)
log.append('without _compute/_info: errors {!r} warnings {!r} docked {}'.format(
    g.errors(), g.warnings(), [d.name for d in g.docked]))

b = c.create(annotateCOMP, 'box_picture')
log.append('annotate: utility {} family {} type {}'.format(getattr(b, 'utility', 'n/a'), b.family, b.OPType))
log.append('annotate pars: ' + ' '.join('{}={!r}'.format(p.name, p.eval()) for p in b.pars()
                                         if p.page is not None and p.page.name not in ('Common',)))
log.append('annotate menus: ' + ' '.join('{}:{}'.format(p.name, p.menuNames) for p in b.pars() if p.isMenu))
log.append('children: {} | findChildren: {} | findChildren utility: {}'.format(
    [o.name for o in c.children], [o.name for o in c.findChildren(depth=1)],
    [o.name for o in c.findChildren(depth=1, includeUtility=True)]))
path = os.path.join(OUT, 'facts_{}.tox'.format(RUN))
c.save(path)
back = host.loadTox(path)
log.append('reloaded: ' + ', '.join('{} {}'.format(o.name, o.OPType) for o in back.findChildren(depth=1, includeUtility=True)))
back.destroy()
with open(os.path.join(OUT, RUN + '.txt'), 'w') as f:
    f.write('\n'.join(log) + '\n')
print('\n'.join(log))
