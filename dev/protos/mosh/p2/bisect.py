"""DEV ONLY (datamosh pass 2): what inside datamosh makes audio_in()'s operators cook with nothing pulling it.
Copies of the .tox, unwired, each with one thing taken away; 1 s. Writes dev/out/datamosh/p2_bisect.txt."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUTF = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'p2_bisect.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()


def load(name):
    c = host.loadTox(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.tox'))
    c.name = name
    c.viewer = False
    return c


def const_exprs(c, needle):
    n = 0
    for o in c.findChildren():
        for p in o.pars():
            if p.mode == ParMode.EXPRESSION and needle in p.expr:
                p.val = 0
                n += 1
    return n


cases = [load('v1_as_is')]
c = load('v2_no_audio_refs'); cases.append(c); const_exprs(c, "op('audio')")
c = load('v3_no_chop_refs'); cases.append(c); const_exprs(c, "op('")
c = load('v4_no_window'); cases.append(c); c.op('window').destroy()
c = load('v5_no_events'); cases.append(c)
for n in ('counts', 'steps', 'skip_audio', 'skip_on', 'key_audio', 'key_on', 'key_named', 'skip_any', 'key_any',
          'events', 'flash_limit', 'flash', 'skip_sel', 'key_sel', 'skip_env', 'key_env', 'skip_pulse', 'key_pulse'):
    c.op(n).destroy()
c = load('v6_no_mosh_motion'); cases.append(c); c.op('mosh').destroy(); c.op('motion').destroy()
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
print('bisecting')
