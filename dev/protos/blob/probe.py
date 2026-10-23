# DEV ONLY probe: what the Blob Track TOP gives (Info DAT / Info CHOP layout, parameter names).
host = op(TDLIB_PARENT)
if host.op('probe'):
    host.op('probe').destroy()
box = host.create(baseCOMP, 'probe')
m = box.create(moviefileinTOP, 'm')
m.par.file.expr = "app.samplesFolder + '/Map/Nature/Movie.4.mp4'"
mono = box.create(monochromeTOP, 'mono'); mono.inputConnectors[0].connect(m)
lvl = box.create(lumalevelTOP, 'lvl'); lvl.inputConnectors[0].connect(mono)
blk = box.create(constantTOP, 'blk'); blk.par.colorr = blk.par.colorg = blk.par.colorb = 0.6
bt = box.create(blobtrackTOP, 'bt'); bt.inputConnectors[0].connect(lvl); bt.inputConnectors[1].connect(blk)
idat = box.create(infoDAT, 'idat'); idat.par.op = bt.path
ichop = box.create(infoCHOP, 'ichop'); ichop.par.op = bt.path
print('bt pars:', [(p.page.name if p.page else None, p.name) for p in bt.pars() if p.page and p.page.name in ('Blob Track', 'Constraints', 'Revival')])
print('bt docked:', [d.name for d in bt.docked])
import os
OUT = os.path.expanduser('~/tdlib/dev/out/blob/probe.txt')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
def report():
    L = ['idat {} x {}'.format(idat.numRows, idat.numCols)]
    for r in range(min(idat.numRows, 6)):
        L.append('  ' + repr([c.val for c in idat.row(r)]))
    L.append('ichop chans {} samples {}'.format([c.name for c in ichop.chans()][:40], ichop.numSamples))
    L.append('bt errors {!r} {!r} res {} {}'.format(bt.errors(), bt.warnings(), bt.width, bt.height))
    open(OUT, 'w').write('\n'.join(L) + '\n')
run('args[0]()', report, delayFrames=30)
