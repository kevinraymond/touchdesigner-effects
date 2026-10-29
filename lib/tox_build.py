"""Shared by every builder, which exec()s this file into its own globals before it builds,
and by tests/check_tox.py, which execs it for digest() and component_sources(). Nothing
here runs at load time or touches TouchDesigner outside a function.

Started from Fosfora's integrations/touchdesigner/tox_build.py (digest, the self-contained
and docked-DAT checks, save_tox); the standard effect shell and the readability, I/O and
resolution checks are this library's promises (docs/BRIEF.md) turned into code.
"""

import glob
import hashlib
import json
import os
import re

REPO = 'kevinraymond/touchdesigner-effects'
DOCS_URL = 'https://github.com/' + REPO + '/blob/main/docs/effects/{}.md'
DOWNLOAD_URL = 'https://github.com/' + REPO + '/releases/latest/download/{}.tox'

# TouchDesigner's own operators, present in every install: a reference into them is not a leak
# (every Time COMP clones /sys/local/time; palette components point into /sys and /ui).
SYSTEM = ('/sys/', '/ui/')
# The free Non-Commercial license renders at most this many pixels on each side.
MAX_RES = 1280
# Saved in the .tox, so the picture reads on the node when it is dragged in.
NODE_W, NODE_H = 480, 270
# One node color for the whole library (the orange of its orange/blue palette).
NODE_COLOR = (0.95, 0.55, 0.15)
# Shown while nothing is wired into the effect's TOP input; an effect that needs motion passes
# one of the sample movies instead (SAMPLE_MOVIE), as an expression on app.samplesFolder.
SAMPLE_MEDIA = "app.samplesFolder + '/Map/Banana.tif'"
SAMPLE_MOVIE = "app.samplesFolder + '/Map/Nature/Movie.1.mp4'"
WINDOW_W, WINDOW_H = 1280, 720
# The standard Flashing parameter (docs/TD_IDIOMS.md A1) and the shortest time each setting
# allows between two flashes. Never under 1/3 s: WCAG 2.3.1 allows three flashes a second.
# Custom parameter styles that name an operator: their val is a path, their eval() the operator.
OP_STYLES = ('OP', 'COMP', 'OBJ', 'PanelCOMP', 'TOP', 'CHOP', 'SOP', 'MAT', 'DAT', 'POP')
FLASHING = (('off', 'Off'), ('calm', 'Calm'), ('wcag', 'Up to 3 per second'))
FLASH_INTERVAL = {'off': None, 'calm': 1.0, 'wcag': 1 / 3}
# The clock a shader gets (clock_seconds()): absTime.seconds wrapped every CLOCK seconds (about 4.6 h).
# A uniform is a 32-bit float, and absTime.seconds counts from TouchDesigner's start: after 12 hours it
# is good to 1/256 s, after 3 days to 1/32 s (two frames), so frame-timed noise, gaps between frames
# and smooth motion all coarsen the longer a show runs (board #4680). Wrapped, it stays within 1 ms.
# Shaders take differences of it modulo CLOCK (lib/glsl's clock, pace, speed); anything that must be
# exact (which update, which frame) is counted in Python, as VHS + CRT's e-ink and plasma do.
CLOCK = 16384

_ABSOLUTE = re.compile(r'^(/|[A-Za-z]:[/\\]|\\\\)')
_ABSOLUTE_OP_CALL = re.compile(r"""op\(\s*['"]/(?!sys/|ui/)""")
_EXTENSION_PAR = re.compile(r'ext\d+object$')
_PERIODIC = re.compile(r'math\.(sin|cos)\(')


# ---- Sources and hashes (also used outside TouchDesigner) -----------------------------------
def component_sources(root, comp_dir):
    """What a component's .tox is built from, as patterns relative to root: the shared library
    (every lib/*.py, and the shaders in lib/glsl/ that several effects share), the component's
    builder (build_<name>.py) and everything in its src/. A change to any of them needs a
    rebuild, and tests/check_tox.py fails until it happens."""
    rel = os.path.relpath(comp_dir, root).replace(os.sep, '/')
    name = os.path.basename(comp_dir)
    patterns = ['lib/*.py', '{}/build_{}.py'.format(rel, name)]
    if glob.glob(os.path.join(root, 'lib', 'glsl', '*')):
        patterns.append('lib/glsl/*')
    if glob.glob(os.path.join(comp_dir, 'src', '*')):
        patterns.append(rel + '/src/*')
    return patterns


def digest(root, patterns):
    """sha256 over the files the patterns name (relative to root), each pattern's matches sorted."""
    h = hashlib.sha256()
    for pattern in patterns:
        paths = sorted(p for p in glob.glob(os.path.join(root, pattern)) if os.path.isfile(p))
        if not paths:
            raise FileNotFoundError(os.path.join(root, pattern))
        for path in paths:
            with open(path, 'rb') as f:
                h.update(os.path.relpath(path, root).replace(os.sep, '/').encode() + b'\0' + f.read() + b'\0')
    return h.hexdigest()


def lib_glsl(root, name):
    """A shader shared by several effects, from lib/glsl/ (depth_near.glsl, depth_find.glsl)."""
    with open(os.path.join(root, 'lib', 'glsl', name)) as f:
        return f.read()


def lib_module(root, name):
    """Another shared file, lib/<name>.py, as a dict of its names: lib_module(_ROOT, 'font5x7')."""
    path = os.path.join(root, 'lib', name + '.py')
    ns = {'__name__': 'lib.' + name}
    exec(compile(open(path).read(), path, 'exec'), ns)
    return ns


# ---- Building ---------------------------------------------------------------------------------
class Expr:
    """A parameter value that is an expression: mk(..., index=Expr('parent().par.View.menuIndex'))."""

    def __init__(self, text):
        self.text = text


def setpars(o, **values):
    pars = {p.name: p for p in o.pars()}
    for name, value in values.items():
        if name not in pars:
            raise RuntimeError('{} has no parameter {!r}; it has: {}'.format(o.OPType, name, sorted(pars)))
        if isinstance(value, Expr):
            pars[name].expr = value.text
        else:
            pars[name].val = value


def mk(host, kind, name, inputs=(), comment='', at=None, **pars):
    """Create, comment, set parameters and wire the inputs in one call. Inside the effect being built the
    operator joins the current section() and finish_effect() places it; anywhere else at=(x, y) places it."""
    o = host.create(kind, name)
    if host.path == _LAYOUT['comp']:
        if _LAYOUT['current'] is None:
            raise RuntimeError('{} was made before any section(): say which part of the network it belongs '
                               'to'.format(o.name))
        _LAYOUT['of'][o.name] = _LAYOUT['current']
    elif at is not None:
        o.nodeX, o.nodeY = at
    setpars(o, **pars)
    # Multi-input operators (Switch, Merge, Layout) grow a connector as each one is wired; a GLSL
    # TOP stops at 3, so glsl() handles more.
    for i, src in enumerate(inputs):
        o.inputConnectors[i].connect(src)
    if comment:
        o.comment = comment
    return o


def docked(o, suffix, text, comment):
    """Fill the DAT TouchDesigner docked to o when it created it (callbacks, a shader, keys)
    instead of adding one beside it, which would leave the docked one behind as junk."""
    (dat,) = [d for d in o.docked if d.isDAT and d.name.endswith(suffix)]
    dat.text = text
    dat.comment = comment
    return dat


def uniforms(g, **values):
    """Set a GLSL TOP's vector uniforms: uniforms(g, uAmount=0.5, uTint=(1, 0.5, 0), uTime=clock_seconds()).
    Each value is a number, an Expr, or a tuple of up to four of them (x, y, z, w)."""
    g.seq.vec.numBlocks = max(len(values), 1)
    for i, (name, v) in enumerate(values.items()):
        getattr(g.par, 'vec{}name'.format(i)).val = name
        for axis, x in zip('xyzw', v if isinstance(v, (tuple, list)) else (v,)):
            p = getattr(g.par, 'vec{}value{}'.format(i, axis))
            if isinstance(x, Expr):
                p.expr = x.text
            else:
                p.val = x


def glsl(host, name, inputs, pixel, comment, res=None, fmt=None, at=None, **values):
    """A GLSL TOP with its docked pixel shader filled (never a second DAT beside it), any number
    of inputs, an optional custom resolution and pixel format, and uniforms (see uniforms())."""
    # A new GLSL TOP has 3 input connectors that don't grow within one Python call, and
    # setInputs() doesn't add more either; its TOPs parameter appends further inputs as
    # sTD2DInputs[3], [4]... (2025.33230, dev/selftest.py checks a 5-input GLSL TOP).
    g = mk(host, glslTOP, name, inputs[:3], comment, at=at)
    if len(inputs) > 3:
        g.par.tops = ' '.join(o.name for o in inputs[3:])
    docked(g, '_pixel', pixel, comment)
    if res:
        setpars(g, outputresolution='custom', resolutionw=res[0], resolutionh=res[1])
    if fmt:
        setpars(g, format=fmt)
    if values:
        uniforms(g, **values)
    return g


def audio_in(comp, root):
    """The effect's audio front end. Whatever is wired into input 2 (Fosfora's signal, raw audio,
    TouchDesigner's audioAnalysis or Essentia rhythm CHOP, or nothing) becomes the channels beat,
    beat_count, bar_count, beat_phase, level, build, drop_count, section_count, source, the seven bands and
    beat_period;
    lib/audio_callbacks.py says how (build and the drop and section counts need Fosfora). One
    Script CHOP does it and cooks only when something uses it, so nothing in the audio front end
    runs while the effect's output is unused (TD_IDIOMS C5, dev/idle.py checks it); for raw audio
    it measures the low band itself (numpy), since a time-sliced Audio Filter CHOP there cooked
    every frame, used or not (2025.33230). Needs new_effect(..., audio=True); returns the Script
    CHOP."""
    script = mk(comp, scriptCHOP, 'audio', [comp.op('in2_audio')],
                'Input 2 as beat, beat_count, level and the rest (lib/audio_callbacks.py).')
    docked(script, '_callbacks', open(os.path.join(root, 'lib', 'audio_callbacks.py')).read(),
           'Turns whatever is on input 2 into beat, beat_count, level and the rest.')
    return script


def optical_flow(comp, root, source, levels=(8, 4), new_frame=2e-5, cut=(0.02, 4.0, 0.25), flow=True):
    """The input's motion, shared by Datamosh and Fluid: its luma at 1/8 and 1/4 (lum8, lum4; lum2 too
    when levels has 2; levels=(8,) stops at 1/8, as Words, whose cells are 8 pixels, needs no finer), each beside
    the previous input frame's (lum8p...); whether this frame brings a new input frame and whether it is a cut
    (change, change_avg, clock: r new frame, g cut); and Lucas-Kanade optical flow at 1/8, then 1/4 starting from
    it (lk8, lk4: rg the displacement in UV units since the last input frame, b its confidence). new_frame is the mean luma change at 1/8 that
    makes a new frame; cut is (least change that is a cut, how many times the running mean of the
    changes it must be, seconds between cuts). flow=False leaves out the flow (lk8, lk4) and lum8p, which only lk8
    reads, for an effect that needs only the luma and the clock (Temporal Resonator, Caustics). Every size follows
    source through the resolution menu: an expression reading another operator's size kept an unwired sample movie
    cooking while nothing used the effect. The shaders are lib/glsl's lum, change, clock and lk. Returns the
    operators by name."""
    ops = {}
    for k in (8, 4, 2):
        if k not in levels:
            continue
        ops['lum{}'.format(k)] = glsl(comp, 'lum{}'.format(k), [source], lib_glsl(root, 'lum.glsl'),
                                      'Luma at 1/{}.'.format(k), fmt='mono32float', uK=k)
        setpars(ops['lum{}'.format(k)], outputresolution={8: 'eighth', 4: 'quarter', 2: 'half'}[k])
        if flow or k != 8:
            ops['lum{}p'.format(k)] = mk(comp, cacheTOP, 'lum{}p'.format(k), [ops['lum{}'.format(k)]],
                                         'lum{} of the previous input frame.'.format(k), cachesize=2, outputindex=-1)
    lum8 = ops['lum8']
    seen = ops['seen'] = mk(comp, feedbackTOP, 'seen', [lum8],
                            'What change saw last frame: its g is the luma then.', top='change')
    ops['change'] = glsl(comp, 'change', [lum8, seen], lib_glsl(root, 'change.glsl'),
                         'Per pixel, how much the input changed since the last frame seen.', fmt='rgba32float',
                         uTime=clock_seconds())
    avg = ops['change_avg'] = mk(comp, analyzeTOP, 'change_avg', [ops['change']],
                                 'The mean change: 0 when no new frame came.', op='average',
                                 analyzechannel='independent')
    clock_fb = ops['clock_fb'] = mk(comp, feedbackTOP, 'clock_fb', [avg], "The clock's last frame.",
                                    top='clock')
    ops['clock'] = glsl(comp, 'clock', [avg, clock_fb], lib_glsl(root, 'clock.glsl'),
                        'One pixel: is this a new input frame, is it a cut (experimental).', fmt='rgba32float',
                        uS=(new_frame, cut[0], cut[1], 0.1), uC=(clock_seconds(), cut[2]))
    if not flow:
        return ops
    ops['lk8'] = glsl(comp, 'lk8', [lum8, ops['lum8p'], lum8], lib_glsl(root, 'lk.glsl'),
                      'Optical flow at 1/8.', fmt='rgba32float', uP=(0, 1e-4, 4))
    if 4 in levels:
        ops['lk4'] = glsl(comp, 'lk4', [ops['lum4'], ops['lum4p'], ops['lk8']], lib_glsl(root, 'lk.glsl'),
                          'Optical flow at 1/4, starting from lk8.', fmt='rgba32float', uP=(1, 1e-4, 8))
    return ops


def structure_tensor(comp, root, source, sigma=2.0, ease=None):
    """The picture's local orientation, shared by the effects that follow its edges (Paint; Reaction-diffusion
    and Pencil to come): the structure tensor of its color (tensor: E, F, G from Jaehne's derivative filter),
    smoothed by a Gaussian of sigma pixels at 720 high across and then down (tensor_h, tensor_v; sigma may be an
    Expr), and its eigenanalysis (flow: rg the direction along the edges, a unit vector in pixels; b the
    anisotropy 0-1, 0 where nothing has a direction; a the strongest change). With ease (seconds), the smoothed
    tensor is eased over time first (tensor_fb, tensor_ease), so the direction turns smoothly instead of jittering
    with the picture's noise and flicker. Each pass is the input's size, in 16-bit float; edges hold rather than
    fall to black. The shaders are lib/glsl's tensor, tensor_blur, tensor_ease and tensor_flow, after Kyprianidis,
    Kang and Doellner (2009, 2011). Returns the operators by name."""
    ops = {}
    ops['tensor'] = glsl(comp, 'tensor', [source], lib_glsl(root, 'tensor.glsl'),
                         "The structure tensor of the picture's color, per pixel.", fmt='rgba16float')
    ops['tensor_h'] = glsl(comp, 'tensor_h', [ops['tensor']], lib_glsl(root, 'tensor_blur.glsl'),
                           'The tensor smoothed across.', fmt='rgba16float', uB=(1, 0, sigma))
    ops['tensor_v'] = glsl(comp, 'tensor_v', [ops['tensor_h']], lib_glsl(root, 'tensor_blur.glsl'),
                           'The tensor smoothed down.', fmt='rgba16float', uB=(0, 1, sigma))
    smooth = ops['tensor_v']
    if ease is not None:
        ops['tensor_fb'] = mk(comp, feedbackTOP, 'tensor_fb', [smooth], "tensor_ease's last frame.",
                              top='tensor_ease')
        ops['tensor_ease'] = glsl(comp, 'tensor_ease', [smooth, ops['tensor_fb']], lib_glsl(root, 'tensor_ease.glsl'),
                                  'The tensor eased over {:g} s, so the direction turns smoothly.'.format(ease),
                                  fmt='rgba16float', uE=(Expr('min(absTime.stepSeconds, 0.1)'), ease))
        smooth = ops['tensor_ease']
    ops['flow'] = glsl(comp, 'flow', [smooth], lib_glsl(root, 'tensor_flow.glsl'),
                       'Along the edges: rg the direction, b how clear it is (anisotropy).', fmt='rgba16float')
    for o in ops.values():
        if o.OPType == 'glslTOP':
            setpars(o, inputextenduv='hold')
    return ops


def pyramid(comp, root, source, levels, fmt='rgba32float', prefix='g', what='The picture'):
    """The picture's Gaussian pyramid, shared by the effects that work on its octaves of detail (Video Vocoder,
    Detail): source, then levels more (g1, g2...), each half the size of the one before and smoothed before it was
    halved (lib/glsl pyramid_down.glsl), after Burt and Adelson's Laplacian pyramid (1983). A Laplacian band k is
    level k minus level k + 1 read through pyramid.glsl's expand(), and summing the bands back up through the same
    expand() gives the picture back exactly, so an effect changes the bands and collapses them in its own shader.
    Every size follows source through the resolution menu, in 32-bit float by default; edges hold. An effect with
    several pyramids names each one's levels by its own prefix, and says what it halves in what. Returns the levels,
    [source, g1, ...]."""
    out = [source]
    for k in range(1, levels + 1):
        g = glsl(comp, '{}{}'.format(prefix, k), [out[-1]], lib_glsl(root, 'pyramid_down.glsl'),
                 '{} at 1/{} of its size, smoothed before it was halved (pyramid level {}).'.format(what, 2 ** k, k),
                 fmt=fmt)
        setpars(g, outputresolution='half', inputextenduv='hold')
        out.append(g)
    return out


def clock_seconds():
    """absTime.seconds for a shader's uniform, wrapped every CLOCK seconds so a 32-bit float keeps it to 1 ms
    however long TouchDesigner has run. Smooth motion driven by it jumps once at each wrap; take
    differences modulo CLOCK. assert_idiomatic refuses a shader handed the raw clock."""
    return Expr('absTime.seconds % {}'.format(CLOCK))


def flow_speed(comp, root, mo, start, dead=0.25, hold=0.3):
    """The input's motion as a speed, shared by Fluid and VHS + CRT, from optical_flow()'s ops (mo): pace (one
    pixel: when the last new input frame came, and the gap between frames) and motion (lk4, or lk8 when the flow
    stops at 1/8, smoothed over 5 x 5 and divided by that gap: rg cells per second at that flow's size, b
    confidence), held between the input's frames, so a slow clip moves like a live camera, dying away hold seconds
    after the last new frame, and nothing across a cut; dead is a dead zone in cells per frame. start is a 1 x 1
    32-bit TOP both Feedback TOPs (pace_fb, motion_fb) start from. The shaders are lib/glsl's pace and speed.
    Returns (pace, motion)."""
    pace_fb = mk(comp, feedbackTOP, 'pace_fb', [start], "pace's last frame.", top='pace')
    pace = glsl(comp, 'pace', [mo['clock'], pace_fb], lib_glsl(root, 'pace.glsl'),
                'One pixel: when the last new input frame came, and the gap between frames.', fmt='rgba32float',
                uP=(clock_seconds(), 0.25))
    motion_fb = mk(comp, feedbackTOP, 'motion_fb', [start], "motion's last frame.", top='motion')
    flow = mo['lk4'] if 'lk4' in mo else mo['lk8']
    motion = glsl(comp, 'motion', [flow, motion_fb, pace], lib_glsl(root, 'speed.glsl'),
                  "The input's motion at {} of its size, as a speed, held between the input's frames.".format(
                      'a quarter' if flow is mo.get('lk4') else 'an eighth'),
                  fmt='rgba32float', uM=(clock_seconds(), Expr('min(absTime.stepSeconds, 0.05)'), dead, hold))
    return pace, motion


def flash_gate(comp, trigger, name='flash'):
    """Every flash an effect makes goes through here (docs/TD_IDIOMS.md A1). A Trigger CHOP turns
    trigger's channels into one-frame-wide pulses no closer together than the Flashing parameter
    allows (Re-Trigger Delay = FLASH_INTERVAL), and a Math CHOP passes nothing when Flashing is
    Off. Shape the flash itself (its envelope) downstream; never bypass the gate."""
    calm, wcag = FLASH_INTERVAL['calm'], FLASH_INTERVAL['wcag']
    limit = mk(comp, triggerCHOP, name + '_limit', [trigger],
               'Flashes no closer together than the Flashing parameter allows.',
               retrigger=Expr("{} if parent().par.Flashing == 'wcag' else {}".format(wcag, calm)),
               retriggerunit='seconds', attack=0, peak=1, decay=0, sustain=0)
    return mk(comp, mathCHOP, name, [limit], 'Nothing passes when Flashing is Off.',
              gain=Expr("0 if parent().par.Flashing == 'off' else 1"))


def _par(group):
    """append*() returns a ParGroup in current builds; the first Par is the one we want."""
    try:
        return group[0]
    except TypeError:
        return group


def custom(page, kind, name, label, default, help_text, lo=None, hi=None, clamp=False):
    """A custom parameter with its default, range and help text (every one needs help)."""
    p = _par(getattr(page, 'append' + kind)(name, label=label))
    if default is not None:
        p.default = default
        p.val = default
    if lo is not None:
        p.normMin, p.min, p.clampMin = lo, lo, clamp
    if hi is not None:
        p.normMax, p.max, p.clampMax = hi, hi, clamp
    p.help = help_text
    return p


# ---- Laying out the network ------------------------------------------------------------------------
# Opening an effect shows its network read left to right in titled Network Boxes, one for each part of the
# effect, in rows (lanes): the picture's along the top from input 1 to the output, then any others, then the
# audio and the depth, which start from inputs 2 and 3 (docs/BUILDING.md, Laying out the network). The builder
# names the parts with section(); finish_effect() places every operator from what reads what, and
# assert_laid_out() checks the result.
LAYOUT_COL = 200       # from one column of operators to the next (a column holding a wider node is wider)
LAYOUT_NODE_W = 130    # an operator's usual width (2025.33230)
LAYOUT_GAP = 40        # between two operators stacked in a column
LAYOUT_DOCK_GAP = 30   # between an operator and the DAT docked under it (TouchDesigner's own: 120 from its bottom)
LAYOUT_PAD = 20        # a box's margin around its operators
LAYOUT_TITLE = 30      # a box's title bar (the Annotate COMP's Title Height)
LAYOUT_TITLE_CHAR = 10  # the width a box leaves for each character of its title
LAYOUT_BOX_GAP = 20    # between two boxes side by side
LAYOUT_LANE_GAP = 60   # between two lanes
FIRST_LANES = ('docs', 'picture')
LAST_LANES = ('audio', 'depth')
# Box colors: dark, so the operators stand out, and never the only sign of what a box holds (its title is).
BOX_COLORS = {'docs': (0.22, 0.22, 0.22), 'io': (0.17, 0.22, 0.3), 'picture': (0.24, 0.2, 0.3),
              'audio': (0.16, 0.25, 0.18), 'depth': (0.28, 0.22, 0.15)}
# The effect being built (its path), its sections (key -> title, lane, order), which section each operator mk()
# made belongs to (name -> key), and the section operators join now.
_LAYOUT = {'comp': None, 'sections': {}, 'of': {}, 'current': None}
_OP_NAME = re.compile(r"""op\(\s*['"]([A-Za-z0-9_]+)['"]\s*\)""")


def section(key, title=None, lane=None):
    """The operators mk() makes from here on (and everything built on it: glsl(), the lib helpers) go in the
    Network Box key, titled with what that part of the effect does, in plain words. lane is the row of boxes it
    sits in: 'picture' (the default) runs along the top from input 1 to the output; 'audio' and 'depth' come last,
    since they start from inputs 2 and 3; any other name makes a lane of its own between them, in the order first
    named. Within a lane, boxes run left to right in the order their contents read each other. Naming a section
    again goes back into it."""
    s = _LAYOUT['sections'].setdefault(key, {'title': None, 'lane': None, 'order': len(_LAYOUT['sections'])})
    if title is not None:
        s['title'] = title
    if lane is not None:
        s['lane'] = lane
    _LAYOUT['current'] = key


def put(o, key):
    """Move o, made some other way than mk() (a loaded .tox), into section key."""
    _LAYOUT['of'][o.name] = key


def plan_layout(nodes, sections):
    """Where each operator and box goes. Plain Python, no TouchDesigner, so it can be tried on a dumped network.
    nodes: name -> dict(w, h, section, wires (the names wired into it), refs (the names its parameters read, not a
    Feedback TOP's loop), docked (the heights of the DATs docked to it, top to bottom)), in the order they were made.
    sections: key -> dict(title, lane, order).

    Columns: what an operator is wired from sits left of it, and so does what it reads from its own box (a
    reference to another box is left free: TouchDesigner draws no line for it, and the picture's shaders read the
    audio's values all along the way). Each box keeps its columns together, wide enough for its title; boxes in a
    lane run side by side in the order they are wired; the 'output' box takes the last column. Each operator sits
    as far right as what reads it allows, and level with what it reads in its box. Returns ({name: (x, y)},
    [(key, x, y, w, h)]) in TouchDesigner's units: y up, each the lower-left corner."""
    used = [k for k in sorted(sections, key=lambda k: sections[k]['order'])
            if any(n['section'] == k for n in nodes.values())]
    lane_of = {k: sections[k]['lane'] or 'picture' for k in used}
    lanes = [ln for ln in FIRST_LANES if ln in lane_of.values()]
    for k in used:
        if lane_of[k] not in lanes and lane_of[k] not in LAST_LANES:
            lanes.append(lane_of[k])
    lanes += [ln for ln in LAST_LANES if ln in lane_of.values()]
    names = list(nodes)
    index = {n: i for i, n in enumerate(names)}
    sec = {n: nodes[n]['section'] for n in names}
    members = {k: [n for n in names if sec[n] == k] for k in used}
    reads = {n: sorted({r for r in nodes[n]['wires'] if r in nodes} |
                       {r for r in nodes[n]['refs'] if r in nodes and sec[r] == sec[n]}) for n in names}
    users = {n: [m for m in names if n in reads[m]] for n in names}

    # Everything an operator reads comes before it: a loop can't be laid out left to right.
    order, state = [], {}

    def visit(n, path):
        if state.get(n) == 'done':
            return
        if state.get(n) == 'open':
            raise RuntimeError('these operators read each other in a loop, so none of them can sit right of all it '
                               'reads: {} (only a Feedback TOP may close a loop)'.format(
                                   ' -> '.join(path[path.index(n):] + [n])))
        state[n] = 'open'
        for r in reads[n]:
            visit(r, path + [n])
        state[n] = 'done'
        order.append(n)
    for n in names:
        visit(n, [])

    # Boxes in a lane run in the order they are wired (else in the order they were named).
    in_lane = {}
    for ln in lanes:
        ks = [k for k in used if lane_of[k] == ln]
        after = {k: {sec[r] for n in members[k] for r in reads[n] if sec[r] != k and sec[r] in ks} for k in ks}
        seq = []
        while len(seq) < len(ks):
            ready = [k for k in ks if k not in seq and after[k] <= set(seq)]
            if not ready:
                raise RuntimeError('sections {} in lane {} are wired to each other both ways: put them in one '
                                   'section or in separate lanes'.format(sorted(k for k in ks if k not in seq), ln))
            seq.append(min(ready, key=lambda k: sections[k]['order']))
        in_lane[ln] = seq

    def columns(col):
        """Where each column starts: LAYOUT_COL apart, more after a column holding a node wider than the usual."""
        widest = {}
        for n in names:
            widest[col[n]] = max(widest.get(col[n], 0), nodes[n]['w'])
        xs = [0]
        for c in range(max(col.values()) + 2):
            xs.append(xs[-1] + max(LAYOUT_COL, widest.get(c, 0) + LAYOUT_COL - LAYOUT_NODE_W))
        return xs

    def span(k, col, xs):
        lo = min(xs[col[n]] for n in members[k])
        hi = max(xs[col[n]] + nodes[n]['w'] for n in members[k])
        return lo, max(hi, lo + len(sections[k]['title']) * LAYOUT_TITLE_CHAR)

    col = {n: 0 for n in names}
    for _ in range(4 * len(names) + 10):
        changed = False
        for n in order:
            want = max([col[r] + 1 for r in reads[n]] + [col[n]])
            if want > col[n]:
                col[n], changed = want, True
        # Each operator as far right as what reads it allows, so a chain sits next to what it feeds; one read only
        # from other boxes goes no further than its own box already reaches, so boxes never push each other on.
        for n in reversed(order):
            if sec[n] == 'output' or not users[n]:
                continue
            want = min(col[m] for m in users[n]) - 1
            if not any(sec[m] == sec[n] for m in users[n]):
                others = [col[m] for m in members[sec[n]] if m != n]
                if not others:
                    continue
                want = min(want, max(others))
            if want > col[n]:
                col[n], changed = want, True
        for ln in lanes:
            right = None
            for k in in_lane[ln]:
                lo, hi = span(k, col, columns(col))
                while right is not None and lo - LAYOUT_PAD < right + LAYOUT_BOX_GAP:
                    for n in members[k]:
                        col[n] += 1
                    changed = True
                    lo, hi = span(k, col, columns(col))
                right = hi + LAYOUT_PAD
        if 'output' in used:
            xs = columns(col)
            rest = max(span(k, col, xs)[1] for k in used if k != 'output')
            last = max(col[n] for n in names if sec[n] != 'output') + 1
            while xs[last] - LAYOUT_PAD < rest + LAYOUT_PAD + LAYOUT_BOX_GAP:
                last += 1
            for n in members['output']:
                if col[n] < last:
                    col[n], changed = last, True
        if not changed:
            break
    else:
        raise RuntimeError('the layout did not settle')

    def extent(n):
        return nodes[n]['h'] + sum(LAYOUT_DOCK_GAP + h for h in nodes[n]['docked'])

    # Down from the top of each box's contents, a column at a time: stacked in the order of where the operators
    # each one is wired to sit (what it reads on a sweep to the right, what reads it on a sweep back), then each as
    # level with what it reads as the ones above it allow.
    down, height = {n: 0 for n in names}, {}
    for k in used:
        cols = sorted({col[n] for n in members[k]})

        def stack(c, near):
            here = []
            for n in members[k]:
                if col[n] == c:
                    mine = [down[m] for m in near(n) if sec[m] == k and col[m] != c]
                    here.append((sum(mine) / len(mine) if mine else down[n], index[n], n))
            cursor = 0
            for want, _, n in sorted(here):
                down[n] = max(want, cursor)
                cursor = down[n] + extent(n) + LAYOUT_GAP
            return cursor - LAYOUT_GAP
        for c in cols:
            stack(c, lambda n: reads[n])
        for c in reversed(cols):
            stack(c, lambda n: users[n])
        for c in cols:
            stack(c, lambda n: reads[n])
        top = min(down[n] for n in members[k])
        for n in members[k]:
            down[n] -= top
        height[k] = max(down[n] + extent(n) for n in members[k])

    xs = columns(col)
    pos, boxes, top = {}, [], 0
    for ln in lanes:
        box_h = max(height[k] for k in in_lane[ln]) + 2 * LAYOUT_PAD + LAYOUT_TITLE
        for k in in_lane[ln]:
            for n in members[k]:
                pos[n] = (xs[col[n]], top - LAYOUT_TITLE - LAYOUT_PAD - down[n] - nodes[n]['h'])
            lo, hi = span(k, col, xs)
            boxes.append((k, lo - LAYOUT_PAD, top - box_h, hi - lo + 2 * LAYOUT_PAD, box_h))
        top -= box_h + LAYOUT_LANE_GAP
    return pos, boxes


def _reads(o, siblings):
    """The names among siblings that o reads, as (wires, refs): what is wired into it, and what its parameters
    name (an OP parameter, or op('name') in an expression), except a Feedback TOP's Target TOP, the loop it
    closes."""
    wires, found = set(), set()
    for ic in o.inputConnectors:
        wires.update(c.owner.name for c in ic.connections)
    for p in o.pars():
        if o.OPType == 'feedbackTOP' and p.name == 'top':
            continue
        if p.mode == ParMode.EXPRESSION:
            found.update(_OP_NAME.findall(p.expr))
        elif p.isOP and isinstance(p.val, str):
            found.update(v.rstrip('/').split('/')[-1] for v in p.val.split())
    return wires & siblings, found & siblings - wires - {o.name}


def _prune_docked(comp):
    """A GLSL TOP comes with three docked DATs (2025.33230): its pixel shader, a compute shader and an Info DAT.
    Drop the shader its mode doesn't run, which would read as part of the effect. Keep the Info DAT: when a shader
    fails to compile, the node only says so, and the Info DAT says where."""
    for o in comp.findChildren(type=glslTOP):
        compute = o.par.mode.eval() == 'compute'
        unused = o.name + ('_pixel' if compute else '_compute')
        setpars(o, **{'pixeldat' if compute else 'computedat': ''})
        for d in list(o.docked):
            if d.name == unused:
                d.destroy()


def _docked(o):
    """The DATs docked to o, top to bottom: shaders and callbacks first, then an Info DAT."""
    return sorted(o.docked, key=lambda d: (d.OPType == 'infoDAT', d.name))


def lay_out(comp):
    """Place every operator in comp by plan_layout(), each docked DAT under its operator, and a Network Box
    (an Annotate COMP) around each section, titled; done by finish_effect(). Every operator must belong to a
    titled section."""
    _prune_docked(comp)
    items = [o for o in comp.children if o.dock is None and o.OPType != 'annotateCOMP']
    names = {o.name for o in items}
    stray = sorted(n for n in names if n not in _LAYOUT['of'])
    if stray:
        raise RuntimeError('{}: not in any section(): {}'.format(comp.path, ', '.join(stray)))
    for k in sorted({_LAYOUT['of'][n] for n in names}):
        if not _LAYOUT['sections'][k]['title']:
            raise RuntimeError('{}: section {!r} has no title'.format(comp.path, k))
    by = {o.name: o for o in items}
    made = [n for n in _LAYOUT['of'] if n in by]
    nodes = {}
    for n in made:
        wires, refs = _reads(by[n], names)
        nodes[n] = {'w': by[n].nodeWidth, 'h': by[n].nodeHeight, 'section': _LAYOUT['of'][n], 'wires': wires,
                    'refs': refs, 'docked': [d.nodeHeight for d in _docked(by[n])]}
    pos, boxes = plan_layout(nodes, _LAYOUT['sections'])
    for n, (x, y) in pos.items():
        o = by[n]
        o.nodeX, o.nodeY = x, y
        for d in _docked(o):
            y -= LAYOUT_DOCK_GAP + d.nodeHeight
            d.nodeX, d.nodeY = x, y
    for key, x, y, w, h in boxes:
        s = _LAYOUT['sections'][key]
        box = comp.create(annotateCOMP, 'box_' + key)
        box.name = 'box_' + key   # an Annotate COMP names itself annotate1 whatever create() asks
        kind = 'io' if key in ('input', 'output') else s['lane'] if s['lane'] in BOX_COLORS else 'picture'
        if key == 'docs':
            kind = 'docs'
        setpars(box, Mode='networkbox', Titletext=s['title'], Backcolorr=BOX_COLORS[kind][0],
                Backcolorg=BOX_COLORS[kind][1], Backcolorb=BOX_COLORS[kind][2])
        box.nodeX, box.nodeY, box.nodeWidth, box.nodeHeight = x, y, w, h
        box.comment = 'A Network Box around this part of the effect: ' + s['title']
    _LAYOUT['comp'] = None


def new_effect(name, title, summary, readme, tags=(), audio=False, flashing=False, sample=SAMPLE_MEDIA,
               parent_path=None, depth=False):
    """The standard shell every effect starts from: a COMP with the library's color, tags and
    node size, a README DAT, input 1 a TOP (sample media until something is wired) and, with
    audio=True, input 2 an optional CHOP. depth=True (with audio=True: input 2 is always the
    audio) adds input 3, an optional TOP: a depth map or mask, which depth_in() reads. flashing=True, for an effect that can flash, adds the
    standard Flashing parameter (finish_effect() places it); read it from inside the effect as
    parent().par.Flashing, and never flash more often than FLASH_INTERVAL allows. Returns (comp, page, source): the effect's custom
    page and the TOP to start the effect from. finish_effect() adds the rest and saves.
    parent_path defaults to TDLIB_PARENT when the caller defined one (the dev loop does), else
    /project1. Any previous copy there is replaced."""
    if parent_path is None:
        parent_path = globals().get('TDLIB_PARENT', '/project1')
    host = op(parent_path)
    old = host.op(name)
    if old:
        old.destroy()
    comp = host.create(baseCOMP, name)
    comp.nodeX, comp.nodeY = 0, 0
    comp.nodeWidth, comp.nodeHeight = NODE_W, NODE_H
    comp.color = NODE_COLOR
    comp.comment = summary
    for tag in ('touchdesigner-effects',) + tuple(tags) + (('flashing',) if flashing else ()):
        comp.tags.add(tag)
    page = comp.appendCustomPage(title)
    _LAYOUT.update(comp=comp.path, sections={}, of={}, current=None)
    section('docs', 'Read me', lane='docs')
    # One line per paragraph (src/readme.txt): the viewer wraps it to its own width.
    mk(comp, textDAT, 'README', comment='What this effect does and how to use it.', wordwrap='on').text = readme

    # A COMP orders its inputs by the In operators' names, not their positions (TouchDesigner
    # 2025.33230, dev/probes/input_order.py): the digit keeps the TOP first.
    section('input', 'Input 1, or a sample picture while nothing is wired in', lane='picture')
    mk(comp, inTOP, 'in1_top', comment='Input 1: the picture to process.')
    mk(comp, moviefileinTOP, 'sample', comment='Shown until a TOP is wired into input 1.', file=Expr(sample))
    source = mk(comp, switchTOP, 'source', [comp.op('in1_top'), comp.op('sample')],
                comment='Input 1 when it is wired, the sample picture when it is not.',
                index=Expr('0 if parent().inputConnectors[0].connections else 1'))
    # Inputs 2 and 3 open the audio and depth lanes; the builder titles them when it builds on them.
    if audio:
        section('audio', 'Audio (input 2)', lane='audio')
        mk(comp, inCHOP, 'in2_audio', comment='Input 2 (optional): audio or beat channels, e.g. Fosfora or audio analysis.')
    if depth:
        if not audio:
            raise ValueError('depth=True needs audio=True: input 2 is always the audio, input 3 the depth')
        section('depth', 'Depth or a mask (input 3)', lane='depth')
        mk(comp, inTOP, 'in3_top',
           comment='Input 3 (optional): a depth map or mask, grayscale: brighter is nearer, or inside.')
    _LAYOUT['current'] = None
    return comp, page, source


def depth_in(comp, fallback=None):
    """Input 3 (new_effect(..., depth=True)) when a TOP is wired into it, else fallback: a TOP the
    effect makes from input 1, or by default input 1's brightness (brighter is nearer), so the
    effect works with nothing on input 3. Returns the Switch TOP to read the depth from."""
    if fallback is None:
        fallback = mk(comp, monochromeTOP, 'depth_guess', [comp.op('source')],
                      "Input 1's brightness, standing in for depth while nothing is wired into input 3.")
    return mk(comp, switchTOP, 'depth', [comp.op('in3_top'), fallback],
              'Input 3 (depth or mask) when it is wired, else the stand-in.',
              index=Expr('0 if parent().inputConnectors[2].connections else 1'))


def finish_effect(comp, last, version, page=None):
    """Add the output, Open Window, the About page and the node's picture, and lay out the network
    (lay_out()). save_effect() next."""
    if page is None:
        page = comp.customPages[0]
    # DATs TouchDesigner docked to an operator and the builder left as they were (a GLSL
    # TOP's info DAT, say) belong to their host; say so rather than leave them blank.
    for o in comp.findChildren():
        for d in o.docked:
            if d.comment.strip():
                continue
            if d.OPType == 'infoDAT' and o.OPType in ('glslTOP', 'glslMAT'):
                d.comment = ("What TouchDesigner reports compiling {}'s shaders: where they fail, if they "
                             'do.'.format(o.name))
            else:
                d.comment = 'Docked to {}; TouchDesigner made it with it.'.format(o.name)
    section('output', lane='picture')
    _LAYOUT['sections']['output']['title'] = _LAYOUT['sections']['output']['title'] or 'Output'
    mk(comp, outTOP, 'out_top', [last], "Output 1: the effect's picture.")

    if 'flashing' in comp.tags:
        flash = custom(page, 'Menu', 'Flashing', 'Flashing', None,
                       'How much the effect may flash. Off: never. Calm: at most one flash a second. '
                       'Up to 3 per second: the WCAG 2.3.1 limit, which no setting exceeds.')
        flash.menuNames = [n for n, _ in FLASHING]
        flash.menuLabels = [label for _, label in FLASHING]
        flash.default = flash.val = 'calm'
        flash.startSection = True
    opener = custom(page, 'Pulse', 'Openwindow', 'Open Window', None,
                    'Show the picture in its own window, 1280 x 720 or filling a display. Esc closes it.')
    opener.startSection = True
    custom(page, 'Toggle', 'Fullscreen', 'Full Screen', False,
           'Open the window filling the whole display, for a projector or a second screen.')
    custom(page, 'Int', 'Display', 'Display', 0, 'Which display the window opens on; 0 is the primary display.',
           0, 3).clampMin = True
    mk(comp, windowCOMP, 'window', comment='Open Window shows out_top here; Esc closes it.',
       winop='out_top', title=comp.name, justifyoffsetto='specifydisplay', display=Expr('parent().par.Display'),
       justifyh='center', justifyv='center', size=Expr("'fill' if parent().par.Fullscreen else 'custom'"),
       winw=WINDOW_W, winh=WINDOW_H, borders=Expr('not parent().par.Fullscreen'), blocksleep=True,
       closeescape=True)

    about = comp.appendCustomPage('About')
    for p in (custom(about, 'Str', 'Version', 'Version', version, 'Version of this effect.'),
              custom(about, 'Str', 'Builtwith', 'Built With', 'TouchDesigner ' + app.build,
                     'The TouchDesigner build this .tox was saved in; older builds may not open it.')):
        p.readOnly = True
    custom(about, 'Pulse', 'Help', 'Open Docs', None, "Open this effect's page in a browser.")
    section('docs')
    parexec = mk(comp, parameterexecuteDAT, 'parexec', comment='Open Window and Open Docs.')
    parexec.text = ('def onPulse(par):\n'
                    "    if par.name == 'Openwindow':\n"
                    "        op('window').par.winopen.pulse()\n"
                    "    elif par.name == 'Help':\n"
                    '        ui.viewFile({!r})\n').format(DOCS_URL.format(comp.name))
    setpars(parexec, op='..', pars='Openwindow Help', onpulse=True, valuechange=False)

    comp.par.opviewer = './out_top'
    comp.viewer = True
    lay_out(comp)
    return comp


def save_effect(comp, comp_dir, root):
    """Save comp as comp_dir/<name>.tox, with the manifest tests/check_tox.py checks (and its
    inputs, which a bundle reads to wire each effect)."""
    path, manifest = save_tox(comp, comp_dir, comp.name, {
        'version': comp.par.Version.eval(),
        'sources_sha256': digest(root, component_sources(root, comp_dir)),
        'inputs': [c.inOP.name for c in comp.inputConnectors],
    })
    print('built', comp.path, 'version', manifest['version'], 'in', app.build, '->', path)
    return path, manifest


# ---- Save-time checks ---------------------------------------------------------------------------
README_HEADING = re.compile(r'^[A-Z][A-Z0-9]+\b(?!\S*[a-z]).{0,50}$')   # USE, INPUT 2 (optional): audio...
README_ITEM = re.compile(r'^(- | |http|\{|\d+[.:)] )')                   # a list item, numbered too, a link...


def hard_wrapped(text):
    """The lines of a README where a paragraph runs on to the next line (docs/BUILDING.md, The README): the
    README holds one line per paragraph and per list item, so the viewer wraps it to its own width. After the
    first block (title, license, docs link), a line may be followed directly only by a list item (- or
    numbered), an indented line, a link or a format placeholder; a heading, a list item or a link by anything."""
    lines = text.split('\n')
    start = lines.index('') if '' in lines else len(lines)
    found = []
    for i in range(start, len(lines) - 1):
        a, b = lines[i], lines[i + 1]
        if not a.strip() or not b.strip() or README_HEADING.match(a) or README_ITEM.match(a) or README_ITEM.match(b):
            continue
        found.append(i + 1)
    return found


def _in_box(o, comp):
    """Whether o is part of a Network Box inside comp: TouchDesigner's own Annotate COMP, cloned from /sys."""
    p = o.parent()
    while p is not None and p.path != comp.path:
        if p.OPType == 'annotateCOMP':
            return True
        p = p.parent()
    return False


def _all(comp):
    """comp and everything inside it, except the insides of its Network Boxes."""
    return [comp] + [o for o in comp.findChildren() if not _in_box(o, comp)]


def assert_self_contained(comp):
    """A .tox is loaded under some other path: nothing inside may point outside it."""
    leaks = []
    for o in _all(comp):
        # A file path, a clone master or a global shortcut on any COMP follows it into
        # every user's project (two instances sharing a shortcut is an error).
        for name in ('externaltox', 'clone', 'opshortcut'):
            par = getattr(o.par, name, None)
            value = par.eval() if par is not None else None
            if value not in ('', None) and not str(getattr(value, 'path', value)).startswith(SYSTEM):
                leaks.append('{}.{} = {}'.format(o.path, name, value))
        for p in o.pars():
            if p.mode == ParMode.EXPRESSION and _ABSOLUTE_OP_CALL.search(p.expr):
                leaks.append('{}.{} expression {}'.format(o.path, p.name, p.expr))
            if p.mode == ParMode.CONSTANT and p.style in ('File', 'FileSave', 'Folder'):
                if isinstance(p.val, str) and _ABSOLUTE.match(p.val):
                    leaks.append('{}.{} = {} (bundled media comes from app.samplesFolder)'.format(
                        o.path, p.name, p.val))
            if not p.isOP:
                continue
            if p.mode == ParMode.CONSTANT and isinstance(p.val, str) and p.val.startswith('/') \
                    and not p.val.startswith(SYSTEM):
                leaks.append('{}.{} = {}'.format(o.path, p.name, p.val))
            target = p.eval()
            if (hasattr(target, 'path') and not (target.path + '/').startswith(comp.path + '/')
                    and not target.path.startswith(SYSTEM)):
                leaks.append('{}.{} -> {}'.format(o.path, p.name, target.path))
        if o.isDAT and o.name != 'README' and _ABSOLUTE_OP_CALL.search(o.text):
            leaks.append('{} text names an absolute path: {}'.format(
                o.path, _ABSOLUTE_OP_CALL.search(o.text).group(0)))
    if leaks:
        raise RuntimeError('{} points outside itself:\n  {}'.format(comp.path, '\n  '.join(leaks)))


def _op_refs(o):
    """Paths of every operator o's parameters point at."""
    refs = set()
    for p in o.pars():
        if p.isOP:
            target = p.eval()
            if hasattr(target, 'path'):
                refs.add(target.path)
    return refs


def assert_no_unused_docked(comp):
    """TouchDesigner docks DATs to some operators when it creates them: callbacks for a Script
    CHOP or OSC In DAT, shaders and an Info DAT for a GLSL TOP, keys for a Ramp TOP. A docked
    DAT is in use when its host points at it (callbacks, pixeldat, dat, ...) or it points at
    its host (an Info DAT). A builder that wires its own DAT instead of filling the docked one
    leaves the docked one behind as dead weight."""
    unused = []
    for o in _all(comp):
        docked = [d for d in o.docked if d.isDAT]
        if not docked:
            continue
        used = _op_refs(o)
        for d in docked:
            if d.path not in used and o.path not in _op_refs(d):
                unused.append('{} (docked to {}, which does not use it)'.format(d.path, o.name))
    if unused:
        raise RuntimeError('{} carries unused docked DATs:\n  {}'.format(comp.path, '\n  '.join(unused)))


def assert_readable(comp):
    """Opening the .tox shows how it works: a README with its CREDITS (the papers, techniques, code
    and projects it uses or follows, docs/BUILDING.md), one line per paragraph, a comment on every operator, help on every
    parameter, the About page, tags, the library color and a node big enough to read."""
    problems = []
    readme = comp.op('README')
    if readme is None or not readme.text.strip():
        problems.append('no README DAT, or an empty one')
    elif not re.search(r'^CREDITS\n+\S', readme.text, re.M):
        problems.append('the README has no CREDITS section: what the effect uses or follows (docs/BUILDING.md, '
                        'Credits)')
    elif hard_wrapped(readme.text):
        problems.append('the README is wrapped by hand (line {}): write one line per paragraph and per list item, '
                        'so the viewer wraps it to its width (docs/BUILDING.md)'.format(hard_wrapped(readme.text)[0] + 1))
    for o in _all(comp):
        if not o.comment.strip():
            problems.append('{} has no comment'.format(o.path))
    for p in comp.customPars:
        if not (getattr(p, 'help', '') or '').strip():
            problems.append('parameter {} has no help text'.format(p.name))
    names = {p.name for p in comp.customPars}
    for name in ('Version', 'Builtwith', 'Help'):
        if name not in names:
            problems.append('About page lacks {}'.format(name))
    if not comp.tags:
        problems.append('no tags')
    if tuple(round(c, 3) for c in comp.color) != tuple(round(c, 3) for c in NODE_COLOR):
        problems.append('node color {} is not the library color {}'.format(tuple(comp.color), NODE_COLOR))
    if comp.nodeWidth < NODE_W or comp.nodeHeight < NODE_H:
        problems.append('node is {} x {}, smaller than {} x {}'.format(comp.nodeWidth, comp.nodeHeight, NODE_W, NODE_H))
    if problems:
        raise RuntimeError('{} is not readable inside:\n  {}'.format(comp.path, '\n  '.join(problems)))


def assert_standard_io(comp):
    """Input 1 a TOP, optional input 2 a CHOP and after it an optional input 3 TOP (depth or a mask),
    output 1 a TOP, and nothing else: in particular no sound. TouchDesigner saves an Audio
    Device Out's state with the project, so one that was playing starts again the moment the
    project opens, and nobody dragging in an effect expects music."""
    ins = [c.inOP.OPType for c in comp.inputConnectors]
    outs = [c.outOP.OPType for c in comp.outputConnectors]
    problems = []
    if ins not in (['inTOP'], ['inTOP', 'inCHOP'], ['inTOP', 'inCHOP', 'inTOP']):
        problems.append('inputs are {}, expected a TOP, then optionally a CHOP and a second TOP'.format(ins))
    if outs != ['outTOP']:
        problems.append('outputs are {}, expected one TOP'.format(outs))
    for o in comp.findChildren(type=audiodeviceoutCHOP):
        problems.append('{} makes sound; a component outputs only its picture'.format(o.path))
    if problems:
        raise RuntimeError('{} does not have the standard inputs and outputs:\n  {}'.format(
            comp.path, '\n  '.join(problems)))


def assert_nc_resolution(comp):
    """Nothing renders larger than the Non-Commercial license allows."""
    big = []
    for o in _all(comp):
        if not o.isTOP or getattr(o.par, 'outputresolution', None) is None:
            continue
        if o.par.outputresolution.eval() == 'custom':
            w, h = o.par.resolutionw.eval(), o.par.resolutionh.eval()
            if w > MAX_RES or h > MAX_RES:
                big.append('{} renders {} x {}'.format(o.path, w, h))
    if big:
        raise RuntimeError('{} exceeds the Non-Commercial {} x {} cap:\n  {}'.format(
            comp.path, MAX_RES, MAX_RES, '\n  '.join(big)))


def assert_idiomatic(comp):
    """The idioms in docs/TD_IDIOMS.md a script can judge (each line names its item there);
    the rest are reviewed by hand in effects/<name>/review.md."""
    problems = []
    pages = [p.name for p in comp.customPages]
    if not pages or pages[0] == 'About' or pages[-1] != 'About':
        problems.append("P1: pages are {}; the effect's page comes first, About last".format(pages))
    for name in ('Version', 'Builtwith'):
        p = getattr(comp.par, name, None)
        if p is not None and not p.readOnly:
            problems.append('P1: {} is editable; it should be read-only'.format(name))
    for p in comp.customPars:
        if len(p.tupletName) > 10:
            problems.append('P4: the parameter name {} is {} characters; keep names to 10 or fewer'.format(
                p.tupletName, len(p.tupletName)))
        if p.readOnly or p.mode != ParMode.CONSTANT or p.style in ('Pulse', 'Momentary', 'Header'):
            continue
        # An operator parameter (Words' Text, a DAT) evaluates to the operator; its default is the path.
        value, default = (p.val if p.style in OP_STYLES else p.eval()), p.default
        same = abs(value - default) < 1e-6 if isinstance(value, float) else value == default
        if not same:
            problems.append('P3: {} is {!r}, not its default {!r}; save at the defaults so Reset returns '
                            'here'.format(p.name, value, default))
    viewer = comp.par.opviewer.eval()
    if not comp.viewer or getattr(viewer, 'name', None) != 'out_top':
        problems.append('I2: the node does not show out_top (viewer {}, Node View {})'.format(comp.viewer, viewer))
    extensions = [p for p in comp.pars() if _EXTENSION_PAR.match(p.name) and (p.eval() or p.expr)]
    if extensions and not comp.par.initextonstart.eval():
        problems.append('E1: it has extensions but Init Extensions on Start is off')
    for o in _all(comp)[1:]:
        if o.OPType == 'scriptCHOP':
            dat = o.par.callbacks.eval()
            if dat is None or 'CookLevel.WHEN_USED' not in dat.text:
                problems.append('C1: {} does not return CookLevel.WHEN_USED from onGetCookLevel'.format(o.path))
        if o.OPType == 'executeDAT' and o.par.active.eval() and (o.par.framestart.eval() or o.par.frameend.eval()):
            problems.append('C2: {} runs Python every frame (Frame Start/End on)'.format(o.path))
        if o.isDAT and o.name != 'README' and 'cook(force=True)' in o.text.replace(' ', ''):
            problems.append('C2: {} forces a cook'.format(o.path))
        # A uniform whose value grows with absTime.seconds (not wrapped with %, not turned into an angle's
        # sine or cosine in Python, which works in double precision) coarsens as TouchDesigner runs.
        for p in o.pars('vec*value*'):
            if (p.mode == ParMode.EXPRESSION and 'absTime.seconds' in p.expr and '%' not in p.expr
                    and not _PERIODIC.search(p.expr)):
                problems.append('C4: {} hands its shader absTime.seconds ({}), a 32-bit float that coarsens as '
                                'TouchDesigner runs; use clock_seconds(), or count in Python'.format(p.owner.path, p.name))
    if 'flashing' in comp.tags:
        flash = getattr(comp.par, 'Flashing', None)
        if flash is None:
            problems.append('A1: tagged flashing but has no Flashing parameter (new_effect(flashing=True))')
        elif list(flash.menuNames) != [n for n, _ in FLASHING] or flash.default != 'calm':
            problems.append('A1: Flashing is {} defaulting to {!r}; it must be the standard menu, default '
                            'calm'.format(list(flash.menuNames), flash.default))
    if problems:
        raise RuntimeError('{} is not idiomatic (docs/TD_IDIOMS.md):\n  {}'.format(comp.path, '\n  '.join(problems)))


def assert_loads_clean(comp):
    """It works with nothing wired, as a drag-in leaves it, and a second copy beside the first
    works too; every parameter expression evaluates (docs/TD_IDIOMS.md I3)."""
    twin = comp.parent().copy(comp, name=comp.name + '_twin')
    problems = []
    # An expression on an operator nothing cooks (a Switch TOP's unselected input) fails
    # silently until it is selected: evaluate every one.
    for o in _all(comp):
        for p in o.pars():
            if p.mode == ParMode.EXPRESSION:
                try:
                    p.eval()
                except Exception as e:
                    problems.append('{}.{} expression {!r} fails: {}'.format(o.path, p.name, p.expr, e))
    try:
        for c in (comp, twin):
            c.op('out_top').cook(force=True)
            for kind, text in (('errors', c.errors(recurse=True)), ('warnings', c.warnings(recurse=True))):
                if text:
                    problems.append('{} {}: {}'.format(c.path, kind, text))
    finally:
        twin.destroy()
    if problems:
        raise RuntimeError('{} does not load clean:\n  {}'.format(comp.path, '\n  '.join(problems)))


def assert_laid_out(comp):
    """The network reads left to right in titled Network Boxes (docs/TD_IDIOMS.md D7, lay_out()): every operator
    in exactly one box, boxes and operators clear of each other, each docked DAT under its operator, every wire
    running from left to right, and nothing an operator reads from its own box right of it (a Feedback TOP's
    Target TOP is the loop it closes, and exempt)."""
    problems = []
    boxes = [b for b in comp.children if b.OPType == 'annotateCOMP']
    items = [o for o in comp.children if o.OPType != 'annotateCOMP']
    names = {o.name for o in items}

    def rect(o):
        return o.nodeX, o.nodeY, o.nodeX + o.nodeWidth, o.nodeY + o.nodeHeight

    def overlap(a, b):
        a, b = rect(a), rect(b)
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    for b in boxes:
        if b.par.Mode.eval() != 'networkbox' or not b.par.Titletext.eval().strip():
            problems.append('{} is not a titled Network Box'.format(b.name))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if overlap(a, b):
                problems.append('boxes {} and {} overlap'.format(a.name, b.name))
    box_of = {}
    for o in items:
        x0, y0, x1, y1 = rect(o)
        inside = [b.name for b in boxes if rect(b)[0] <= x0 and x1 <= rect(b)[2] and rect(b)[1] <= y0
                  and y1 <= rect(b)[3] - b.par.Titleheight.eval()]
        box_of[o.name] = inside[0] if inside else None
        if len(inside) != 1:
            problems.append('{} is in {} boxes{}'.format(o.name, len(inside), ': ' + ', '.join(inside) if inside else ''))
        if o.dock is not None and not (o.nodeX == o.dock.nodeX and o.nodeY < o.dock.nodeY):
            problems.append('{} is not under {}, which it is docked to'.format(o.name, o.dock.name))
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if overlap(a, b):
                problems.append('{} and {} overlap'.format(a.name, b.name))
    for o in items:
        if o.dock is not None:
            continue
        for ic in o.inputConnectors:
            for c in ic.connections:
                if c.owner.nodeX + c.owner.nodeWidth >= o.nodeX:
                    problems.append('the wire from {} to {} runs backward'.format(c.owner.name, o.name))
        for name in _reads(o, names)[1]:
            r = comp.op(name)
            if r.dock is None and box_of[name] == box_of[o.name] and r.nodeX > o.nodeX:
                problems.append('{} reads {}, which sits right of it in its box'.format(o.name, name))
    if problems:
        raise RuntimeError('{} is not laid out (docs/TD_IDIOMS.md D7):\n  {}'.format(comp.path, '\n  '.join(problems)))


EFFECT_CHECKS = (assert_self_contained, assert_no_unused_docked, assert_readable, assert_standard_io,
                 assert_nc_resolution, assert_idiomatic, assert_loads_clean, assert_laid_out)


def save_tox(comp, out_dir, stem, manifest, checks=EFFECT_CHECKS):
    """Check comp, save <stem>.tox and write <stem>.json: manifest plus the build and the file's hash."""
    for check in checks:
        check(comp)
    path = comp.save(os.path.join(out_dir, stem + '.tox'))
    with open(path, 'rb') as f:
        tox = f.read()
    manifest = dict(manifest, touchdesigner_build=app.build,
                    tox_sha256=hashlib.sha256(tox).hexdigest(), tox_bytes=len(tox))
    with open(os.path.join(out_dir, stem + '.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')
    return path, manifest
