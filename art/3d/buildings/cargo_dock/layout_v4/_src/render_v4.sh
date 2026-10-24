#!/bin/bash
# v4 stills + strip via three.js headless (site page /workspace/dockl/site/index_v4.html, shot4.js). Run under the heavy lock:
#   flock /tmp/planet_stack_heavy.lock nice -n 19 taskset -c 0-3 bash render_v4.sh   (server on 23917 started outside the lock with 3>&-)
# GC-1 heavy clips (22 s, 10/24 2:29 PM): mid-travel still at t 11.1; strip at approach done / pick / hoisted / travel / set / hook up
set -x
CT=369.5,1.5,8.6,48
E="&dock=dock_v4.glb&dx=360&px=457&slots=slots_v4.json&fbx=362.4&fill=18&bed=B&clip=Store_A_Slot_19"
cd /workspace/dockl; mkdir -p v4/r
nice -n 19 node shot4.js 23917 $CT v4/r/full_375.png 375 667 2 "$E&ct_t=11.1"
nice -n 19 node shot4.js 23917 $CT v4/r/full_393.png 393 852 3 "$E&ct_t=11.1"
for T in 2.8 6.0 8.6 11.1 17.2 19.2; do nice -n 19 node shot4.js 23917 $CT v4/r/clip_$T.png 375 667 2 "$E&ct_t=$T"; done
echo ALLDONE
