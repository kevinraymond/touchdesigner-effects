"""DEV ONLY (blob_track pass 1): copies of the built /tdlib_dev_blob/blob_track with different
settings, on the dancer clip and a synthetic Fosfora-shaped signal; frames saved with
dev/capture.py. Settings come from look_settings.py beside this file (rewritten per run):
  TAG       output folder under dev/out/blob_track/
  VARIANTS  {name: {par: value}}; '_clip' picks 'dancer' (default) or 'plaza', '_unwired'
            leaves input 1 empty, '_sample' sets the sample movie's file expression, '_audio'
            picks 'fosfora' (synthetic, default), 'mp3' (the sample track) or 'none'
  AT        capture times (s); EXTRA {name: (variant, inner TOP)} extra TOPs to save
  RATES     {count channel: Hz} for the synthetic signal; WHEN (variant, CHOP, threshold) also
            saves frames while that CHOP is above the threshold (dev/capture.py events)
Run after the builder: TD_PARENT=/tdlib_dev_blob dev/td.sh dev/protos/blob/pass1/look.py
After the last capture it removes the copies and the rig and stops the master cooking.
"""
import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'look_settings.py')).read(),
             'look_settings.py', 'exec'), globals())

host = op(TDLIB_PARENT)
master = host.op('blob_track')
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')

rig = host.op('rig')
if rig is not None:
    rig.destroy()
rig = host.create(baseCOMP, 'rig')
rig.nodeX, rig.nodeY = -800, 0
rig.comment = 'DEV ONLY: test inputs for blob_track.'
# Outs are ordered by name: out1 dancer, out2 plaza, out3 synthetic Fosfora, out4 the MP3.
for k, (name, y) in enumerate((('dancer', 200), ('plaza', 50))):
    clip = mk(rig, moviefileinTOP, name, 0, y, comment='x', file=os.path.join(READY, 'b{}_{}.mp4'.format(k + 1, name)))
    mk(rig, outTOP, 'out{}_{}'.format(k + 1, name), 200, y, [clip], comment='x')
# Synthetic Fosfora: beats at 2/s, bars at 0.5/s, a build ramp, a drop every 7 s, a section every 11 s.
chans = []
RATES = dict({'beat_count': 2.0, 'bar_count': 0.5, 'drop_count': 1 / 7.0, 'section_count': 1 / 11.0},
             **globals().get('RATES', {}))
for name, y in (('beat_count', -200), ('bar_count', -300), ('drop_count', -400), ('section_count', -500)):
    hz = RATES[name]
    lfo = mk(rig, lfoCHOP, 'lfo_' + name, 0, y, comment='x', wavetype='square', frequency=hz, offset=0.5, amp=0.5,
             phase=0.25)
    cnt = mk(rig, countCHOP, 'count_' + name, 200, y, [lfo], comment='x')
    chans.append(mk(rig, renameCHOP, name, 400, y, [cnt], comment='x', renamefrom='*', renameto=name))
build = mk(rig, lfoCHOP, 'build_lfo', 0, -600, comment='x', wavetype='ramp', frequency=1 / 7.0, offset=0, amp=1)
chans.append(mk(rig, renameCHOP, 'build', 400, -600, [build], comment='x', renamefrom='*', renameto='build'))
const = mk(rig, constantCHOP, 'levels', 400, -700, comment='x')
const.seq.const.numBlocks = 2
setpars(const, const0name='energy', const0value=0.6, const1name='bar_phase', const1value=0.5)
chans.append(const)
sig = mk(rig, mergeCHOP, 'signal', 600, -400, chans, comment='x')
mk(rig, outCHOP, 'out3_fosfora', 800, -400, [sig], comment='x')
mp3 = mk(rig, audiofileinCHOP, 'mp3', 0, -900, comment='x',
         file=Expr("app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'"), repeat='on')
mk(rig, outCHOP, 'out4_mp3', 800, -900, [mp3], comment='x')

for c in host.findChildren(depth=1):
    if c.name.startswith('v_'):
        c.destroy()
copies = {}
for i, (name, pars) in enumerate(VARIANTS.items()):
    c = host.copy(master, name='v_' + name)
    c.allowCooking = True
    c.nodeX, c.nodeY = 600 * (i % 4), -400 * (1 + i // 4)
    pars = dict(pars)
    unwired = pars.pop('_unwired', False)
    audio = pars.pop('_audio', 'fosfora')
    which = pars.pop('_clip', 'dancer')
    sample = pars.pop('_sample', None)
    for k, v in pars.items():
        setattr(c.par, k, v)
    if sample:
        c.op('sample').par.file.expr = sample
    if not unwired:
        c.inputConnectors[0].connect(rig.outputConnectors[0 if which == 'dancer' else 1])
    if audio == 'fosfora':
        c.inputConnectors[1].connect(rig.outputConnectors[2])
    elif audio == 'mp3':
        c.inputConnectors[1].connect(rig.outputConnectors[3])
    copies[name] = c

OUT = os.path.join(_ROOT, 'dev', 'out', 'blob_track', TAG)
tops = {name: c.op('out_top') for name, c in copies.items()}
for name, (variant, inner) in EXTRA.items():
    tops[name] = copies[variant].op(inner)
WHEN = globals().get('WHEN')   # (variant, CHOP inside it, threshold): also save frames when it is above
when = None
if WHEN:
    when = lambda: copies[WHEN[0]].op(WHEN[1])[0].eval() > WHEN[2]
capture(tops, OUT, at=AT, keep_cooking=True, when=when, events=6)

SAMPLES = {}


def sample():
    for name, c in copies.items():
        for o in c.findChildren():
            if o.isTOP or o.isCHOP:
                SAMPLES.setdefault((name, o.name), []).append((o.cookTime, getattr(o, 'gpuCookTime', 0) or 0))
        bi = c.op('blob_info')
        SAMPLES.setdefault((name, '#num_blobs'), []).append((bi['num_blobs'].eval() if bi['num_blobs'] is not None else -1, 0))


def med(v):
    v = sorted(v)
    return v[len(v) // 2] if v else 0


def report():
    lines = ['median over {} samples (ms cpu/gpu); indicative only, TD is shared'.format(
        len(next(iter(SAMPLES.values()), [])))]
    for name in copies:
        rows = [(o, med([x[0] for x in v]), med([x[1] for x in v])) for (n, o), v in SAMPLES.items() if n == name]
        blobs = [r for r in rows if r[0] == '#num_blobs']
        rows = [r for r in rows if r[0] != '#num_blobs']
        cpu, gpu = sum(r[1] for r in rows), sum(r[2] for r in rows)
        top = sorted(rows, key=lambda r: -(r[1] + r[2]))[:6]
        lines.append('{}: cpu {:.2f} gpu {:.2f} num_blobs {} | {}'.format(
            name, cpu, gpu, blobs[0][1] if blobs else '?', ', '.join('{} {:.2f}/{:.2f}'.format(*r) for r in top)))
        problems = copies[name].errors(recurse=True) + copies[name].warnings(recurse=True)
        if problems:
            lines.append('   problems: ' + problems)
    with open(os.path.join(OUT, 'costs.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')


for k in range(8):
    run('args[0]()', sample, delayMilliSeconds=int((AT[0] + (AT[-1] - AT[0]) * k / 7.0) * 1000) - 120)


def stop():
    # The Mac is shared: nothing of this run keeps playing or cooking once it is done.
    report()
    for c in list(host.findChildren(depth=1)):
        if c.name.startswith('v_') or c.name == 'rig':
            c.destroy()
    master.allowCooking = False


run('args[0]()', stop, delayMilliSeconds=int(AT[-1] * 1000) + 400)
print('look', TAG, list(copies))
