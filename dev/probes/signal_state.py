# DEV ONLY probe: is the demo's copy of Fosfora's signal receiving, next to the project's own?
for path in ('/tdlib_demo/fosfora_signal', '/project1/fosfora_examples/fosfora_signal'):
    s = op(path)
    if s is None:
        print(path, 'missing'); continue
    out = s.op('out_signal')
    out.cook(force=True)
    names = [c.name for c in out.chans()]
    print(path, 'chans', len(names), 'online' in names, {n: round(out[n].eval(), 3) for n in ('online', 'beat_count', 'bar_count', 'energy', 'bpm') if n in names})
    print('  pars:', {p.name: p.eval() for p in s.customPars if p.name in ('Active', 'Port', 'Status', 'Version')})
    print('  errors:', s.errors(recurse=True), s.warnings(recurse=True))
print([n for n in op('/project1/fosfora_examples/fosfora_signal/out_signal').chans()][40:])
