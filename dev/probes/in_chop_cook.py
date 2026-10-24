# DEV ONLY probe: why a COMP's In CHOP cooks every frame while the COMP is unused. Four COMPs,
# each with a time-varying CHOP wired to its input: In CHOP alone; In CHOP wired to a Script CHOP
# (WHEN_USED); In CHOP wired to a Null CHOP; a Script CHOP reading the In CHOP by reference, not
# by wire. Each is pulled once first, as a built effect has been. Counts cooks over 60 frames unused, then 30 frames with each COMP's last CHOP pulled.
import os
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
src = host.create(constantCHOP, 'src')
src.par.const0name = 'beat_count'
src.par.const0value.expr = 'int(absTime.seconds * 8)'
CB = """
def onGetCookLevel(scriptOp):
    return CookLevel.WHEN_USED
def onCook(scriptOp):
    {read}
    scriptOp.clear()
    scriptOp.numSamples = 1
    scriptOp.appendChan('v')[0] = v
"""
cases = {}
REAL = open(os.path.expanduser('~/tdlib/lib/audio_callbacks.py')).read()
VARIANTS = {
    'reads_rate': "x = op('in2_audio')\n    v = x.rate",
    'reads_names': "x = op('in2_audio')\n    v = len([c.name for c in x.chans()])",
    'reads_by_name': "x = op('in2_audio')\n    v = x['beat_count'][-1] if x.numChans else -1",
    'reads_numpy': "x = op('in2_audio')\n    v = float(x.numpyArray().sum()) if x.numChans else -1",
    'reads_time': "t = absTime.seconds\n    x = op('in2_audio')\n    v = x[0][-1] if x.numChans else -1",
}
for name, kind in [('script_ref', 'ref'), ('lib_callbacks', 'lib')] + [(k, k) for k in VARIANTS]:
    c = host.create(baseCOMP, name)
    i = c.create(inCHOP, 'in2_audio')
    last = i
    if kind == 'wired':
        s = c.create(scriptCHOP, 'audio')
        s.inputConnectors[0].connect(i)
        [d for d in s.docked if d.name.endswith('_callbacks')][0].text = CB.format(read="v = scriptOp.inputs[0][0][-1] if scriptOp.inputs and scriptOp.inputs[0].numChans else -1")
        last = s
    elif kind == 'null':
        last = c.create(nullCHOP, 'n')
        last.inputConnectors[0].connect(i)
    elif kind in ('lib', 'lib_np'):
        s = c.create(scriptCHOP, 'audio')
        text = REAL if kind == 'lib' else REAL.replace('def onSetupParameters(scriptOp):\n    return\n', '')
        [d for d in s.docked if d.name.endswith('_callbacks')][0].text = text
        last = s
    elif kind in VARIANTS:
        s = c.create(scriptCHOP, 'audio')
        [d for d in s.docked if d.name.endswith('_callbacks')][0].text = CB.format(read=VARIANTS[kind])
        last = s
    elif kind == 'ref':
        s = c.create(scriptCHOP, 'audio')
        [d for d in s.docked if d.name.endswith('_callbacks')][0].text = CB.format(read="t = absTime.seconds\n    x = op('in2_audio')\n    v = x[0][-1] if x.numChans else -1")
        last = s
    c.inputConnectors[0].connect(src)
    cases[name] = (c, last)
state = {'n': 0, 'log': []}
def snap():
    return {k: {o.name: o.cookAbsFrame for o in c.findChildren()} for k, (c, _) in cases.items()}
def tick():
    n = state['n']; state['n'] += 1
    if n == 5:
        for k, (c, last) in cases.items():
            last.cook()  # each has been used once, as a built effect has
    if n == 30:
        state['a'] = snap()
    if n == 90:
        b = snap()
        state['log'].append('unused 60 frames: ' + '; '.join('{}: {}'.format(k, [o for o in b[k] if b[k][o] != state['a'][k][o]]) for k in b))
        state['a'] = b
        state['vals'] = {}
    if 90 < n <= 120:
        for k, (c, last) in cases.items():
            last.cook()
            if last.numChans:
                state['vals'].setdefault(k, set()).add(round(last[0].eval(), 2))
    if n == 121:
        b = snap()
        state['log'].append('pulled 30 frames: ' + '; '.join('{}: {}'.format(k, [o for o in b[k] if b[k][o] != state['a'][k][o]]) for k in b))
        state['log'].append('distinct values seen while pulled: ' + str({k: len(v) for k, v in state['vals'].items()}))
        open(os.path.expanduser('~/tdlib/dev/out/in_chop_cook.txt'), 'w').write('\n'.join(state['log']) + '\n')
        for o in list(host.children):
            if o.valid:
                o.destroy()
        return
    run('args[0]()', tick, delayFrames=1)
tick()
