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
so every flash an effect can make is asked for. beat=music is the same shape at a dance tempo, MUSIC_BPM
with a bar every 4 beats and no drops, sections or build: a beat's reaction that lasts a few tenths of
a second gets to finish (and come back) before the next, which the stress beat's 8 a second can hide.
The stress beat also swings each of the seven bands (as Fosfora's feature bus sends them, feat_sub_bass ...
feat_brilliance) fully on and off 8 times a second, each a seventh of a cycle after the one below, for the
effects that follow the bands; beat=music pulses them as a dance beat's drums would (the kick's on each beat, the
highest on every eighth note). beat=song plays a track as raw audio instead, as music really arrives:
private/assets/ready/m1x_ease_from_drop.wav, or song=<name> for another .wav there, looping.
"""

import os

MUSIC_BPM = 140
BANDS = ('sub_bass', 'bass', 'low_mid', 'mid', 'upper_mid', 'presence', 'brilliance')   # audio_in()'s, lowest first
READY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'private', 'assets', 'ready')


def test_args(args):
    """TD_ARGS words: effect names, then options: clip=<name> (default b1_dancer), beat=none or music."""
    opts = dict(clip='b1_dancer', beat='stress')
    opts.update(a.split('=', 1) for a in args if '=' in a)
    return [a for a in args if '=' not in a], opts


def testbed(host, opts):
    path = os.path.join(READY, opts['clip'] + '.mp4')
    clip = mk(host, moviefileinTOP, 'clip', comment='The test clip.',
              file=path if os.path.exists(path) else app.samplesFolder + '/Map/Nature/Movie.1.mp4', at=(-600, 0))
    depth = os.path.join(READY, opts['clip'] + '_depth.mp4')
    if os.path.exists(path) and os.path.exists(depth):
        follow_frame(host, clip, mk(host, moviefileinTOP, 'clip_depth', comment="The test clip's depth.",
                                    file=depth, at=(-600, -150)))
    if opts['beat'] == 'none':
        return clip, None
    if opts['beat'] == 'song':
        track = os.path.join(READY, opts.get('song', 'm1x_ease_from_drop') + '.wav')
        return clip, mk(host, audiofileinCHOP, 'song', comment='A track, as raw audio.', file=track, repeat='on',
                        at=(-600, -300))
    beat = mk(host, constantCHOP, 'stress', comment='A beat far busier than music.', at=(-600, -300))
    chans = (('beat_count', 'int(absTime.seconds * 8)'), ('bar_count', 'int(absTime.seconds * 2)'),
             ('drop_count', 'int(absTime.seconds)'), ('boundary_count', 'int(absTime.seconds / 2)'),
             ('build', '0.5 + 0.5 * math.sin(absTime.seconds)'), ('energy', '0.8'),
             ('beat_phase', 'absTime.seconds * 8 % 1'), ('bar_phase', 'absTime.seconds * 2 % 1')) + tuple(
        ('feat_' + band, '1 if (absTime.seconds * 8 + {} / 7) % 1 < 0.5 else 0'.format(k))
        for k, band in enumerate(BANDS))
    if opts['beat'] == 'music':
        b = MUSIC_BPM / 60
        beat.comment = 'A beat at {} BPM, a bar every 4 beats, no drops or sections.'.format(MUSIC_BPM)
        chans = (('beat_count', 'int(absTime.seconds * {})'.format(b)), ('bar_count', 'int(absTime.seconds * {})'.format(b / 4)),
                 ('drop_count', '0'), ('boundary_count', '0'), ('build', '0'), ('energy', '0.8'),
                 ('beat_phase', 'absTime.seconds * {} % 1'.format(b)), ('bar_phase', 'absTime.seconds * {} % 1'.format(b / 4)))
        # The bands as a dance beat's drums: the kick's (sub bass, bass) on each beat, low mid on the off-beats, the
        # rest on every eighth note (4.7 a second at 140 BPM), each on for a quarter of its step. An effect that eases
        # a band's fall (Video Vocoder's Release) smooths these less than the stress beat's 8 a second.
        steps = ((b, 0), (b, 0), (b, 0.5), (2 * b, 0), (2 * b, 0), (2 * b, 0), (2 * b, 0))
        chans += tuple(('feat_' + band, '1 if (absTime.seconds * {} - {}) % 1 < 0.25 else 0'.format(rate, at))
                       for band, (rate, at) in zip(BANDS, steps))
    beat.seq.const.numBlocks = len(chans)
    for i, (name, expr) in enumerate(chans):
        setpars(beat, **{'const{}name'.format(i): name, 'const{}value'.format(i): Expr(expr)})
    return clip, beat


def follow_frame(host, movie, other):
    """Make the Movie File In other show movie's current frame (an Info CHOP's index) instead of
    playing by itself. A movie playing by itself moves on only while something pulls it, so a depth
    clip that only one effect reads falls behind its picture clip whenever the picture runs without
    that effect (dev/flash.py records the clip alone first; the demo shows one effect at a time)."""
    info = mk(host, infoCHOP, other.name + '_at',
              comment='Where {} is (index: its frame), for {}.'.format(movie.name, other.name), op=movie.name, at=(other.nodeX - 200, other.nodeY))
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
