"""DEV ONLY. The GLSL TOP's CHOP uniform arrays (board #4848, Marbling): its Arrays page is the sequence 'array',
array0name, array0type (float, vec2, vec3, vec4), array0chop, array0arraytype (uniformarray, texturebuffer). Feeds a
Script CHOP of 5 channels x 3 samples (channel c, sample i holds 10 * c + i) as a uniform vec4 array and writes what
the shader reads back: which channel lands in which component, which sample in which element, and whether a fifth
channel is dropped. Writes dev/out/probes/glsl_arrays.txt."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out = os.path.join(_ROOT, 'dev', 'out', 'probes', 'glsl_arrays.txt')
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid:
        o.destroy()
s = host.create(scriptCHOP, 's')
next(d for d in s.docked if d.name.endswith('_callbacks')).text = '''
def onSetupParameters(scriptOp):
    return
def onPulse(par):
    return
def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 3
    for c in range(5):
        ch = scriptOp.appendChan('c{}'.format(c))
        ch.vals = [10.0 * c + i for i in range(3)]
'''
g = host.create(glslTOP, 'g')
g.par.outputresolution = 'custom'
g.par.resolutionw, g.par.resolutionh = 3, 1
g.par.format = 'rgba32float'
g.seq.array.numBlocks = 1
g.par.array0name = 'uArr'
g.par.array0type = 'vec4'
g.par.array0chop = s.path
g.par.array0arraytype = 'uniformarray'
next(d for d in g.docked if d.name.endswith('_pixel')).text = '''uniform vec4 uArr[3];
out vec4 fragColor;
void main() { fragColor = uArr[int(gl_FragCoord.x)]; }
'''


def report():
    a = g.numpyArray()
    lines = ['errors {!r} warnings {!r}'.format(g.errors(), g.warnings())]
    for i in range(3):
        lines.append('element {}: {}'.format(i, ' '.join('{:.1f}'.format(v) for v in a[0, i])))
    open(out, 'w').write('\n'.join(lines) + '\n')


run('args[0]()', report, delayFrames=10)
