# DEV ONLY, never part of anything shipped: the Execute DAT dev/td.sh talks to.
# Every 10 frames it checks DIR/cmd.py; when the file changes it runs it and writes what it
# printed (or the traceback) to DIR/out.txt, first line '# <time> abs frame <n> OK|ERROR'.
#
# mbpm2 already runs one: fosfora_dev_watcher in ~/Desktop/fosfora-dev.toe, polling
# ~/fosfora-td-dev (dev/td.sh's default TD_WATCH). This copy is for when that one is gone.
# To install it in a dev project (not a project you ship), paste in the textport:
#
#   w = op('/project1').create(executeDAT, 'tdlib_dev_watcher'); w.text = open('/path/to/dev/watcher.py').read(); w.par.framestart = True
#
# and point dev/td.sh at its folder with TD_WATCH=tdlib-dev (relative to the home folder).
import io, os, sys, time, traceback

DIR = os.path.expanduser('~/tdlib-dev')
CMD = os.path.join(DIR, 'cmd.py')
OUT = os.path.join(DIR, 'out.txt')


def onFrameStart(frame):
	if absTime.frame % 10:
		return
	try:
		mtime = os.stat(CMD).st_mtime
	except OSError:
		return
	if mtime == me.fetch('cmd_mtime', 0.0, search=False):
		return
	me.store('cmd_mtime', mtime)
	buf = io.StringIO()
	saved, sys.stdout = sys.stdout, buf
	ok = True
	try:
		with open(CMD) as f:
			code = compile(f.read(), CMD, 'exec')
		exec(code, dict(globals()))
	except Exception:
		ok = False
		traceback.print_exc(file=buf)
	finally:
		sys.stdout = saved
	with open(OUT, 'w') as f:
		f.write('# {} abs frame {} {}\n'.format(time.strftime('%H:%M:%S'), absTime.frame, 'OK' if ok else 'ERROR'))
		f.write(buf.getvalue())
	return
