"""DEV ONLY: how much Mosh / Motion it takes to read on the dancer."""
import os
SHOOT_DIR = 'p1_s2'
SHOOT_VARIANTS = {'a_m4': {}, 'b_m7': {'Mosh': 0.7}, 'c_m9': {'Mosh': 0.9}, 'd_m10': {'Mosh': 1.0},
                  'e_mo16': {'Motion': 1.6}, 'f_blk7': {'Mode': 'blocks', 'Mosh': 0.7}}
SHOOT_AT = (1.0, 1.8, 2.3, 2.7, 3.2, 4.0, 5.0)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
