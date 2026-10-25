"""DEV ONLY. The point cloud prototype's splat pass (dev/protos/point_cloud/look.py): its pixel
format and a few pixels, to see whether the added-up weights clamp. dev/td.sh dev/probes/pass_format.py"""
host = op(TDLIB_PARENT)
acc, mat = host.op('pass_d_splats'), host.op('matacc_d_splats')
print('format par', acc.par.format.eval(), '| pixelFormat', getattr(acc, 'pixelFormat', '?'))
print('mat blend', [(p, getattr(mat.par, p).eval()) for p in ('blending', 'blendop', 'srcblend', 'destblend', 'blendopa', 'srcblenda', 'destblenda', 'premultrgbbyalpha')])
print('pass premult', acc.par.premultrgbbyalpha.eval())
for x, y in ((150, 500), (300, 450), (640, 360), (900, 200)):
    print((x, y), [round(v, 3) for v in acc.sample(x=x, y=y)])
