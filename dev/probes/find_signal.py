"""DEV ONLY. Inside TouchDesigner: list every Fosfora signal output (an out_signal CHOP) in the
project and whether it is live: everything up its path cooking, and its last heartbeat (1 a second)
under 1.5 s old. A copy whose parent is bypassed holds its last values, online = 1 included, so a
frozen online means the component stopped, not Fosfora. Changes nothing.

    dev/td.sh dev/probes/find_signal.py
"""


def live(comp):
    """(cooking: every COMP from comp up allows cooking, seconds since its last heartbeat or None)."""
    cooking, o = True, comp
    while o is not None and o.path != '/':
        cooking = cooking and o.allowCooking
        o = o.parent()
    ext = getattr(comp.ext, 'FosforaSignalExt', None)
    at = getattr(ext, 'status_at', None) if ext is not None else None
    return cooking, (absTime.seconds - at) if at is not None else None


for o in op('/').findChildren(name='out_signal', type=CHOP):
    names = [c.name for c in o.chans()]
    cooking, age = live(o.parent())
    print(o.path, 'LIVE' if cooking and age is not None and age < 1.5 else 'STALE',
          '(cooking {}, heartbeat {})'.format(cooking, 'none' if age is None else '{:.1f} s ago'.format(age)),
          {n: round(o[n].eval(), 2) for n in ('online', 'uptime', 'beat_count', 'energy') if n in names})
