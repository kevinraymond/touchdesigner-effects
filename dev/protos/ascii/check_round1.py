"""DEV ONLY. Cook the ASCII round-1 network once and print every error and warning (a GLSL
compile error shows as a warning), then stop it cooking again."""
r = op(TDLIB_PARENT + '/r1')
r.allowCooking = True
bad = 0
for o in r.children:
    if o.isTOP or o.isCHOP:
        o.cook(force=True)
        msg = (o.errors() + ' ' + o.warnings()).strip()
        if msg:
            bad += 1
            print(o.name, '::', msg[:600])
for o in r.findChildren(type=infoDAT):
    t = o.text.strip()
    if 'ERROR' in t.upper():
        print(o.name, t[:800])
print('checked', len(r.children), 'ops,', bad, 'with messages')
r.allowCooking = False
