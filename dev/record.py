"""DEV ONLY. Inside TouchDesigner: record effects as video clips with sound, for the README, the
docs previews or a demo reel. The free license can't encode H.264, so this records Motion JPEG
.mov files and dev/clips.py turns them into MP4s (and previews) on the Linux side:

    TD_ARGS='ascii clip=b2_plaza seconds=8' dev/td.sh dev/record.py
    dev/td.sh --pull dev/out/record/done
    uv run dev/clips.py dev/out/record

Words in TD_ARGS: effect names (none: every effect), and input and depth for the clip and its depth
map as they are (to tile beside the effects, dev/tile.py), clip=<name> for private/assets/ready/
<name>.mp4 (default b1_dancer; TouchDesigner's sample movie when it isn't there), seconds=<n>
(default 8), audio=<file> for a track in private/assets/ready/ (default: m1_* when there, else
TouchDesigner's sample MP3; audio=none records silence and feeds no beat), <Par>=<value> (a capitalized
name) to set that parameter on every effect that has one, tag=<word> to add _<word> to the file names
(TD_ARGS='particles Behavior=push tag=push'), and settle=<s> to let each effect cook that long on the playing clip
before the clip and track restart, for an effect that starts by growing in (Reaction-Diffusion fades in over 4 s).

Each effect is loaded from effects/<n>/<n>.tox (a bundle when named) into TDLIB_PARENT at its
defaults, the clip, its depth (<clip>_depth.mp4, on input 3 of an effect that takes one) and the
track restart together, and the effect hears the track on input 2 while a
Movie File Out records its output and the track at 30 fps (at its defaults, but for any <Par>=<value>).
One effect at a time, nothing else of ours cooking. Before the first take the clip plays for WARMUP seconds: cued while it was still
opening, the first take started at another point of the clip than the rest (ASCII, first, ran
out of step in the Showreel's tiled preview). Writes dev/out/record/<effect>_<clip>.mov, then dev/out/record/done with each file's
frames written and dropped (TouchDesigner repeats a frame to keep time when it drops one: keep the
Mac otherwise idle while recording).
"""

import glob
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUT = os.path.join(_HERE, 'out', 'record')
READY = os.path.join(_ROOT, 'private', 'assets', 'ready')
FPS = 30
MARGIN = 1.0  # seconds after the clip and track restart before recording starts
WARMUP = 1.5  # seconds the clip plays before the first take, so it is open and running when cued
TAKES = ('input', 'depth')  # names that record the clip and its depth as they are


def options(args):
    names = [a for a in args if '=' not in a]
    opts = dict(a.split('=', 1) for a in args if '=' in a)
    clip = os.path.join(READY, opts.get('clip', 'b1_dancer') + '.mp4')
    if not os.path.exists(clip):
        clip = app.samplesFolder + '/Map/Nature/Movie.1.mp4'
    audio = opts.get('audio')
    if audio == 'none':
        track = None
    elif audio:
        track = os.path.join(READY, audio if '.' in audio else audio + '.wav')
    else:
        mine = sorted(glob.glob(os.path.join(READY, 'm1_*.wav')))
        track = mine[0] if mine else app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'
    pars = {k: v for k, v in opts.items() if k[:1].isupper()}
    return names, clip, track, float(opts.get('seconds', 8)), pars, opts.get('tag'), float(opts.get('settle', 0))


def main():
    host = op(TDLIB_PARENT)
    for o in list(host.children):
        if o.valid:  # destroying an operator also destroys the DATs docked to it
            o.destroy()
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(os.path.join(OUT, 'done')):
        os.remove(os.path.join(OUT, 'done'))
    names, clip_file, track_file, seconds, pars, tag, settle = options(globals().get('TDLIB_ARGS') or [])
    takes = [n for n in TAKES if n in names]
    names = [n for n in names if n not in TAKES]
    paths = [p for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox')))
             if not (names or takes) or os.path.splitext(os.path.basename(p))[0] in names]
    paths += [p for p in sorted(glob.glob(os.path.join(_ROOT, 'bundles', '*', '*.tox')))
              if os.path.splitext(os.path.basename(p))[0] in names]  # bundles by name only
    clip = mk(host, moviefileinTOP, 'clip', comment='The clip.', file=clip_file, at=(-600, 0))
    depth_file = os.path.splitext(clip_file)[0] + '_depth.mp4'
    depth = mk(host, moviefileinTOP, 'clip_depth', comment="The clip's depth.",
               file=depth_file, at=(-600, -150)) if os.path.exists(depth_file) else None
    track = mk(host, audiofileinCHOP, 'track', comment='The track.', file=track_file,
               repeat='on', at=(-600, -300)) if track_file else None
    view = mk(host, nullTOP, 'view', comment='What gets recorded.', at=(400, 0))
    rec = mk(host, moviefileoutTOP, 'rec', [view], comment='Records the view and the track.',
             type='movie', videocodec='mjpa', qualityscale=1.0, fps=FPS, limitlength=True,
             length=seconds, lengthunit='seconds', at=(600, 0))
    if track:
        rec.par.audiochop = track
    info = mk(host, infoCHOP, 'rec_info', comment='Frames written and dropped.', op=rec, at=(800, 0))
    # Each take: (name, what to record, the effect to let cook or None).
    effects = [(n, clip if n == 'input' else depth, None) for n in takes if n == 'input' or depth is not None]
    for path in paths:
        fx = host.loadTox(path)
        fx.nodeX, fx.nodeY = 0, 300 * len(effects)
        fx.inputConnectors[0].connect(clip)
        if track and len(fx.inputConnectors) > 1:
            fx.inputConnectors[1].connect(track)
        if depth is not None and len(fx.inputConnectors) > 2:
            fx.inputConnectors[2].connect(depth)
        for k, v in pars.items():
            p = getattr(fx.par, k, None)
            if p is not None:
                p.val = type(p.default)(float(v)) if isinstance(p.default, (int, float)) and not isinstance(p.default, bool) else v
        fx.allowCooking = False
        effects.append((fx.name, fx, fx))
    stem = os.path.splitext(os.path.basename(clip_file))[0] + ('_' + tag if tag else '')
    lines = []

    def begin(i):
        name, what, fx = effects[i]
        for _, _, o in effects:
            if o is not None:
                o.allowCooking = o is fx
        view.inputConnectors[0].connect(what.outputConnectors[0] if what.isCOMP else what)
        if settle and fx is not None:
            pull(absTime.seconds + settle)   # nothing records yet, so pull the view to keep the effect cooking
            run('args[0](args[1])', cue, i, delayMilliSeconds=int(settle * 1000))
        else:
            cue(i)

    def pull(until):
        view.cook(force=True)
        if absTime.seconds < until:
            run('args[0](args[1])', pull, until, delayFrames=1)

    def cue(i):
        name = effects[i][0]
        clip.par.cuepulse.pulse()
        if depth is not None:
            depth.par.cuepulse.pulse()
        if track:
            track.par.cuepulse.pulse()
        rec.par.file = os.path.join(OUT, '{}_{}.mov'.format(name, stem))
        run('args[0](args[1])', start, i, delayMilliSeconds=int(MARGIN * 1000))

    def start(i):
        rec.par.record = True
        run('args[0](args[1])', stop, i, delayMilliSeconds=int((seconds + 0.5) * 1000))

    def stop(i):
        rec.par.record = False
        info.cook(force=True)
        lines.append('{} {} frames written, {} dropped'.format(
            os.path.basename(rec.par.file.eval()), int(info['total_frames_written']),
            int(info['total_frames_dropped'])))
        if i + 1 < len(effects):
            run('args[0](args[1])', begin, i + 1, delayFrames=5)
            return
        with open(os.path.join(OUT, 'done'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        for o in list(host.children):
            o.allowCooking = False
        run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=30)

    def warm(frames):
        for o in (clip, depth):
            if o is not None:
                o.cook(force=True)
        if frames > 0:
            run('args[0](args[1])', warm, frames - 1, delayFrames=1)
        else:
            begin(0)

    if not effects:
        print('no effects to record')
        return
    warm(int(WARMUP * 60))
    print('recording {} for {:g} s each on {} with {}{}'.format(
        ', '.join(n for n, _, _ in effects), seconds, stem,
        os.path.basename(track_file) if track_file else 'no sound', ', ' + str(pars) if pars else ''))


main()
