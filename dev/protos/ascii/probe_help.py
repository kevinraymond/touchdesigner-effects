# DEV ONLY probe: copy TouchDesigner's parameter help (Config/TDParameterHelp.json) to dev/out for local lookup.
import os, shutil
src = app.installFolder + '/Contents/Resources/tfs/Config/TDParameterHelp.json'
dst = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'out', 'ascii')
os.makedirs(dst, exist_ok=True)
shutil.copy(src, dst)
print('copied', os.path.getsize(src), 'bytes')
