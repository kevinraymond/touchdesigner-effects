"""DEV ONLY. Print the Info DAT of every GLSL TOP in TDLIB_PARENT's pencil that warns or errs (where its shader
fails to compile): dev/td.sh dev/protos/pencil/info.py"""
fx = op(TDLIB_PARENT).op('pencil')
for o in fx.findChildren(type=glslTOP):
    if o.warnings() or o.errors():
        for d in o.docked:
            if d.OPType == 'infoDAT':
                d.cook(force=True)
                print('==', o.name)
                print(d.text[:3000])
