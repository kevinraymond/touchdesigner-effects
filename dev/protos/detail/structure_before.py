# DEV ONLY, for Detail's PR: dev/probes/structure_dump.py run on the effects as they were before the lib change
# (copied to ~/tdlib_old on the Mac), so dev/probes/structure_diff.py can show the rebuild changed only text.
# TD_ARGS='before' dev/td.sh dev/protos/detail/structure_before.py
import os
_text = open(os.path.expanduser('~/tdlib/dev/probes/structure_dump.py')).read()
_text = _text.replace("glob.glob(os.path.join(ROOT, 'effects', '*', '*.tox'))",
                      "glob.glob(os.path.join(os.path.expanduser('~/tdlib_old'), 'effects', '*', '*.tox'))")
assert '~/tdlib_old' in _text
exec(compile(_text, 'structure_dump.py', 'exec'), globals())
