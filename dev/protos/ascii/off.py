"""DEV ONLY. Stop everything in TDLIB_PARENT from cooking or playing (the Mac is shared): the test
movies and audio files at its top level paused, every COMP's cooking off. Never touches parameters
inside an effect (pausing the effect's own sample Movie File In blanks it).

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/off.py
"""


def off(host):
    for o in host.findChildren(depth=1):
        if o.OPType == 'moviefileinTOP':
            o.par.play = False
        if o.OPType == 'audiofileinCHOP':
            o.par.play = False
    for o in host.findChildren(depth=1):
        if o.isCOMP:
            o.allowCooking = False
    return [o.name for o in host.findChildren(depth=1)]


if __name__ == '__tdlib__' and __file__.endswith('off.py'):
    print('off in', TDLIB_PARENT, off(op(TDLIB_PARENT)))
