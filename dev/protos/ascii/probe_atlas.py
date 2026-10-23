# DEV ONLY probe: how a Text TOP with a Specification DAT places glyphs in cell-sized slots.
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
host = op(TDLIB_PARENT)
if host.op('probe'):
    host.op('probe').destroy()
box = host.create(baseCOMP, 'probe')
box.allowCooking = True
RAMP, CW, CH = '|.:-=+*#%@Mg_', 10, 20
t0 = box.create(textTOP, 'typeface_probe')
t0.par.font = 'Courier New'
print('typeface menu', list(t0.par.typeface.menuNames)[:12], list(t0.par.typeface.menuLabels)[:12])
tops = {}
configs = [('cn_center', 'Courier New', 'center', CH / 2, 16, False),
           ('cn_bottom4', 'Courier New', 'bottom', 4, 16, False),
           ('cn_bold_b5', 'Courier New', 'bottom', 5, 17, True),
           ('menlo_b5', 'Menlo', 'bottom', 5, 16, False),
           ('andale_b5', 'Andale Mono', 'bottom', 5, 16, False)]
for i, (name, font, ay, y, size, bold) in enumerate(configs):
    tab = box.create(tableDAT, 'tab_' + name)
    tab.clear()
    tab.appendRow(['x', 'y', 'text'])
    for k, ch in enumerate(RAMP):
        tab.appendRow([k * CW + CW / 2, y, ch])
    t = box.create(textTOP, name)
    t.par.text = ''
    t.par.specdat = tab.name
    t.par.font = font
    if bold:
        names = list(t.par.typeface.menuNames)
        b = [n for n in names if 'bold' in n.lower()]
        if b:
            t.par.typeface = b[0]
        print(name, 'typeface', t.par.typeface.eval(), names)
    t.par.fontsizexunit = 'pixels'
    t.par.fontsizex = size
    t.par.keepfontratio = True
    t.par.alignx, t.par.aligny = 'center', ay
    t.par.outputresolution = 'custom'
    t.par.resolutionw, t.par.resolutionh = CW * len(RAMP), CH
    tops[name] = t
capture(tops, os.path.join(_ROOT, 'dev', 'out', 'ascii', 'atlas'), at=(0.5,))
run('args[0].allowCooking = False', box, delayMilliSeconds=1500)
