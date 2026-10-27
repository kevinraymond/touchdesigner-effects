# DEV ONLY probe: a new Trigger CHOP's threshold parameters and defaults (2025.33230), and a Lag CHOP's, for Video
# Vocoder's gate on the bands' jumps.
host = op(TDLIB_PARENT)
t = host.create(triggerCHOP, 'probe_trigger')
l = host.create(lagCHOP, 'probe_lag')
for o in (t, l):
    print(o.OPType, [(p.name, p.default, p.label) for p in o.pars() if p.page is not None and p.page.name in ('Trigger', 'Lag', 'Envelope')][:30])
    o.destroy()
