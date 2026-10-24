#!/bin/bash
# Heavy-job gate: waits while any Playtester process runs (cwd under /workspace/playtest), then
# flock /tmp/planet_stack_heavy.lock nice -n 19 <cmd> -t 4   (blender: -t goes before -P, so callers pass it themselves)
pt() { for p in $(pgrep -u "$(id -u)" -f 'node|chrome|puppeteer' 2>/dev/null); do c=$(readlink /proc/$p/cwd 2>/dev/null); [[ $c == /workspace/playtest* ]] && return 0; done; return 1; }
while pt; do echo "[run_heavy] Playtester running, paused $(date +%H:%M:%S)"; sleep 20; done
exec flock /tmp/planet_stack_heavy.lock nice -n 19 "$@"
