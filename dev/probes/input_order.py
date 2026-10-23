# DEV ONLY probe: what orders a COMP's input connectors, the In OPs' names or their positions?
# Read immediately and again 10 frames later (the order may only update on a later frame).
import os
host = op(TDLIB_PARENT)
c = host.op('probe_order') or host.create(baseCOMP, 'probe_order')
for o in list(c.children):
    o.destroy()
z = c.create(inTOP, 'z_top'); z.nodeX, z.nodeY = 0, 100
m = c.create(inCHOP, 'm_chop'); m.nodeX, m.nodeY = 0, -100
log = ['now, z_top above m_chop: {}'.format([x.inOP.name for x in c.inputConnectors])]
def later():
    log.append('10 frames later: {}'.format([x.inOP.name for x in c.inputConnectors]))
    z.nodeY, m.nodeY = -100, 100
    run('args[0]()', later2, delayFrames=10)
def later2():
    log.append('moved m_chop above z_top, 10 frames later: {}'.format([x.inOP.name for x in c.inputConnectors]))
    open(os.path.expanduser('~/tdlib/dev/out/input_order.txt'), 'w').write('\n'.join(log) + '\n')
    c.destroy()
run('args[0]()', later, delayFrames=10)
print('\n'.join(log))
