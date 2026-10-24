# DEV ONLY probe: what is cooking in the tdlib roots, the slowest operators, and pending run() calls.
import time
rows = []
for root in [c for c in op('/').findChildren(type=COMP, depth=1) if c.name.startswith('tdlib')]:
    for o in [root] + root.findChildren():
        try:
            age = absTime.frame - o.cookAbsFrame
        except Exception:
            continue
        cpu = getattr(o, 'cpuCookTime', 0) or 0
        gpu = getattr(o, 'gpuCookTime', 0) or 0
        if age < 120 and o.family in ('TOP', 'CHOP', 'SOP', 'DAT', 'POP'):
            rows.append((cpu + gpu, cpu, gpu, age, o.path, o.OPType))
rows.sort(reverse=True)
print('ops cooked in the last 2 s:', len(rows))
for t, cpu, gpu, age, path, kind in rows[:15]:
    print('{:8.1f} ms cpu {:8.1f} gpu {:6.1f}  {:4d} frames ago  {} ({})'.format(t, cpu, gpu, age, path, kind))
print('pending runs:', len(runs))
for r in list(runs)[:20]:
    try:
        print('  ', r.source[:120].replace('\n', ' '), '| delay frames', getattr(r, 'remainingFrames', '?'), 'ms', getattr(r, 'remainingMilliseconds', '?'))
    except Exception as e:
        print('  ', r, e)
