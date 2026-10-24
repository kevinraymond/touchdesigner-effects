"""DEV ONLY (datamosh pass 1). Test rig around the built effect in TDLIB_PARENT, then a timed shoot.

    TD_PARENT=/tdlib_dev_mosh dev/td.sh dev/protos/mosh/p1/<wrapper>.py    (wrappers set the globals below)
    dev/td.sh --pull dev/out/datamosh/<dir>/done

Rig: 'clip' (the dancer, or SHOOT_CLIP), 'sig' (a Fosfora-shaped CHOP: beat_count 2/s, bar_count
every 4 beats, build/drop_count/section_count/energy/bar_phase from a Constant CHOP the timeline
sets), and one copy of /datamosh per variant, each wired to clip and (if SHOOT_AUDIO) sig.
Timeline: SHOOT_EVENTS = [(seconds, variant or '*', {par: value} or 'sig:{chan: value}' or 'pulse:Name')].
Logs the clock (new frame, cut, mean), skip_env, key_env, beat/bar counts per frame to log.txt.
"""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())

G = globals()
OUTD = os.path.join(_ROOT, 'dev', 'out', 'datamosh', G.get('SHOOT_DIR', 'test'))
CLIP = G.get('SHOOT_CLIP', os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4'))
CUE = G.get('SHOOT_CUE', 8.0)            # seconds into the clip to start (the dancer loops at 10.1 s)
VARIANTS = G.get('SHOOT_VARIANTS', {'smear': {}})
EVENTS = G.get('SHOOT_EVENTS', [])
AT = G.get('SHOOT_AT', (1.5, 2.2, 2.6, 3.0, 3.6, 4.5, 6.0))
AUDIO = G.get('SHOOT_AUDIO', False)
if G.get('SHOOT_ALIGN'):   # start the captures relative to the next multiple of SHOOT_ALIGN seconds (the unwired cut)
    _off = G['SHOOT_ALIGN'] - (absTime.seconds - G.get('SHOOT_PHASE', 0)) % G['SHOOT_ALIGN']
    _off = _off + G['SHOOT_ALIGN'] if _off < 1.2 else _off
    AT = tuple(round(a + _off, 3) for a in AT)
    EVENTS = [(t + _off, w, x) for t, w, x in EVENTS]
host = op(TDLIB_PARENT)
fx = host.op('datamosh')
fx.nodeX, fx.nodeY = 0, 600
fx.allowCooking = False
for c in list(host.children):
    if c.name.startswith('v_') or c.name in ('sig_beats', 'sig_beatc', 'sig_bars', 'sig_const', 'sig', 'meter', 'meter2'):
        c.destroy()
clip = host.op('clip') or host.create(moviefileinTOP, 'clip')
clip.par.file = CLIP
clip.par.play = True
clip.par.cuepoint = CUE
clip.par.cuepointunit = 'seconds'
clip.nodeX, clip.nodeY = -600, 0
lfo = host.create(lfoCHOP, 'sig_beats')
lfo.par.wavetype, lfo.par.frequency, lfo.par.offset, lfo.par.amp = 'square', 2, 0.5, 0.5
cnt = host.create(countCHOP, 'sig_beatc')
cnt.inputConnectors[0].connect(lfo)
cnt.par.output = 'off'
const = host.create(constantCHOP, 'sig_const')
const.seq.const.numBlocks = 6
for i, (n, v) in enumerate((('energy', 0.5), ('build', 0.0), ('drop_count', 0), ('boundary_count', 0),
                            ('beat_phase', 0.0), ('bar_phase', 0.0))):
    setattr(const.par, 'const{}name'.format(i), n)
    setattr(const.par, 'const{}value'.format(i), v)
ren = host.create(renameCHOP, 'sig_bars')
ren.inputConnectors[0].connect(cnt)
ren.par.renamefrom, ren.par.renameto = '*', 'beat_count'
sig = host.create(mergeCHOP, 'sig')
sig.inputConnectors[0].connect(ren)
sig.inputConnectors[1].connect(const)
tops, comps = {'0_input': clip}, {}
for i, (name, pars) in enumerate(VARIANTS.items()):
    v = host.copy(fx, name='v_' + name)
    v.allowCooking = True
    v.nodeX, v.nodeY = 600 * i, 0
    for k, val in pars.items():
        setattr(v.par, k, val)
    if not G.get('SHOOT_UNWIRED'):
        v.inputConnectors[0].connect(clip)
    if AUDIO == 'mp3':
        mp3 = host.op('mp3') or host.create(audiofileinCHOP, 'mp3')
        mp3.par.file = app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'
        mp3.par.repeat = 'on'
        v.inputConnectors[1].connect(mp3)
    elif AUDIO:
        v.inputConnectors[1].connect(sig)
    tops[name] = v.op('out_top')
    if G.get('SHOOT_UNWIRED'):
        tops['0_input'] = v.op('source')
    comps[name] = v
run("args[0].par.cuepulse.pulse()", clip, delayFrames=1)
cnt.par.resetpulse.pulse()
for fb in host.findChildren(type=feedbackTOP):
    fb.par.resetpulse.pulse()


def event(spec):
    who, what = spec
    for name, v in comps.items():
        if who not in ('*', name):
            continue
        if isinstance(what, str) and what.startswith('pulse:'):
            getattr(v.par, what[6:]).pulse()
        elif isinstance(what, str) and what.startswith('sig:'):
            for k, val in eval(what[4:]).items():
                for i in range(6):
                    if getattr(const.par, 'const{}name'.format(i)).eval() == k:
                        setattr(const.par, 'const{}value'.format(i), val)
        else:
            for k, val in what.items():
                setattr(v.par, k, val)


for t, who, what in EVENTS:
    run('args[0](args[1])', event, (who, what), delayMilliSeconds=int(t * 1000))

LOG = []
first = list(comps.values())[0]
meter = host.create(toptoCHOP, 'meter')
meter.par.top = first.op('clock')
meter2 = host.create(toptoCHOP, 'meter2')
meter2.par.top = first.op('change_avg')
T0 = absTime.seconds


def tick(n):
    try:
        meter.cook(force=True)
        meter2.cook(force=True)
        a = first.op('audio')
        LOG.append('{:.3f} d {:.4f} new {:.0f} cut {:.0f} mean {:.4f} skip {:.2f} key {:.2f} beats {:.0f} bars {:.0f} drops {:.0f} build {:.2f}'.format(
            absTime.seconds - T0, meter2['r'][0], meter['r'][0], meter['g'][0], meter['b'][0], first.op('skip_env')['skip'][0],
            first.op('key_env')['key'][0], a['beat_count'][0], a['bar_count'][0], a['drop_count'][0], a['build'][0]))
    except Exception as e:
        LOG.append('err {}'.format(e))
    if absTime.seconds - T0 < max(AT) + 0.3:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
    else:
        os.makedirs(OUTD, exist_ok=True)
        open(os.path.join(OUTD, 'log.txt'), 'w').write('\n'.join(LOG) + '\n')
        for c in op(TDLIB_PARENT).findChildren(type=COMP, depth=1):
            c.allowCooking = False
        clip.par.play = False


capture(tops, OUTD, at=AT, keep_cooking=True)
tick(0)
problems = []
for v in comps.values():
    for e in (v.errors(recurse=True), v.warnings(recurse=True)):
        if e:
            problems.append('{}: {}'.format(v.name, e))
print('shooting', list(tops), 'problems:', problems)
