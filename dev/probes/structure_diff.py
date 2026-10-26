"""DEV ONLY, plain Python: what changed between two structure dumps (dev/probes/structure_dump.py), other than where
operators sit. Prints every operator added or removed and every field that differs; the Network Boxes (inside of
which the dump skips) show as added operators. Exit status 1 when anything differs.

    uv run dev/probes/structure_diff.py dev/out/structure/before dev/out/structure/after vhs_crt
"""
import json
import os
import sys


def diff(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append('{}.{}: added {!r}'.format(path, k, b[k]))
            elif k not in b:
                out.append('{}.{}: removed (was {!r})'.format(path, k, a[k]))
            else:
                out += diff(a[k], b[k], '{}.{}'.format(path, k))
        return out
    if a != b:
        sa, sb = repr(a), repr(b)
        if len(sa) > 200 or len(sb) > 200:
            return ['{}: differs ({} -> {} characters)'.format(path, len(sa), len(sb))]
        return ['{}: {} -> {}'.format(path, sa, sb)]
    return []


def main():
    before, after, names = sys.argv[1], sys.argv[2], sys.argv[3:]
    changed = False
    for name in names:
        a = json.load(open(os.path.join(before, name + '.json')))
        b = json.load(open(os.path.join(after, name + '.json')))
        print('==', name, len(a), '->', len(b), 'operators')
        for op in sorted(set(a) - set(b)):
            print('  removed', op, a[op]['type'], '(docked to {})'.format(a[op]['dock']) if a[op]['dock'] else '')
            changed = True
        for op in sorted(set(b) - set(a)):
            print('  added', op, b[op]['type'])
            changed = True
        for op in sorted(set(a) & set(b)):
            for line in diff(a[op], b[op], op):
                print(' ', line)
                changed = True
    sys.exit(1 if changed else 0)


main()
