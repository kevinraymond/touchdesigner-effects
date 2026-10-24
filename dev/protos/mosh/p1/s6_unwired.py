"""DEV ONLY: unwired, through the sample cut (t = 0 is the cut): Smear, Blocks + Keyframe, Chroma."""
import os
SHOOT_DIR = 'p1_s6'
SHOOT_UNWIRED = True
SHOOT_ALIGN = 6
SHOOT_VARIANTS = {'a_smear': {}, 'b_blocks': {'Mode': 'blocks'}, 'c_chroma': {'Chroma': 1.0}}
SHOOT_EVENTS = [(3.0, 'b_blocks', 'pulse:Keyframe')]
SHOOT_AT = (-0.3, 0.3, 0.8, 1.5, 2.5, 3.3, 3.6, 4.5)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
