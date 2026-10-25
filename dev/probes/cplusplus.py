"""DEV ONLY. Inside TouchDesigner: does C++ load on this license? Prints the license, every
C++ or Custom OP in the project and its problems; with arguments, creates each OP under
TDLIB_PARENT/cpp_probe (fed an Audio Oscillator), cooks it and prints what it made.

Kept as the test behind research.md's answer (2026-10-25, 2025.33230): C++ and Custom OPs run
on the Non-Commercial license. The library still stays GLSL/Python, since a plugin can't live
inside a .tox; this probe only checks what competing native plugins can reach.

    dev/td.sh dev/probes/cplusplus.py
    TD_ARGS='essentiarhythmCHOP cplusplusTOP=/path/CPUMemoryTOP.plugin' dev/td.sh dev/probes/cplusplus.py
    TD_ARGS=clean dev/td.sh dev/probes/cplusplus.py

A plugin binary TouchDesigner hasn't loaded on this machine before opens a permission dialog
that blocks it until someone answers: only name plugins someone is there to allow.
"""

for name in ('type', 'disablePro', 'machine'):
    try:
        print('licenses.{}: {!r}'.format(name, getattr(licenses, name)))
    except Exception as e:
        print('licenses.{}: {}'.format(name, e))
try:
    for lic in licenses:
        print('  license: type {!r}, status {!r}, version {!r}'.format(
            getattr(lic, 'type', None), getattr(lic, 'status', None), getattr(lic, 'version', None)))
except Exception as e:
    print('  licenses not iterable: {}'.format(e))
print('app: {} {} on {}'.format(app.product, app.build, app.osName))
for fam, types in families.items():
    hits = [str(t) for t in types if 'cplusplus' in str(t).lower() or 'essentia' in str(t).lower()]
    if hits:
        print('{} types: {}'.format(fam, hits))


def native(o):
    t = o.OPType.lower()
    return 'cplusplus' in t or 'essentia' in t


def report(o):
    print('{} ({}): {} chans {}, {}x{}, problems: {}'.format(
        o.path, o.OPType, getattr(o, 'numChans', '-'),
        [c.name for c in o.chans()][:6] if o.family == 'CHOP' else '-',
        getattr(o, 'width', '-'), getattr(o, 'height', '-'),
        (o.errors() + ' ' + o.warnings()).strip() or 'none'))


found = [o for o in op('/').findChildren() if native(o)]
print('C++/Custom OPs in the project: {}'.format(len(found)))
for o in found:
    report(o)

probe = op(TDLIB_PARENT + '/cpp_probe')
if TDLIB_ARGS == ['clean']:
    if probe:
        probe.destroy()
    print('cleaned')
elif TDLIB_ARGS:
    if probe is None:
        probe = op(TDLIB_PARENT).create(baseCOMP, 'cpp_probe')
    osc = probe.op('osc') or probe.create(audiooscillatorCHOP, 'osc')
    for arg in TDLIB_ARGS:
        optype, _, plugin = arg.partition('=')
        name = optype + ('_' + plugin.rsplit('/', 1)[-1].split('.')[0] if plugin else '')
        o = probe.op(name)
        if o is None:
            try:
                o = probe.create(optype, name)
            except Exception as e:
                print('{}: create failed: {}'.format(arg, e))
                continue
        if plugin:
            o.par.plugin = plugin
        if o.family == 'CHOP' and not o.inputs:
            try:
                osc.outputConnectors[0].connect(o)
            except Exception as e:
                print('{}: no input: {}'.format(o.name, e))
        o.cook(force=True)
        report(o)
        if o.family == 'TOP' and o.width:
            a = o.numpyArray()
            print('  pixels: min {:.3f} max {:.3f} mean {:.3f}'.format(a.min(), a.max(), a.mean()))
