# DEV ONLY probe (blob pass 1): API details the builder relies on.
import os
host = op(TDLIB_PARENT)
box = host.op('probe_api')
if box:
    box.destroy()
box = host.create(baseCOMP, 'probe_api')
print('stepSeconds', hasattr(absTime, 'stepSeconds'), getattr(absTime, 'stepSeconds', None))
m = box.create(mathCHOP, 'm')
print('math chanop', m.par.chanop.menuNames)
print('math chopop', m.par.chopop.menuNames)
h = box.create(holdCHOP, 'h')
print('hold pars', [(p.name, p.eval(), p.menuNames if p.isMenu else '') for p in h.pars() if p.page and p.page.name == 'Hold'])
s = box.create(slopeCHOP, 's')
print('slope pars', [(p.name, p.eval(), p.menuNames if p.isMenu else '') for p in s.pars() if p.page and p.page.name == 'Slope'])
t = box.create(triggerCHOP, 't')
print('trigger defaults', {n: t.par[n].eval() for n in ('threshup', 'triggeron', 'retrigger', 'attack', 'peak', 'decay', 'sustain', 'release', 'complete')})
bt = box.create(blobtrackTOP, 'bt')
print('bt defaults', {p.name: p.eval() for p in bt.pars() if p.page and p.page.name in ('Blob Track', 'Constraints', 'Revival')})
fb = box.create(feedbackTOP, 'fb')
print('fb pars', [(p.name, p.eval()) for p in fb.pars() if p.page and p.page.name == 'Feedback'])
c = box.create(choptoTOP, 'c')
print('choptotop', [(p.name, p.eval(), p.menuNames if p.isMenu else '') for p in c.pars() if p.page and p.page.name == 'CHOP to'])
pg = box.appendCustomPage('X')
a = pg.appendMenu('Mode', label='Mode')[0]
a.menuNames = ['a', 'b']; a.menuLabels = ['A', 'B']
b = pg.appendFloat('Amt', label='Amt')[0]
print('enableExpr attr', hasattr(b, 'enableExpr'))
b.enableExpr = "me.par.Mode == 'b'"
print('enable now', b.enable)
a.val = 'b'
print('enable after', b.enable)
g = box.create(glslTOP, 'g')
print('glsl docked', [d.name for d in g.docked])
print('glsl res pars', [(p.name, p.eval(), p.menuNames if p.isMenu else '') for p in g.pars() if p.name in ('outputresolution', 'format', 'inputextenduv', 'extend')])
print('blob docked', [d.name for d in bt.docked])
print('lim pars', [(p.name, p.menuNames) for p in box.create(limitCHOP, 'l').pars() if p.name in ('type', 'min', 'max')])
box.destroy()
