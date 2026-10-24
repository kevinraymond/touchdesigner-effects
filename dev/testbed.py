"""DEV ONLY. Inside TouchDesigner: the test input dev/flash.py and dev/perf.py feed each effect.
exec() it into a script's globals after lib/tox_build.py, then:

    names, opts = test_args(TDLIB_ARGS)      # effect names; clip=<name>, beat=none
    clip, beat = testbed(op(TDLIB_PARENT), opts)

clip plays private/assets/ready/<clip>.mp4, b1_dancer by default (TouchDesigner's sample movie
when that isn't there). With beat=none, beat is None and input 2 stays unwired, which tells an
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
