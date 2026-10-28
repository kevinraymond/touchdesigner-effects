"""DEV ONLY probe for Words (board #4673), 2025.33230: what the Text TOP tells Python about a word's size, whether one
Text TOP draws a whole atlas of words from a spec DAT in one cook, whether a Script DAT cooks again when a parameter its
callback reads changes, and whether a compute shader's shared-memory atomics (atomicOr, atomicMax) work on the Mac.
Writes dev/out/probe_words/result.txt and a PNG of the atlas, then done:

    dev/td.sh dev/probes/words_text.py && dev/td.sh --pull dev/out/probe_words/done"""
import os
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
host = op(TDLIB_PARENT)
out_dir = os.path.join(_ROOT, 'dev', 'out', 'probe_words')
os.makedirs(out_dir, exist_ok=True)
for f in ('done', 'result.txt', 'atlas.png', 'cs.png'):
    if os.path.exists(os.path.join(out_dir, f)):
        os.remove(os.path.join(out_dir, f))
for o in list(host.children):
    if o.valid and o.name.startswith('probe_w'):
        o.destroy()
lines = []
WORDS = ('body electric soul love face limbs joints walk neck waist knees swimmer water green-shine bending rowers '
         'horseman girls mothers I a gyp Wy').split()

# 1. Measuring: evalTextSize and anything else on the class
t = host.create(textTOP, 'probe_w_measure')
lines.append('textTOP members: ' + ', '.join(m for m in dir(t) if not m.startswith('_') and
                                            any(k in m.lower() for k in ('text', 'font', 'line', 'size', 'asc',
                                                                         'desc', 'cap', 'eval'))))
for p in t.pars():
    if any(k in p.name.lower() for k in ('font', 'size', 'spec', 'typeface', 'align', 'wrap', 'legacy', 'kern',
                                         'resolution', 'smooth', 'antial')):
        lines.append('  par {} ({}) = {!r}{}'.format(p.name, p.label, p.eval(),
                                                     ' menu {}'.format(p.menuNames) if p.isMenu else ''))
t.par.fontsizexunit = 'pixels'
for font in ('Arial', 'Arial Black', 'Impact', 'Helvetica Neue', 'Futura', 'Georgia', 'Verdana', 'NoSuchFont'):
    t.par.font = font
    t.par.fontsizex = 100
    try:
        sizes = [(w, t.evalTextSize(w)) for w in ('body', 'gyp', 'I', 'Wy', 'electric')]
    except Exception as e:
        sizes = repr(e)
    extra = []
    for m in ('ascender', 'descender', 'capHeight', 'fontSupportsChars'):
        try:
            v = getattr(t, m)
            extra.append('{} {}'.format(m, v('body') if callable(v) else v))
        except Exception as e:
            extra.append('{} {!r}'.format(m, e))
    lines.append('font {}: {} | {}'.format(font, sizes, '; '.join(extra)))

# 2. An atlas: every word once, at its measured width, on shelves, one cook
t.par.font = 'Arial'
t.par.fontsizex = 96
spec = host.create(tableDAT, 'probe_w_spec')
spec.clear()
spec.appendRow(['x', 'y', 'text'])
AW, AH = 1280, 1024
x, y, shelf = 4, AH - 4, 0
rects = []
for w in WORDS * 3:
    ww, hh = t.evalTextSize(w)
    if x + ww + 4 > AW:
        x, y = 4, y - shelf - 4
        shelf = 0
    shelf = max(shelf, hh)
    rects.append((w, x, y - hh, ww, hh))
    spec.appendRow([x, y - 0.8 * hh, w])   # y as the baseline, guessing it is 0.8 down the line
    x += ww + 4
atlas = host.create(textTOP, 'probe_w_atlas')
atlas.par.text = ''
atlas.par.specdat = spec.name
atlas.par.font = 'Arial'
atlas.par.fontsizexunit = 'pixels'
atlas.par.fontsizex = 96
atlas.par.outputresolution = 'custom'
atlas.par.resolutionw, atlas.par.resolutionh = AW, AH
if hasattr(atlas.par, 'legacyparsing'):
    atlas.par.legacyparsing = False
t0 = time.perf_counter()
atlas.cook(force=True)
lines.append('atlas: {} words, cook {:.1f} ms (python), cpuCookTime {}, errors {!r} warnings {!r}'.format(
    spec.numRows - 1, 1000 * (time.perf_counter() - t0), atlas.cpuCookTime, atlas.errors(), atlas.warnings()))
lines.append('first rects (word, x, y bottom, w, h): {}'.format(rects[:5]))

# 3. A Script DAT whose callback reads its parent's parameter: does changing it cook the DAT again?
box = host.create(baseCOMP, 'probe_w_box')
pg = box.appendCustomPage('P')
pg.appendStr('Fontname')
box.par.Fontname = 'Arial'
sd = box.create(scriptDAT, 'script')
sd.docked[0].text = '''
def onCook(scriptOp):
    scriptOp.clear()
    n = int(scriptOp.storage.get('n', 0)) + 1
    scriptOp.storage['n'] = n
    scriptOp.appendRow([parent().par.Fontname.eval(), n])
'''
sd.cook(force=True)
a = sd[0, 1].val
box.par.Fontname = 'Impact'
b_before = sd[0, 1].val
state = {'frame': 0}

# 4. Shared atomics in a compute shader: atomicOr builds a bitmask, atomicMax picks a winner.
CS = '''layout (local_size_x = 1024) in;
shared uint sBits[7000];
shared uint sBest;
void main() {
    uint t = gl_LocalInvocationIndex;
    for (uint i = t; i < 7000u; i += 1024u) sBits[i] = 0u;
    if (t == 0u) sBest = 0u;
    memoryBarrierShared();
    barrier();
    atomicOr(sBits[t >> 5], 1u << (t & 31u));
    atomicMax(sBest, (t * 2654435761u) >> 8);
    memoryBarrierShared();
    barrier();
    if (t < 32u) imageStore(mTDComputeOutputs[0], ivec2(int(t), 0),
                            TDOutputSwizzle(vec4(float(sBits[t]) / 4294967295.0, float(sBest & 0xFFFFu), float(sBest >> 16), 1.0)));
}
'''
cs = host.create(glslTOP, 'probe_w_cs')
cs.par.mode = 'compute'
cs.par.autodispatchsize = False
cs.par.dispatchsizex = cs.par.dispatchsizey = cs.par.dispatchsizez = 1
cs.par.outputresolution = 'custom'
cs.par.resolutionw, cs.par.resolutionh = 32, 1
cs.par.format = 'rgba32float'
next(d for d in cs.docked if 'compute' in d.name).text = CS


def tick():
    state['frame'] += 1
    if state['frame'] < 5:
        sd.cook()
        cs.cook()
        run('args[0]()', tick, delayFrames=1)
        return
    c = sd[0, 1].val
    lines.append('script DAT: cook count {} before the change, {} right after it, {} a few frames later; row {}'.format(
        a, b_before, c, [x.val for x in sd.row(0)]))
    arr = cs.numpyArray()
    if arr is not None:
        best = int(round(arr[0, 0, 1])) | (int(round(arr[0, 0, 2])) << 16)
        want = max((t * 2654435761) % 2 ** 32 >> 8 for t in range(1024))
        lines.append('compute atomics: bits {} (want all 1.0 for the first 32 words); best {} (want {}); errors {!r} '
                     'warnings {!r}'.format([round(float(v), 3) for v in arr[0, :32, 0]], best, want, cs.errors(),
                                            cs.warnings()))
    else:
        lines.append('compute: no pixels; errors {!r} warnings {!r}'.format(cs.errors(), cs.warnings()))
    info = next((d for d in cs.docked if 'info' in d.name), None)
    if info is not None:
        lines.append('cs info: ' + info.text[:600].replace('\n', ' | '))
    atlas.save(os.path.join(out_dir, 'atlas.png'))
    open(os.path.join(out_dir, 'result.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(out_dir, 'done'), 'w').write('result.txt\n')
    print('\n'.join(lines))


run('args[0]()', tick, delayFrames=1)
print('probe_words running: pull dev/out/probe_words/done')
