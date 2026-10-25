"""DEV ONLY probe: a GLSL TOP in compute mode as a line sorter (2025.33230), for Pixel Sort. Which parameters set the
mode and the dispatch size, which DATs does it dock, does shared memory with barrier() work (MoltenVK on the Mac),
how large a workgroup does it take, does imageStore() scatter, and what does a whole-row bitonic sort of a
1280 x 720 picture cost on the GPU? Steps frames itself and writes dev/out/probe_cs/result.txt, then done:

    dev/td.sh dev/probes/compute_sort.py && dev/td.sh --pull dev/out/probe_cs/done"""
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
host = op(TDLIB_PARENT)
out_dir = os.path.join(_ROOT, 'dev', 'out', 'probe_cs')
os.makedirs(out_dir, exist_ok=True)
for f in ('done', 'result.txt'):
    if os.path.exists(os.path.join(out_dir, f)):
        os.remove(os.path.join(out_dir, f))
for o in list(host.children):
    if o.valid and o.name.startswith('probe_cs'):
        o.destroy()
lines = []
W, H = 1280, 720

# Each workgroup sorts one row by luma: keys (luma 10 bits, then x 11 bits) in shared memory, a bitonic network
# over 2048 slots (pads sort last), then each pixel of the row gathers the color its key came from. With SCATTER the
# row is written mirrored (x -> W-1-x), to see that imageStore() writes where it's told, not where it was invoked.
SHADER = '''layout (local_size_x = NT, local_size_y = 1) in;
shared uint s[2048];
void main() {
    uint t = gl_LocalInvocationID.x;
    int row = int(gl_WorkGroupID.y);
    int w = textureSize(sTD2DInputs[0], 0).x;
    for (uint i = t; i < 2048u; i += NTU) {
        uint key = 0xFFFFFFFFu;
        if (int(i) < w) {
            vec3 c = texelFetch(sTD2DInputs[0], ivec2(int(i), row), 0).rgb;
            uint v = uint(clamp(dot(c, vec3(0.2126, 0.7152, 0.0722)), 0.0, 1.0) * 1023.0 + 0.5);
            key = (v << 11) | i;
        }
        s[i] = key;
    }
    memoryBarrierShared();
    barrier();
    for (uint k = 2u; k <= 2048u; k <<= 1) {
        for (uint j = k >> 1; j > 0u; j >>= 1) {
            for (uint p = t; p < 1024u; p += NTU) {
                uint i = ((p & ~(j - 1u)) << 1) | (p & (j - 1u));
                uint l = i | j;
                bool up = (i & k) == 0u;
                uint a = s[i];
                uint b = s[l];
                if ((a > b) == up) { s[i] = b; s[l] = a; }
            }
            memoryBarrierShared();
            barrier();
        }
    }
    for (uint i = t; int(i) < w; i += NTU) {
        int o = int(s[i] & 2047u);
        vec4 c = texelFetch(sTD2DInputs[0], ivec2(o, row), 0);
        int x = SCATTER ? w - 1 - int(i) : int(i);
        imageStore(mTDComputeOutputs[0], ivec2(x, row), TDOutputSwizzle(c));
    }
}
'''

g0 = host.create(glslTOP, 'probe_cs_pars')
lines.append('docked on create: {}'.format([d.name for d in g0.docked]))
keys = ('mode', 'dispatch', 'compute', 'dat', 'access', 'version', 'glsl', 'shader', 'res', 'format')
for p in g0.pars():
    if any(k in p.name.lower() for k in keys):
        lines.append('  par {} ({}) = {!r}{}'.format(p.name, p.label, p.eval(),
                                                     ' menu {}'.format(p.menuNames) if p.isMenu else ''))
mode_par = next((p for p in g0.pars() if p.isMenu and 'compute' in ' '.join(p.menuNames).lower()), None)
lines.append('mode par: {}'.format(mode_par and (mode_par.name, mode_par.menuNames)))
if mode_par is not None:
    mode_par.val = next(n for n in mode_par.menuNames if 'compute' in n.lower())
    lines.append('docked after compute mode: {}'.format([d.name for d in g0.docked]))
    for p in g0.pars():
        if any(k in p.name.lower() for k in keys):
            lines.append('  par {} ({}) = {!r}'.format(p.name, p.label, p.eval()))

noise = host.create(noiseTOP, 'probe_cs_noise')
noise.par.outputresolution = 'custom'
noise.par.resolutionw, noise.par.resolutionh = W, H
noise.par.mono = False
noise.par.period = 0.05
noise.par.tz.expr = 'absTime.seconds'
tests = {}
for nt, scatter in ((1024, False), (512, False), (256, False), (512, True)):
    name = 'probe_cs_{}{}'.format(nt, '_s' if scatter else '')
    g = host.create(glslTOP, name)
    g.inputConnectors[0].connect(noise)
    if mode_par is not None:
        getattr(g.par, mode_par.name).val = mode_par.val
    dock = [d for d in g.docked if d.isDAT and ('compute' in d.name or 'pixel' in d.name)]
    dat = next((d for d in dock if 'compute' in d.name), dock[0])
    dat.text = SHADER.replace('NTU', '{}u'.format(nt)).replace('NT', str(nt)).replace(
        'SCATTER', 'true' if scatter else 'false')
    for p in g.pars():
        if p.name == 'computedat':
            p.val = dat.name
    g.par.autodispatchsize = False
    g.par.dispatchsizex, g.par.dispatchsizey, g.par.dispatchsizez = 1, H, 1
    tests[name] = (g, nt, scatter, dat.name)
null = host.create(nullTOP, 'probe_cs_view')
state = {'frame': 0, 'gpu': {n: [] for n in tests}}
names = list(tests)
PER = 40  # frames each test is pulled, alone; the first 10 settle


def check(name):
    g, nt, scatter, dat = tests[name]
    a = g.numpyArray()  # rows bottom to top, floats 0-1
    src = noise.numpyArray()
    if a is None or src is None:
        return 'no pixels'
    if scatter:
        a = a[:, ::-1]
    lum = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    q = np.round(np.clip(lum, 0, 1) * 1023)
    sorted_rows = int(np.sum(np.all(np.diff(q, axis=1) >= 0, axis=1)))
    # luma rounded on the GPU and in numpy can differ by one level at a .5: allow that
    near_rows = int(np.sum(np.all(np.diff(q, axis=1) >= -1, axis=1)))
    same = bool(np.allclose(np.sort(a[..., 0], axis=1), np.sort(src[..., 0], axis=1), atol=1e-3))
    return '{} of {} rows sorted ({} to within a level), each row the same colors as the input: {}; dat {}; errors {!r} warnings {!r}'.format(
        sorted_rows, a.shape[0], near_rows, same, dat, g.errors(), g.warnings())


def tick():
    i, f = divmod(state['frame'], PER)
    state['frame'] += 1
    if i < len(names):
        g = tests[names[i]][0]
        if f == 0:
            null.inputConnectors[0].connect(g)
        null.cook()
        if f >= 10 and g.cookAbsFrame >= absTime.frame - 1:
            state['gpu'][names[i]].append(getattr(g, 'gpuCookTime', 0.0) or 0.0)
        run('args[0]()', tick, delayFrames=1)
        return
    for o, *_rest in tests.values():
        o.cook(force=True)
    if f < 3:
        run('args[0]()', tick, delayFrames=1)
        return
    for name in tests:
        gpu = state['gpu'][name]
        lines.append('{}: {}; GPU {:.3f} ms mean, {:.3f} max over {} frames'.format(
            name, check(name), sum(gpu) / max(len(gpu), 1), max(gpu or [0]), len(gpu)))
    open(os.path.join(out_dir, 'result.txt'), 'w').write('\n'.join(lines) + '\n')
    open(os.path.join(out_dir, 'done'), 'w').write('result.txt\n')
    null.inputConnectors[0].disconnect()
    print('\n'.join(lines))


run('args[0]()', tick, delayFrames=1)
print('probe_cs running: pull dev/out/probe_cs/done')
