"""DEV ONLY. Inside TouchDesigner: save frames of some TOPs over the next seconds, for contact
sheets (dev/sheet.py). exec() this file into a dev script's globals, then call capture():

    exec(compile(open(os.path.join(_ROOT, 'dev', 'capture.py')).read(), 'capture.py', 'exec'), globals())
    capture({'a_trace': op(TDLIB_PARENT + '/proto_a/out'), 'b_hud': ...},
            os.path.join(_ROOT, 'dev', 'out', 'blob', 'round1'), at=(1, 2, 4, 6))

It saves <out_dir>/<name>_<i>.png for every TOP at each time (seconds after the call, timed by
the wall clock so dropped frames don't shift it), then writes <out_dir>/done listing the files.
The frames are saved after dev/td.sh has returned; collect them with

    dev/td.sh --pull dev/out/blob/round1/done

Options:
  keep_cooking=True   cook the TOPs every frame until the last capture, for stateful networks
                      (feedback, trackers) that nothing views and so would otherwise stall
  when=fn, events=N   also save <name>_event<k>.png on the first N frames where fn() is true
                      (a beat, a cut), at most one per 10 frames

Keep `at` short (a few seconds apart, under a minute in all): other sessions share this
TouchDesigner.
"""

import os


def capture(tops, out_dir, at=(1, 2, 4, 6), keep_cooking=False, when=None, events=4):
    os.makedirs(out_dir, exist_ok=True)
    done = os.path.join(out_dir, 'done')
    if os.path.exists(done):
        os.remove(done)
    saved = []

    def shoot(i):
        for name, top in tops.items():
            path = os.path.join(out_dir, '{}_{}.png'.format(name, i))
            top.save(path)
            saved.append(os.path.basename(path))
        if i == len(at) - 1:
            with open(done, 'w') as f:
                f.write('\n'.join(saved) + '\n')

    for i, seconds in enumerate(at):
        run('args[0](args[1])', shoot, i, delayMilliSeconds=int(seconds * 1000))

    if keep_cooking or when:
        state = {'events': 0, 'cooldown': 0, 'end': absTime.seconds + max(at) + 0.5}

        def tick():
            if keep_cooking:
                for top in tops.values():
                    top.cook()
            state['cooldown'] -= 1
            if when and state['events'] < events and state['cooldown'] <= 0 and when():
                for name, top in tops.items():
                    top.save(os.path.join(out_dir, '{}_event{}.png'.format(name, state['events'])))
                state['events'] += 1
                state['cooldown'] = 10
            if absTime.seconds < state['end']:
                run('args[0]()', tick, delayFrames=1)

        tick()
    print('capturing {} TOPs at {} s into {}'.format(len(tops), list(at), out_dir))
