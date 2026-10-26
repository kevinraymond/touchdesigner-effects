"""DEV ONLY. Datamosh round 1 prototypes (board #4520). Builds, in TDLIB_PARENT:

  src     test input: sample movies, a panned/zoomed still and moving shapes, cut by its Source par
  flow    shared motion estimation: Lucas-Kanade flow (2 levels) and macroblock search, cut measure
  a_smear  motion-vector smear with a codec-like residual (LK flow)
  b_bloom  a_smear, but on Hold the flow field freezes and is reapplied every frame
  c_blocks macroblock codec model: encoder + decoder chains, quarter-pel block vectors, frozen blocks,
           keyframe recovered by a column sweep of intra blocks
  d_audio  c_blocks driven by the sample MP3: a beat drops the keyframe and freezes the vectors,
           the picture fades back toward the encoder's in between
  e_chroma a_smear with luma refreshed quickly and chroma left moshed

    TD_PARENT=/tdlib_dev_mosh dev/td.sh dev/protos/mosh/build.py

Then dev/protos/mosh/shoot.py to capture, stop.py to stop cooking, clean.py to remove it all.
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

P = TDLIB_PARENT
host = op(P)
W, H = 1280, 720
CUT = 0.08          # mean abs luma change between frames that counts as a cut
SRC = "op('{}/src')".format(P)


def G(name):
    return open(os.path.join(_HERE, 'glsl', name)).read()


COMMON = G('common.glsl')


def fresh(name, x, y, comment):
    old = host.op(name)
    if old:
        old.destroy()
    c = host.create(baseCOMP, name)
    c.nodeX, c.nodeY = x, y
    c.comment = comment
    return c


def glsl(where, name, x, y, inputs, code, uniforms=(), res=None, fmt='rgba16float', comment=''):
    # A GLSL TOP made from Python has 3 input connectors that never grow; its TOPs parameter
    # appends more as sTD2DInputs[3], [4], ... (probe_inputs.py, 2025.33230).
    g = mk(where, glslTOP, name, inputs[:3], comment=comment, format=fmt, at=(x, y))
    if len(inputs) > 3:
        g.par.tops = ' '.join(o.name for o in inputs[3:])
    if res:
        setpars(g, outputresolution='custom', resolutionw=res[0], resolutionh=res[1])
    docked(g, '_pixel', code, comment or name)
    if uniforms:
        g.seq.vec.numBlocks = len(uniforms)
    for i, (uname, vals) in enumerate(uniforms):
        pars = {'vec{}name'.format(i): uname}
        for axis, v in zip('xyzw', vals):
            pars['vec{}value{}'.format(i, axis)] = v
        setpars(g, **pars)
    return g


def sel(where, name, x, y, path):
    return mk(where, selectTOP, name, comment='From ' + path, top=path, at=(x, y))


def keep(where, last):
    """DEV ONLY: a Cache TOP set to Always Cook pulls the chain every frame, so the feedback
    state advances while nothing views it (no Python per frame)."""
    mk(where, nullTOP, 'out', [last], comment='Output.', at=(last.nodeX + 200, last.nodeY))
    mk(where, cacheTOP, 'keep', [where.op('out')],
       comment='DEV ONLY: always cooks, so the prototype runs unviewed.', alwayscook=True, cachesize=1, at=(last.nodeX + 400, last.nodeY))


# ---- src: the test input ------------------------------------------------------------------------
src = fresh('src', -1600, 0, 'Test input: cuts between sources by Source.')
page = src.appendCustomPage('Harness')
custom(page, 'Int', 'Source', 'Source', 0, 'Which source plays.', 0, 5)
custom(page, 'Float', 'Kf', 'Keyframe', 0.0, '1 while a keyframe is being shown.', 0, 1)
custom(page, 'Float', 'Kft', 'Keyframe Time', -100.0, 'absTime.seconds when the last keyframe started.')
custom(page, 'Float', 'Hold', 'Hold', 0.0, '1 while the bloom variant holds its flow.', 0, 1)
T = 'absTime.seconds'
movie = lambda rel: Expr("app.samplesFolder + '/{}'".format(rel))
s0 = mk(src, moviefileinTOP, 'bldg', comment='Grass in front of a colorful building.', file=movie('Map/Nature/Movie.2.mp4'), at=(0, 0))
j = mk(src, moviefileinTOP, 'jelly', comment='Still.', file=movie('Map/Jellybeans.1.jpg'), at=(0, -150))
s1 = mk(src, transformTOP, 'jelly_pan', [j], comment='Still, panned, rotated and zoomed.',
        tx=Expr('0.06*math.sin({}*1.3)'.format(T)), ty=Expr('0.04*math.sin({}*0.9)'.format(T)),
        rotate=Expr('12*math.sin({}*0.5)'.format(T)), sx=Expr('1.35+0.15*math.sin({}*0.7)'.format(T)),
        sy=Expr('1.35+0.15*math.sin({}*0.7)'.format(T)), extend='mirror', at=(200, -150))
s2 = mk(src, moviefileinTOP, 'water', comment='Water over rocks.', file=movie('Map/Nature/Movie.4.mp4'), at=(0, -300))
s3 = glsl(src, 'shapes', [], G('shapes.glsl'), [('uTime', (Expr(T),))], res=(W, H), fmt='rgba8fixed',
          comment='Moving textured shapes.', at=(0, -450))
c = mk(src, moviefileinTOP, 'count', comment='Countdown.', file=movie('Map/Count.mov'), at=(0, -600))
s4 = mk(src, fitTOP, 'count_fit', [c], comment='Countdown at 1280x720.', outputresolution='custom',
        resolutionw=W, resolutionh=H, at=(200, -600))
d = mk(src, moviefileinTOP, 'drums', comment='Still.', file=movie('Map/OilDrums.jpg'), at=(0, -750))
s5 = mk(src, transformTOP, 'drums_pan', [d], comment='Still, slow push in and drift.',
        tx=Expr('0.05*math.sin({}*0.8)'.format(T)), sx=Expr('1.25+0.2*math.sin({}*0.6)'.format(T)),
        sy=Expr('1.25+0.2*math.sin({}*0.6)'.format(T)), extend='mirror', at=(200, -750))
sw = mk(src, switchTOP, 'sw', [s0, s1, s2, s3, s4, s5], comment='Cuts between sources.',
        index=Expr('parent().par.Source'), outputresolution='custom', resolutionw=W, resolutionh=H, at=(500, -300))
mk(src, nullTOP, 'out', [sw], comment='The test input.', at=(700, -300))

# ---- flow: shared motion estimation ---------------------------------------------------------------
fl = fresh('flow', -1200, 0, 'Shared motion estimation: LK flow, block vectors, cut measure.')
inp = sel(fl, 'in', 0, 0, P + '/src/out')
mk(fl, cacheTOP, 'in_prev', [inp], comment='Previous input frame.', cachesize=2, outputindex=-1, at=(200, 200))
lums = {}
for k, y in ((2, 0), (4, -200), (8, -400)):
    l = glsl(fl, 'lum{}'.format(k), [inp], G('lum.glsl'), [('uK', (k,))], res=(W // k, H // k),
             fmt='mono32float', comment='Luma at 1/{}.'.format(k), at=(200, y))
    lp = mk(fl, cacheTOP, 'lum{}p'.format(k), [l], comment='Previous frame of lum{}.'.format(k),
            cachesize=2, outputindex=-1, at=(400, y - 80))
    lums[k] = (l, lp)
dif = glsl(fl, 'diff', list(lums[8]), G('diff.glsl'), fmt='mono32float', comment='Abs luma change.', at=(600, -600))
cut = mk(fl, analyzeTOP, 'cut', [dif], comment='Mean abs luma change: the cut measure.', op='average',
         analyzechannel='red', at=(800, -600))
lk8 = glsl(fl, 'lk8', [lums[8][0], lums[8][1], lums[8][0]], G('lk.glsl'), [('uP', (0, 1e-4, 4))],
           fmt='rgba32float', comment='Lucas-Kanade at 1/8.', at=(600, -400))
lk4 = glsl(fl, 'lk4', [lums[4][0], lums[4][1], lk8], G('lk.glsl'), [('uP', (1, 1e-4, 8))],
           fmt='rgba32float', comment='Lucas-Kanade at 1/4, started from 1/8.', at=(800, -200))
fsfb = mk(fl, feedbackTOP, 'flowsm_fb', [lk4], comment='Previous smoothed flow.', top='flowsm', at=(1000, -50))
fsm = glsl(fl, 'flowsm', [fsfb, lk4, cut], G('flowsmooth.glsl'), [('uS', (0.5, CUT, 0.2, W))],
           fmt='rgba32float', comment='Smoothed flow.', at=(1200, -200))
mk(fl, nullTOP, 'flow', [fsm], comment='Flow (UV units).', at=(1400, -200))
NB = (W // 16, H // 16)
sadc = glsl(fl, 'bm_sad_c', [lums[4][0], lums[4][1], lums[4][0]], G('bm_sad.glsl'), [('uP', (6, 4, 0))],
            res=(NB[0] * 13, NB[1] * 13), fmt='rgba32float', comment='Block costs at 1/4: 16 px blocks, +-6 px (24 full).', at=(800, 0))
bmc = glsl(fl, 'bm_min_c', [sadc], G('bm_min.glsl'), [('uP', (6, 0.004, 0, 4)), ('uFull', (W, H))],
           res=NB, fmt='rgba32float', comment='Best coarse offset per block.', at=(1000, 0))
sadf = glsl(fl, 'bm_sad_f', [lums[2][0], lums[2][1], bmc], G('bm_sad.glsl'), [('uP', (2, 8, 1))],
            res=(NB[0] * 5, NB[1] * 5), fmt='rgba32float', comment='Block costs at 1/2 around the coarse offset, +-2 px.', at=(800, 150))
bmf = glsl(fl, 'bm_min_f', [sadf], G('bm_min.glsl'), [('uP', (2, 0.004, 1, 2)), ('uFull', (W, H))],
           res=NB, fmt='rgba32float', comment='Best offset per block, quarter-pel: the block vectors.', at=(1000, 150))
mk(fl, nullTOP, 'mv', [bmf], comment='Block vectors (UV units).', at=(1200, 100))
vis = glsl(fl, 'vis', [fl.op('flow'), fl.op('mv')], '''
// DEV ONLY: left half LK flow, right half block vectors; mid gray = still, +x orange, -x blue.
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    vec2 v = uv.x < 0.5 ? texture(sTD2DInputs[0], vec2(uv.x * 2.0, uv.y)).rg
                        : texelFetch(sTD2DInputs[1], ivec2(vec2((uv.x - 0.5) * 2.0, uv.y) * uTD2DInfos[1].res.zw), 0).rg;
    v *= vec2(1280.0, 720.0) / 6.0;
    vec3 c = vec3(0.5) + v.x * vec3(0.45, 0.2, -0.35) + v.y * vec3(0.25, 0.25, 0.25);
    fragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
''', res=(W, H), fmt='rgba8fixed', comment='DEV ONLY: flow picture.', at=(1400, 0))
mk(fl, cacheTOP, 'keep', [vis], comment='DEV ONLY: always cooks.', alwayscook=False, cachesize=1, at=(1600, 0))

KF = "{}.par.Kf.eval()".format(SRC)
REFRESH = Expr('{} * 0.13'.format(KF))


def smear_variant(name, y, comment, flow_in=None, ugain=1.0, uB=(1, 1, 0)):
    v = fresh(name, -800, y, comment)
    i = sel(v, 'in', 0, 0, P + '/src/out')
    ip = sel(v, 'in_prev', 0, -150, P + '/flow/in_prev')
    f = sel(v, 'flow', 0, -300, P + '/flow/flow')
    ct = sel(v, 'cut', 0, -450, P + '/flow/cut')
    if flow_in:
        f = flow_in(v, f)
    fb = mk(v, feedbackTOP, 'fb', [i], comment='Previous output.', top='mosh', at=(200, 150))
    m = glsl(v, 'mosh', [fb, i, ip, f, ct], COMMON + G('smear.glsl'),
             [('uA', (REFRESH, ugain, CUT, 1)), ('uB', uB)], comment='Smear + residual.', at=(400, 0))
    keep(v, m)
    return v


smear_variant('a_smear', 0, 'Motion-vector smear with a codec-like residual, LK flow.')


def held(v, f):
    return mk(v, cacheTOP, 'flow_hold', [f], comment='Flow, frozen while Hold.', cachesize=1,
              active=Expr('not {}.par.Hold.eval()'.format(SRC)), at=(200, -300))


NOT_HOLD = Expr('0 if {}.par.Hold.eval() else 1'.format(SRC))
smear_variant('b_bloom', -600, 'Bloom: the flow frozen on Hold and reapplied every frame.', flow_in=held, ugain=1.5,
              uB=(NOT_HOLD, NOT_HOLD, 0))
smear_variant('e_chroma', -2400, 'Chroma mosh: luma recovers quickly, chroma stays moshed.', uB=(1, 1, 0.12))

SLOT = Expr('int(absTime.seconds * 4)')
SEED = Expr('absTime.frame % 10007')
SWEEP = Expr("(lambda d: d / 0.6 if 0 <= d <= 0.7 else -1)(absTime.seconds - {}.par.Kft.eval())".format(SRC))
Q = 1 / 32


def blocks_variant(name, y, comment, audio=False):
    v = fresh(name, -800, y, comment)
    i = sel(v, 'in', 0, 0, P + '/src/out')
    mv = sel(v, 'mv', 0, -300, P + '/flow/mv')
    ct = sel(v, 'cut', 0, -450, P + '/flow/cut')
    fbe = mk(v, feedbackTOP, 'fb_enc', [i], comment="Encoder's previous picture.", top='enc', at=(200, 150))
    fbd = mk(v, feedbackTOP, 'fb_dec', [i], comment="Decoder's previous picture.", top='dec', at=(200, 300))
    code = COMMON + G('blocks.glsl')
    glsl(v, 'enc', [fbe, i, fbe, mv, ct, fbe], code,  # input 5 unused here; the shader indexes it
         [('uA', (Q, 1, CUT, 1)), ('uB', (0, 0, SLOT, -1)), ('uC', (0, 16, SEED, 0)), ('uD', (0, 0, 0, 0))],
         comment="Encoder's reconstruction.", at=(400, 150))
    if audio:
        # The sample WAV is a 2.7 s one-shot (one hit per loop); the MP3 is a 70 s track with beats.
        a = mk(v, audiofileinCHOP, 'audio', comment='Sample music.',
               file=Expr("app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'"), playmode='sequential', repeat='on', at=(-400, -700))
        lp = mk(v, audiofilterCHOP, 'bass', [a], comment='Lows.', filter='lowpass', units='frequency',
                cutofffrequency=150, at=(-200, -700))
        mono = mk(v, mathCHOP, 'mono', [lp], comment='Mix to one channel.', chopop='off', chanop='avg', at=(0, -700))
        rms = mk(v, analyzeCHOP, 'rms', [mono], comment='Level this frame.', function='rmspower', at=(200, -700))
        slow = mk(v, lagCHOP, 'slow', [rms], comment='Slow level.', lag1=0.6, lag2=0.6, lagunit='seconds', at=(200, -850))
        slowg = mk(v, mathCHOP, 'slowg', [slow], comment='Onset margin.', gain=1.35, postoff=0.002, at=(400, -850))
        on = mk(v, mathCHOP, 'onset', [rms, slowg], comment='Level above the slow level.', chopop='sub', at=(400, -700))
        mk(v, triggerCHOP, 'beat', [on], comment='Beat envelope; at most one a second (Calm).',
           threshold=0.0, retrigger=1.0, retriggerunit='seconds', attack=0, peak=1, peaklen=0.3,
           peaklenunit='seconds', decay=0, sustain=0, release=0, at=(600, -700))
        mvh = mk(v, cacheTOP, 'mv_hold', [mv], comment='Block vectors, frozen during a beat.', cachesize=1,
                 active=Expr("op('beat')[0] < 0.5"), at=(200, -300))
        drop = Expr("0 if op('beat')[0] > 0.5 else 1")
        fade = Expr("0 if op('beat')[0] > 0.5 else 0.03")
        glsl(v, 'dec', [fbd, i, fbe, mvh, ct, v.op('enc')], code,
             [('uA', (Q, 1, CUT, drop)), ('uB', (0.015, 0, SLOT, SWEEP)), ('uC', (0, 16, SEED, 1)),
              ('uD', (0, fade, 0, 0))], comment="Decoder's picture: the output.", at=(400, 0))
    else:
        glsl(v, 'dec', [fbd, i, fbe, mv, ct, v.op('enc')], code,
             [('uA', (Q, 1, CUT, 1)), ('uB', (0.02, 0, SLOT, SWEEP)), ('uC', (0, 16, SEED, 1)), ('uD', (0, 0, 0, 0))],
             comment="Decoder's picture: the output.", at=(400, 0))
    keep(v, v.op('dec'))
    return v


blocks_variant('c_blocks', -1200, 'Macroblock codec model: dropped I-frame, frozen blocks, sweep recovery.')
blocks_variant('d_audio', -1800, 'Blocks + audio: beats drop the keyframe and freeze vectors.', audio=True)

# DEV ONLY: the mean luminance of each output, read every frame by shoot.py for a rough flash check.
mt = fresh('meter', -1600, -600, 'DEV ONLY: mean luminance of each output.')
for k, name in enumerate(['src', 'a_smear', 'b_bloom', 'c_blocks', 'd_audio', 'e_chroma']):
    s_ = sel(mt, 'sel_' + name, 0, -150 * k, P + '/' + name + '/out')
    mk(mt, analyzeTOP, 'lum_' + name, [s_], comment='Mean luminance.', op='average',
       analyzechannel='luminance', at=(200, -150 * k))
for c in host.children:
    if c.op('keep'):
        c.op('keep').cook(force=True)
problems = []
for o in host.findChildren():
    for p in o.pars():
        if p.mode == ParMode.EXPRESSION:
            try:
                p.eval()
            except Exception as e:
                problems.append('{}.{}: {}'.format(o.path, p.name, e))
    for e in (o.errors(), o.warnings()):
        if e:
            problems.append('{}: {}'.format(o.path, e))
print('built', [c.name for c in host.children])
print('problems:', len(problems))
for p in problems[:20]:
    print(' ', p[:400])
