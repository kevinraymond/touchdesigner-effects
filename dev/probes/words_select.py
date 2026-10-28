"""DEV ONLY probe for Words (board #4673): the Select DAT's column parameters, and what atlas_spec gives."""
c = op(TDLIB_PARENT).op('words')
s = c.op('atlas_spec')
for p in s.pars():
    if any(k in p.name for k in ('row', 'col', 'extract', 'name')):
        print(p.name, repr(p.eval()), p.menuNames if p.isMenu else '')
s.cook(force=True)
print(s.numRows, s.numCols, s.errors(), s.warnings())
