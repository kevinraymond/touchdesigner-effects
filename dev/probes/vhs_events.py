"""DEV ONLY probe: while dev/protos/vhs_crt/look.py's build runs, save its output on the first frames an inner CHOP
channel passes a threshold (an e-ink refresh at its blackest, a burst): TD_ARGS='chop=refresh above=0.5 out=ink_ev'
dev/td.sh dev/probes/vhs_events.py, then dev/td.sh --pull dev/out/vhs_crt/<out>/done"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
opts = dict(chop='refresh', above='0.5', out='events', seconds='4', events='4')
opts.update(w.split('=', 1) for w in TDLIB_ARGS)
fx = op(TDLIB_PARENT + '/vhs_crt')
chop, above = fx.op(opts['chop']), float(opts['above'])
capture({'out': fx.op('out_top')}, os.path.join(_ROOT, 'dev', 'out', 'vhs_crt', opts['out']),
        at=(float(opts['seconds']),), keep_cooking=True, when=lambda: chop[0] > above, events=int(opts['events']))
