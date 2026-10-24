# DEV ONLY (blob_track pass 1): read-only look at /tdlib_demo/blob_track; changes nothing.
d = op('/tdlib_demo')
fx = d.op('blob_track') if d else None
print('blob_track', fx is not None, 'allowCooking', fx.allowCooking if fx else None,
      'version', fx.par.Version.eval() if fx else None)
if fx:
    print('inputs', [c.connections[0].owner.name if c.connections else None for c in fx.inputConnectors])
    print('errors', repr(fx.errors(recurse=True)), 'warnings', repr(fx.warnings(recurse=True)))
    print('pars at default', all(p.eval() == p.default for p in fx.customPars if p.mode == ParMode.CONSTANT
                                  and p.style not in ('Pulse', 'Momentary', 'Header') and not p.readOnly))
print('demo pars', [(p.name, p.eval(), list(p.menuNames) if p.isMenu else '') for p in d.customPars] if d else None)
print('cooking in /tdlib_dev_blob', [(c.name, c.allowCooking) for c in op('/tdlib_dev_blob').findChildren(depth=1)])
