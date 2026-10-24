"""DEV ONLY: unwired (the sample movie): defaults, Blocks with a Keyframe sweep, Hold, Chroma."""
import os
SHOOT_DIR = 'p1_s5'
SHOOT_UNWIRED = True
SHOOT_VARIANTS = {'a_smear': {}, 'b_blocks': {'Mode': 'blocks', 'Mosh': 0.8}, 'c_hold': {}, 'd_chroma': {'Chroma': 1.0, 'Mosh': 0.8}}
SHOOT_EVENTS = [(1.0, 'c_hold', {'Hold': True}), (3.0, 'c_hold', {'Hold': False}), (3.2, 'b_blocks', 'pulse:Keyframe')]
SHOOT_AT = (0.9, 2.0, 3.0, 3.4, 3.6, 3.9, 4.6)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
