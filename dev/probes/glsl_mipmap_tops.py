"""DEV ONLY. Does a GLSL TOP with Input Smoothness Mipmap mipmap the inputs it takes through its TOPs parameter
(sTD2DInputs[3] and on) as it does its wired ones? Reads level 3 of a checkerboard of 1-pixel squares (gray 0.5 if
the level averages 8 x 8 blocks, 0 or 1 if it doesn't) through input 0 and, from a second checkerboard TOP that is
wired nowhere else, through input 3; with Input Extend Mode UV Hold and Repeat. Each value is written to all four
channels of its own output, since TOP.sample() can misplace channels of a 32-bit float output (docs/BUILDING.md)."""
host = op(TDLIB_PARENT)
for o in list(host.children):
    o.destroy()
board = host.create(glslTOP, 'checker')
board.par.outputresolution = 'custom'
board.par.resolutionw, board.par.resolutionh = 512, 512
[d for d in board.docked if d.name.endswith('_pixel')][0].text = (
    'out vec4 fragColor;\nvoid main(){ ivec2 p = ivec2(gl_FragCoord.xy); fragColor = vec4(vec3(float((p.x + p.y) % 2)), 1.0); }\n')
board2 = host.create(glslTOP, 'checker2')
board2.par.outputresolution = 'custom'
board2.par.resolutionw, board2.par.resolutionh = 512, 512
[d for d in board2.docked if d.name.endswith('_pixel')][0].text = [d for d in board.docked if d.name.endswith('_pixel')][0].text
blank = host.create(constantTOP, 'blank')
for which in (0, 3):
    g = host.create(glslTOP, 'lod{}'.format(which))
    for i in range(3):
        g.inputConnectors[i].connect(board if i == 0 else blank)
    g.par.tops = 'checker2'
    [d for d in g.docked if d.name.endswith('_pixel')][0].text = (
        'out vec4 fragColor;\nvoid main(){ fragColor = vec4(textureLod(sTD2DInputs[%d], vUV.st, 3.0).rrr, 1.0); }\n' % which)
    for ext in ('hold', 'repeat'):
        g.par.inputextenduv = ext
        for f in ('linear', 'mipmap'):
            g.par.inputfiltertype = f
            g.cook(force=True)
            print('input', which, 'extend', ext, 'filter', f, 'level 3 reads', round(g.sample(x=200, y=200)[0], 3),
                  g.errors() or g.warnings() or 'ok')
