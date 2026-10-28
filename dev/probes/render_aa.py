"""DEV ONLY. The Render TOP's anti-aliasing menu and what Lens Flare's render is set to (2025.33230).
dev/td.sh dev/probes/render_aa.py"""
r = op(TDLIB_PARENT + '/lens_flare/render')
print('antialias', r.par.antialias.menuNames, '->', r.par.antialias.eval(), '| default', r.par.antialias.default)
print('ghost instances', op(TDLIB_PARENT + '/lens_flare/ghost_geo').par.numinstances.eval())
for p in r.pars():
    if p.isMenu and p.page is not None and p.page.name not in ('Common',):
        print(' ', p.name, p.eval(), list(p.menuNames)[:8])
