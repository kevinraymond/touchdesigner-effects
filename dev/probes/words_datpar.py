"""DEV ONLY probe for Words (board #4673), 2025.33230: which paths a COMP's own DAT parameter resolves (its child
'text'?), and what eval() and val give for each, so the Text parameter can default to the built-in text."""
host = op(TDLIB_PARENT)
for o in list(host.children):
    if o.valid and o.name.startswith('probe_dp'):
        o.destroy()
c = host.create(baseCOMP, 'probe_dp')
c.create(textDAT, 'text').text = 'inside'
host.create(textDAT, 'probe_dp_sibling')
pg = c.appendCustomPage('P')
p = pg.appendDAT('Text', label='Text')[0]
for v in ('text', './text', 'probe_dp/text', '../probe_dp/text', 'probe_dp_sibling', ''):
    p.val = v
    e = p.eval()
    print(repr(v), '->', e.path if e is not None else None, '| val', repr(p.val))
p.default = 'text'
p.val = 'text'
print('style', p.style, 'default', repr(p.default))
p.expr = "me.op('text')"
print('expr me.op:', p.eval())
p.expr = "op('text')"
print('expr op:', p.eval())
