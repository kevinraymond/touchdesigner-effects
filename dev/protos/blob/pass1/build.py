# DEV ONLY (blob_track pass 1): run the builder, then stop the dev copy cooking (the Mac is shared).
import os
_B = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..',
                                  'effects', 'blob_track', 'build_blob_track.py'))
_ns = dict(globals(), __file__=_B)
exec(compile(open(_B).read(), _B, 'exec'), _ns)
op(TDLIB_PARENT + '/blob_track').allowCooking = False
