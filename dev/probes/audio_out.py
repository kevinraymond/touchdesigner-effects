"""DEV ONLY. Inside TouchDesigner: every Audio Device Out CHOP in the project and what feeds it
(it changes nothing).

    dev/td.sh dev/probes/audio_out.py
"""

now = absTime.frame
for o in op('/').findChildren(type=audiodeviceoutCHOP):
    src = o.inputs[0] if o.inputs else None
    print('{}: active {}, volume {}, device {!r}, cooked {} frames ago, input {}'.format(
        o.path, o.par.active.eval(), o.par.volume.eval(), o.par.device.eval(), now - o.cookAbsFrame,
        src.path if src else None))
t = op('/tdlib_demo/track')
print('track: play {}, file {}, cooked {} frames ago, peak now {:.3f}'.format(
    t.par.play.eval(), t.par.file.eval().rsplit('/', 1)[-1], now - t.cookAbsFrame,
    max(abs(v) for c in t.chans() for v in c.vals) if t.numChans else 0))
for o in op('/').findChildren(type=audiodeviceoutCHOP):
    print('  {} problems: {}; driver {!r}; info: {}'.format(
        o.name, (o.errors() + o.warnings()) or 'none', o.par.driver.eval() if hasattr(o.par, 'driver') else None,
        ', '.join('{}={}'.format(r[0].val, r[1].val) for r in op(o.path + '_probe_info').rows())
        if op(o.path + '_probe_info') else 'no info DAT'))
