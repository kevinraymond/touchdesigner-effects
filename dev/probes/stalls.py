# DEV ONLY probe: every frame's wall-clock length for 45 s; frames over 50 ms go to
# dev/out/stalls.txt with the time they ended, to match against what ran then.
import os, time
out = os.path.expanduser('~/tdlib/dev/out/stalls.txt')
if os.path.exists(out):
    os.remove(out)
state = {'prev': time.time(), 'end': time.time() + 30, 'gaps': [], 'frames': 0}
def tick():
    now = time.time()
    gap = now - state['prev']
    state['prev'] = now
    state['frames'] += 1
    if gap > 0.05:
        state['gaps'].append('{}.{:03d} {:6.0f} ms'.format(time.strftime('%H:%M:%S', time.localtime(now)), int(now % 1 * 1000), gap * 1000))
    if now < state['end']:
        run('args[0]()', tick, delayFrames=1)
        return
    total = sum(float(g.split()[1]) for g in state['gaps']) / 1000
    open(out, 'w').write('{} frames in 30 s; {} frames over 50 ms, {:.1f} s lost in them\n{}\n'.format(
        state['frames'], len(state['gaps']), total, '\n'.join(state['gaps'])))
run('args[0]()', tick, delayFrames=1)
print('logging frame times for 45 s from', time.strftime('%H:%M:%S'))
