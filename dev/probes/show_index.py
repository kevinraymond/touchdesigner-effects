"""DEV ONLY. Inside TouchDesigner: how /tdlib_demo/show's Index is set and what is wired in (it changes nothing)."""

s = op('/tdlib_demo/show')
p = s.par.index
print('index mode {}, expr {!r}, val {!r}, eval {}'.format(p.mode, p.expr, p.val, p.eval()))
print('inputs:', [(c.index, [x.owner.name for x in c.connections]) for c in s.inputConnectors])
c = op('/tdlib_demo/clip').par.play
print('clip file:', op('/tdlib_demo/clip').par.file.eval().rsplit('/', 1)[-1])
print('clip play: mode {}, expr {!r}, eval {}; Demo page Effect {!r}, Play {}'.format(
    c.mode, c.expr, c.eval(), parent_eff if (parent_eff := op('/tdlib_demo').par.Effect.eval()) else None,
    op('/tdlib_demo').par.Play.eval()))
