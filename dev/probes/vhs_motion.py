"""DEV ONLY probe: the speed field VHS + CRT's plasma reads (lib flow_speed()'s motion), in output pixels per
panel frame, while dev/protos/vhs_crt/look.py's build runs: TD_ARGS='' dev/td.sh dev/probes/vhs_motion.py"""
import numpy as np
fx = op(TDLIB_PARENT + '/vhs_crt')
m = fx.op('motion')
a = m.numpyArray()
src = fx.op('source')
scale = src.width / m.width
v = np.hypot(a[..., 0], a[..., 1]) * scale / 60.0
print('motion', m.width, m.height, 'px/frame: median {:.2f} p90 {:.2f} p99 {:.2f} max {:.2f}'.format(
    *np.percentile(v, [50, 90, 99]), v.max()))
