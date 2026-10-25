"""DEV ONLY probe: when does a Texture 3D TOP write a slice (2025.33230)? With a still input, with a 16 fps movie in a
60 fps project, with Replace Single and a Replace Index that changes every frame, and with Active off. Also: does a
TOP report its GPU memory? A GLSL TOP pulls each one every frame (a time uniform) and records what it sees.

    dev/td.sh dev/probes/texture3d_writes.py && dev/td.sh --pull dev/out/probe_t3w/done"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
host = op(TDLIB_PARENT)
out_dir = os.path.join(_ROOT, 'dev', 'out', 'probe_t3w')
os.makedirs(out_dir, exist_ok=True)
for f in ('done', 'result.txt'):
    if os.path.exists(os.path.join(out_dir, f)):
        os.remove(os.path.join(out_dir, f))
for o in list(host.children):
    if o.name.startswith('probe_t3w'):
        o.destroy()
N = 16
lines = []
start = absTime.frame

# Each pixel x reads slice x's red (what the source held when it was written) and the GLSL TOP's time uniform makes
# it cook, and so pull its input, every frame.
SHADER = '''uniform float uT;
out vec4 fragColor;
void main() {
    int i = int(gl_FragCoord.x);
    vec4 c = texelFetch(sTD3DInputs[0], ivec3(0, 0, i), 0);
    fragColor = vec4(c.r, c.g, uT, 1.0);
}
'''


def reader(name, t3):
    g = host.create(glslTOP, 'probe_t3w_g_' + name)
    g.inputConnectors[0].connect(t3)
    g.par.outputresolution = 'custom'
    g.par.resolutionw, g.par.resolutionh = N, 1
    g.par.format = 'rgba32float'
    g.seq.vec.numBlocks = 1
    g.par.vec0name = 'uT'
    g.par.vec0valuex.expr = 'absTime.frame % 4096'
    [d for d in g.docked if d.name.endswith('_pixel')][0].text = SHADER
    return g


def history(name, src, **pars):
    t = host.create(texture3dTOP, 'probe_t3w_' + name)
    t.inputConnectors[0].connect(src)
    t.par.cachesize = N
    for k, v in pars.items():
        if hasattr(v, 'startswith') and v.startswith('='):
            getattr(t.par, k).expr = v[1:]
        else:
            setattr(t.par, k, v)
    return t, reader(name, t)


# A still input: a constant red of 0.5.
still = host.create(constantTOP, 'probe_t3w_still')
still.par.outputresolution = 'custom'
still.par.resolutionw, still.par.resolutionh = 4, 4
still.par.format = 'rgba32float'
still.par.colorr = 0.5
# A 16 fps movie (the test clips are 16 fps) in the project's 60 fps, its red channel tagged with the movie's own
# frame index through a Level TOP? Simpler: a Constant whose red is the movie's index, cooking only when it changes.
movie = host.create(moviefileinTOP, 'probe_t3w_movie')
movie.par.file = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')
movie.par.outputresolution = 'custom'
movie.par.resolutionw, movie.par.resolutionh = 4, 4
# The movie's frame index into red, from a GLSL TOP reading the movie (so it cooks when the movie does).
tag = host.create(glslTOP, 'probe_t3w_tag')
tag.inputConnectors[0].connect(movie)
tag.par.format = 'rgba32float'
tag.seq.vec.numBlocks = 1
tag.par.vec0name = 'uIdx'
tag.par.vec0valuex.expr = "op('probe_t3w_movie').par.index.eval() if hasattr(op('probe_t3w_movie').par, 'index') else 0"
[d for d in tag.docked if d.name.endswith('_pixel')][0].text = '''uniform float uIdx;
out vec4 fragColor;
void main() { vec4 c = texture(sTD2DInputs[0], vUV.st); fragColor = vec4(c.r, c.g, 0, 1); }
'''
# A per-frame counter source, for Replace Single and Active.
count = host.create(constantTOP, 'probe_t3w_count')
count.par.outputresolution = 'custom'
count.par.resolutionw, count.par.resolutionh = 4, 4
count.par.format = 'rgba32float'
count.par.colorr.expr = 'absTime.frame - {}'.format(start)

chains = {
    'still': history('still', still),
    'movie': history('movie', movie),
    'replace': history('replace', count, replacesingle=True, replaceindex='=(absTime.frame - {}) * 3 % {}'.format(start, N)),
    'active': history('active', count, active='=(absTime.frame - {}) % 4 == 0'.format(start)),
}
lines.append('movie pars: ' + ', '.join('{}={!r}'.format(p.name, p.eval()) for p in movie.pars()
                                        if p.name in ('index', 'play', 'playmode', 'speed', 'cuedframe', 'rate')))


def step(k):
    for name, (t, g) in chains.items():
        g.cook()
        row = [g.sample(x=i, y=0) for i in range(N)]
        lines.append('frame {:2d} {:8s} r: {} | t3 cooks {} | gpuMemory {}'.format(
            k, name, [round(px[0], 3) for px in row], t.totalCooks if hasattr(t, 'totalCooks') else '?',
            getattr(t, 'gpuMemory', '?')))
    if k < 20:
        run('args[0](args[1])', step, k + 1, delayFrames=1)
    else:
        mem = {n: getattr(t, 'gpuMemory', None) for n, (t, g) in chains.items()}
        lines.append('gpuMemory by chain: {}'.format(mem))
        lines.append('t3 attrs with mem: {}'.format([a for a in dir(chains['still'][0]) if 'mem' in a.lower()]))
        with open(os.path.join(out_dir, 'result.txt'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        open(os.path.join(out_dir, 'done'), 'w').close()


run('args[0](args[1])', step, 1, delayFrames=1)
print('probing over 20 frames into', out_dir)
