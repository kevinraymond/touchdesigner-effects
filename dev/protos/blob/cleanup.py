# DEV ONLY: remove everything the blob prototypes made in TouchDesigner (TDLIB_PARENT itself).
p = op(TDLIB_PARENT)
if p is not None and p.path == '/tdlib_dev_blob':
    p.destroy()
print('removed /tdlib_dev_blob:', op('/tdlib_dev_blob') is None)
