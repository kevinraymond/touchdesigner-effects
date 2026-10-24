"""DEV ONLY: the pass-1 sheet. The dancer with a Fosfora-shaped signal (2 beats/s, a skip every bar on Calm):
the loop cut (~1.7 s), a build (3-4.2 s) whose drop brings a keyframe (4.8 s), a section change (6.6 s)."""
import os
SHOOT_DIR = 'pass1'
SHOOT_CUE = 8.4
SHOOT_AUDIO = True
SHOOT_VARIANTS = {'a_smear': {}, 'b_blocks': {'Mode': 'blocks'}}
SHOOT_EVENTS = [(3.0, '*', 'sig:{"build": 0.4}'), (3.6, '*', 'sig:{"build": 0.8}'), (4.2, '*', 'sig:{"build": 1.0}'),
                (4.8, '*', 'sig:{"build": 0.0, "drop_count": 1}'), (6.6, '*', 'sig:{"boundary_count": 1}')]
SHOOT_AT = (1.5, 1.9, 2.3, 2.8, 3.5, 4.2, 4.7, 5.2, 5.8, 6.5, 7.2)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
