"""DEV ONLY (datamosh pass 2): bisect, round 4, every copy pulled for 10 frames then left, then 1 s:
y1 as is; y2 .width/.height expressions frozen; y3 y2 + Null CHOPs (cook type selective) in front of the Script CHOP;
y4 a shell built live (new_effect + audio_in). Writes dev/out/datamosh/p2_bisect4.txt."""
import os, re
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_bisect4.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
TOX = os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox')
L = []


def freeze(c):
    for o in c.findChildren():
        for p in o.pars():
            if p.mode == ParMode.EXPRESSION and re.search(r'\.(width|height)', p.expr):
                p.val = p.eval()


cases = []
for n in ('y1_as_is', 'y2_frozen', 'y3_frozen_nulls'):
    c = host.loadTox(TOX)
    c.name = n
    c.viewer = False
    cases.append(c)
freeze(cases[1])
freeze(cases[2])
c = cases[2]
null = c.create(nullCHOP, 'probe_null0')
L.append('null CHOP pars: ' + ' '.join(p.name + ('[' + ','.join(p.menuNames) + ']' if p.isMenu else '')
                                     for p in null.pars() if p.page is not None and p.page.name != 'Common'))
null1 = c.create(nullCHOP, 'probe_null1')
for nl in (null, null1):
    if hasattr(nl.par, 'cooktype'):
        nl.par.cooktype = 'selective'
null.inputConnectors[0].connect(c.op('in2_audio'))
null1.inputConnectors[0].connect(c.op('audio_rms'))
c.op('audio').inputConnectors[0].connect(null)
c.op('audio').inputConnectors[1].connect(null1)
shell, page, src = new_effect('y4_live_shell', 'P', 'probe', 'probe', audio=True, parent_path=TDLIB_PARENT)
script = audio_in(shell, _ROOT)
finish_effect(shell, src, '0')
shell.viewer = False
cases.append(shell)
F0 = {}


def done():
    L.extend('{}: cooked {}'.format(c.name, [o.name for o in c.findChildren() if o.cookAbsFrame > F0['f']] or 'none')
             for c in cases)
    open(OUTF, 'w').write('\n'.join(L) + '\n')
    open(OUTF + '.done', 'w').write('ok\n')
    for c in cases:
        c.allowCooking = False
    run('[o.destroy() for o in list(args[0].children) if o.valid]; args[0].destroy()', op(TDLIB_PARENT), delayFrames=3)


def pull(n):
    if n < 10:
        for c in cases:
            c.op('out_top').cook()
        cases[3].op('audio').cook()
        run('args[0](args[1])', pull, n + 1, delayFrames=1)
        return
    F0['f'] = absTime.frame + 1
    run('args[0]()', done, delayMilliSeconds=1000)


if os.path.exists(OUTF + '.done'):
    os.remove(OUTF + '.done')
run('args[0](args[1])', pull, 0, delayFrames=10)
print('bisecting 4')
