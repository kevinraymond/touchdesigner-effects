"""DEV ONLY. Inside TouchDesigner: why /tdlib_demo/speaker might not cook (it changes nothing)."""

s = op('/tdlib_demo/speaker')
print('speaker: bypass {}, lock {}, allowCooking {}, display {}, render {}, viewer {}, cook frame {} (now {})'.format(
    s.bypass, s.lock, s.allowCooking, getattr(s, 'display', None), getattr(s, 'render', None), s.viewer,
    s.cookAbsFrame, absTime.frame))
print('pars changed from default:', {p.name: p.eval() for p in s.pars() if not p.isDefault and p.page.name != 'Common'})
print('parent /tdlib_demo: allowCooking {}, bypass {}'.format(s.parent().allowCooking, s.parent().bypass))
print('track -> speaker connected:', [c.owner.name for c in s.inputConnectors[0].connections])
