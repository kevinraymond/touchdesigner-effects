"""DEV ONLY. Read-only: the default of some parameters of a new operator, and the value they have on an
operator of the open project. TD_ARGS='glslTOP inputextenduv inputfiltertype' dev/td.sh dev/probes/par_defaults.py
(a path after the names, such as /tdlib_dev/particles/sim, also prints that operator's values)."""
kind, *names = [a for a in TDLIB_ARGS if not a.startswith('/')]
paths = [a for a in TDLIB_ARGS if a.startswith('/')]
host = op(TDLIB_PARENT)
o = host.create(eval(kind), 'par_defaults_probe')
try:
    for n in names:
        p = getattr(o.par, n)
        print(kind, n, 'default', p.default, 'new', p.eval())
    for path in paths:
        for n in names:
            print(path, n, getattr(op(path).par, n).eval())
finally:
    o.destroy()
