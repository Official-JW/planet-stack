#!/bin/bash
# Workbench proof strips (light; render hold allows Workbench). Sequential, nice 19, -t 4. Pad = AA2 WIP pad (read-only, unpacked to /tmp).
set -euo pipefail
B=/workspace/planet-stack/art/3d/crew/boarding; S=$B/_src; BL=/opt/blender-4.2.3-linux-x64/blender; GT=/home/box/apps/gltftools; W=/tmp/cb_wb; mkdir -p $W
GLB=${GLB:-/tmp/bp_fin.glb}
nice -n 19 $GT/node_modules/.bin/gltfpack -i /tmp/lp2/landing_wip/launch_pad_game.glb -o $W/pad_plain.glb -noq -kn -km -ke >/dev/null
L='0:01.6 Cargo Mgr radios crew|0:09 crew walk to pad|0:21 CM at ladder, others queue|0:38 all 4 on the ladder|0:44.1 CM steps off onto the wing|0:49.6 crew 2 steps over kerb into hatch'
LF='0:24 CM climbing, crew 2 mounting|0:31 three on the ladder|0:38 all 4 on the ladder|0:43.3 CM lead boot onto the wing|0:46.0 CM crosses kerb into hatch|0:56.6 crew 4 crosses into hatch'
(cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $GLB $W/pose6 1.6,9,21,38,44.1,49.6 >/dev/null)
(cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $GLB $W/posef 24,31,38,43.3,46.0,56.6 >/dev/null)
for c in game close; do
  rm -rf $W/wb_$c
  nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose6 --engine WORKBENCH --cam $c --out $W/wb_$c > $W/log_$c.txt 2>&1
  n=$([ $c = game ] && echo gamecam || echo close)
  python3 $S/make_strip.py $W/wb_$c $B/proofs/crew_boarding_strip_${n}_393x852_workbench.png "$L"
done
for wh in 375x667 393x852; do
  rm -rf $W/wb_f$wh
  nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/posef --engine WORKBENCH --cam focus --focus 3.854,3.017,-10.775 --dist 109.7 --w ${wh%x*} --h ${wh#*x} --out $W/wb_f$wh > $W/log_f$wh.txt 2>&1
  BAND=$([ $wh = 375x667 ] && echo 144,383 || echo 184,489) python3 $S/make_strip.py $W/wb_f$wh $B/proofs/crew_boarding_strip_focuscam_${wh}_workbench.png "$LF"
done
echo STRIPS_DONE
