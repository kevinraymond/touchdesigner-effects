"""DEV ONLY: the dancer's loop cut, Smear and Blocks at their defaults, no audio."""
import os
SHOOT_DIR = 'p1_s1'
SHOOT_VARIANTS = {'smear': {}, 'blocks': {'Mode': 'blocks'}, 'clean': {'Mosh': 0.0, 'Moshcuts': False}}
SHOOT_AT = (1.0, 2.0, 2.4, 2.8, 3.2, 3.8, 4.6, 6.0)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
