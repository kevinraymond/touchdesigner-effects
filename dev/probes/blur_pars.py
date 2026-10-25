"""DEV ONLY. The Blur TOP's parameters and their defaults (2025.33230), for VHS + CRT's glow."""
host = op(TDLIB_PARENT)
b = host.create(blurTOP, 'probe_blur')
for p in b.pars():
    if p.page is not None and p.page.name not in ('Common',):
        print(p.page.name, p.name, repr(p.label), p.default, p.menuNames if p.isMenu else '')
b.destroy()
