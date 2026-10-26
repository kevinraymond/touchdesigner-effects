# DEV ONLY probe: everything about each built component except where its operators sit, as JSON, so two builds can be
# compared (dev/probes/structure_diff.py): every operator below the top (not inside a Network Box, which is
# TouchDesigner's own), its type, comment, flags, wires, docked DATs, every parameter (mode, value or expression;
# custom ones with their default, range, menu and help) and a DAT's text. TDLIB_ARGS: the run's folder name, then
# the components (default: every effect and bundle). Writes dev/out/structure/<run>/<name>.json.
import glob
import json
import os

ROOT = os.path.expanduser('~/tdlib')
ARGS = TDLIB_ARGS or ['r1']
OUT = os.path.join(ROOT, 'dev', 'out', 'structure', ARGS[0])
os.makedirs(OUT, exist_ok=True)
host = op(TDLIB_PARENT)
scratch = host.op('structure_probe') or host.create(baseCOMP, 'structure_probe')
paths = sorted(glob.glob(os.path.join(ROOT, 'effects', '*', '*.tox'))) + \
    sorted(glob.glob(os.path.join(ROOT, 'bundles', '*', '*.tox')))
paths = [p for p in paths if len(ARGS) < 2 or os.path.splitext(os.path.basename(p))[0] in ARGS[1:]]


def boxed(o, top):
    p = o.parent()
    while p is not None and p != top:
        if p.OPType == 'annotateCOMP':
            return True
        p = p.parent()
    return False


def par_state(p):
    s = {'mode': str(p.mode)}
    if p.mode == ParMode.EXPRESSION:
        s['expr'] = p.expr
    elif p.mode == ParMode.EXPORT:
        s['export'] = str(p.exportSource)
    elif p.mode == ParMode.BIND:
        s['bind'] = p.bindExpr
    else:
        s['val'] = str(p.val)
    if p.isCustom:
        s.update(default=str(p.default), help=p.help, label=p.label, page=p.page.name if p.page else None,
                 min=str(p.min), max=str(p.max), normMin=str(p.normMin), normMax=str(p.normMax),
                 clampMin=p.clampMin, clampMax=p.clampMax, readOnly=p.readOnly, enableExpr=p.enableExpr,
                 startSection=p.startSection, menuNames=list(p.menuNames) if p.isMenu else None,
                 menuLabels=list(p.menuLabels) if p.isMenu else None)
    return s


done = []
for path in paths:
    for o in list(scratch.children):
        if o.valid:
            o.destroy()
    fx = scratch.loadTox(path)
    ops = {}
    for o in [fx] + list(fx.findChildren()):
        if boxed(o, fx):
            continue
        rel = '.' if o == fx else o.path[len(fx.path) + 1:]
        ops[rel] = {
            'type': o.OPType, 'comment': o.comment, 'tags': sorted(o.tags),
            'flags': {k: getattr(o, k, None) for k in ('viewer', 'bypass', 'lock', 'display', 'render', 'cloneImmune',
                                                       'allowCooking', 'expose', 'activeViewer')},
            'inputs': [[c.owner.name + ':' + str(c.index) for c in ic.connections] for ic in o.inputConnectors],
            'docked': sorted(d.name for d in o.docked), 'dock': o.dock.name if o.dock else None,
            'pars': {p.name: par_state(p) for p in o.pars()},
            'text': o.text if o.isDAT else None,
            'pages': [pg.name for pg in o.customPages] if o.isCOMP else None,
        }
    with open(os.path.join(OUT, fx.name + '.json'), 'w') as f:
        json.dump(ops, f, indent=0, sort_keys=True)
    done.append('{} {}'.format(fx.name, len(ops)))
    fx.destroy()
scratch.destroy()
print('dumped', len(done), ':', ', '.join(done))
