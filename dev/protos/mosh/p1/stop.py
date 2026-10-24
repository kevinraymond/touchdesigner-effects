"""DEV ONLY (datamosh pass 1): nothing in TDLIB_PARENT cooks or plays: every COMP off, the clip paused."""
host = op(TDLIB_PARENT)
for c in host.findChildren(type=COMP, depth=1):
    c.allowCooking = False
clip = host.op('clip')
if clip is not None:
    clip.par.play = False
print('stopped', [c.name for c in host.children], 'cooking:', [c.name for c in host.findChildren(type=COMP, depth=1) if c.allowCooking])
