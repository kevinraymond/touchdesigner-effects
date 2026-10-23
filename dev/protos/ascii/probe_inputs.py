# DEV ONLY probe: how to wire more than two inputs into a GLSL TOP from Python.
host = op(TDLIB_PARENT)
if host.op('probe'):
    host.op('probe').destroy()
box = host.create(baseCOMP, 'probe')
box.allowCooking = False
g = box.create(glslTOP, 'g')
srcs = [box.create(constantTOP, 'c{}'.format(i)) for i in range(4)]
print('connectors at start', len(g.inputConnectors))
for i, s in enumerate(srcs):
    try:
        g.inputConnectors[i].connect(s)
        print('connected', i, '-> connectors', len(g.inputConnectors), 'inputs', [o.name for o in g.inputs])
    except IndexError:
        print('no connector', i, 'of', len(g.inputConnectors))
        s.outputConnectors[0].connect(g.inputConnectors[-1])
        print('  via last free connector -> inputs', [o.name for o in g.inputs], 'connectors', len(g.inputConnectors))
print('top pars', [p.name for p in g.pars() if 'top' in p.name.lower()][:20])
print('setInputs?', hasattr(g, 'setInputs'))
