"""DEV ONLY. A Switch TOP's parameter names and their menus in this build. dev/td.sh dev/probes/switch_pars.py"""
o = op(TDLIB_PARENT).create(switchTOP, 'probe_switch')
for p in o.pars():
    if p.page is not None and p.page.name == 'Switch':
        print(p.name, '|', p.label, '|', list(p.menuNames) if p.isMenu else p.default)
o.destroy()
