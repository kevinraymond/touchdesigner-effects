"""DEV ONLY. Round 1, sequence 2: pushed-in oil drums -> moving shapes over a still background (local motion)."""
import os
MOSH_PREFIX = 's2_'
MOSH_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                        'dev', 'out', 'mosh', 'round1')
MOSH_SEQ = (5, 3)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'))
