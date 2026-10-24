"""DEV ONLY (datamosh pass 2): bisect, round 2. 1 s. Writes dev/out/datamosh/p2_bisect2.txt."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_bisect2.txt')
TMP = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_bare.tox')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
TOX = os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox')
cases = []
c = host.loadTox(TOX); c.name = 'w1_no_script'; c.viewer = False; c.op('audio').destroy(); cases.append(c)
c = host.loadTox(TOX); c.name = 'w2_audio_only'; c.viewer = False; cases.append(c)
for o in list(c.children):
    if o.valid and o.name not in ('in1_top', 'in2_audio', 'audio_low', 'audio_rms', 'audio', 'out_top', 'README'):
        o.destroy()
c = host.loadTox(TOX); c.name = 'w3_no_out_link'; c.viewer = False; c.par.opviewer = ''; cases.append(c)
b = host.create(baseCOMP, 'w4_bare_saved')
i = b.create(inCHOP, 'in2_audio')
f = b.create(audiofilterCHOP, 'audio_low'); f.inputConnectors[0].connect(i)
a = b.create(analyzeCHOP, 'audio_rms'); a.inputConnectors[0].connect(f); a.par.function = 'rmspower'
b.save(TMP)
b.destroy()
c = host.loadTox(TMP); c.name = 'w4_bare_loaded'; cases.append(c)
shell, page, src = new_effect('w5_live_shell', 'P', 'probe', 'probe', audio=True, parent_path=TDLIB_PARENT)
audio_in(shell, _ROOT)
shell.viewer = False
cases.append(shell)
F0 = {}


def done():
    lines = ['{}: cooked {}'.format(c.name, [o.name for o in c.findChildren() if o.cookAbsFrame > F0['f']] or 'none')
             for c in cases]
    open(OUTF, 'w').write('\n'.join(lines) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    for c in cases:
        c.allowCooking = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=3)


def start():
    F0['f'] = absTime.frame
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0]()', start, delayFrames=20)
print('bisecting 2')
