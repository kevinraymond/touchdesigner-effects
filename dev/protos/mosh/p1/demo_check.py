"""DEV ONLY, read-only: is /tdlib_demo/datamosh the current build, clean, wired?"""
import json, os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
fx = op('/tdlib_demo/datamosh')
want = json.load(open(os.path.join(_ROOT, 'effects', 'datamosh', 'datamosh.json')))['tox_sha256']
print('present', fx is not None)
if fx is not None:
    print('sha matches', fx.fetch('tox_sha256', None) == want, 'version', fx.par.Version.eval())
    print('pages', [p.name for p in fx.customPages], 'pars', [p.name for p in fx.customPages[0].pars])
    print('inputs', [[c.owner.name for c in ic.connections] for ic in fx.inputConnectors])
    print('allowCooking', fx.allowCooking, 'errors', repr(fx.errors(recurse=True)), 'warnings', repr(fx.warnings(recurse=True)))
    d = op('/tdlib_demo')
    print('demo Effect', d.par.Effect.eval() if hasattr(d.par, 'Effect') else None, 'Play', d.par.Play.eval() if hasattr(d.par, 'Play') else None)
