"""DEV ONLY. Remove the (empty) TDLIB_PARENT COMP that dev/td.sh created for the mosh prototypes."""
p = op(TDLIB_PARENT)
left = [c.name for c in p.children]
if left:
    print('not removed: still holds', left)
else:
    p.destroy()
    print('removed', TDLIB_PARENT)
