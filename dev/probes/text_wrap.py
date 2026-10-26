# DEV ONLY probe: does a Text DAT wrap long lines in its viewer? Its Word Wrap parameter's menu and default.
host = op(TDLIB_PARENT)
t = host.create(textDAT, 'wrap_probe')
p = t.par.wordwrap
print('Word Wrap menu:', list(zip(p.menuNames, p.menuLabels)), 'default', p.default, 'page', p.page.name)
t.destroy()
