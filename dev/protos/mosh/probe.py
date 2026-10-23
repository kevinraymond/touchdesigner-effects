# DEV ONLY probe (datamosh round 1): what this TouchDesigner offers for motion estimation.
host = op(TDLIB_PARENT)
print('build', app.build, 'os', app.osName, 'fps', project.cookRate, 'realTime', project.realTime)
try:
    print('license', [ (l.type, l.version) for l in licenses ] if hasattr(licenses, '__iter__') else licenses)
except Exception as e:
    print('license?', e)
print('timeline play', root.time.play, 'rate', root.time.rate)
names = [n for n in dir(td) if n.endswith('TOP')]
print('flow-ish TOPs', [n for n in names if any(k in n.lower() for k in ('flow', 'optic', 'motion', 'vector', 'nvidia', 'cache', 'timemachine', 'analyze'))])
of = host.op('of_probe') or host.create(opticalflowTOP, 'of_probe')
c = host.op('of_src') or host.create(constantTOP, 'of_src')
of.inputConnectors[0].connect(c)
of.cook(force=True)
print('opticalflowTOP errors:', repr(of.errors()), 'warnings:', repr(of.warnings()), 'res', of.width, of.height)
m = host.op('mv_probe') or host.create(moviefileinTOP, 'mv_probe')
print('moviefilein playmode default', m.par.playmode.eval(), [p.name for p in m.pars() if p.name in ('play','speed','cuestart','index','playmode','loop')])
for o in (of, c, m):
    o.destroy()
