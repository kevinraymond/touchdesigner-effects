"""DEV ONLY. Inside TouchDesigner: what /tdlib_demo's beat carries, and what each effect makes of it
(it changes nothing; reading the channels cooks each audio CHOP once).

    dev/td.sh dev/probes/demo_beat.py
"""

d = op('/tdlib_demo')
sig = d.op('fosfora_signal/out_signal')
if sig is not None:
    print('fosfora_signal:', {n: round(sig[n].eval(), 3) for n in ('online', 'beat_count', 'bar_count', 'energy', 'bpm')
                              if sig[n] is not None})
beat = d.op('beat')
print('beat index', beat.par.index.eval(), '(0 Fosfora, 1 track):', beat.numChans, 'channels')
track = d.op('track')
print('track:', track.numChans, 'channels at', track.rate, 'Hz; speaker active', d.op('speaker').par.active.eval())
for name in ('ascii', 'blob_track', 'datamosh'):
    a = d.op(name + '/audio')
    if a is not None and a.numChans:
        print('  {}/audio (cooked {} frames ago):'.format(name, absTime.frame - a.cookAbsFrame),
              {c.name: round(c.eval(), 3) for c in a.chans()})
