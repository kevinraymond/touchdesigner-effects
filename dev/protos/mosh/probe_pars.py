# DEV ONLY probe: parameter names of the operators the mosh prototypes use.
import os
host = op(TDLIB_PARENT)
out = []
for kind in (glslTOP, feedbackTOP, cacheTOP, analyzeTOP, transformTOP, switchTOP, selectTOP, fitTOP,
             audiofileinCHOP, audiofilterCHOP, analyzeCHOP, triggerCHOP, logicCHOP, filterCHOP, lagCHOP,
             countCHOP, mathCHOP, constantCHOP, toptoCHOP, timerCHOP):
    if host.op('pp'):
        host.op('pp').destroy()
    o = host.create(kind, 'pp')
    pars = []
    for p in o.pars():
        if p.page is not None and p.page.name in ('Common',) and kind not in (glslTOP,):
            continue
        s = p.name
        if p.isMenu:
            s += '[' + ','.join((p.menuNames or [])[:12]) + ']'
        pars.append(s)
    out.append('{}: {}'.format(o.OPType, ' '.join(pars)))
    if kind is glslTOP:
        out.append('  glsl docked: ' + ', '.join(d.name for d in o.docked))
        out.append('  format menu: ' + ','.join(o.par.format.menuNames))
    o.destroy()
path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'dev', 'out', 'mosh', 'pars.txt')
os.makedirs(os.path.dirname(path), exist_ok=True)
open(path, 'w').write('\n'.join(out) + '\n')
print('wrote', path, len(out))
