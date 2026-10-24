"""DEV ONLY: Fosfora-shaped song structure: a build, the drop (keyframe), a Skip pulse, a new section."""
import os
SHOOT_DIR = 'p1_s4'
SHOOT_CUE = 2.0
SHOOT_AUDIO = True
SHOOT_VARIANTS = {'a_smear': {}, 'b_blocks': {'Mode': 'blocks'}, 'c_off': {'Flashing': 'off'}}
SHOOT_EVENTS = [(0.3, '*', 'sig:{"build": 0.3}'), (0.9, '*', 'sig:{"build": 0.7}'), (1.5, '*', 'sig:{"build": 1.0}'),
                (2.2, '*', 'sig:{"build": 0.0, "drop_count": 1}'), (3.6, '*', 'pulse:Skip'),
                (4.6, '*', 'sig:{"section_count": 1}')]
SHOOT_AT = (0.8, 1.5, 2.15, 2.5, 2.9, 3.5, 4.0, 4.55, 4.9, 5.4)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
