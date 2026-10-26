"""DEV ONLY: blob-track overlay, round 1 prototypes. Builds the shared inputs and the variants
under TDLIB_PARENT (run with TD_PARENT=/tdlib_dev_blob dev/td.sh dev/protos/blob/build_round1.py).
rebuild_some.py rebuilds only the variants it names; cleanup.py removes them all. Nothing here ships.
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_HERE, 'font5x7.py')).read(), 'font5x7.py', 'exec'), globals())

host = op(TDLIB_PARENT)
ONLY = [s for s in globals().get('BLOB_ONLY', '').split(',') if s]
T = Expr('absTime.seconds')
BEAT_THRESHOLD = 0.02


def src(name):
    return open(os.path.join(_HERE, name)).read()


def shader(body, data=None, packed=None, pre=''):
    """Font + helpers, then a blob reader bound to an input (`data`: the raw Info CHOP texture,
    `packed`: the table unpack.glsl writes), then the body."""
    head = font_glsl() + src('common.glsl') + pre
    if data is not None:
        head += '#define DATA {}\n'.format(data) + src('blobdata.glsl')
    if packed is not None:
        head += '#define DATA {}\n'.format(packed) + src('packed.glsl')
    return head + src(body)


WORDS = ['NODE', 'SYNC', 'SCAN', 'LOCK', 'PING', 'ECHO', 'FLUX', 'GRID', 'VOID', 'HALO', 'TRAK', 'BEAT',
         'KICK', 'WAVE', 'DATA', 'LOST', 'SEEK', 'ZERO', 'MASS', 'IRIS']
WORDS_GLSL = 'const int NWORDS = {};\nconst int WORDS[{}] = int[{}]({});\n'.format(
    len(WORDS), 4 * len(WORDS), 4 * len(WORDS), ','.join(str(c) for w in WORDS for c in codes(w)))


def fresh(name):
    old = host.op(name)
    if old:
        old.destroy()
    c = host.create(baseCOMP, name)
    c.comment = 'DEV ONLY: blob round 1 prototype.'
    return c


def glsl(comp, name, x, y, inputs, code, w=1280, h=720, fmt='rgba8fixed', comment='', vecs=()):
    g = mk(comp, glslTOP, name, inputs, comment=comment, outputresolution='custom',
           resolutionw=w, resolutionh=h, format=fmt, at=(x, y))
    docked(g, '_pixel', code, comment or name)
    if vecs:
        g.seq.vec.numBlocks = len(vecs)
    for k, (uname, vals) in enumerate(vecs):
        g.par['vec{}name'.format(k)] = uname
        for axis, v in zip('xyzw', vals):
            p = g.par['vec{}value{}'.format(k, axis)]
            if isinstance(v, Expr):
                p.expr = v.text
            else:
                p.val = v
    return g


def wanted(name):
    return not ONLY or name in ONLY


# ---- Shared inputs: two sample movies, a synthetic moving scene, the sample audio ------------
inp = host.op('inputs')
if inp is None or wanted('inputs'):
    inp = fresh('inputs')
    m4 = mk(inp, moviefileinTOP, 'movie4', file=Expr("app.samplesFolder + '/Map/Nature/Movie.4.mp4'"), at=(0, 0))
    m2 = mk(inp, moviefileinTOP, 'movie2', file=Expr("app.samplesFolder + '/Map/Nature/Movie.2.mp4'"), at=(0, -150))
    syn = glsl(inp, 'synth', [], src('synth.glsl'), comment='Synthetic moving blobs.',
               vecs=[('uTime', [T])], at=(0, -300))
    sel = mk(inp, switchTOP, 'sel', [m4, m2, syn], index=0, at=(250, -150))
    mk(inp, nullTOP, 'out', [sel], at=(450, -150))
    # Beats from the sample WAV with TouchDesigner's own CHOPs (no Palette): low-passed RMS
    # against its own slow average; the Trigger CHOP's Re-Trigger Delay is the flash limit
    # (1 s = Calm). No Audio Device Out: nothing is heard.
    au = mk(inp, audiofileinCHOP, 'audio', file=Expr("app.samplesFolder + '/Audio/SonarBlackie666.wav'"),
            playmode='sequential', repeat=True, mono=True, at=(0, -500))
    lp = mk(inp, audiofilterCHOP, 'lowpass', [au], filter='lowpass', cutofffrequency=150, at=(200, -500))
    rms = mk(inp, analyzeCHOP, 'rms', [lp], function='rmspower', at=(400, -500))
    slow = mk(inp, lagCHOP, 'slow', [rms], lag1=0.6, lag2=0.6, at=(600, -600))
    onset = mk(inp, mathCHOP, 'onset', [rms, slow], chopop='sub', at=(800, -500))
    beat = mk(inp, triggerCHOP, 'beat', [onset], threshup=BEAT_THRESHOLD, retrigger=1.0,
              attack=0, peak=1, decay=0.4, sustain=0, release=0, at=(1000, -500))
    count = mk(inp, countCHOP, 'count', [beat], at=(1200, -600))
    mk(inp, mergeCHOP, 'trailin', [rms, onset, beat], at=(1000, -800))
    mk(inp, trailCHOP, 'trail', [inp.op('trailin')], wlength=8, at=(1200, -800))
SRC = inp.op('out').path
AUD = inp.path


def tracker(comp, x, y, prep, background, **pars):
    """Blob Track TOP in background-subtraction mode (input 2 connected): true rectangles,
    faster than SimpleBlobDetector. Its Info CHOP as a data texture (row 0 num_blobs, then
    id, u, v, width, height per blob)."""
    bt = mk(comp, blobtrackTOP, 'track', [prep, background], downloadtype='nextframe', **pars, at=(x, y))
    info = mk(comp, infoCHOP, 'info', op=bt.path, at=(x + 200, y))
    # One channel per row: keep at most 96 blobs (481 rows); past 1280 rows the Non-Commercial
    # key clamps the texture.
    cap = mk(comp, selectCHOP, 'cap', [info], channames='num_blobs blob[0-95]:*', at=(x + 300, y - 100))
    data = mk(comp, choptoTOP, 'data', chop=cap.path, dataformat='r', format='mono32float', at=(x + 400, y))
    return bt, info, data


# The tracker runs on a small picture: OpenCV's contour pass and the GPU-to-CPU download scale
# with pixels, and u, v, width, height come back normalized anyway.
TW, TH = 320, 180


def black(comp, x, y):
    return mk(comp, constantTOP, 'black', outputresolution='custom', resolutionw=TW, resolutionh=TH,
              colorr=0, colorg=0, colorb=0, at=(x, y))


def small_mono(comp, x, y, s):
    return mk(comp, monochromeTOP, 'mono', [s], outputresolution='custom', resolutionw=TW, resolutionh=TH, at=(x, y))


def highlights(comp, x, y, mono, subtract=0.6, gain=2.0):
    """Brighter than the neighborhood (prep.glsl), so one threshold fits dark and bright footage."""
    blur = mk(comp, blurTOP, 'local_mean', [mono], size=28, at=(x, y - 150))
    return glsl(comp, 'prep', [mono, blur], src('prep.glsl'), w=TW, h=TH,
                vecs=[('uK', [subtract, gain, 0, 0])], at=(x + 200, y))


def finish(comp, last):
    out = mk(comp, nullTOP, 'out', [last], at=(last.nodeX + 200, last.nodeY))
    # DEV ONLY: keeps the chain cooking every frame (tracking IDs and running backgrounds need
    # every frame); capture_round1.py turns the whole COMP's cooking off afterwards.
    mk(comp, cacheTOP, 'keep', [out], cachesize=1, alwayscook=True, at=(out.nodeX + 200, out.nodeY))
    return out


built = []

# ---- A "trace": highlights, one GLSL pass over a compact blob table ---------------------------
if wanted('a_trace'):
    a = fresh('a_trace')
    s = mk(a, selectTOP, 'src', top=SRC, at=(0, 0))
    mono = small_mono(a, 200, -200, s)
    prep = highlights(a, 400, -200, mono)
    bt, info, data = tracker(a, 800, -200, prep, black(a, 600, -350), threshold=0.42, minblobsize=0.02,
                             deleteoverlap=True, deleteoverlaptol=0.6)
    table = glsl(a, 'table', [data], shader('unpack.glsl', data=0), w=96, h=2, fmt='rgba32float', at=(1000, -300))
    draw = glsl(a, 'draw', [s, table], shader('a_trace.glsl', packed=1),
                vecs=[('uTime', [T]), ('uLook', [1, 1, 1, 0.55]), ('uLook2', [24, 0, 0, 0])], at=(1200, 0))
    finish(a, draw)
    built.append(a)

# ---- B "instanced": motion against a running background; Geometry COMP instancing ------------
if wanted('b_instanced'):
    b = fresh('b_instanced')
    s = mk(b, selectTOP, 'src', top=SRC, at=(0, 0))
    mono0 = small_mono(b, 200, -200, s)
    mono = mk(b, blurTOP, 'soft', [mono0], size=3, at=(300, -200))
    fb = mk(b, feedbackTOP, 'fb', [mono], top='bg', at=(200, -400))
    bg = mk(b, crossTOP, 'bg', [fb, mono], cross=0.2, at=(400, -400))
    mot = glsl(b, 'motion', [mono, bg], src('motion.glsl'), w=TW, h=TH, vecs=[('uK', [0, 10, 0, 0])], at=(600, -400))
    motb = mk(b, blurTOP, 'motion_blur', [mot], size=6, at=(800, -400))
    bt = mk(b, blobtrackTOP, 'track', [motb, black(b, 800, -550)], downloadtype='nextframe',
            threshold=0.18, minblobsize=0.02, maxblobsize=0.35, deleteoverlap=True, at=(1000, -200))
    info = mk(b, infoDAT, 'info', op=bt.path, at=(800, -200))
    blobs = mk(b, dattoCHOP, 'blobs', dat=info.path, output='chanpercol', firstrow='names',
               firstcolumn='values', at=(1000, -200))
    mat = mk(b, lineMAT, 'lines', widthnear=1.5, widthfar=1.5, linenearcolorr=1, linenearcolorg=0.6,
             linenearcolorb=0.18, at=(1200, -500))
    matw = mk(b, lineMAT, 'lines_white', widthnear=1, widthfar=1, linenearcolorr=0.7, linenearcolorg=0.7,
              linenearcolorb=0.7, at=(1200, -650))
    asp = 1280 / 720
    geo = mk(b, geometryCOMP, 'boxes', material='lines', instancing=True, instanceop='blobs',
             instancetx='u', instancety='v', instancesx='width', instancesy='height', sx=asp, at=(1200, -200))
    for ch in list(geo.children):
        ch.destroy()
    pts = mk(geo, tableDAT, 'bracket_pts', comment='Corner brackets and a center cross, unit box.', at=(0, 200))
    rows = [['P(0)', 'P(1)', 'P(2)']]
    prims = [['vertices', 'close']]
    k = 0.22
    for sx_, sy_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        cx, cy = 0.5 * sx_, 0.5 * sy_
        rows += [[cx - k * sx_, cy, 0], [cx, cy, 0], [cx, cy - k * sy_, 0]]
        prims.append(['{} {} {}'.format(len(rows) - 4, len(rows) - 3, len(rows) - 2), 0])
    rows += [[-0.06, 0, 0], [0.06, 0, 0], [0, -0.06, 0], [0, 0.06, 0]]
    n0 = len(rows) - 1   # point index = row index - 1 (row 0 is the header)
    prims += [['{} {}'.format(n0 - 4, n0 - 3), 0], ['{} {}'.format(n0 - 2, n0 - 1), 0]]
    pts.clear()
    for r in rows:
        pts.appendRow(r)
    pr = mk(geo, tableDAT, 'bracket_prims', comment='Polylines through bracket_pts.', at=(0, 0))
    pr.clear()
    for r in prims:
        pr.appendRow(r)
    sop = mk(geo, dattoSOP, 'brackets', pointsdat='bracket_pts', primsdat='bracket_prims', at=(200, 100))
    sop.render = sop.display = True
    chain = mk(b, geometryCOMP, 'chain', material='lines_white', sx=asp, at=(1200, -350))
    for ch in list(chain.children):
        ch.destroy()
    # The chain runs left to right: samples sorted by u.
    srt = mk(b, sortCHOP, 'by_u', [blobs], method='increasing', select='byname', names='u', at=(900, -650))
    cu = mk(b, selectCHOP, 'sel_uv', [srt], channames='u v width', at=(1000, -650))
    # tz is the box width: the orthographic camera ignores it, and CHOP to SOP wants all three.
    mk(b, renameCHOP, 'chain_pts', [cu], renamefrom='u v width', renameto='tx ty tz', at=(1200, -650))
    cs = mk(chain, choptoSOP, 'path', chop='../chain_pts', at=(0, 0))
    cs.render = cs.display = True
    cam = mk(b, cameraCOMP, 'cam', projection='ortho', orthowidth=asp, tx=asp / 2, ty=0.5, tz=5, at=(1400, -350))
    ren = mk(b, renderTOP, 'render', camera='cam', geometry='boxes chain', outputresolution='custom',
             resolutionw=1280, resolutionh=720, bgcolora=0, at=(1600, -200))
    # Labels: Text TOP + Specification DAT (x, y in pixels, text), built from the blob CHOP with CHOPs.
    su = mk(b, selectCHOP, 'sel_u', [blobs], channames='u', at=(1000, -800))
    xu = mk(b, mathCHOP, 'x_px', [su], gain=1280, at=(1200, -800))
    rx = mk(b, renameCHOP, 'x', [xu], renamefrom='u', renameto='x', at=(1400, -800))
    sh = mk(b, selectCHOP, 'sel_h', [blobs], channames='height', at=(1000, -950))
    hh = mk(b, mathCHOP, 'half_h', [sh], gain=0.5, at=(1200, -950))
    sv = mk(b, selectCHOP, 'sel_v', [blobs], channames='v', at=(1000, -1100))
    vh = mk(b, mergeCHOP, 'v_h', [sv, hh], at=(1400, -1000))
    top_ = mk(b, mathCHOP, 'top_edge', [vh], chanop='add', at=(1600, -1000))
    yp = mk(b, mathCHOP, 'y_px', [top_], gain=720, postoff=4, at=(1800, -1000))
    ry = mk(b, renameCHOP, 'y', [yp], renamefrom='*', renameto='y', at=(2000, -1000))
    si = mk(b, selectCHOP, 'sel_id', [blobs], channames='id', at=(1000, -1250))
    rt = mk(b, renameCHOP, 'text', [si], renamefrom='id', renameto='text', at=(1200, -1250))
    sc = mk(b, mergeCHOP, 'spec_chop', [rx, ry, rt], at=(2200, -900))
    spec = mk(b, choptoDAT, 'spec', chop=sc.path, output='colperchan', names=True, at=(2400, -900))
    txt = mk(b, textTOP, 'labels', specdat=spec.path,
             fontfile=Expr("app.samplesFolder + '/Fonts/PTMono-Regular.ttf'"), fontsizex=13, alignx='center',
             aligny='bottom', outputresolution='custom', resolutionw=1280, resolutionh=720, bgalpha=0,
             fontcolorr=1, fontcolorg=0.6, fontcolorb=0.18, at=(2600, -900))
    full = mk(b, monochromeTOP, 'mono_full', [s], at=(1400, 0))
    dim = mk(b, levelTOP, 'dim', [full], brightness1=0.55, at=(1600, 0))
    o1 = mk(b, overTOP, 'over_boxes', [ren, dim], at=(1800, 0))
    o2 = mk(b, overTOP, 'over_labels', [txt, o1], at=(2000, 0))
    finish(b, o2)
    built.append(b)

# ---- C "scanner": edge density; magnified one-bit contents ------------------------------------
if wanted('c_scan'):
    c = fresh('c_scan')
    s = mk(c, selectTOP, 'src', top=SRC, at=(0, 0))
    mono = small_mono(c, 200, -200, s)
    mean = mk(c, blurTOP, 'mean', [mono], size=4, at=(400, -450))
    edge = mk(c, edgeTOP, 'edge', [mono], strength=4, at=(400, -200))
    blur = mk(c, blurTOP, 'blur', [edge], size=5, at=(600, -200))
    bt, info, data = tracker(c, 800, -200, blur, black(c, 600, -350), threshold=0.3, minblobsize=0.03,
                             maxblobsize=0.3, deleteoverlap=True)
    table = glsl(c, 'table', [data], shader('unpack.glsl', data=0), w=96, h=2, fmt='rgba32float', at=(1400, -300))
    draw = glsl(c, 'draw', [s, table, mean], shader('c_scan.glsl', packed=1),
                vecs=[('uTime', [T]), ('uLook', [2.0, 0.06, 1, 12])], at=(1600, 0))
    finish(c, draw)
    built.append(c)

# ---- D "beat": highlights, audio-driven words, partner lines and rate-limited flashes ---------
if wanted('d_beat'):
    d = fresh('d_beat')
    s = mk(d, selectTOP, 'src', top=SRC, at=(0, 0))
    mono = small_mono(d, 200, -200, s)
    prep = highlights(d, 400, -200, mono)
    bt, info, data = tracker(d, 800, -200, prep, black(d, 600, -350), threshold=0.42, minblobsize=0.02,
                             deleteoverlap=True, deleteoverlaptol=0.6)
    table = glsl(d, 'table', [data], shader('unpack.glsl', data=0), w=96, h=2, fmt='rgba32float', at=(1000, -300))
    draw = glsl(d, 'draw', [s, table], shader('d_beat.glsl', packed=1, pre=WORDS_GLSL),
                vecs=[('uTime', [T]),
                      ('uBeat', [Expr("op('{}/beat')[0]".format(AUD)), Expr("op('{}/count')[0]".format(AUD)),
                                 Expr("min(1, op('{}/rms')[0] * 6)".format(AUD)), 1]),
                      ('uLook', [1, 0.3, 0, 0])], at=(1200, 0))
    finish(d, draw)
    built.append(d)

# ---- E "grid": GPU-only detection (no Blob Track TOP, nothing read back to the CPU) -----------
if wanted('e_grid'):
    e = fresh('e_grid')
    s = mk(e, selectTOP, 'src', top=SRC, at=(0, 0))
    prev = mk(e, feedbackTOP, 'prev', [s], top='src', at=(200, -300))
    gw, gh = 48, 27
    P_ = ('uP', [0.05, 1.0, 0.6, 0.55])
    energy = glsl(e, 'energy', [s, prev], shader('e_grid.glsl', pre='#define PASS 1\n'), w=gw, h=gh,
                  fmt='rgba16float', vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])], at=(400, -200))
    fb = mk(e, feedbackTOP, 'smooth_fb', [energy], top='smooth', at=(400, -450))
    smooth = glsl(e, 'smooth', [energy, fb], shader('e_grid.glsl', pre='#define PASS 2\n'), w=gw, h=gh,
                  fmt='rgba16float', vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])], at=(600, -200))
    peaks = glsl(e, 'peaks', [smooth], shader('e_grid.glsl', pre='#define PASS 3\n'), w=gw, h=gh,
                 fmt='rgba32float', vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])], at=(800, -200))
    draw = glsl(e, 'draw', [s, peaks], shader('e_grid.glsl', pre='#define PASS 4\n'),
                vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])], at=(1000, 0))
    finish(e, draw)
    built.append(e)

for comp in built:
    for o in comp.findChildren():
        if o.isTOP or o.isCHOP or o.isSOP:
            o.cook(force=True)
    bad = [(o.path, o.errors(), o.warnings()) for o in comp.findChildren() if o.errors() or o.warnings()]
    print(comp.name, 'ops', len(comp.findChildren()), 'problems', bad if bad else 'none')
    comp.allowCooking = False
bi = host.op('b_instanced')
if bi and bi in built:
    print('brackets sop points', bi.op('boxes/brackets').numPoints, 'prims', bi.op('boxes/brackets').numPrims)
    print('chain sop points', bi.op('chain/path').numPoints)
    print('spec rows', [[c.val for c in r] for r in bi.op('spec').rows()[:3]])
