"""DEV ONLY. Inside TouchDesigner: build a small effect through lib/tox_build.py's standard
shell and check that it saves, then break each save-time check once on purpose and check that
it refuses. A check that has never refused anything guards nothing.

    dev/td.sh dev/selftest.py
    (or in a textport: __file__ = '/path/to/dev/selftest.py'; exec(open(__file__).read()))

Saves only under dev/out/ (gitignored). Builds land in TDLIB_PARENT (dev/td.sh sets it).
"""

import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUT = os.path.join(_HERE, 'out', 'selftest')

SHADER = """out vec4 fragColor;
void main()
{
    vec4 c = texture(sTD2DInputs[0], vUV.st);
    fragColor = TDOutputSwizzle(vec4(1.0 - c.rgb, c.a));
}
"""


def good(name='selftest_ok'):
    comp, page, source = new_effect(name, 'Selftest', 'Selftest: inverts its input.', 'Selftest README.\n',
                                    tags=('selftest',), audio=True)
    custom(page, 'Float', 'Amount', 'Amount', 1.0, 'How much to invert.', 0, 1, True)
    glsl = mk(comp, glslTOP, 'glsl', 0, 0, [source], comment='Inverts the picture.')
    docked(glsl, '_pixel', SHADER, 'The pixel shader: one minus the color.')
    finish_effect(comp, glsl, '0.0.1', page)
    return comp


def all_checks(comp):
    for check in EFFECT_CHECKS:
        check(comp)


def _set(path, **pars):
    return lambda comp: setpars(comp.op(path) if path else comp, **pars)


def _extra(kind, name, comment='', **pars):
    return lambda comp: mk(comp, kind, name, 400, -600, comment=comment, **pars)


def _own_shader(comp):
    """The mistake the docked check exists for: a new DAT wired in, the docked one left behind."""
    mine = mk(comp, textDAT, 'my_shader', 0, -600, comment='a second shader')
    mine.text = SHADER
    comp.op('glsl').par.pixeldat = 'my_shader'


def _attr(path, **values):
    def apply(comp):
        o = comp.op(path) if path else comp
        for k, v in values.items():
            setattr(o, k, v)
    return apply


def _clone_outside(comp):
    master = comp.parent().op('selftest_master') or comp.parent().create(baseCOMP, 'selftest_master')
    setpars(comp, enablecloning=False, clone=master.path)


def _constant(path, name, value):
    def apply(comp):
        p = getattr(comp.op(path).par, name)
        p.mode = ParMode.CONSTANT
        p.val = value
    return apply


def _no_help(comp):
    custom(comp.customPages[0], 'Float', 'Bare', 'Bare', 0.5, '')


BREAKS = [
    ('external .tox', _set('', externaltox='/Users/someone/effect.tox'), 'points outside'),
    ('clone outside', _clone_outside, 'points outside'),
    ('global shortcut', _set('', opshortcut='myeffect'), 'points outside'),
    ('absolute OP path', _extra(selectTOP, 'sel', 'x', top='/project1'), 'points outside'),
    ('expression naming an absolute path', _extra(constantTOP, 'k', 'x', colorr=Expr("op('/project1').nodeX")),
     'expression'),
    ('absolute media path', _constant('sample', 'file', '/Users/someone/picture.png'), 'app.samplesFolder'),
    ('script naming an absolute path', lambda c: setattr(_extra(textDAT, 't', 'x')(c), 'text',
                                                         "op('/project1/thing').cook()"), 'text names'),
    ('own DAT beside the docked one', _own_shader, 'unused docked'),
    ('operator without a comment', _extra(nullTOP, 'quiet'), 'has no comment'),
    ('parameter without help', _no_help, 'no help text'),
    ('another node color', _attr('', color=(0.5, 0.5, 0.5)), 'node color'),
    ('node too small', _attr('', nodeWidth=100), 'node is'),
    ('no README', lambda c: c.op('README').destroy(), 'README'),
    ('two TOP outputs', _extra(outTOP, 'out_two', 'x'), 'outputs are'),
    ('a second TOP input', _extra(inTOP, 'in_two', 'x'), 'inputs are'),
    ('over the Non-Commercial cap', _extra(constantTOP, 'big', 'x', outputresolution='custom', resolutionw=1920,
                                            resolutionh=1080), 'exceeds'),
]


def _check_source_follows_wiring(host, comp):
    """Input 1 replaces the sample picture when a TOP is wired in, and the sample comes back
    when it is unwired, without anything forcing a cook: checked over later frames (run()
    with delayFrames), written to dev/out/selftest/wiring.txt."""
    source, log = comp.op('source'), []
    feed = host.op('selftest_feed') or mk(host, noiseTOP, 'selftest_feed', -700, 0, comment='selftest input',
                                          outputresolution='custom', resolutionw=320, resolutionh=200)

    def note(stage):
        log.append('{}: index {} source {} x {}'.format(stage, source.par.index.eval(), source.width, source.height))

    def unwired_again():
        note('unwired again (want index 1, the sample size)')
        with open(os.path.join(OUT, 'wiring.txt'), 'w') as f:
            f.write('\n'.join(log) + '\n')

    def wired():
        note('wired (want index 0, 320 x 200)')
        comp.inputConnectors[0].disconnect()
        run('args[0]()', unwired_again, delayFrames=15)

    note('unwired (want index 1, the sample size)')
    comp.inputConnectors[0].connect(feed)
    run('args[0]()', wired, delayFrames=15)


def main():
    host = op(globals().get('TDLIB_PARENT', '/project1'))
    os.makedirs(OUT, exist_ok=True)
    report = []

    # The intact effect passes every check, saves, and its shell is wired as promised.
    comp = good()
    path, manifest = save_tox(comp, OUT, comp.name, {'version': '0.0.1', 'sources_sha256': 'selftest'})
    report.append('ok    intact effect saves: {} ({} bytes, build {})'.format(
        os.path.basename(path), manifest['tox_bytes'], manifest['touchdesigner_build']))
    w = comp.op('window').par.winop.eval()
    report.append('{} window shows {}'.format('ok   ' if w is not None and w.name == 'out_top' else 'MISS ', w))
    report.append('info  docked to glsl: {}'.format([(d.name, d.OPType) for d in comp.op('glsl').docked]))
    report.append('info  inputs {}, outputs {}'.format([c.inOP.name for c in comp.inputConnectors],
                                                       [c.outOP.name for c in comp.outputConnectors]))
    # Loaded somewhere else, as a user's drag-in does: no errors, the sample on its output.
    elsewhere = host.op('selftest_elsewhere') or mk(host, baseCOMP, 'selftest_elsewhere', 0, -600, comment='x')
    loaded = elsewhere.loadTox(path)
    loaded.op('out_top').cook(force=True)
    errors = loaded.errors(recurse=True)
    report.append('{} loaded elsewhere: {}, out {} x {}, errors {!r}'.format(
        'ok   ' if not errors and loaded.op('out_top').width == 1280 else 'MISS ', loaded.path,
        loaded.op('out_top').width, loaded.op('out_top').height, errors))
    elsewhere.destroy()
    _check_source_follows_wiring(host, comp)
    sample = comp.op('sample')
    sample.cook(force=True)
    report.append('info  sample media {} x {} from {}'.format(sample.width, sample.height, sample.par.file.eval()))

    failed = 0
    for what, breaker, expect in BREAKS:
        comp = good('selftest_break')
        breaker(comp)
        try:
            all_checks(comp)
            failed += 1
            report.append('MISS  {}: saved without complaint'.format(what))
        except RuntimeError as e:
            msg = str(e)
            if expect in msg:
                report.append('ok    {}: {}'.format(what, msg.splitlines()[-1].strip()))
            else:
                failed += 1
                report.append('MISS  {}: refused, but for something else: {}'.format(what, msg))
        comp.destroy()
    report.append('ALL OK' if not failed and not any(r.startswith('MISS') for r in report)
                  else '{} problem(s)'.format(sum(r.startswith('MISS') for r in report)))
    print('\n'.join(report))


main()
