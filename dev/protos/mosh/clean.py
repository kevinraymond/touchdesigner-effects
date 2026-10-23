"""DEV ONLY. Remove every datamosh prototype from TDLIB_PARENT."""
host = op(TDLIB_PARENT)
names = [c.name for c in host.children]
for c in list(host.children):
    c.destroy()
print('destroyed', names)
