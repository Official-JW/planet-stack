#!/bin/bash
# Heavy-job gate: waits while any Playtester process runs (cwd under /workspace/playtest), then
# flock /tmp/planet_stack_heavy.lock nice -n 19 <cmd> -t 4   (blender: -t goes before -P, so callers pass it themselves)
pt() { for p in $(pgrep -u "$(id -u)" -f 'node|chrome|puppeteer' 2>/dev/null); do c=$(readlink /proc/$p/cwd 2>/dev/null); [[ $c == /workspace/playtest* ]] && return 0; done; return 1; }
# yield to the crew hotfix / flame renders (Director 10/24): wait while one of them is queued on or holding the lock
pri() { pgrep -af 'flock /tmp/planet_stack_heavy.lock' | grep -v "$$" | grep -Eqi 'crew|hotfix|flame|plume|exhaust|boarding'; }
while pt || pri; do echo "[run_heavy] Playtester or crew/flame job first, paused $(date +%H:%M:%S)"; sleep 20; done
exec flock /tmp/planet_stack_heavy.lock nice -n 19 "$@"
