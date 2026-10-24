# DEV ONLY probe for the ASCII pass 1: menu names and behaviors the builder depends on.
#   TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/probe_pass1.py
import os

host = op(TDLIB_PARENT)
if host.op('probe'):
    host.op('probe').destroy()
box = host.create(baseCOMP, 'probe')


def menu(o, name):
    p = getattr(o.par, name)
    print('{}.{}: {}'.format(o.OPType, name, list(p.menuNames)))


g = box.create(glslTOP, 'g')
menu(g, 'format')
menu(g, 'outputresolution')
menu(g, 'inputfiltertype')
print('glsl docked:', [d.name for d in g.docked])
t = box.create(textTOP, 't')
menu(t, 'typeface')
menu(t, 'fontsizexunit')
menu(t, 'antialias') if hasattr(t.par, 'antialias') else None
print('text font now', t.par.font.eval(), 'has fontfile', hasattr(t.par, 'fontfile'))
a = box.create(analyzeTOP, 'a')
menu(a, 'op')
menu(a, 'analyzechannel')
m = box.create(mathCHOP, 'm')
menu(m, 'chopop')
menu(m, 'chanop')
lag = box.create(lagCHOP, 'lag')
print('lag pars', [p.name for p in lag.pars() if p.name.startswith('lag')])
menu(lag, 'lagunit')
b = box.create(blurTOP, 'b')
print('blur pars', [p.name for p in b.pars()][:20])
tr = box.create(triggerCHOP, 'tr')
menu(tr, 'dshape')
menu(tr, 'triggeron')
print('trigger thresh defaults', tr.par.threshold.eval(), tr.par.threshup.eval(), tr.par.threshdown.eval())
sel = box.create(selectCHOP, 'sel')
print('select pars', [p.name for p in sel.pars()][:12])
c = box.create(constantCHOP, 'c')
c.par.const0value.expr = 'math.ceil(1.2) + absTime.stepSeconds * 0'
print('math in expr ->', c.par.const0value.eval())
try:
    print('absTime.stepSeconds', absTime.stepSeconds)
except Exception as e:
    print('no stepSeconds', e)
sc = box.create(scriptCHOP, 'sc')
print('script docked', [d.name for d in sc.docked])
ev = box.create(evaluateDAT, 'ev')
print('evaluate pars', [p.name for p in ev.pars()][:10])
box.destroy()
