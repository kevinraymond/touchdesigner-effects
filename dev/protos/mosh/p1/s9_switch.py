"""DEV ONLY: Mode switches mid-motion (1.0 s to Blocks, 2.0 s back to Smear): no jolt."""
import os
SHOOT_DIR = 'p1_s9'
SHOOT_CUE = 3.0
SHOOT_VARIANTS = {'a_switch': {}}
SHOOT_EVENTS = [(1.0, '*', {'Mode': 'blocks'}), (2.0, '*', {'Mode': 'smear'})]
SHOOT_AT = (0.95, 1.08, 1.2, 1.95, 2.08, 2.2)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
