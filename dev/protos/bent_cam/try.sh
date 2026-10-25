#!/usr/bin/env bash
# DEV ONLY. Build Bent Cam, then measure what beats do (dev/reaction.py) and its flashes under the stress beat at one
# Flashing setting (default calm), for trying beat responses: dev/protos/bent_cam/try.sh [setting]
set -euo pipefail
cd "$(dirname "$0")/../../.."
dev/td.sh effects/bent_cam/build_bent_cam.py | tail -1
TD_ARGS='bent_cam' dev/td.sh dev/reaction.py > /dev/null
dev/td.sh --pull dev/out/reaction/done
uv run -q --with numpy dev/reaction_report.py dev/out/reaction 2>&1 | grep -E "^bent_cam "
TD_ARGS="bent_cam flashing=${1:-calm}" dev/td.sh dev/flash.py > /dev/null
dev/td.sh --pull dev/out/flash/b1_dancer/done
uv run -q --with numpy dev/flashcount.py dev/out/flash/b1_dancer 2>&1 | grep -E "^bent_cam_${1:-calm}"
