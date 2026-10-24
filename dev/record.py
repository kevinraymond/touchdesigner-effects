"""DEV ONLY. Inside TouchDesigner: record effects as video clips with sound, for the README, the
docs previews or a demo reel. The free license can't encode H.264, so this records Motion JPEG
.mov files and dev/clips.py turns them into MP4s (and previews) on the Linux side:

    TD_ARGS='ascii clip=b2_plaza seconds=8' dev/td.sh dev/record.py
    dev/td.sh --pull dev/out/record/done
    uv run dev/clips.py dev/out/record

Words in TD_ARGS: effect names (none: every effect), clip=<name> for private/assets/ready/
<name>.mp4 (default b1_dancer; TouchDesigner's sample movie when it isn't there), seconds=<n>
(default 8), audio=<file> for a track in private/assets/ready/ (default: m1_* when there, else
TouchDesigner's sample MP3; audio=none records silence and feeds no beat).

Each effect is loaded from effects/<n>/<n>.tox (a bundle when named) into TDLIB_PARENT at its
defaults, the clip, its depth (<clip>_depth.mp4, on input 3 of an effect that takes one) and the
track restart together, and the effect hears the track on input 2 while a
Movie File Out records its output and the track at 30 fps. One effect at a time, nothing else of
ours cooking. Writes dev/out/record/<effect>_<clip>.mov, then dev/out/record/done with each file's
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
    return names, clip, track, float(opts.get('seconds', 8))


def main():
    host = op(TDLIB_PARENT)
    for o in list(host.children):
        if o.valid:  # destroying an operator also destroys the DATs docked to it
            o.destroy()
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(os.path.join(OUT, 'done')):
        os.remove(os.path.join(OUT, 'done'))
    names, clip_file, track_file, seconds = options(globals().get('TDLIB_ARGS') or [])
    paths = [p for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox')))
             if not names or os.path.splitext(os.path.basename(p))[0] in names]
    paths += [p for p in sorted(glob.glob(os.path.join(_ROOT, 'bundles', '*', '*.tox')))
              if os.path.splitext(os.path.basename(p))[0] in names]  # bundles by name only
    clip = mk(host, moviefileinTOP, 'clip', -600, 0, comment='The clip.', file=clip_file)
    depth_file = os.path.splitext(clip_file)[0] + '_depth.mp4'
    depth = mk(host, moviefileinTOP, 'clip_depth', -600, -150, comment="The clip's depth.",
               file=depth_file) if os.path.exists(depth_file) else None
    track = mk(host, audiofileinCHOP, 'track', -600, -300, comment='The track.', file=track_file,
               repeat='on') if track_file else None
    view = mk(host, nullTOP, 'view', 400, 0, comment='What gets recorded.')
    rec = mk(host, moviefileoutTOP, 'rec', 600, 0, [view], comment='Records the view and the track.',
             type='movie', videocodec='mjpa', qualityscale=1.0, fps=FPS, limitlength=True,
             length=seconds, lengthunit='seconds')
    if track:
        rec.par.audiochop = track
    info = mk(host, infoCHOP, 'rec_info', 800, 0, comment='Frames written and dropped.', op=rec)
    effects = []
    for path in paths:
        fx = host.loadTox(path)
        fx.nodeX, fx.nodeY = 0, 300 * len(effects)
        fx.inputConnectors[0].connect(clip)
        if track and len(fx.inputConnectors) > 1:
            fx.inputConnectors[1].connect(track)
        if depth is not None and len(fx.inputConnectors) > 2:
            fx.inputConnectors[2].connect(depth)
        fx.allowCooking = False
        effects.append(fx)
    stem = os.path.splitext(os.path.basename(clip_file))[0]
    lines = []

    def begin(i):
        fx = effects[i]
        for o in effects:
            o.allowCooking = o is fx
        view.inputConnectors[0].connect(fx.outputConnectors[0])
        clip.par.cuepulse.pulse()
        if depth is not None:
            depth.par.cuepulse.pulse()
        if track:
            track.par.cuepulse.pulse()
        rec.par.file = os.path.join(OUT, '{}_{}.mov'.format(fx.name, stem))
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

    if not effects:
        print('no effects to record')
        return
    begin(0)
    print('recording {} for {:g} s each on {} with {}'.format(
        ', '.join(fx.name for fx in effects), seconds, stem,
        os.path.basename(track_file) if track_file else 'no sound'))


main()
