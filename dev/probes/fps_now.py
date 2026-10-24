# DEV ONLY probe: TouchDesigner's frame rate right now, from a Perform CHOP over 2 seconds.
import os
host = op(TDLIB_PARENT)
p = host.op('probe_fps') or host.create(performCHOP, 'probe_fps')
out = os.path.expanduser('~/tdlib/dev/out/fps_now.txt')
if os.path.exists(out):
    os.remove(out)
samples = []
def tick(n):
    p.cook(force=True)
    samples.append((p['fps'].eval(), p['msec'].eval() if 'msec' in [c.name for c in p.chans()] else -1))
    if n < 120:
        run('args[0](args[1])', tick, n + 1, delayFrames=1)
        return
    fps = [a for a, _ in samples[10:]]
    cooking = [c.path for c in op('/').findChildren(type=COMP, depth=1) if c.name.startswith('tdlib')]
    open(out, 'w').write('fps min {:.1f} mean {:.1f} max {:.1f}; cook rate {}; tdlib roots {}\n'.format(
        min(fps), sum(fps) / len(fps), max(fps), project.cookRate, cooking))
    p.destroy()
tick(0)
