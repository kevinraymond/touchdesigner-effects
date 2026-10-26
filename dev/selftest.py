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


def good(name='selftest_ok', flashing=False, depth=False, more=None):
    """An effect that passes every check; more(comp) adds to it before finish_effect() lays it out."""
    comp, page, source = new_effect(name, 'Selftest', 'Selftest: inverts its input.',
                                    'Selftest README.\n\nCREDITS\nOriginal: a test of the save-time checks.\n',
                                    tags=('selftest',), audio=True, flashing=flashing, depth=depth)
    custom(page, 'Float', 'Amount', 'Amount', 1.0, 'How much to invert.', 0, 1, True)
    section('invert', 'Inverts the picture')
    glsl = mk(comp, glslTOP, 'glsl', [source], comment='Inverts the picture.')
    docked(glsl, '_pixel', SHADER, 'The pixel shader: one minus the color.')
    if more:
        more(comp)
    finish_effect(comp, glsl, '0.0.1', page)
    return comp


def all_checks(comp):
    for check in EFFECT_CHECKS:
        check(comp)


def _set(path, **pars):
    return lambda comp: setpars(comp.op(path) if path else comp, **pars)


def _extra(kind, name, comment='', **pars):
    return lambda comp: mk(comp, kind, name, comment=comment, at=(400, -600), **pars)


def _own_shader(comp):
    """The mistake the docked check exists for: a new DAT wired in, the docked one left behind."""
    mine = mk(comp, textDAT, 'my_shader', comment='a second shader')
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


def _about_not_last(comp):
    custom(comp.appendCustomPage('Extra'), 'Float', 'Late', 'Late', 0.0, 'A page after About.')


def _editable_version(comp):
    comp.par.Version.readOnly = False


def _extension_lazy(comp):
    ext = mk(comp, textDAT, 'SelftestExt', comment='an extension')
    ext.text = 'class SelftestExt:\n    def __init__(self, ownerComp):\n        self.ownerComp = ownerComp\n'
    setpars(comp, ext0object="op('./SelftestExt').module.SelftestExt(me)", initextonstart=False)


def _script_chop_always(comp):
    chop = mk(comp, scriptCHOP, 'script', comment='a Script CHOP')
    docked(chop, '_callbacks', 'def onCook(scriptOp):\n    scriptOp.clear()\n    return\n', 'its callbacks')


def _flashing_without_par(comp):
    comp.tags.add('flashing')


def _shader_error(comp):
    comp.op('glsl_pixel').text = 'this is not GLSL'


def _hidden_expression_error(comp):
    """An expression error on an operator nothing cooks: a Switch TOP's unselected input."""
    sw = mk(comp, switchTOP, 'sw', [comp.op('glsl')], comment='x', index=0)
    bad = mk(comp, constantTOP, 'bad', comment='x', colorr=Expr('sin(1)'))
    sw.inputConnectors[1].connect(bad)


def _move(name, dx=0, dy=0, onto=None):
    def apply(comp):
        o = comp.op(name)
        if onto:
            o.nodeX, o.nodeY = comp.op(onto).nodeX, comp.op(onto).nodeY
        o.nodeX, o.nodeY = o.nodeX + dx, o.nodeY + dy
    return apply


def _no_help(comp):
    custom(comp.customPages[0], 'Float', 'Bare', 'Bare', 0.5, '')


def _long_name(comp):
    custom(comp.customPages[0], 'Float', 'Toolongname', 'Too Long Name', 0.5, 'A name of 11 characters.')


BREAKS = [
    ('About not the last page', _about_not_last, 'About last'),
    ('Version editable', _editable_version, 'read-only'),
    ('a parameter off its default', _set('', Amount=0.25), 'not its default'),
    ('a parameter name over 10 characters', _long_name, 'keep names to 10 or fewer'),
    ('node shows nothing', _attr('', viewer=False), 'does not show out_top'),
    ('extension without Init on Start', _extension_lazy, 'Init Extensions on Start'),
    ('Script CHOP cooking always', _script_chop_always, 'WHEN_USED'),
    ('Python every frame', _extra(executeDAT, 'ticker', 'x', framestart=True), 'every frame'),
    ('a forced cook', lambda c: setattr(_extra(textDAT, 'forcer', 'x')(c), 'text',
                                        "parent().op('out_top').cook(force = True)"), 'forces a cook'),
    ('flashing without the Flashing parameter', _flashing_without_par, 'no Flashing parameter'),
    ('a shader handed the raw clock', lambda c: uniforms(c.op('glsl'), uTime=Expr('absTime.seconds')),
     'clock_seconds()'),
    ('an error inside', _shader_error, 'does not load clean'),
    ('an expression error nothing cooks', _hidden_expression_error, "expression 'sin(1)' fails"),
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
    ('a README without credits', lambda c: setattr(c.op('README'), 'text', 'Selftest README.\n'), 'CREDITS'),
    ('a README wrapped by hand', lambda c: setattr(c.op('README'), 'text', 'Selftest README.\n\nA paragraph broken '
     'across\ntwo lines by hand.\n\nCREDITS\nOriginal: a test of the save-time checks.\n'), 'wrapped by hand (line 4)'),
    ('two TOP outputs', _extra(outTOP, 'out_two', 'x'), 'outputs are'),
    ('a second TOP input before the audio', _extra(inTOP, 'in1b_top', 'x'), 'inputs are'),
    ('makes sound', _extra(audiodeviceoutCHOP, 'speaker', 'x', active=False), 'makes sound'),
    ('over the Non-Commercial cap', _extra(constantTOP, 'big', 'x', outputresolution='custom', resolutionw=1920,
                                            resolutionh=1080), 'exceeds'),
    ('an operator outside every box', lambda c: mk(c, nullTOP, 'loose', [c.op('glsl')], comment='x', at=(-3000, 3000)),
     'loose is in 0 boxes'),
    ('a wire running backward', _move('glsl', dx=-600), 'runs backward'),
    ('operators on top of each other', _move('sample', onto='in1_top', dx=30), 'overlap'),
    ('a docked DAT away from its operator', _move('glsl_pixel', dx=400), 'is not under glsl'),
    ('a box without a title', _set('box_input', Titletext=''), 'not a titled Network Box'),
    ('an operator reading one right of it in its box',
     lambda c: setattr(c.op('sample').par.speed, 'expr', "1 if op('source') else 1"), 'sits right of it in its box'),
]


def _check_source_follows_wiring(host, comp):
    """Input 1 replaces the sample picture when a TOP is wired in, and the sample comes back
    when it is unwired, without anything forcing a cook: checked over later frames (run()
    with delayFrames), written to dev/out/selftest/wiring.txt."""
    source, log = comp.op('source'), []
    feed = host.op('selftest_feed') or mk(host, noiseTOP, 'selftest_feed', comment='selftest input',
                                          outputresolution='custom', resolutionw=320, resolutionh=200, at=(-700, 0))

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


def _check_many_inputs(host):
    """mk() wires more inputs than a new GLSL TOP has connectors, and the shader sees them all."""
    box = host.op('selftest_inputs') or mk(host, baseCOMP, 'selftest_inputs', comment='x', at=(0, -900))
    for o in list(box.children):
        o.destroy()
    consts = [mk(box, constantTOP, 'c{}'.format(i), comment='x', colorr=i / 10.0,
                 outputresolution='custom', resolutionw=8, resolutionh=8, at=(0, -100 * i)) for i in range(5)]
    g = glsl(box, 'g', consts, 'out vec4 fragColor;\nvoid main() {\n'
             '    fragColor = vec4(texture(sTD2DInputs[1], vUV.st).r, texture(sTD2DInputs[2], vUV.st).r,\n'
             '                     texture(sTD2DInputs[3], vUV.st).r, texture(sTD2DInputs[4], vUV.st).r);\n}\n',
             'reads inputs 2 to 5', res=(8, 8), fmt='rgba32float', at=(300, 0))
    g.cook(force=True)
    px = [round(float(v), 2) for v in g.numpyArray()[0, 0]]
    box.destroy()
    return '{} 5-input GLSL TOP reads inputs 2-5 as {} (want [0.1, 0.2, 0.3, 0.4])'.format(
        'ok   ' if px == [0.1, 0.2, 0.3, 0.4] else 'MISS ', px)


def _check_blob_track_docked():
    """A Blob Track TOP docks DATs of its own; an effect built around one must still save."""
    def blob(comp):
        bt = mk(comp, blobtrackTOP, 'blobs', [comp.op('source')], comment='tracks blobs')
        for d in bt.docked:
            d.comment = 'the tracker\'s own'
    comp = good('selftest_blob', more=blob)
    bt = comp.op('blobs')
    try:
        all_checks(comp)
        verdict = 'ok   '
        why = ''
    except RuntimeError as e:
        verdict, why = 'MISS ', ': ' + str(e).splitlines()[-1].strip()
    docked_names = [(d.name, d.OPType) for d in bt.docked]
    comp.destroy()
    return '{} an effect with a Blob Track TOP passes every check; docked {}{}'.format(verdict, docked_names, why)


def _check_audio_in_saves(host):
    """An effect with audio_in() passes every check unwired, and analysis channels at a control
    rate on input 2 raise no warnings (the raw-audio filter sees them too)."""
    def audio(comp):
        section('audio')
        audio_in(comp, _ROOT)
    comp = good('selftest_audio_saves', more=audio)
    try:
        all_checks(comp)
        verdict, why = 'ok   ', ''
    except RuntimeError as e:
        verdict, why = 'MISS ', ': ' + str(e).splitlines()[-1].strip()
    chans = mk(host, constantCHOP, 'selftest_chans', comment='x', const0name='energy', const0value=0.5, at=(-500, -1600))
    comp.inputConnectors[1].connect(chans)
    comp.op('audio').cook(force=True)
    warnings = comp.warnings(recurse=True) + comp.errors(recurse=True)
    if warnings:
        verdict, why = 'MISS ', why + '; with channels on input 2: ' + warnings
    chans.destroy()
    comp.destroy()
    return '{} an effect with audio_in() passes every check, and channels on input 2 warn nothing{}'.format(verdict, why)


def _check_depth_in(host):
    """An effect with input 3 (new_effect(depth=True), depth_in()) passes every check with its
    inputs in the standard order, and depth shows input 3 once a TOP is wired into it, else the
    stand-in from input 1."""
    def depth(comp):
        section('depth')
        depth_in(comp)
    comp = good('selftest_depth', depth=True, more=depth)
    depth = comp.op('depth')
    try:
        all_checks(comp)
        verdict, why = 'ok   ', ''
    except RuntimeError as e:
        verdict, why = 'MISS ', ': ' + str(e).splitlines()[-1].strip()
    unwired = depth.par.index.eval()
    feed = mk(host, noiseTOP, 'selftest_depth_feed', comment='x', outputresolution='custom',
              resolutionw=64, resolutionh=36, at=(-700, -400))
    comp.inputConnectors[2].connect(feed)
    depth.cook(force=True)
    wired, size = depth.par.index.eval(), (depth.width, depth.height)
    if (unwired, wired, size) != (1, 0, (64, 36)):
        verdict, why = 'MISS ', why + ' (want index 1 unwired, 0 and 64 x 36 wired)'
    names = [c.inOP.name for c in comp.inputConnectors]
    feed.destroy()
    comp.destroy()
    return '{} an effect with input 3 passes every check; inputs {}; depth index {} unwired, {} wired ({} x {}){}'.format(
        verdict, names, unwired, wired, size[0], size[1], why)


def _check_flash_gate(host):
    """A 4 Hz pulse train through flash_gate() at each Flashing setting, counted over 6 s on later
    frames: Off passes none, Calm at most one a second, Up to 3 per second at most three."""
    gates = {}
    for setting in ('off', 'calm', 'wcag'):
        comp = good('selftest_flash_' + setting, flashing=True)
        comp.par.Flashing = setting
        lfo = mk(comp, lfoCHOP, 'pulses', comment='x', wavetype='square', frequency=4,
                 offset=0.5, amp=0.5)
        gate = flash_gate(comp, lfo)
        gates[setting] = (comp, mk(comp, countCHOP, 'flashes', [gate], comment='x'),
                          mk(comp, countCHOP, 'raw', [lfo], comment='x'))
    start = {}

    def pull():
        for comp, count, raw in gates.values():
            count.cook()
            raw.cook()

    def tick(n):
        pull()
        if n == 60:
            start.update({k: (c[0].eval(), r[0].eval()) for k, (_, c, r) in gates.items()})
        if n < 420:
            run('args[0](args[1])', tick, n + 1, delayFrames=1)
            return
        lines = []
        for k, (comp, c, r) in gates.items():
            flashes, pulses = c[0].eval() - start[k][0], r[0].eval() - start[k][1]
            limit = {'off': 0, 'calm': 6, 'wcag': 18}[k]
            lines.append('{} Flashing {}: {} flashes from {} pulses in 6 s (at most {})'.format(
                'ok   ' if flashes <= limit and (k == 'off' or flashes > 0) else 'MISS ', k, flashes, pulses, limit))
            comp.destroy()
        with open(os.path.join(OUT, 'flash.txt'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        open(os.path.join(OUT, 'done'), 'w').write('flash.txt\n')

    if os.path.exists(os.path.join(OUT, 'done')):
        os.remove(os.path.join(OUT, 'done'))
    tick(0)


def _check_audio_in(host):
    """audio_in() on each kind of input 2, read over 3 s of later frames: nothing; beat_count and
    energy; kick pulses as audioAnalysis gives them and low; Fosfora's signal (beat and bar counts, build,
    beat_phase, bar_phase, and bass beside energy: level follows bass); raw audio (the sample MP3)."""
    cases = {}

    def effect(kind):
        comp = good('selftest_audio_' + kind)
        return comp, audio_in(comp, _ROOT)

    comp, script = effect('none')
    cases['none'] = (comp, script, [])
    for kind, beat_name, level_name, level in (('counted', 'beat_count', 'energy', 0.6), ('pulses', 'kick', 'low', 0.4)):
        comp, script = effect(kind)
        lfo = mk(host, lfoCHOP, 'selftest_lfo_' + kind, comment='x', wavetype='square',
                 frequency=2, offset=0.5, amp=0.5, at=(-900, -1200))
        beats = mk(host, countCHOP, 'selftest_count_' + kind, [lfo], comment='x', at=(-700, -1200)) if kind == 'counted' else lfo
        named = mk(host, renameCHOP, 'selftest_named_' + kind, [beats], comment='x',
                   renamefrom='*', renameto=beat_name, at=(-500, -1200))
        const = mk(host, constantCHOP, 'selftest_level_' + kind, comment='x', const0name=level_name, const0value=level, at=(-500, -1300))
        merged = mk(host, mergeCHOP, 'selftest_in_' + kind, [named, const], comment='x', at=(-300, -1200))
        comp.inputConnectors[1].connect(merged)
        cases[kind] = (comp, script, list(dict.fromkeys([lfo, beats, named, const, merged])))
    comp, script = effect('fosfora')
    made = []
    for name, hz, y in (('beat_count', 2, -1700), ('bar_count', 0.5, -1800)):
        lfo = mk(host, lfoCHOP, 'selftest_lfo_' + name, comment='x', wavetype='square',
                 frequency=hz, offset=0.5, amp=0.5, at=(-900, y))
        count = mk(host, countCHOP, 'selftest_count_' + name, [lfo], comment='x', at=(-700, y))
        made += [lfo, count, mk(host, renameCHOP, 'selftest_named_' + name, [count], comment='x',
                                renamefrom='*', renameto=name, at=(-500, y))]
    const = mk(host, constantCHOP, 'selftest_fosfora_levels', comment='x', at=(-500, -1900))
    const.seq.const.numBlocks = 5
    made.append(setpars(const, const0name='energy', const0value=0.6, const1name='build', const1value=0.7,
                        const2name='beat_phase', const2value=0.25, const3name='bar_phase', const3value=0.5,
                        const4name='bass', const4value=0.45) or const)
    made.append(mk(host, mergeCHOP, 'selftest_in_fosfora', [made[2], made[5], made[6]], comment='x', at=(-300, -1800)))
    comp.inputConnectors[1].connect(made[-1])
    cases['fosfora'] = (comp, script, made)
    comp, script = effect('raw')
    music = mk(host, audiofileinCHOP, 'selftest_music', comment='x',
               file=Expr("app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'"), at=(-500, -1500))
    comp.inputConnectors[1].connect(music)
    cases['raw'] = (comp, script, [music])
    start = {}

    def tick(n):
        for _, script, _ in cases.values():
            script.cook()
        if n == 30:
            start.update({k: (script['beat_count'].eval(), script['bar_count'].eval())
                          for k, (_, script, _) in cases.items()})
        if n < 210:
            run('args[0](args[1])', safe_tick, n + 1, delayFrames=1)
            return
        lines = []
        # source, beats in 3 s, bars in 3 s (4 beats to a bar unless the input has bars), level
        # (None: any above 0.05), build, beat_phase (None: any in 0..1)
        want = {'none': (0, (0, 0), (0, 0), 0, 0, 0), 'counted': (2, (5, 7), (1, 2), 0.6, 0, None),
                'pulses': (2, (5, 7), (1, 2), 0.4, 0, None), 'fosfora': (3, (5, 7), (1, 2), 0.45, 0.7, 0.25),
                'raw': (1, (2, 30), (0, 8), None, 0, None)}
        for k, (comp, script, extra) in cases.items():
            src, n_beats, n_bars, level, build, phase = (script[c].eval() for c in (
                'source', 'beat_count', 'bar_count', 'level', 'build', 'beat_phase'))
            n_beats -= start[k][0]
            n_bars -= start[k][1]
            w_src, beats, bars, w_level, w_build, w_phase = want[k]
            good_level = (level > 0.05) if w_level is None else abs(level - w_level) < 0.05
            good_phase = (0 <= phase < 1) if w_phase is None else abs(phase - w_phase) < 0.01
            ok = (src == w_src and beats[0] <= n_beats <= beats[1] and bars[0] <= n_bars <= bars[1]
                  and good_level and abs(build - w_build) < 0.01 and good_phase)
            lines.append('{} audio {}: source {:.0f}, {:.0f} beats and {:.0f} bars in 3 s (want {}-{}, {}-{}), '
                         'level {:.2f}, build {:.2f}, beat_phase {:.2f}'.format(
                             'ok   ' if ok else 'MISS ', k, src, n_beats, n_bars, beats[0], beats[1], bars[0],
                             bars[1], level, build, phase))
            for o in extra:
                o.destroy()
            comp.destroy()
        with open(os.path.join(OUT, 'audio.txt'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        open(os.path.join(OUT, 'audio_done'), 'w').write('audio.txt\n')

    def safe_tick(n):
        # A failure on a later frame lands in the textport, not in dev/td.sh's output: write it down.
        try:
            tick(n)
        except Exception:
            import traceback
            with open(os.path.join(OUT, 'audio.txt'), 'w') as f:
                f.write('MISS  audio check failed on frame {}:\n{}'.format(n, traceback.format_exc()))
            open(os.path.join(OUT, 'audio_done'), 'w').write('audio.txt\n')

    if os.path.exists(os.path.join(OUT, 'audio_done')):
        os.remove(os.path.join(OUT, 'audio_done'))
    safe_tick(0)


def main():
    host = op(globals().get('TDLIB_PARENT', '/project1'))
    os.makedirs(OUT, exist_ok=True)
    report = []

    # The intact effect passes every check, saves, and its shell is wired as promised.
    comp = good()
    path, manifest = save_tox(comp, OUT, comp.name, {'version': '0.0.1', 'sources_sha256': 'selftest'})
    flash = good('selftest_flash', flashing=True)
    all_checks(flash)
    report.append('ok    a flashing effect passes, Flashing {} default {!r}'.format(
        list(flash.par.Flashing.menuLabels), flash.par.Flashing.default))
    flash.destroy()
    report.append('ok    intact effect saves: {} ({} bytes, build {})'.format(
        os.path.basename(path), manifest['tox_bytes'], manifest['touchdesigner_build']))
    w = comp.op('window').par.winop.eval()
    report.append('{} window shows {}'.format('ok   ' if w is not None and w.name == 'out_top' else 'MISS ', w))
    report.append('info  docked to glsl: {}'.format([(d.name, d.OPType) for d in comp.op('glsl').docked]))
    report.append('info  inputs {}, outputs {}'.format([c.inOP.name for c in comp.inputConnectors],
                                                       [c.outOP.name for c in comp.outputConnectors]))
    # Loaded somewhere else, as a user's drag-in does: no errors, the sample on its output.
    elsewhere = host.op('selftest_elsewhere') or mk(host, baseCOMP, 'selftest_elsewhere', comment='x', at=(0, -600))
    loaded = elsewhere.loadTox(path)
    loaded.op('out_top').cook(force=True)
    errors = loaded.errors(recurse=True)
    report.append('{} loaded elsewhere: {}, out {} x {}, errors {!r}'.format(
        'ok   ' if not errors and loaded.op('out_top').width == 1280 else 'MISS ', loaded.path,
        loaded.op('out_top').width, loaded.op('out_top').height, errors))
    elsewhere.destroy()
    _check_source_follows_wiring(host, comp)
    report.append(_check_many_inputs(host))
    report.append(_check_blob_track_docked())
    report.append(_check_audio_in_saves(host))
    report.append(_check_depth_in(host))
    _check_flash_gate(host)
    _check_audio_in(host)
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
