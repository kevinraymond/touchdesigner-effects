"""DEV ONLY. Round 1, sequence 1: building (gentle natural motion) -> panned, zoomed jellybeans (global motion)."""
import os
MOSH_PREFIX = 's1_'
MOSH_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                        'dev', 'out', 'mosh', 'round1')
MOSH_SEQ = (0, 1)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'))
