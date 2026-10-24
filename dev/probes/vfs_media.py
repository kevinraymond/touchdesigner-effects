"""DEV ONLY. Inside TouchDesigner (in TDLIB_PARENT, removed after): can a component carry a movie and a
song in its Virtual File System, play them through a Movie File In and an Audio File In by a path
relative to itself, and keep playing them saved as a .tox and loaded under another path?

    dev/td.sh dev/probes/vfs_media.py && dev/td.sh --pull dev/out/vfs_media/done
"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_ROOT, 'dev', 'out', 'vfs_media')
os.makedirs(OUT, exist_ok=True)
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
host = op(TDLIB_PARENT) or op('/').create(baseCOMP, TDLIB_PARENT.strip('/'))
for o in list(host.children):
    if o.valid:
        o.destroy()
lines = []
c = host.create(baseCOMP, 'vfstest')
for name in ('b1_dancer.mp4', 'm1x_ease_from_drop.wav'):
    f = c.vfs.addFile(os.path.join(READY, name))
    lines.append('vfs file {} size {} virtualPath {}'.format(f.name, f.size, getattr(f, 'virtualPath', '?')))
m = c.create(moviefileinTOP, 'm')
m.par.file.expr = "'vfs:' + parent().path + ':b1_dancer.mp4'"
a = c.create(audiofileinCHOP, 'a')
a.par.file.expr = "'vfs:' + parent().path + ':m1x_ease_from_drop.wav'"
tox = os.path.join(OUT, 'vfstest.tox')
st = dict(n=0)


def report(tag, comp):
    mm, aa = comp.op('m'), comp.op('a')
    mm.cook(force=True)
    aa.cook(force=True)
    lines.append('{}: {} movie {} x {} file {!r} errors {!r} | audio chans {} rate {} errors {!r}'.format(
        tag, comp.path, mm.width, mm.height, mm.par.file.eval(), mm.errors() + mm.warnings(),
        aa.numChans, aa.rate, aa.errors() + aa.warnings()))


def later():
    report('in place', c)
    c.save(tox)
    lines.append('saved {} bytes'.format(os.path.getsize(tox)))
    c2 = host.loadTox(tox)
    c2.name = 'elsewhere'
    run('args[0](args[1])', check2, c2, delayFrames=30)


def check2(c2):
    report('loaded again', c2)
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('ok\n')
    for o in list(host.children):
        if o.valid:
            o.destroy()
    os.remove(tox)


for f in ('report.txt', 'done'):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
run('args[0]()', later, delayFrames=30)
print('testing the VFS')
