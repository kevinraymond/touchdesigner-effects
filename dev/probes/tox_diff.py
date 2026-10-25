"""DEV ONLY probe: compare two builds of an effect, operator by operator: type, wiring, every parameter
(value or expression) and DAT text with // comments and comment lines dropped. Words: a=<tox> b=<tox>
(repo-relative). TD_ARGS='a=dev/out/compare/datamosh_head.tox b=effects/datamosh/datamosh.tox' dev/td.sh dev/probes/tox_diff.py"""
import os, re
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
opts = dict(w.split('=', 1) for w in TDLIB_ARGS)
host = op(TDLIB_PARENT)
for n in ('diff_a', 'diff_b'):
    if host.op(n):
        host.op(n).destroy()
comps = []
for n in ('a', 'b'):
    c = host.loadTox(os.path.join(_ROOT, opts[n]))
    c.name = 'diff_' + n
    comps.append(c)


def code(text):
    lines = [re.sub(r'//.*$', '', l).rstrip() for l in text.split('\n')]
    return '\n'.join(l for l in lines if l.strip())


def desc(c):
    out = {}
    for o in c.findChildren():
        rel = o.path[len(c.path) + 1:]
        pars = {}
        for p in o.pars():
            if p.name in ('comment',) or p.isPulse:
                continue
            pars[p.name] = ('expr', p.expr) if p.mode == ParMode.EXPRESSION else ('val', str(p.val))
        out[rel] = dict(type=o.OPType, inputs=[i.name for i in o.inputs], pars=pars,
                        text=code(o.text) if o.isDAT and o.name != 'README' else None)
    return out


da, db = desc(comps[0]), desc(comps[1])
diffs = []
for k in sorted(set(da) | set(db)):
    if k not in da or k not in db:
        diffs.append('only in {}: {}'.format('b' if k in db else 'a', k))
        continue
    a, b = da[k], db[k]
    for f in ('type', 'inputs', 'text'):
        if a[f] != b[f]:
            diffs.append('{} {} differs'.format(k, f))
    for p in sorted(set(a['pars']) | set(b['pars'])):
        if a['pars'].get(p) != b['pars'].get(p):
            diffs.append('{}.{}: {} -> {}'.format(k, p, a['pars'].get(p), b['pars'].get(p)))
print(len(da), 'operators in a,', len(db), 'in b;', len(diffs), 'differences')
print('\n'.join(diffs[:60]))
for c in comps:
    c.destroy()
