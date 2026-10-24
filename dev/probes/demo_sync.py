"""DEV ONLY. Are /tdlib_demo's clip and clip_depth on the same frame? Reads both (pulling clip_depth
once), read-only otherwise. dev/td.sh dev/probes/demo_sync.py"""
d = op('/tdlib_demo')
host = op(TDLIB_PARENT)
probe = host.op('sync_info') or host.create(infoCHOP, 'sync_info')
probe.par.op = d.op('clip_depth').path
d.op('clip_depth').cook(force=True)
probe.cook(force=True)
print('clip index', round(d.op('clip_info')['index'].eval(), 2), '| clip_depth index', round(probe['index'].eval(), 2),
      '| clip_depth playmode', d.op('clip_depth').par.playmode.eval(), '| Effect', d.par.Effect.eval())
probe.destroy()
