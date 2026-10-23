"""DEV ONLY. TouchDesigner's frame rate over 2 s, and whether the prototypes are cooking."""
import os, time
OUTF = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'dev', 'out', 'mosh', 'fps.txt')
start = (time.time(), absTime.frame)
cooking = [c.name for c in op(TDLIB_PARENT).children if c.allowCooking]
def done(start, cooking):
    t, f = time.time(), absTime.frame
    open(OUTF, 'w').write('fps {:.1f} over {:.1f} s; cookRate {}; mosh comps cooking: {}\n'.format(
        (f - start[1]) / (t - start[0]), t - start[0], project.cookRate, cooking))
run('args[0](args[1], args[2])', done, start, cooking, delayMilliSeconds=2000)
