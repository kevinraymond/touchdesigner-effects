"""DEV ONLY. Inside TouchDesigner: Blob Track on each test clip under a few settings, to choose its
defaults from numbers and pictures rather than one clip:

    dev/td.sh dev/blob_sweep.py
    TD_WAIT=600 dev/td.sh --pull dev/out/blob_sweep/done
    cat dev/out/blob_sweep/report.txt      # and dev/out/blob_sweep/<clip>_<setting>.jpg

One blob_track.tox in TDLIB_PARENT, nothing on input 2 (tracking only, no beat behaviors). For each
clip and setting: restart the clip, let the background settle for WARMUP seconds, then for MEASURE
seconds (the clips loop, as in the demo) count the boxes showing, the new boxes a second and how long
boxes last, and save one frame of the output halfway. TD_ARGS: clip names to limit it to.
"""

import glob
import json
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
OUT = os.path.join(_HERE, 'out', 'blob_sweep')
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
WARMUP, MEASURE = 2.0, 10.0
HIDDEN = 0.001  # track.glsl: a held slot whose box isn't showing yet
VARIED = ('Detector', 'Track', 'Threshold', 'Minsize', 'Maxcount')
SETTINGS = (  # name, changes from the defaults
    ('default', {}),
    ('minsize06', {'Minsize': 0.06}),
    ('thresh40', {'Threshold': 0.4}),
    ('max20', {'Maxcount': 20}),
    ('bright', {'Track': 'bright'}),
    ('standout', {'Track': 'contrast'}),
    ('grid', {'Detector': 'grid'}),
)

args = globals().get('TDLIB_ARGS') or []
clips = sorted(p for p in glob.glob(os.path.join(READY, 'b*.mp4'))
               if not args or os.path.splitext(os.path.basename(p))[0] in args)
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, '*')):
    os.remove(f)
host = op(TDLIB_PARENT) or op('/').create(baseCOMP, TDLIB_PARENT.strip('/'))
for o in list(host.children):
    if o.valid:
        o.destroy()
clip = host.create(moviefileinTOP, 'clip')
fx = host.loadTox(os.path.join(_ROOT, 'effects', 'blob_track', 'blob_track.tox'))
fx.inputConnectors[0].connect(clip)
defaults = {n: getattr(fx.par, n).default for n in VARIED}
runs = [(c, s, changes) for c in clips for s, changes in SETTINGS]
results = []


def begin(i):
    path, name, changes = runs[i]
    if clip.par.file.eval() != path:
        clip.par.file = path
    for n in VARIED:
        getattr(fx.par, n).val = changes.get(n, defaults[n])
    clip.par.cuepulse.pulse()
    st = dict(i=i, start=absTime.seconds, seen={}, shown=[], handed0=None, saved=False)
    run('args[0](args[1])', tick, st, delayFrames=1)


def tick(st):
    t = absTime.seconds - st['start']
    a = fx.op('track').numpyArray()  # pulls the tracker every frame, used or not
    if t >= WARMUP:
        m = t - WARMUP
        labels = {int(round(a[2, s, 0])) for s in range(a.shape[1]) if a[1, s, 1] > HIDDEN}
        for lab in labels:
            first, _ = st['seen'].get(lab, (m, m))
            st['seen'][lab] = (first, m)
        st['shown'].append(len(labels))
        if st['handed0'] is None:
            st['handed0'] = a[2, 0, 1]
        if not st['saved'] and m >= MEASURE / 2:
            path, name, _ = runs[st['i']]
            fx.op('out_top').save(os.path.join(OUT, '{}_{}.jpg'.format(
                os.path.splitext(os.path.basename(path))[0], name)))
            st['saved'] = True
        if m >= MEASURE:
            finish(st, a[2, 0, 1], m)
            return
    run('args[0](args[1])', tick, st, delayFrames=1)


def finish(st, handed, m):
    path, name, _ = runs[st['i']]
    seen = st['seen']
    # Boxes that came and went inside the window, not cut by its start or end.
    lives = sorted(last - first for first, last in seen.values() if first > 0.1 and last < m - 0.1)
    new = sum(1 for first, _ in seen.values() if first > 0.1)
    shown = st['shown']
    results.append(dict(
        clip=os.path.splitext(os.path.basename(path))[0], setting=name,
        boxes_mean=round(sum(shown) / len(shown), 1), boxes_max=max(shown),
        new_per_s=round(new / m, 2), ids_per_s=round(float(handed - st['handed0']) / m, 1),
        life_median=round(lives[len(lives) // 2], 2) if lives else None,
        short=round(sum(1 for x in lives if x < 1.0) / len(lives), 2) if lives else None))
    if st['i'] + 1 < len(runs):
        run('args[0](args[1])', begin, st['i'] + 1, delayFrames=2)
        return
    head = '{:16} {:10} {:>6} {:>4} {:>8} {:>8} {:>7} {:>6}'.format(
        'clip', 'setting', 'boxes', 'max', 'new/s', 'ids/s', 'life s', '<1 s')
    lines = [head]
    for r in results:
        lines.append('{clip:16} {setting:10} {boxes_mean:6} {boxes_max:4} {new_per_s:8} {ids_per_s:8} '
                     '{life:>7} {short:>6}'.format(life=str(r['life_median']), **{k: (v if v is not None else '-')
                                                                                for k, v in r.items()}))
    open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    json.dump(results, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
    open(os.path.join(OUT, 'done'), 'w').write('report.txt\n')
    for o in list(host.children):
        o.allowCooking = False


begin(0)
print('sweeping blob_track: {} clips x {} settings, about {:.0f} s'.format(
    len(clips), len(SETTINGS), len(runs) * (WARMUP + MEASURE + 0.1)))
