#!/bin/bash
# v3 Workbench proof strips (light work, allowed under the render hold). One Blender job at a time, nice -n 19, -t 4.
# Pad = committed launch pad 7e02552 (read-only: `git show 7e02552:art/3d/buildings/launch_pad/launch_pad_game.glb`), unpacked with gltfpack -noq.
# Focus strips are two-stage, as the game camera runs them (plain lookAt, 38 deg vFOV, 18 deg look-down, distance from frame_w as in qa3d-next fitSite()):
#   stage 1  Board_Focus     (3.854, 11.05, -10.775) frame_w 105.9 : crew_climb start .. trigger (C1_Hips y >= 14 m, 35.092 s absolute)
#   stage 2  Board_Focus_Top (3.854, 15.861, -10.775) frame_w 16.1 : trigger .. end
# Distances (cam_fit_v3.py): 375x667 -> 273.52 / 41.58 m, 393x852 -> 333.38 / 50.68 m.
set -euo pipefail
B=/workspace/planet-stack/art/3d/crew/boarding; S=$B/_src; BL=/opt/blender-4.2.3-linux-x64/blender; GT=/home/box/apps/gltftools; W=/tmp/cb_wb3; mkdir -p $W
GLB=${GLB:-$B/crew_boarding.glb}
PAD=${PAD:-$W/pad_7e02552.glb}
[ -f $PAD ] || (cd /workspace/planet-stack && git show 7e02552:art/3d/buildings/launch_pad/launch_pad_game.glb > $PAD)
nice -n 19 $GT/node_modules/.bin/gltfpack -i $PAD -o $W/pad_plain.glb -noq -kn -km -ke >/dev/null
F1='3.854,11.05,-10.775'; F2='3.854,15.861,-10.775'
T1='24,28,33'; T2='38,44.1,49.6'
LF='0:24 Board_Focus: CM climbing, crew 2 mounting|0:28 Board_Focus: three on the ladder|0:33 Board_Focus: CM nearing 14 m|0:38 Board_Focus_Top: CM at the top|0:44.1 Board_Focus_Top: CM onto the wing|0:49.6 Board_Focus_Top: crew 2 on the wing'
(cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $GLB $W/pose1 $T1 >/dev/null)
(cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $GLB $W/pose2 $T2 >/dev/null)
for wh in 375x667 393x852; do
  if [ $wh = 375x667 ]; then D1=273.52; D2=41.58; BAND=144,383; else D1=333.38; D2=50.68; BAND=184,489; fi
  rm -rf $W/wb_$wh; mkdir -p $W/wb_$wh
  nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose1 --engine WORKBENCH --cam focus --focus $F1 --dist $D1 --w ${wh%x*} --h ${wh#*x} --out $W/wb_$wh --pattern a_%04d.png > $W/log1_$wh.txt 2>&1
  nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose2 --engine WORKBENCH --cam focus --focus $F2 --dist $D2 --w ${wh%x*} --h ${wh#*x} --out $W/wb_$wh --pattern b_%04d.png > $W/log2_$wh.txt 2>&1
  for i in 0 1 2; do mv $W/wb_$wh/a_000$i.png $W/wb_$wh/f_000$i.png; mv $W/wb_$wh/b_000$i.png $W/wb_$wh/f_000$((i+3)).png; done
  BAND=$BAND python3 $S/make_strip.py $W/wb_$wh $B/proofs/crew_boarding_strip_focus2stage_${wh}_workbench.png "$LF"
done
echo STRIPS_DONE
