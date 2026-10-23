"""DEV ONLY. Stop every datamosh prototype cooking (they stay in place for the next shoot)."""
host = op(TDLIB_PARENT)
for c in host.children:
    if c.isCOMP:
        c.allowCooking = False
print('stopped', [c.name for c in host.children])
