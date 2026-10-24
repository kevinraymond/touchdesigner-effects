#!/usr/bin/env bash
# DEV ONLY. Run one of this repo's Python files inside TouchDesigner on another machine and
# print what it printed (or its traceback):
#
#   dev/td.sh effects/glow/build_glow.py
#   dev/td.sh dev/selftest.py
#   dev/td.sh --pull [dev/out/<dir>/done]   # only copy results back, first waiting for that file
#   TD_ARGS='ascii datamosh' dev/td.sh dev/flash.py   # words the script reads as TDLIB_ARGS
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
#
# Several sessions may share one TouchDesigner. A lock here (flock, per host and TD_REPO) runs
# one push-run-pull at a time, since concurrent rsyncs into one folder corrupt each other; a
# lock on the Mac (TD_WATCH/tdlib.lock) guards cmd.py against sessions on other machines. Give
# each session its own TD_PARENT so their builds don't collide. Anything a
# script schedules for later frames (captures with dev/capture.py) runs after the lock is
# released; collect it with --pull.
set -euo pipefail

HOST=${TD_HOST:-kevin@mbpm2}
REPO=${TD_REPO:-tdlib}
WATCH=${TD_WATCH:-fosfora-td-dev}
PARENT=${TD_PARENT:-/tdlib_dev}
WAIT=${TD_WAIT:-120}

root=$(cd "$(dirname "$0")/.." && pwd)
exec 9>"${XDG_RUNTIME_DIR:-/tmp}/tdlib-td-${HOST//[^A-Za-z0-9]/_}-${REPO//[^A-Za-z0-9]/_}.lock"
flock 9

pull() {
  rsync -a --include '*/' --include '*.tox' --include '*.json' --exclude '*' --prune-empty-dirs \
    "$HOST:$REPO/effects" "$HOST:$REPO/bundles" "$root/" 2>/dev/null || true
  rsync -a "$HOST:$REPO/dev/out/" "$root/dev/out/" 2>/dev/null || true
}

if [ "${1:-}" = "--pull" ]; then
  if [ -n "${2:-}" ]; then
    ssh "$HOST" "for i in \$(seq $((WAIT * 2))); do [ -e ~/$REPO/$2 ] && exit 0; sleep 0.5; done; \
      echo 'no $2 after ${WAIT} s' >&2; exit 1"
  fi
  pull
  exit 0
fi

[ $# -eq 1 ] || { echo "usage: $0 <repo-relative .py file> | --pull [marker]" >&2; exit 2; }
script=$(realpath --relative-to="$root" "$1")
[ -f "$root/$script" ] || { echo "no such file: $script" >&2; exit 2; }

# Sources out; built files stay where they are on both sides until they come back below.
rsync -a --delete --exclude .git --exclude '/effects/*/*.tox' --exclude '/effects/*/*.json' \
  --exclude '/bundles/*/*.tox' --exclude '/bundles/*/*.json' --exclude /dev/out "$root/" "$HOST:$REPO/"

args=$(TD_ARGS="${TD_ARGS:-}" python3 -c 'import json, os; print(json.dumps(os.environ["TD_ARGS"].split()))')

# One ssh: take the lock (a lock older than 10 minutes is left from a dead run and is broken),
# note the watcher's last answer (its first line carries the time and the absolute frame, so it
# changes every run), hand it cmd.py, wait for a different answer, release the lock.
ssh "$HOST" "cd $WATCH && \
  for i in \$(seq 1200); do \
    mkdir tdlib.lock 2>/dev/null && break; \
    [ -n \"\$(find tdlib.lock -maxdepth 0 -mmin +10 2>/dev/null)\" ] && rmdir tdlib.lock; \
    sleep 0.5; \
  done; \
  trap 'rmdir tdlib.lock 2>/dev/null' EXIT; \
  before=\$(head -1 out.txt 2>/dev/null); mkdir -p ~/$REPO/dev/out; \
  cat > cmd.py.tmp && mv cmd.py.tmp cmd.py; \
  for i in \$(seq $((WAIT * 2))); do \
    [ \"\$(head -1 out.txt 2>/dev/null)\" != \"\$before\" ] && { sleep 0.5; cat out.txt; exit 0; }; \
    sleep 0.5; \
  done; echo 'no answer from the watcher in ${WAIT} s: is TouchDesigner running, with the watcher active?' >&2; exit 1" <<EOF
# Written by tdlib dev/td.sh: runs $script from ~/$REPO inside TouchDesigner.
import os
TDLIB_PARENT = '$PARENT'
TDLIB_ARGS = $args
if op(TDLIB_PARENT) is None:
    op('/').create(baseCOMP, TDLIB_PARENT.strip('/')).comment = 'DEV ONLY: tdlib builds from dev/td.sh. Delete freely.'
# The script gets TouchDesigner's names but not the watcher's own (DIR, CMD, OUT...).
_ns = {k: v for k, v in globals().items()
       if k not in ('DIR', 'CMD', 'OUT', 'onFrameStart', 'io', 'sys', 'time', 'traceback')}
_ns.update(TDLIB_PARENT=TDLIB_PARENT, TDLIB_ARGS=TDLIB_ARGS, __file__=os.path.expanduser('~/$REPO/$script'), __name__='__tdlib__')
exec(compile(open(_ns['__file__']).read(), _ns['__file__'], 'exec'), _ns)
EOF

pull
