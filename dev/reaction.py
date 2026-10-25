"""DEV ONLY. Inside TouchDesigner: record what the music does to each effect's picture, for
dev/reaction_report.py to measure (how much it changes on beats and bars, and with loudness):

    TD_ARGS='ascii datamosh' dev/td.sh dev/reaction.py       # those effects (none named: every one)
    TD_ARGS='glitch audio=m1_cinematic' dev/td.sh dev/reaction.py
    TD_ARGS='ascii Beatglyphs=0.6 tag=g6' dev/td.sh dev/reaction.py   # a setting off its default
    dev/td.sh --pull dev/out/reaction/done
    uv run --with numpy dev/reaction_report.py dev/out/reaction

Each effect is loaded from effects/<n>/<n>.tox into TDLIB_PARENT at its defaults and gets
dev/testbed.py's clip (and its depth on input 3), twice: once hearing the song as raw audio on input
2 (audio=<file in private/assets/ready>, default m1x_ease_from_drop, the docs previews' beat from its
first drop), once with input 2 unwired. Each take cues the clip and the song together, waits SETTLE
seconds and records SECONDS: for the output and the clip, a 64 x 36 grid of their mean colors and of
how much each cell changed since the last frame (measured on every pixel), and what the effect's
audio input made of the song (beat_count, bar_count, level), read back every frame. The take without audio is the control: the
picture changes by itself (the clip moves, a simulation runs), and the report measures that take at
the song take's beat times, so what is left over is the music.

Writes dev/out/reaction/<n>_song.npz and <n>_none.npz (with tag=<word>, <n>_<word>_song.npz), then
dev/out/reaction/done. dev/td.sh returns before the recording ends: wait for done before another
run. About 2 x (SETTLE + SECONDS) s per effect, reading two small textures every frame: keep other
work off TouchDesigner meanwhile.
"""

import glob
import os

import numpy as np

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(_HERE)
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
exec(compile(open(os.path.join(_HERE, 'testbed.py')).read(), 'testbed.py', 'exec'), globals())
OUT = os.path.join(_HERE, 'out', 'reaction')
SETTLE, SECONDS = 1.5, 14.0
GRID = (64, 36)
CHANS = ('beat_count', 'bar_count', 'level', 'source')

METER = """// Over each output cell: the input's mean color as shown (rgb; not linear light, what the eye
// compares), and how much it changed since the last frame (a: each pixel's largest channel change,
// averaged, so a change too fine for the cell's mean color, a glyph for one of the same ink, counts).
out vec4 fragColor;
void main()
{
    vec2 cell = uTD2DInfos[0].res.zw / uTDOutputInfo.res.zw;
    ivec2 lo = ivec2(floor((gl_FragCoord.xy - 0.5) * cell));
    ivec2 hi = ivec2(floor((gl_FragCoord.xy + 0.5) * cell));
    vec4 sum = vec4(0.0);
    float n = 0.0;
    for (int y = lo.y; y < hi.y; y++)
        for (int x = lo.x; x < hi.x; x++) {
            vec3 c = clamp(texelFetch(sTD2DInputs[0], ivec2(x, y), 0).rgb, 0.0, 1.0);
            vec3 d = abs(c - clamp(texelFetch(sTD2DInputs[1], ivec2(x, y), 0).rgb, 0.0, 1.0));
            sum += vec4(c, max(d.r, max(d.g, d.b)));
            n += 1.0;
        }
    fragColor = TDOutputSwizzle(sum / max(n, 1.0));
}
"""


def main():
    host = op(TDLIB_PARENT)
    for o in list(host.children):
        if o.valid:  # destroying an operator also destroys the DATs docked to it
            o.destroy()
    names, opts = test_args(globals().get('TDLIB_ARGS') or [])
    overrides = {k: v for k, v in opts.items() if k[:1].isupper()}
    tag = '_' + opts['tag'] if opts.get('tag') else ''
    song = os.path.join(READY, opts.get('audio', 'm1x_ease_from_drop') + '.wav')
    os.makedirs(OUT, exist_ok=True)
    paths = [p for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox')))
             if not names or os.path.splitext(os.path.basename(p))[0] in names]
    if os.path.exists(os.path.join(OUT, 'done')):
        os.remove(os.path.join(OUT, 'done'))
    clip, _ = testbed(host, dict(opts, beat='none'))
    track = mk(host, audiofileinCHOP, 'track', -600, -300, comment='The song.', file=song, repeat='on')
    view = mk(host, nullTOP, 'view', 400, 0, comment='What the output meter reads.')
    meters = []
    for name, what, y in (('out', view, 0), ('in', clip, -200)):
        prev = mk(host, cacheTOP, 'prev_' + name, 400, y - 100, [what], 'The ' + name + "'s previous frame.",
                  cachesize=2, outputindex=-1)
        meters.append(glsl(host, 'meter_' + name, 600, y, [what, prev], METER,
                           'Mean color and change per cell: the ' + name + '.', res=GRID, fmt='rgba32float'))

    runs = []
    for path in paths:
        fx = host.loadTox(path)
        fx.nodeX, fx.nodeY = 0, 300 * len(runs)
        wire(fx, clip, None)
        for k, v in overrides.items():
            p = getattr(fx.par, k, None)
            if p is not None:
                p.val = type(p.default)(float(v)) if isinstance(p.default, (int, float)) and not isinstance(p.default, bool) else v
        fx.allowCooking = False
        runs += [(fx, 'none'), (fx, 'song')]

    state = {'i': -1, 'rows': [], 'frames': [], 'cue': 0.0}

    def begin(i):
        state['i'], state['rows'], state['frames'] = i, [], []
        fx, take = runs[i]
        for o in host.findChildren(type=COMP, depth=1):
            o.allowCooking = o is fx
        view.inputConnectors[0].connect(fx.outputConnectors[0])
        if take == 'song':
            fx.inputConnectors[1].connect(track)
        else:
            fx.inputConnectors[1].disconnect()
        clip.par.cuepulse.pulse()
        track.par.cuepulse.pulse()
        state['cue'] = absTime.seconds

    def tick():
        fx, take = runs[state['i']]
        t = absTime.seconds - state['cue']
        if t >= SETTLE:
            audio = fx.op('audio')
            state['rows'].append([t] + [audio[c].eval() for c in CHANS])
            state['frames'].append([m.numpyArray().astype(np.float16) for m in meters])
        if t < SETTLE + SECONDS:
            run('args[0]()', tick, delayFrames=1)
            return
        out, inp = zip(*state['frames'])
        np.savez_compressed(os.path.join(OUT, '{}{}_{}.npz'.format(fx.name, tag, take)),
                            rows=np.array(state['rows'], dtype=np.float64), out=np.array(out), inp=np.array(inp),
                            chans=np.array(('t',) + CHANS), song=os.path.basename(song))
        if state['i'] + 1 < len(runs):
            begin(state['i'] + 1)
            run('args[0]()', tick, delayFrames=1)
            return
        with open(os.path.join(OUT, 'done'), 'w') as f:
            f.write('\n'.join('{}{}_{}.npz'.format(fx.name, tag, take) for fx, take in runs) + '\n')
        for o in list(host.children):
            o.allowCooking = False
        run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=2)

    if not runs:
        print('no effects to record')
        return
    begin(0)
    run('args[0]()', tick, delayFrames=1)
    print('recording {} for {:g} s after {:g} s, with and without {}{}'.format(
        ', '.join(fx.name for fx, take in runs if take == 'song'), SECONDS, SETTLE, os.path.basename(song),
        ', ' + str(overrides) if overrides else ''))


main()
