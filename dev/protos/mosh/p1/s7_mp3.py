"""DEV ONLY: unwired grass -> jellybeans cut (t = 0), the sample MP3 on input 2 (skips every bar)."""
import os
SHOOT_DIR = 'p1_s7'
SHOOT_UNWIRED = True
SHOOT_ALIGN, SHOOT_PHASE = 12, 6
SHOOT_AUDIO = 'mp3'
SHOOT_VARIANTS = {'a_smear': {}, 'b_blocks': {'Mode': 'blocks'}}
SHOOT_AT = (-0.3, 0.4, 1.0, 1.6, 2.4, 3.2, 4.2)
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoot.py')).read(), 'shoot.py', 'exec'), globals())
