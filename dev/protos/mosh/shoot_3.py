"""DEV ONLY. Round 1, sequence 3: building -> water over rocks (sample footage only)."""
import os
MOSH_PREFIX = 's3_'
MOSH_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                        'dev', 'out', 'mosh', 'round1')
MOSH_SEQ = (0, 2)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'))
