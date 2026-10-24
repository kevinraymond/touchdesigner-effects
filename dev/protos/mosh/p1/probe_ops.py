"""DEV ONLY (datamosh pass 1). Probe operator behaviors the effect relies on, then measure the
dancer clip's per-frame luma change for 12 s (dev/out/datamosh/probe/)."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())
OUTD = os.path.join(_ROOT, 'dev', 'out', 'datamosh', 'probe')
os.makedirs(OUTD, exist_ok=True)
host = op(TDLIB_PARENT)
for c in list(host.children):
    c.destroy()
lines = []
t = host.create(triggerCHOP, 'pt')
for n in ('trigger', 'releasepulse', 'channame', 'multitrigger', 'threshold', 'threshup'):
    p = getattr(t.par, n)
    lines.append('trigger.{} style={} val={!r} default={!r}'.format(n, p.style, p.eval(), p.default))
t.cook(force=True)
lines.append('trigger no-input chans: {} errors={!r} warnings={!r}'.format([c.name for c in t.chans()], t.errors(), t.warnings()))
lg = host.create(logicCHOP, 'pl')
lines.append('logic convert labels: {}'.format(list(zip(lg.par.convert.menuNames, lg.par.convert.menuLabels))))
lines.append('logic preop labels: {}'.format(list(zip(lg.par.preop.menuNames, lg.par.preop.menuLabels))))
lines.append('absTime has stepSeconds: {}'.format(hasattr(absTime, 'stepSeconds')))
try:
    lines.append('absTime.stepSeconds = {}'.format(absTime.stepSeconds))
except Exception as e:
    lines.append('stepSeconds error {}'.format(e))
sl = host.create(slopeCHOP, 'ps')
lines.append('slope pars: {}'.format([p.name for p in sl.pars() if p.page is not None and p.page.name != 'Common']))
open(os.path.join(OUTD, 'ops.txt'), 'w').write('\n'.join(lines) + '\n')

# The dancer clip's luma change per TD frame vs the previous TD frame, at 1/8.
clip = mk(host, moviefileinTOP, 'clip', 0, 0, file=os.path.expanduser('~/tdlib/private/assets/ready/b1_dancer.mp4'))
lum = glsl(host, 'lum8', 200, 0, [clip], '''
out vec4 fragColor;
void main() {
    vec2 ipx = uTD2DInfos[0].res.xy; float acc = 0.0;
    for (int j = 0; j < 4; j++) for (int i = 0; i < 4; i++)
        acc += dot(texture(sTD2DInputs[0], vUV.st + vec2(float(2*i-3), float(2*j-3)) * ipx).rgb, vec3(0.2126, 0.7152, 0.0722));
    fragColor = vec4(acc / 16.0, 0.0, 0.0, 1.0);
}''', 'x', fmt='rgba32float')
lum.par.outputresolution = 'eighth'
prev = mk(host, cacheTOP, 'lum8p', 400, -100, [lum], cachesize=2, outputindex=-1)
dif = glsl(host, 'diff', 600, 0, [lum, prev], '''
out vec4 fragColor;
void main() {
    float d = abs(texture(sTD2DInputs[0], vUV.st).r - texture(sTD2DInputs[1], vUV.st).r);
    fragColor = vec4(d, step(0.08, d), 0.0, 1.0);
}''', 'x', fmt='rgba32float')
an = mk(host, analyzeTOP, 'an', 800, 0, [dif], op='average', analyzechannel='independent')
tc = mk(host, toptoCHOP, 'tc', 1000, 0, top='an')
ROWS = []


def tick(n):
    tc.cook(force=True)
    ROWS.append('{} {:.4f} {} {:.5f} {:.5f}'.format(absTime.frame, absTime.seconds, int(clip.par.index.eval()) if False else clip.numImages if False else '-', tc['r'][0] if tc.numChans else -1, tc['g'][0] if tc.numChans > 1 else -1))
    if n < 720:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
    else:
        open(os.path.join(OUTD, 'dancer_change.txt'), 'w').write('\n'.join(ROWS) + '\n')
        open(os.path.join(OUTD, 'done'), 'w').write('ok\n')
        for c in list(op(TDLIB_PARENT).children):
            c.destroy()


if os.path.exists(os.path.join(OUTD, 'done')):
    os.remove(os.path.join(OUTD, 'done'))
run('args[0](args[1])', tick, 0, delayFrames=30)
print('\n'.join(lines))
