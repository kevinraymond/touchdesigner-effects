"""DEV ONLY. Inside TouchDesigner: where the operators at the top level sit (it changes nothing)."""

for o in op('/').children:
    print('{}: x {} y {} w {} h {} viewer {}'.format(o.name, o.nodeX, o.nodeY, o.nodeWidth, o.nodeHeight, o.viewer))
