# DEV ONLY: remove every /tdlib_dev* root COMP the dev loop left in TouchDesigner (/tdlib_demo stays).
gone = []
for c in list(op('/').findChildren(type=COMP, depth=1)):
    if c.valid and c.name.startswith('tdlib_dev'):
        gone.append(c.name)
        c.destroy()
print('removed', gone, '| left:', [c.name for c in op('/').findChildren(type=COMP, depth=1) if c.name.startswith('tdlib')])
