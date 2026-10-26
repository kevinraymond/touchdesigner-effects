"""DEV ONLY. Inside TouchDesigner: record what each effect's output does to luminance, frame by
frame, under a beat-heavy input at each Flashing setting, for dev/flashcount.py to count the
flashes (docs/TD_IDIOMS.md A2):

    TD_ARGS='ascii datamosh' dev/td.sh dev/flash.py    # those effects (none named: every one)
    TD_ARGS='clip=b2_plaza' dev/td.sh dev/flash.py     # every effect on another test clip
    TD_ARGS='blob_track beat=none' dev/td.sh dev/flash.py   # no beat: into dev/out/flash/b1_dancer_no_beat
    TD_ARGS='datamosh beat=music' dev/td.sh dev/flash.py    # a dance-tempo beat: b1_dancer_beat-music
    TD_ARGS='showreel View=cycle' dev/td.sh dev/flash.py    # a setting off its default: b1_dancer_View-cycle
    TD_ARGS='bent_cam flashing=off Zoom=1.1' dev/td.sh dev/flash.py   # one Flashing setting only (a quick sweep)
    dev/td.sh --pull dev/out/flash/b1_dancer/done
    uv run --with numpy dev/flashcount.py dev/out/flash/b1_dancer

Each effect is loaded from effects/<n>/<n>.tox (a bundle, bundles/<n>/<n>.tox, when named) into
TDLIB_PARENT and gets dev/testbed.py's input: the test clip and a beat far busier than music, so
every flash it can make is asked for. For each Flashing setting (once, as <n>_fixed, for an effect
without one) it waits SETTLE seconds, then records SECONDS seconds: a GLSL TOP averages the output
in linear light into a 64 x 36 grid of relative luminance and WCAG's red measure, read back every
frame. The clip alone is recorded first (clip_source.npz), so its own changes show.

Writes dev/out/flash/<clip>/<n>_<setting>.npz, then dev/out/flash/<clip>/done. dev/td.sh returns
before the recording ends: wait for done (dev/td.sh --pull) before starting another run, since a new
run clears TDLIB_PARENT and the one still recording then measures the wrong network. Takes about
(1 + settings x effects) x (SETTLE + SECONDS) s, reading a small texture every frame: keep other
work off TouchDesigner meanwhile, since a stalled frame is a frame the recording misses.
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
OUT = os.path.join(_HERE, 'out', 'flash')
SETTLE, SECONDS = 2.0, 10.0
GRID = (64, 36)

METER = """// Average the input over each output cell in linear light: r = relative luminance,
// g = WCAG's saturated-red measure, (R - G - B) x 320 where R / (R + G + B) >= 0.8.
out vec4 fragColor;
vec3 linear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
void main()
{
    vec2 cell = uTD2DInfos[0].res.zw / uTDOutputInfo.res.zw;
    ivec2 lo = ivec2(floor((gl_FragCoord.xy - 0.5) * cell));
    ivec2 hi = ivec2(floor((gl_FragCoord.xy + 0.5) * cell));
    vec2 sum = vec2(0.0);
    float n = 0.0;
    for (int y = lo.y; y < hi.y; y++)
        for (int x = lo.x; x < hi.x; x++) {
            vec3 c = linear(clamp(texelFetch(sTD2DInputs[0], ivec2(x, y), 0).rgb, 0.0, 1.0));
            float s = c.r + c.g + c.b;
            float red = (s > 0.0 && c.r / s >= 0.8) ? max((c.r - c.g - c.b) * 320.0, 0.0) : 0.0;
            sum += vec2(dot(c, vec3(0.2126, 0.7152, 0.0722)), red);
            n += 1.0;
        }
    fragColor = TDOutputSwizzle(vec4(sum / max(n, 1.0), 0.0, 1.0));
}
"""


def main():
    host = op(TDLIB_PARENT)
    for o in list(host.children):
        if o.valid:  # destroying an operator also destroys the DATs docked to it
            o.destroy()
    names, opts = test_args(globals().get('TDLIB_ARGS') or [])
    overrides = {k: v for k, v in opts.items() if k[:1].isupper()}
    beat = {'stress': [], 'none': ['no_beat']}.get(opts['beat'], ['beat-' + opts['beat']])
    out = os.path.join(OUT, '_'.join([opts['clip']] + beat + ['{}-{}'.format(k, v) for k, v in overrides.items()]))
    os.makedirs(out, exist_ok=True)
    paths = [p for p in sorted(glob.glob(os.path.join(_ROOT, 'effects', '*', '*.tox')))
             if not names or os.path.splitext(os.path.basename(p))[0] in names]
    paths += [p for p in sorted(glob.glob(os.path.join(_ROOT, 'bundles', '*', '*.tox')))
              if os.path.splitext(os.path.basename(p))[0] in names]  # bundles by name only
    # Only this run's recordings are replaced; other effects' stay for the report.
    for stem in ['clip'] + [os.path.splitext(os.path.basename(p))[0] for p in paths]:
        for f in glob.glob(os.path.join(out, stem + '_*.npz')):
            os.remove(f)
    if os.path.exists(os.path.join(out, 'done')):
        os.remove(os.path.join(out, 'done'))
    clip, beat = testbed(host, opts)
    view = mk(host, nullTOP, 'view', comment='What the meter reads.', at=(400, 0))
    meter = glsl(host, 'meter', [view], METER, 'Linear luminance and red, per 20 x 20 cell.',
                 res=GRID, fmt='rgba32float', at=(600, 0))

    runs = [('clip', 'source', None, None)]
    for path in paths:
        fx = host.loadTox(path)
        fx.nodeX, fx.nodeY = 0, 300 * len(runs)
        wire(fx, clip, beat)
        for k, v in overrides.items():  # View=cycle and the like: measure a setting other than the default
            if hasattr(fx.par, k):
                setattr(fx.par, k, int(v) if v.lstrip('-').isdigit() else v)
        fx.allowCooking = False
        settings = list(fx.par.Flashing.menuNames) if hasattr(fx.par, 'Flashing') else ['fixed']
        if opts.get('flashing') in settings:  # flashing=off: only that setting, for a quick sweep
            settings = [opts['flashing']]
        runs += [(fx.name, s, fx, s if s != 'fixed' else None) for s in settings]

    state = {'i': -1, 'frames': [], 'start': 0.0}

    def begin(i):
        state['i'], state['frames'] = i, []
        name, setting, fx, flashing = runs[i]
        for o in host.findChildren(type=COMP, depth=1):
            o.allowCooking = o is fx
        view.inputConnectors[0].connect(clip if fx is None else fx.outputConnectors[0])
        if flashing:
            fx.par.Flashing = flashing
        state['start'] = absTime.seconds + SETTLE

    def tick():
        now = absTime.seconds
        if now >= state['start']:
            a = meter.numpyArray()
            state['frames'].append((now, a[:, :, 0].copy(), a[:, :, 1].copy()))
        if now < state['start'] + SECONDS:
            run('args[0]()', tick, delayFrames=1)
            return
        name, setting, _, _ = runs[state['i']]
        t, lum, red = zip(*state['frames'])
        np.savez_compressed(os.path.join(out, '{}_{}.npz'.format(name, setting)), t=np.array(t),
                            lum=np.array(lum, dtype=np.float32), red=np.array(red, dtype=np.float32))
        if state['i'] + 1 < len(runs):
            begin(state['i'] + 1)
            run('args[0]()', tick, delayFrames=1)
            return
        with open(os.path.join(out, 'done'), 'w') as f:
            f.write('\n'.join('{}_{}.npz'.format(n, s) for n, s, _, _ in runs) + '\n')
        for o in list(host.children):
            o.allowCooking = False
        run('[o.destroy() for o in list(args[0].children) if o.valid]', host, delayFrames=2)

    begin(0)
    run('args[0]()', tick, delayFrames=1)
    print('recording {} runs of {:g} s after {:g} s each: {}'.format(
        len(runs), SECONDS, SETTLE, ', '.join('{}_{}'.format(n, s) for n, s, _, _ in runs)))


main()
