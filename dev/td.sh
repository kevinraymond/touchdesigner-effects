#!/usr/bin/env bash
# DEV ONLY. Run one of this repo's Python files inside TouchDesigner on another machine and
# print what it printed (or its traceback):
#
#   dev/td.sh effects/glow/build_glow.py
#   dev/td.sh dev/selftest.py
#
# It copies the repo to $TD_REPO on $TD_HOST, writes a cmd.py that runs the file into the
# folder a watcher Execute DAT polls ($TD_WATCH), waits for the watcher's out.txt to change,
# prints it, and copies back what the run produced: built .tox files and their manifests,
# and anything under dev/out/ (saved frames). Everything it builds lands in $TD_PARENT, one
# COMP at the root, away from the project the watcher lives in.
#
# The watcher is an Execute DAT that, every few frames, runs cmd.py when its mtime changes
# and writes the output to out.txt: on mbpm2 it is fosfora_dev_watcher (from the Fosfora
# project), so TD_WATCH defaults to its folder. See docs/BUILDING.md.
set -euo pipefail

HOST=${TD_HOST:-kevin@mbpm2}
REPO=${TD_REPO:-tdlib}
WATCH=${TD_WATCH:-fosfora-td-dev}
PARENT=${TD_PARENT:-/tdlib_dev}
WAIT=${TD_WAIT:-120}

[ $# -eq 1 ] || { echo "usage: $0 <repo-relative .py file>" >&2; exit 2; }
root=$(cd "$(dirname "$0")/.." && pwd)
script=$(realpath --relative-to="$root" "$1")
[ -f "$root/$script" ] || { echo "no such file: $script" >&2; exit 2; }

# Sources out; built files stay where they are on both sides until they come back below.
rsync -a --delete --exclude .git --exclude '*.tox' --exclude 'effects/*/*.json' \
  --exclude 'bundles/*/*.json' --exclude dev/out "$root/" "$HOST:$REPO/"

# One ssh: note the watcher's last answer (its first line carries the time and the absolute
# frame, so it changes every run), hand it cmd.py, then wait for a different answer.
ssh "$HOST" "cd $WATCH && before=\$(head -1 out.txt 2>/dev/null); mkdir -p ~/$REPO/dev/out; \
  cat > cmd.py.tmp && mv cmd.py.tmp cmd.py; \
  for i in \$(seq $((WAIT * 2))); do \
    [ \"\$(head -1 out.txt 2>/dev/null)\" != \"\$before\" ] && { sleep 0.5; cat out.txt; exit 0; }; \
    sleep 0.5; \
  done; echo 'no answer from the watcher in ${WAIT} s: is TouchDesigner running, with the watcher active?' >&2; exit 1" <<EOF
# Written by tdlib dev/td.sh: runs $script from ~/$REPO inside TouchDesigner.
import os
TDLIB_PARENT = '$PARENT'
if op(TDLIB_PARENT) is None:
    op('/').create(baseCOMP, TDLIB_PARENT.strip('/')).comment = 'DEV ONLY: tdlib builds from dev/td.sh. Delete freely.'
__file__ = os.path.expanduser('~/$REPO/$script')
exec(compile(open(__file__).read(), __file__, 'exec'))
EOF

rsync -a --include '*/' --include '*.tox' --include '*.json' --exclude '*' --prune-empty-dirs \
  "$HOST:$REPO/effects" "$HOST:$REPO/bundles" "$root/" 2>/dev/null || true
rsync -a "$HOST:$REPO/dev/out/" "$root/dev/out/" 2>/dev/null || true
