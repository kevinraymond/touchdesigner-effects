# DEV ONLY: rebuild only the variants named here (wrapper around build_round1.py).
import os
BLOB_ONLY = 'a_trace,d_beat'   # edit: which variants to rebuild
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_round1.py')).read(), 'build_round1.py', 'exec'))
