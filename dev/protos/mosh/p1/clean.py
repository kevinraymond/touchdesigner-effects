"""DEV ONLY (datamosh pass 1): remove everything this pass made in TDLIB_PARENT, then TDLIB_PARENT itself."""
host = op(TDLIB_PARENT)
names = [c.name for c in host.children]
for c in list(host.children):
    c.destroy()
host.destroy()
print('destroyed', names, 'and', TDLIB_PARENT, '; still there:', op(TDLIB_PARENT) is not None)
