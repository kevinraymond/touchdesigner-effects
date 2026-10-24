"""DEV ONLY. Read-only: what is in TDLIB_PARENT right now, and is it cooking?"""
host = op(TDLIB_PARENT)
print('frame', absTime.frame, 'children', [(o.name, o.allowCooking if o.isCOMP else None) for o in host.children])
fx = host.op('ascii')
if fx is not None:
    print('ascii out_top cookAbsFrame', fx.op('out_top').cookAbsFrame, 'render', fx.op('render').cookAbsFrame)
import os
print(os.listdir(os.path.expanduser('~/tdlib/dev/out/ascii/pass2')))
