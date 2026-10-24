"""DEV ONLY: Hold for 1 s, then a section change (Fosfora boundary_count) brings a keyframe: the Blocks sweep."""
import os
SHOOT_DIR = 'p1_s8'
SHOOT_CUE = 3.0
SHOOT_AUDIO = True
SHOOT_VARIANTS = {'a_smear': {'Skipon': 'off'}, 'b_blocks': {'Mode': 'blocks', 'Skipon': 'off'}}
SHOOT_EVENTS = [(0.1, '*', {'Hold': True}), (1.2, '*', {'Hold': False}), (1.25, '*', 'sig:{"boundary_count": 1}')]
SHOOT_AT = (1.1, 1.5, 1.7, 1.9, 2.1, 2.5)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
