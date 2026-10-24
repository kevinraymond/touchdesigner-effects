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
FLASHING = (('off', 'Off'), ('calm', 'Calm'), ('wcag', 'Up to 3 per second'))
FLASH_INTERVAL = {'off': None, 'calm': 1.0, 'wcag': 1 / 3}

_ABSOLUTE = re.compile(r'^(/|[A-Za-z]:[/\\]|\\\\)')
_ABSOLUTE_OP_CALL = re.compile(r"""op\(\s*['"]/(?!sys/|ui/)""")
_EXTENSION_PAR = re.compile(r'ext\d+object$')


# ---- Sources and hashes (also used outside TouchDesigner) -----------------------------------
def component_sources(root, comp_dir):
    """What a component's .tox is built from, as patterns relative to root: the shared library
    (every lib/*.py), the component's builder (build_<name>.py) and everything in its src/. A
    change to any of them needs a rebuild, and tests/check_tox.py fails until it happens."""
    rel = os.path.relpath(comp_dir, root).replace(os.sep, '/')
    name = os.path.basename(comp_dir)
    patterns = ['lib/*.py', '{}/build_{}.py'.format(rel, name)]
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


def mk(host, kind, name, x, y, inputs=(), comment='', **pars):
    """Create, place, comment, set parameters and wire the inputs in one call."""
    o = host.create(kind, name)
    o.nodeX, o.nodeY = x, y
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
    """Set a GLSL TOP's vector uniforms: uniforms(g, uAmount=0.5, uTint=(1, 0.5, 0), uTime=Expr('absTime.seconds')).
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


def glsl(host, name, x, y, inputs, pixel, comment, res=None, fmt=None, **values):
    """A GLSL TOP with its docked pixel shader filled (never a second DAT beside it), any number
    of inputs, an optional custom resolution and pixel format, and uniforms (see uniforms())."""
    # A new GLSL TOP has 3 input connectors that don't grow within one Python call, and
    # setInputs() doesn't add more either; its TOPs parameter appends further inputs as
    # sTD2DInputs[3], [4]... (2025.33230, dev/selftest.py checks a 5-input GLSL TOP).
    g = mk(host, glslTOP, name, x, y, inputs[:3], comment)
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


def audio_in(comp, root, x=-600, y=-350):
    """The effect's audio front end. Whatever is wired into input 2 (Fosfora's signal, raw audio,
    TouchDesigner's audioAnalysis or Essentia rhythm CHOP, or nothing) becomes the channels beat,
    beat_count, bar_count, beat_phase, level, build, drop_count, section_count and source;
    lib/audio_callbacks.py says how (build and the drop and section counts need Fosfora). One
    Script CHOP does it and cooks only when something uses it, so nothing in the audio front end
    runs while the effect's output is unused (TD_IDIOMS C5, dev/idle.py checks it); for raw audio
    it measures the low band itself (numpy), since a time-sliced Audio Filter CHOP there cooked
    every frame, used or not (2025.33230). Needs new_effect(..., audio=True); returns the Script
    CHOP."""
    script = mk(comp, scriptCHOP, 'audio', x, y, [comp.op('in2_audio')],
                'Input 2 as beat, beat_count, level and the rest (lib/audio_callbacks.py).')
    docked(script, '_callbacks', open(os.path.join(root, 'lib', 'audio_callbacks.py')).read(),
           'Turns whatever is on input 2 into beat, beat_count, level and the rest.')
    return script


def flash_gate(comp, trigger, x, y, name='flash'):
    """Every flash an effect makes goes through here (docs/TD_IDIOMS.md A1). A Trigger CHOP turns
    trigger's channels into one-frame-wide pulses no closer together than the Flashing parameter
    allows (Re-Trigger Delay = FLASH_INTERVAL), and a Math CHOP passes nothing when Flashing is
    Off. Shape the flash itself (its envelope) downstream; never bypass the gate."""
    calm, wcag = FLASH_INTERVAL['calm'], FLASH_INTERVAL['wcag']
    limit = mk(comp, triggerCHOP, name + '_limit', x, y, [trigger],
               'Flashes no closer together than the Flashing parameter allows.',
               retrigger=Expr("{} if parent().par.Flashing == 'wcag' else {}".format(wcag, calm)),
               retriggerunit='seconds', attack=0, peak=1, decay=0, sustain=0)
    return mk(comp, mathCHOP, name, x + 200, y, [limit], 'Nothing passes when Flashing is Off.',
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
    mk(comp, textDAT, 'README', -800, 400, comment='What this effect does and how to use it.').text = readme

    # A COMP orders its inputs by the In operators' names, not their positions (TouchDesigner
    # 2025.33230, dev/probes/input_order.py): the digit keeps the TOP first.
    mk(comp, inTOP, 'in1_top', -800, 0, comment='Input 1: the picture to process.')
    mk(comp, moviefileinTOP, 'sample', -800, -150, comment='Shown until a TOP is wired into input 1.',
       file=Expr(sample))
    source = mk(comp, switchTOP, 'source', -600, -50, [comp.op('in1_top'), comp.op('sample')],
                comment='Input 1 when it is wired, the sample picture when it is not.',
                index=Expr('0 if parent().inputConnectors[0].connections else 1'))
    if audio:
        mk(comp, inCHOP, 'in2_audio', -800, -350,
           comment='Input 2 (optional): audio or beat channels, e.g. Fosfora or audio analysis.')
    if depth:
        if not audio:
            raise ValueError('depth=True needs audio=True: input 2 is always the audio, input 3 the depth')
        mk(comp, inTOP, 'in3_top', -800, -650,
           comment='Input 3 (optional): a depth map or mask, grayscale: brighter is nearer, or inside.')
    return comp, page, source


def depth_in(comp, fallback=None, x=-600, y=-650):
    """Input 3 (new_effect(..., depth=True)) when a TOP is wired into it, else fallback: a TOP the
    effect makes from input 1, or by default input 1's brightness (brighter is nearer), so the
    effect works with nothing on input 3. Returns the Switch TOP to read the depth from."""
    if fallback is None:
        fallback = mk(comp, monochromeTOP, 'depth_guess', x - 200, y - 150, [comp.op('source')],
                      "Input 1's brightness, standing in for depth while nothing is wired into input 3.")
    return mk(comp, switchTOP, 'depth', x, y, [comp.op('in3_top'), fallback],
              'Input 3 (depth or mask) when it is wired, else the stand-in.',
              index=Expr('0 if parent().inputConnectors[2].connections else 1'))


def finish_effect(comp, last, version, page=None):
    """Add the output, Open Window, the About page and the node's picture. save_effect() next."""
    if page is None:
        page = comp.customPages[0]
    # DATs TouchDesigner docked to an operator and the builder left as they were (a GLSL
    # TOP's info DAT, say) belong to their host; say so rather than leave them blank.
    for o in comp.findChildren():
        for d in o.docked:
            if not d.comment.strip():
                d.comment = 'Docked to {}; TouchDesigner made it with it.'.format(o.name)
    out = mk(comp, outTOP, 'out_top', 800, 0, [last], "Output 1: the effect's picture.")

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
    mk(comp, windowCOMP, 'window', 800, -300, comment='Open Window shows out_top here; Esc closes it.',
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
    parexec = mk(comp, parameterexecuteDAT, 'parexec', -800, 250, comment='Open Window and Open Docs.')
    parexec.text = ('def onPulse(par):\n'
                    "    if par.name == 'Openwindow':\n"
                    "        op('window').par.winopen.pulse()\n"
                    "    elif par.name == 'Help':\n"
                    '        ui.viewFile({!r})\n').format(DOCS_URL.format(comp.name))
    setpars(parexec, op='..', pars='Openwindow Help', onpulse=True, valuechange=False)

    comp.par.opviewer = './out_top'
    comp.viewer = True
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
def _all(comp):
    return [comp] + list(comp.findChildren())


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
    """Opening the .tox shows how it works: a README, a comment on every operator, help on
    every parameter, the About page, tags, the library color and a node big enough to read."""
    problems = []
    readme = comp.op('README')
    if readme is None or not readme.text.strip():
        problems.append('no README DAT, or an empty one')
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
        value, default = p.eval(), p.default
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
    for o in comp.findChildren():
        if o.OPType == 'scriptCHOP':
            dat = o.par.callbacks.eval()
            if dat is None or 'CookLevel.WHEN_USED' not in dat.text:
                problems.append('C1: {} does not return CookLevel.WHEN_USED from onGetCookLevel'.format(o.path))
        if o.OPType == 'executeDAT' and o.par.active.eval() and (o.par.framestart.eval() or o.par.frameend.eval()):
            problems.append('C2: {} runs Python every frame (Frame Start/End on)'.format(o.path))
        if o.isDAT and o.name != 'README' and 'cook(force=True)' in o.text.replace(' ', ''):
            problems.append('C2: {} forces a cook'.format(o.path))
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


EFFECT_CHECKS = (assert_self_contained, assert_no_unused_docked, assert_readable, assert_standard_io,
                 assert_nc_resolution, assert_idiomatic, assert_loads_clean)


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
