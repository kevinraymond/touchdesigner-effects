# DEV ONLY probe: is the Showreel in /tdlib_demo, wired like the effects and on the Effect menu?
d = op('/tdlib_demo')
s = d.op('showreel')
print('menu:', list(d.par.Effect.menuNames))
print('showreel inputs:', [[c.owner.name for c in ic.connections] for ic in s.inputConnectors], 'node', s.nodeX, s.nodeY,
      s.nodeWidth, s.nodeHeight, 'viewer', s.viewer, 'Flashing', s.par.Flashing.eval(), 'View', s.par.View.eval())
print('effect showing:', d.par.Effect.eval())
