"""DEV ONLY. The compile log of a GLSL TOP inside TDLIB_PARENT (an Info DAT on it, made and removed).
TD_ARGS='particles/sim' dev/td.sh dev/probes/glsl_log.py"""
target = op(TDLIB_PARENT + '/' + TDLIB_ARGS[0])
info = op(TDLIB_PARENT).create(infoDAT, 'glsl_log_tmp')
try:
    info.par.op = target.path
    target.cook(force=True)
    info.cook(force=True)
    print(info.text)
finally:
    info.destroy()
