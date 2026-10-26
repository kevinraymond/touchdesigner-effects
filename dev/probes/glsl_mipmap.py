"""DEV ONLY. Does a GLSL TOP mipmap its inputs, so textureLod() can read a box-averaged level? Prints its input
filter parameter's choices, then reads level 3 of a 1280 x 720 checkerboard of 1-pixel squares (gray 0.5 if the
level averages 8 x 8 blocks, 0 or 1 if it doesn't) with each choice."""
host = op(TDLIB_PARENT)
for o in list(host.children):
    o.destroy()
board = host.create(rampTOP, 'board')
board.par.outputresolution = 'custom'
board.par.resolutionw, board.par.resolutionh = 1280, 720
g0 = host.create(glslTOP, 'checker')
g0.inputConnectors[0].connect(board)
[d for d in g0.docked if d.name.endswith('_pixel')][0].text = (
    'out vec4 fragColor;\nvoid main(){ ivec2 p = ivec2(gl_FragCoord.xy); fragColor = vec4(vec3(float((p.x + p.y) % 2)), 1.0); }\n')
g = host.create(glslTOP, 'lod')
g.inputConnectors[0].connect(g0)
[d for d in g.docked if d.name.endswith('_pixel')][0].text = (
    'out vec4 fragColor;\nvoid main(){ fragColor = vec4(textureLod(sTD2DInputs[0], vUV.st, 3.0).rgb, 1.0); }\n')
pars = [p for p in g.pars() if 'filter' in p.name.lower() or 'smooth' in p.label.lower() or 'mipmap' in p.name.lower()]
for p in pars:
    print(p.name, p.label, p.menuNames if p.isMenu else p.val)
for p in pars:
    if p.isMenu:
        for v in p.menuNames:
            p.val = v
            g.cook(force=True)
            print(p.name, v, [round(x, 3) for x in g.sample(x=640, y=360)], g.errors() or g.warnings() or 'ok')
