"""DEV ONLY. The Count CHOP's parameters and their defaults (2025.33230), for Schlieren's bars: it counts the bars since
the effect started, a step at a time, where audio_in()'s bar_count can jump by a whole song's worth when a signal is
wired in."""
host = op(TDLIB_PARENT)
c = host.create(countCHOP, 'probe_count')
for p in c.pars():
    if p.page is not None and p.page.name not in ('Common',):
        print(p.page.name, p.name, repr(p.label), p.default, p.menuNames if p.isMenu else '')
c.destroy()
