# DEV ONLY: does the Trigger CHOP's Re-Trigger Delay cap flashes? A 4 Hz pulse train into
# triggers with 1 s (Calm) and 1/3 s (WCAG) delays; count pulses and triggers over 6 s.
import os
host = op(TDLIB_PARENT)
if host.op('flashtest'):
    host.op('flashtest').destroy()
box = host.create(baseCOMP, 'flashtest')
lfo = box.create(lfoCHOP, 'pulses')
lfo.par.wavetype = 'square'
lfo.par.frequency = 4
lfo.par.offset = 0.5
lfo.par.amp = 0.5
raw = box.create(countCHOP, 'raw')
raw.inputConnectors[0].connect(lfo)
res = {}
for name, delay in (('calm', 1.0), ('wcag', 1 / 3)):
    t = box.create(triggerCHOP, 'trig_' + name)
    t.inputConnectors[0].connect(lfo)
    t.par.threshup = 0.5
    t.par.retrigger = delay
    t.par.decay = 0.2
    t.par.sustain = 0
    c = box.create(countCHOP, 'count_' + name)
    c.inputConnectors[0].connect(t)
    res[name] = c
# Something must pull the counts every frame: a Null CHOP that a TOP-less Info CHOP watches is
# not enough, so read them through an always-cooking Cache TOP fed by a CHOP to TOP.
m = box.create(mergeCHOP, 'all')
for i, c in enumerate([raw] + list(res.values())):
    m.inputConnectors[i].connect(c)
ct = box.create(choptoTOP, 'tex'); ct.par.chop = m.path
keep = box.create(cacheTOP, 'keep'); keep.inputConnectors[0].connect(ct); keep.par.alwayscook = True
OUT = os.path.expanduser('~/tdlib/dev/out/blob/flash_limit.txt')
start = {}
def first():
    start.update({c.name: c[0].eval() for c in [raw] + list(res.values())})
def report():
    end = {c.name: c[0].eval() for c in [raw] + list(res.values())}
    with open(OUT, 'w') as f:
        f.write('over 6 s: ' + ', '.join('{} {:.0f}'.format(k, end[k] - start[k]) for k in end) + '\n')
    box.destroy()
run('args[0]()', first, delayMilliSeconds=1000)
run('args[0]()', report, delayMilliSeconds=7000)
