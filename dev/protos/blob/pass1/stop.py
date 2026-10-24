# DEV ONLY (blob_track pass 1): stop everything in /tdlib_dev_blob cooking; drop the test copies.
host = op(TDLIB_PARENT)
gone = []
for c in list(host.findChildren(depth=1)):
    if c.name.startswith('v_') or c.name in ('rig', 'probe_api', 'probe_chops'):
        gone.append(c.name)
        c.destroy()
for c in host.findChildren(depth=1):
    if c.isCOMP:
        c.allowCooking = False
print('removed', gone, '| cooking off:', [(c.name, c.allowCooking) for c in host.findChildren(depth=1)])
