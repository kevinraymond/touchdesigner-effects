"""DEV ONLY. Every error and warning inside /tdlib_demo and TDLIB_PARENT, per operator, after
cooking each effect's audio front end and output once (read-only otherwise).
dev/td.sh dev/probes/errors_now.py"""
for root in ('/tdlib_demo', TDLIB_PARENT):
    r = op(root)
    if r is None:
        continue
    for o in r.findChildren(type=scriptCHOP):
        o.cook(force=True)
    for o in [r] + list(r.findChildren()):
        e, w = o.errors(), o.warnings()
        if e or w:
            print(o.path, '| errors:', e, '| warnings:', w)
    print(root, 'checked', len(r.findChildren()), 'operators')
print('demo Effect', op('/tdlib_demo').par.Effect.eval() if op('/tdlib_demo') else None)
