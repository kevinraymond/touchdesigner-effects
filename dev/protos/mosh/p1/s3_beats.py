"""DEV ONLY: defaults candidates with a 2/s beat (bars every 2 s), through the dancer's loop cut (~1.5 s)."""
import os
SHOOT_DIR = 'p1_s3'
SHOOT_CUE = 8.6
SHOOT_AUDIO = True
SHOOT_VARIANTS = {'a_m5': {'Mosh': 0.5}, 'b_m5mo13': {'Mosh': 0.5, 'Motion': 1.3},
                  'c_m3mo15': {'Mosh': 0.3, 'Motion': 1.5}, 'd_blk': {'Mode': 'blocks', 'Mosh': 0.5, 'Motion': 1.3}}
SHOOT_AT = (1.2, 1.7, 2.0, 2.4, 3.0, 3.6, 4.4, 5.4)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
