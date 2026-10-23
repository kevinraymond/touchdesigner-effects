# DEV ONLY probe: which font files ship inside TouchDesigner, and what the Text TOP offers.
import os
c = app.installFolder + '/Contents'
for d in (c, c + '/Resources', c + '/Resources/tfs', c + '/Resources/tfs/Config'):
    try:
        print(d, '->', sorted(os.listdir(d))[:60])
    except Exception as e:
        print(d, e)
hits = []
for d, subs, files in os.walk(c):
    subs[:] = [s for s in subs if s not in ('Samples', 'site-packages', 'Python.framework')]
    for f in files:
        if f.lower().endswith(('.ttf', '.otf', '.ttc', '.fon', '.pfb', '.woff', '.woff2')):
            hits.append(os.path.join(d, f)[len(c):])
print(len(hits), 'font files')
for h in hits[:60]:
    print(' ', h)
