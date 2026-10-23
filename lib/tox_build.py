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

REPO = 'kevinraymond/tdlib'
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
# Shown while nothing is wired into the effect's TOP input.
SAMPLE_MEDIA = "app.samplesFolder + '/Map/Banana.tif'"
WINDOW_W, WINDOW_H = 1280, 720

_ABSOLUTE = re.compile(r'^(/|[A-Za-z]:[/\\]|\\\\)')
_ABSOLUTE_OP_CALL = re.compile(r"""op\(\s*['"]/(?!sys/|ui/)""")


# ---- Sources and hashes (also used outside TouchDesigner) -----------------------------------
def component_sources(root, comp_dir):
    """What a component's .tox is built from, as patterns relative to root: this file, the
    component's builder (build_<name>.py) and everything in its src/. A change to any of them
    needs a rebuild, and tests/check_tox.py fails until it happens."""
    rel = os.path.relpath(comp_dir, root).replace(os.sep, '/')
    name = os.path.basename(comp_dir)
    patterns = ['lib/tox_build.py', '{}/build_{}.py'.format(rel, name)]
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


def new_effect(name, title, summary, readme, tags=(), audio=False, parent_path=None):
    """The standard shell every effect starts from: a COMP with the library's color, tags and
    node size, a README DAT, input 1 a TOP (sample media until something is wired) and, with
    audio=True, input 2 an optional CHOP. Returns (comp, page, source): the effect's custom
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
    for tag in ('tdlib',) + tuple(tags):
        comp.tags.add(tag)
    page = comp.appendCustomPage(title)
    mk(comp, textDAT, 'README', -800, 400, comment='What this effect does and how to use it.').text = readme

    # A COMP orders its inputs by the In operators' names, not their positions (TouchDesigner
    # 2025.33230, dev/probes/input_order.py): the digit keeps the TOP first.
    mk(comp, inTOP, 'in1_top', -800, 0, comment='Input 1: the picture to process.')
    mk(comp, moviefileinTOP, 'sample', -800, -150, comment='Shown until a TOP is wired into input 1.',
       file=Expr(SAMPLE_MEDIA))
    source = mk(comp, switchTOP, 'source', -600, -50, [comp.op('in1_top'), comp.op('sample')],
                comment='Input 1 when it is wired, the sample picture when it is not.',
                index=Expr('0 if parent().inputConnectors[0].connections else 1'))
    if audio:
        mk(comp, inCHOP, 'in2_audio', -800, -350,
           comment='Input 2 (optional): audio or beat channels, e.g. Fosfora or audio analysis.')
    return comp, page, source


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

    opener = custom(page, 'Pulse', 'Openwindow', 'Open Window', None,
                    'Show the picture in its own window, 1280 x 720 or filling a display. Esc closes it.')
    opener.startSection = True
    custom(page, 'Toggle', 'Filldisplay', 'Fill Display', False,
           'Open the window filling the whole display, for a projector or a second screen.')
    custom(page, 'Int', 'Display', 'Display', 0, 'Which display the window opens on; 0 is the primary display.',
           0, 3).clampMin = True
    mk(comp, windowCOMP, 'window', 800, -300, comment='Open Window shows out_top here; Esc closes it.',
       winop='out_top', title=comp.name, justifyoffsetto='specifydisplay', display=Expr('parent().par.Display'),
       justifyh='center', justifyv='center', size=Expr("'fill' if parent().par.Filldisplay else 'custom'"),
       winw=WINDOW_W, winh=WINDOW_H, borders=Expr('not parent().par.Filldisplay'), blocksleep=True,
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
    """Save comp as comp_dir/<name>.tox, with the manifest tests/check_tox.py checks."""
    path, manifest = save_tox(comp, comp_dir, comp.name, {
        'version': comp.par.Version.eval(),
        'sources_sha256': digest(root, component_sources(root, comp_dir)),
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
    """Input 1 a TOP, optional input 2 a CHOP, output 1 a TOP, and nothing else."""
    ins = [c.inOP.OPType for c in comp.inputConnectors]
    outs = [c.outOP.OPType for c in comp.outputConnectors]
    problems = []
    if ins not in (['inTOP'], ['inTOP', 'inCHOP']):
        problems.append('inputs are {}, expected a TOP, then optionally a CHOP'.format(ins))
    if outs != ['outTOP']:
        problems.append('outputs are {}, expected one TOP'.format(outs))
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


EFFECT_CHECKS = (assert_self_contained, assert_no_unused_docked, assert_readable, assert_standard_io,
                 assert_nc_resolution)


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
