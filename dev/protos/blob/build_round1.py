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
    g = mk(comp, glslTOP, name, x, y, inputs, comment=comment, outputresolution='custom',
           resolutionw=w, resolutionh=h, format=fmt)
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
    m4 = mk(inp, moviefileinTOP, 'movie4', 0, 0, file=Expr("app.samplesFolder + '/Map/Nature/Movie.4.mp4'"))
    m2 = mk(inp, moviefileinTOP, 'movie2', 0, -150, file=Expr("app.samplesFolder + '/Map/Nature/Movie.2.mp4'"))
    syn = glsl(inp, 'synth', 0, -300, [], src('synth.glsl'), comment='Synthetic moving blobs.',
               vecs=[('uTime', [T])])
    sel = mk(inp, switchTOP, 'sel', 250, -150, [m4, m2, syn], index=0)
    mk(inp, nullTOP, 'out', 450, -150, [sel])
    # Beats from the sample WAV with TouchDesigner's own CHOPs (no Palette): low-passed RMS
    # against its own slow average; the Trigger CHOP's Re-Trigger Delay is the flash limit
    # (1 s = Calm). No Audio Device Out: nothing is heard.
    au = mk(inp, audiofileinCHOP, 'audio', 0, -500, file=Expr("app.samplesFolder + '/Audio/SonarBlackie666.wav'"),
            playmode='sequential', repeat=True, mono=True)
    lp = mk(inp, audiofilterCHOP, 'lowpass', 200, -500, [au], filter='lowpass', cutofffrequency=150)
    rms = mk(inp, analyzeCHOP, 'rms', 400, -500, [lp], function='rmspower')
    slow = mk(inp, lagCHOP, 'slow', 600, -600, [rms], lag1=0.6, lag2=0.6)
    onset = mk(inp, mathCHOP, 'onset', 800, -500, [rms, slow], chopop='sub')
    beat = mk(inp, triggerCHOP, 'beat', 1000, -500, [onset], threshup=BEAT_THRESHOLD, retrigger=1.0,
              attack=0, peak=1, decay=0.4, sustain=0, release=0)
    count = mk(inp, countCHOP, 'count', 1200, -600, [beat])
    mk(inp, mergeCHOP, 'trailin', 1000, -800, [rms, onset, beat])
    mk(inp, trailCHOP, 'trail', 1200, -800, [inp.op('trailin')], wlength=8)
SRC = inp.op('out').path
AUD = inp.path


def tracker(comp, x, y, prep, background, **pars):
    """Blob Track TOP in background-subtraction mode (input 2 connected): true rectangles,
    faster than SimpleBlobDetector. Its Info CHOP as a data texture (row 0 num_blobs, then
    id, u, v, width, height per blob)."""
    bt = mk(comp, blobtrackTOP, 'track', x, y, [prep, background], downloadtype='nextframe', **pars)
    info = mk(comp, infoCHOP, 'info', x + 200, y, op=bt.path)
    # One channel per row: keep at most 96 blobs (481 rows); past 1280 rows the Non-Commercial
    # key clamps the texture.
    cap = mk(comp, selectCHOP, 'cap', x + 300, y - 100, [info], channames='num_blobs blob[0-95]:*')
    data = mk(comp, choptoTOP, 'data', x + 400, y, chop=cap.path, dataformat='r', format='mono32float')
    return bt, info, data


# The tracker runs on a small picture: OpenCV's contour pass and the GPU-to-CPU download scale
# with pixels, and u, v, width, height come back normalized anyway.
TW, TH = 320, 180


def black(comp, x, y):
    return mk(comp, constantTOP, 'black', x, y, outputresolution='custom', resolutionw=TW, resolutionh=TH,
              colorr=0, colorg=0, colorb=0)


def small_mono(comp, x, y, s):
    return mk(comp, monochromeTOP, 'mono', x, y, [s], outputresolution='custom', resolutionw=TW, resolutionh=TH)


def highlights(comp, x, y, mono, subtract=0.6, gain=2.0):
    """Brighter than the neighborhood (prep.glsl), so one threshold fits dark and bright footage."""
    blur = mk(comp, blurTOP, 'local_mean', x, y - 150, [mono], size=28)
    return glsl(comp, 'prep', x + 200, y, [mono, blur], src('prep.glsl'), w=TW, h=TH,
                vecs=[('uK', [subtract, gain, 0, 0])])


def finish(comp, last):
    out = mk(comp, nullTOP, 'out', last.nodeX + 200, last.nodeY, [last])
    # DEV ONLY: keeps the chain cooking every frame (tracking IDs and running backgrounds need
    # every frame); capture_round1.py turns the whole COMP's cooking off afterwards.
    mk(comp, cacheTOP, 'keep', out.nodeX + 200, out.nodeY, [out], cachesize=1, alwayscook=True)
    return out


built = []

# ---- A "trace": highlights, one GLSL pass over a compact blob table ---------------------------
if wanted('a_trace'):
    a = fresh('a_trace')
    s = mk(a, selectTOP, 'src', 0, 0, top=SRC)
    mono = small_mono(a, 200, -200, s)
    prep = highlights(a, 400, -200, mono)
    bt, info, data = tracker(a, 800, -200, prep, black(a, 600, -350), threshold=0.42, minblobsize=0.02,
                             deleteoverlap=True, deleteoverlaptol=0.6)
    table = glsl(a, 'table', 1000, -300, [data], shader('unpack.glsl', data=0), w=96, h=2, fmt='rgba32float')
    draw = glsl(a, 'draw', 1200, 0, [s, table], shader('a_trace.glsl', packed=1),
                vecs=[('uTime', [T]), ('uLook', [1, 1, 1, 0.55]), ('uLook2', [24, 0, 0, 0])])
    finish(a, draw)
    built.append(a)

# ---- B "instanced": motion against a running background; Geometry COMP instancing ------------
if wanted('b_instanced'):
    b = fresh('b_instanced')
    s = mk(b, selectTOP, 'src', 0, 0, top=SRC)
    mono0 = small_mono(b, 200, -200, s)
    mono = mk(b, blurTOP, 'soft', 300, -200, [mono0], size=3)
    fb = mk(b, feedbackTOP, 'fb', 200, -400, [mono], top='bg')
    bg = mk(b, crossTOP, 'bg', 400, -400, [fb, mono], cross=0.2)
    mot = glsl(b, 'motion', 600, -400, [mono, bg], src('motion.glsl'), w=TW, h=TH, vecs=[('uK', [0, 10, 0, 0])])
    motb = mk(b, blurTOP, 'motion_blur', 800, -400, [mot], size=6)
    bt = mk(b, blobtrackTOP, 'track', 1000, -200, [motb, black(b, 800, -550)], downloadtype='nextframe',
            threshold=0.18, minblobsize=0.02, maxblobsize=0.35, deleteoverlap=True)
    info = mk(b, infoDAT, 'info', 800, -200, op=bt.path)
    blobs = mk(b, dattoCHOP, 'blobs', 1000, -200, dat=info.path, output='chanpercol', firstrow='names',
               firstcolumn='values')
    mat = mk(b, lineMAT, 'lines', 1200, -500, widthnear=1.5, widthfar=1.5, linenearcolorr=1, linenearcolorg=0.6,
             linenearcolorb=0.18)
    matw = mk(b, lineMAT, 'lines_white', 1200, -650, widthnear=1, widthfar=1, linenearcolorr=0.7, linenearcolorg=0.7,
              linenearcolorb=0.7)
    asp = 1280 / 720
    geo = mk(b, geometryCOMP, 'boxes', 1200, -200, material='lines', instancing=True, instanceop='blobs',
             instancetx='u', instancety='v', instancesx='width', instancesy='height', sx=asp)
    for ch in list(geo.children):
        ch.destroy()
    pts = mk(geo, tableDAT, 'bracket_pts', 0, 200, comment='Corner brackets and a center cross, unit box.')
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
    pr = mk(geo, tableDAT, 'bracket_prims', 0, 0, comment='Polylines through bracket_pts.')
    pr.clear()
    for r in prims:
        pr.appendRow(r)
    sop = mk(geo, dattoSOP, 'brackets', 200, 100, pointsdat='bracket_pts', primsdat='bracket_prims')
    sop.render = sop.display = True
    chain = mk(b, geometryCOMP, 'chain', 1200, -350, material='lines_white', sx=asp)
    for ch in list(chain.children):
        ch.destroy()
    # The chain runs left to right: samples sorted by u.
    srt = mk(b, sortCHOP, 'by_u', 900, -650, [blobs], method='increasing', select='byname', names='u')
    cu = mk(b, selectCHOP, 'sel_uv', 1000, -650, [srt], channames='u v width')
    # tz is the box width: the orthographic camera ignores it, and CHOP to SOP wants all three.
    mk(b, renameCHOP, 'chain_pts', 1200, -650, [cu], renamefrom='u v width', renameto='tx ty tz')
    cs = mk(chain, choptoSOP, 'path', 0, 0, chop='../chain_pts')
    cs.render = cs.display = True
    cam = mk(b, cameraCOMP, 'cam', 1400, -350, projection='ortho', orthowidth=asp, tx=asp / 2, ty=0.5, tz=5)
    ren = mk(b, renderTOP, 'render', 1600, -200, camera='cam', geometry='boxes chain', outputresolution='custom',
             resolutionw=1280, resolutionh=720, bgcolora=0)
    # Labels: Text TOP + Specification DAT (x, y in pixels, text), built from the blob CHOP with CHOPs.
    su = mk(b, selectCHOP, 'sel_u', 1000, -800, [blobs], channames='u')
    xu = mk(b, mathCHOP, 'x_px', 1200, -800, [su], gain=1280)
    rx = mk(b, renameCHOP, 'x', 1400, -800, [xu], renamefrom='u', renameto='x')
    sh = mk(b, selectCHOP, 'sel_h', 1000, -950, [blobs], channames='height')
    hh = mk(b, mathCHOP, 'half_h', 1200, -950, [sh], gain=0.5)
    sv = mk(b, selectCHOP, 'sel_v', 1000, -1100, [blobs], channames='v')
    vh = mk(b, mergeCHOP, 'v_h', 1400, -1000, [sv, hh])
    top_ = mk(b, mathCHOP, 'top_edge', 1600, -1000, [vh], chanop='add')
    yp = mk(b, mathCHOP, 'y_px', 1800, -1000, [top_], gain=720, postoff=4)
    ry = mk(b, renameCHOP, 'y', 2000, -1000, [yp], renamefrom='*', renameto='y')
    si = mk(b, selectCHOP, 'sel_id', 1000, -1250, [blobs], channames='id')
    rt = mk(b, renameCHOP, 'text', 1200, -1250, [si], renamefrom='id', renameto='text')
    sc = mk(b, mergeCHOP, 'spec_chop', 2200, -900, [rx, ry, rt])
    spec = mk(b, choptoDAT, 'spec', 2400, -900, chop=sc.path, output='colperchan', names=True)
    txt = mk(b, textTOP, 'labels', 2600, -900, specdat=spec.path,
             fontfile=Expr("app.samplesFolder + '/Fonts/PTMono-Regular.ttf'"), fontsizex=13, alignx='center',
             aligny='bottom', outputresolution='custom', resolutionw=1280, resolutionh=720, bgalpha=0,
             fontcolorr=1, fontcolorg=0.6, fontcolorb=0.18)
    full = mk(b, monochromeTOP, 'mono_full', 1400, 0, [s])
    dim = mk(b, levelTOP, 'dim', 1600, 0, [full], brightness1=0.55)
    o1 = mk(b, overTOP, 'over_boxes', 1800, 0, [ren, dim])
    o2 = mk(b, overTOP, 'over_labels', 2000, 0, [txt, o1])
    finish(b, o2)
    built.append(b)

# ---- C "scanner": edge density; magnified one-bit contents ------------------------------------
if wanted('c_scan'):
    c = fresh('c_scan')
    s = mk(c, selectTOP, 'src', 0, 0, top=SRC)
    mono = small_mono(c, 200, -200, s)
    mean = mk(c, blurTOP, 'mean', 400, -450, [mono], size=4)
    edge = mk(c, edgeTOP, 'edge', 400, -200, [mono], strength=4)
    blur = mk(c, blurTOP, 'blur', 600, -200, [edge], size=5)
    bt, info, data = tracker(c, 800, -200, blur, black(c, 600, -350), threshold=0.3, minblobsize=0.03,
                             maxblobsize=0.3, deleteoverlap=True)
    table = glsl(c, 'table', 1400, -300, [data], shader('unpack.glsl', data=0), w=96, h=2, fmt='rgba32float')
    draw = glsl(c, 'draw', 1600, 0, [s, table, mean], shader('c_scan.glsl', packed=1),
                vecs=[('uTime', [T]), ('uLook', [2.0, 0.06, 1, 12])])
    finish(c, draw)
    built.append(c)

# ---- D "beat": highlights, audio-driven words, partner lines and rate-limited flashes ---------
if wanted('d_beat'):
    d = fresh('d_beat')
    s = mk(d, selectTOP, 'src', 0, 0, top=SRC)
    mono = small_mono(d, 200, -200, s)
    prep = highlights(d, 400, -200, mono)
    bt, info, data = tracker(d, 800, -200, prep, black(d, 600, -350), threshold=0.42, minblobsize=0.02,
                             deleteoverlap=True, deleteoverlaptol=0.6)
    table = glsl(d, 'table', 1000, -300, [data], shader('unpack.glsl', data=0), w=96, h=2, fmt='rgba32float')
    draw = glsl(d, 'draw', 1200, 0, [s, table], shader('d_beat.glsl', packed=1, pre=WORDS_GLSL),
                vecs=[('uTime', [T]),
                      ('uBeat', [Expr("op('{}/beat')[0]".format(AUD)), Expr("op('{}/count')[0]".format(AUD)),
                                 Expr("min(1, op('{}/rms')[0] * 6)".format(AUD)), 1]),
                      ('uLook', [1, 0.3, 0, 0])])
    finish(d, draw)
    built.append(d)

# ---- E "grid": GPU-only detection (no Blob Track TOP, nothing read back to the CPU) -----------
if wanted('e_grid'):
    e = fresh('e_grid')
    s = mk(e, selectTOP, 'src', 0, 0, top=SRC)
    prev = mk(e, feedbackTOP, 'prev', 200, -300, [s], top='src')
    gw, gh = 48, 27
    P_ = ('uP', [0.05, 1.0, 0.6, 0.55])
    energy = glsl(e, 'energy', 400, -200, [s, prev], shader('e_grid.glsl', pre='#define PASS 1\n'), w=gw, h=gh,
                  fmt='rgba16float', vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])])
    fb = mk(e, feedbackTOP, 'smooth_fb', 400, -450, [energy], top='smooth')
    smooth = glsl(e, 'smooth', 600, -200, [energy, fb], shader('e_grid.glsl', pre='#define PASS 2\n'), w=gw, h=gh,
                  fmt='rgba16float', vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])])
    peaks = glsl(e, 'peaks', 800, -200, [smooth], shader('e_grid.glsl', pre='#define PASS 3\n'), w=gw, h=gh,
                 fmt='rgba32float', vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])])
    draw = glsl(e, 'draw', 1000, 0, [s, peaks], shader('e_grid.glsl', pre='#define PASS 4\n'),
                vecs=[('uTime', [T]), P_, ('uLook', [1, 0.35, 0, 0])])
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
