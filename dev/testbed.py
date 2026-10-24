"""DEV ONLY. Inside TouchDesigner: the test input dev/flash.py and dev/perf.py feed each effect.
exec() it into a script's globals after lib/tox_build.py, then:

    names, opts = test_args(TDLIB_ARGS)      # effect names; clip=<name>, beat=none
    clip, beat = testbed(op(TDLIB_PARENT), opts)
    wire(fx, clip, beat)                     # for each effect

clip plays private/assets/ready/<clip>.mp4, b1_dancer by default (TouchDesigner's sample movie
when that isn't there), and clip_depth beside it its depth, <clip>_depth.mp4, when there is one:
wire() gives it to an effect that takes input 3. clip_depth shows the clip's frame (follow_frame())
rather than play by itself, so it stays in step even when the clip runs alone first. With beat=none, beat is None and input 2 stays unwired, which tells an
effect's own changes from the ones the beat drives. beat is a Constant CHOP shaped like Fosfora's signal and far busier than music: 8 beats,
2 bars, 1 drop and half a section change a second, a build rising and falling, loud throughout,
so every flash an effect can make is asked for.
"""

import os

READY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'private', 'assets', 'ready')


def test_args(args):
    """TD_ARGS words: effect names, then options: clip=<name> (default b1_dancer), beat=none."""
    opts = dict(clip='b1_dancer', beat='stress')
    opts.update(a.split('=', 1) for a in args if '=' in a)
    return [a for a in args if '=' not in a], opts


def testbed(host, opts):
    path = os.path.join(READY, opts['clip'] + '.mp4')
    clip = mk(host, moviefileinTOP, 'clip', -600, 0, comment='The test clip.',
              file=path if os.path.exists(path) else app.samplesFolder + '/Map/Nature/Movie.1.mp4')
    depth = os.path.join(READY, opts['clip'] + '_depth.mp4')
    if os.path.exists(path) and os.path.exists(depth):
        follow_frame(host, clip, mk(host, moviefileinTOP, 'clip_depth', -600, -150, comment="The test clip's depth.",
                                    file=depth))
    if opts['beat'] == 'none':
        return clip, None
    beat = mk(host, constantCHOP, 'stress', -600, -300, comment='A beat far busier than music.')
    chans = (('beat_count', 'int(absTime.seconds * 8)'), ('bar_count', 'int(absTime.seconds * 2)'),
             ('drop_count', 'int(absTime.seconds)'), ('boundary_count', 'int(absTime.seconds / 2)'),
             ('build', '0.5 + 0.5 * math.sin(absTime.seconds)'), ('energy', '0.8'),
             ('beat_phase', 'absTime.seconds * 8 % 1'), ('bar_phase', 'absTime.seconds * 2 % 1'))
    beat.seq.const.numBlocks = len(chans)
    for i, (name, expr) in enumerate(chans):
        setpars(beat, **{'const{}name'.format(i): name, 'const{}value'.format(i): Expr(expr)})
    return clip, beat


def follow_frame(host, movie, other):
    """Make the Movie File In other show movie's current frame (an Info CHOP's index) instead of
    playing by itself. A movie playing by itself moves on only while something pulls it, so a depth
    clip that only one effect reads falls behind its picture clip whenever the picture runs without
    that effect (dev/flash.py records the clip alone first; the demo shows one effect at a time)."""
    info = mk(host, infoCHOP, other.name + '_at', other.nodeX - 200, other.nodeY,
              comment='Where {} is (index: its frame), for {}.'.format(movie.name, other.name), op=movie.name)
    setpars(other, playmode='specify', indexunit='indices', index=Expr("op('{}')['index']".format(info.name)))
    return info


def wire(fx, clip, beat):
    """Input 1 the clip, input 2 the beat (unless None), input 3 the clip's depth when the effect
    takes one and the clip has one (with none, the effect uses its own stand-in)."""
    fx.inputConnectors[0].connect(clip)
    if beat is not None and len(fx.inputConnectors) > 1:
        fx.inputConnectors[1].connect(beat)
    depth = clip.parent().op('clip_depth')
    if depth is not None and len(fx.inputConnectors) > 2:
        fx.inputConnectors[2].connect(depth)
