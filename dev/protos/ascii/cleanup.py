"""DEV ONLY. Remove everything the ASCII prototypes built (the whole TDLIB_PARENT COMP)."""
host = op(TDLIB_PARENT)
names = [o.name for o in host.children]
host.destroy()
print('destroyed', TDLIB_PARENT, 'with', names)
