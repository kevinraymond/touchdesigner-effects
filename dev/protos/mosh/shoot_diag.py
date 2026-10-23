"""DEV ONLY. Diagnostic shoot: building -> panned jellybeans, with the flow picture."""
import os
MOSH_SEQ = (0, 1)
MOSH_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                   'dev', 'out', 'mosh', 'diag')
MOSH_EXTRA = (('f_vis', 'flow/vis'),)
op(TDLIB_PARENT + '/flow/keep').par.alwayscook = True
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'))
