"""DEV ONLY. Read-only: is /tdlib_demo/ascii there, clean, and idle? Removes the empty TDLIB_PARENT that
dev/td.sh makes for the run."""
fx = op('/tdlib_demo/ascii')
demo = op('/tdlib_demo')
print('ascii', fx is not None and fx.par.Version.eval(), 'errors', repr(fx.errors(recurse=True)),
      'warnings', repr(fx.warnings(recurse=True)))
print('demo Effect', demo.par.Effect.eval() if hasattr(demo.par, 'Effect') else None,
      'Play', demo.par.Play.eval() if hasattr(demo.par, 'Play') else None,
      'render last cooked', absTime.frame - fx.op('render').cookFrame, 'frames ago')
host = op(TDLIB_PARENT)
if host is not None and not host.children:
    host.destroy()
