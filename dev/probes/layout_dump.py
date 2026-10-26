# DEV ONLY probe: every built effect's network as JSON, to draw and measure outside TouchDesigner.
# Each effects/<n>/<n>.tox (and the showreel) is loaded into a scratch COMP, its children dumped
# (place, size, family, wires, docking, which siblings its parameters and expressions name), then
# removed. TDLIB_ARGS: the run's folder, then the components (default: all). Writes
# dev/out/layout/<run>/layout.json.
import glob
import json
import os
import re

ROOT = os.path.expanduser('~/tdlib')
RUN = (globals().get('TDLIB_ARGS') or ['r1'])[0]
OUT = os.path.join(ROOT, 'dev', 'out', 'layout', RUN)
NAMED = re.compile(r"""op\(\s*['"]([A-Za-z0-9_]+)['"]""")
os.makedirs(OUT, exist_ok=True)
host = op(TDLIB_PARENT)
scratch = host.op('layout_probe') or host.create(baseCOMP, 'layout_probe')
paths = sorted(glob.glob(os.path.join(ROOT, 'effects', '*', '*.tox'))) + \
    sorted(glob.glob(os.path.join(ROOT, 'bundles', '*', '*.tox')))
NAMES = (globals().get('TDLIB_ARGS') or [])[1:]
paths = [p for p in paths if not NAMES or os.path.splitext(os.path.basename(p))[0] in NAMES]
dump = {}
for path in paths:
    for o in list(scratch.children):
        if o.valid:
            o.destroy()
    fx = scratch.loadTox(path)
    fx.viewer = False
    nodes, boxes = [], []
    for o in fx.children:
        if o.OPType == 'annotateCOMP':
            boxes.append({'name': o.name, 'title': o.par.Titletext.eval(), 'x': o.nodeX, 'y': o.nodeY,
                          'w': o.nodeWidth, 'h': o.nodeHeight, 'color': [o.par.Backcolorr.eval(),
                                                                         o.par.Backcolorg.eval(), o.par.Backcolorb.eval()]})
            continue
        names = set()
        for p in o.pars():
            if p.isOP and p.mode == ParMode.CONSTANT and isinstance(p.val, str) and p.val:
                names.add(p.val.split('/')[-1])
            if p.mode == ParMode.EXPRESSION:
                names.update(NAMED.findall(p.expr))
        nodes.append({
            'name': o.name, 'type': o.OPType, 'family': o.family,
            'x': o.nodeX, 'y': o.nodeY, 'w': o.nodeWidth, 'h': o.nodeHeight,
            'inputs': [[c.owner.name for c in ic.connections] for ic in o.inputConnectors],
            'dock': o.dock.name if o.dock else None,
            'showdocked': getattr(o, 'showDocked', None),
            'viewer': o.viewer, 'color': list(o.color),
            'refs': sorted(n for n in names if n != o.name and fx.op(n) is not None),
            'comment': o.comment,
        })
    dump[fx.name] = {'nodes': nodes, 'boxes': boxes}
    fx.destroy()
scratch.destroy()
with open(os.path.join(OUT, 'layout.json'), 'w') as f:
    json.dump(dump, f, indent=1)
print('dumped', len(dump), 'networks:', ', '.join('{} {}'.format(k, len(v['nodes'])) for k, v in dump.items()))
