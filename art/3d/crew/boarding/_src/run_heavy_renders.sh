#!/bin/bash
# QUEUED heavy renders for the crew boarding proofs (Cycles strips + MP4), v2. DO NOT RUN until Art & Animation gives an explicit go
# (render hold extended indefinitely, pending Playtester sign-off run 2). House rule: nice -n 19, -t 4, one render at a time - this script is sequential.
# Usage: bash art/3d/crew/boarding/_src/run_heavy_renders.sh            (from anywhere; ~1.4 h at 4 threads, mostly the MP4)
#        STEP=strip bash ...   -> only the Cycles strips;  STEP=mp4 bash ... -> only the MP4
set -euo pipefail
B=/workspace/planet-stack/art/3d/crew/boarding; S=$B/_src; BL=/opt/blender-4.2.3-linux-x64/blender
GT=/home/box/apps/gltftools; W=/tmp/cb_heavy; mkdir -p $W $B/proofs
PAD=${PAD:-/workspace/planet-stack/art/3d/buildings/launch_pad/launch_pad_game.glb}   # read-only: only unpacked to /tmp, never written
# for the option-1 hatch landing use Art Assistant 2's pad once committed (WIP, read-only: PAD=/tmp/lp2/landing_wip/launch_pad_game.glb)
BF=${BF:-3.854,3.017,-10.775}; BFD=${BFD:-109.7}   # Board_Focus (glTF) + camera distance, see crew_boarding_timing.json board_focus
nice -n 19 $GT/node_modules/.bin/gltfpack -i $PAD -o $W/pad_plain.glb -noq -kn -km -ke >/dev/null
cp $S/dump_poses.mjs $GT/dp.mjs
L='0:01.6 Cargo Mgr radios crew|0:09 crew walk to pad|0:21 CM at ladder, others queue|0:38 all 4 on the ladder|0:44.1 CM steps off onto the wing|0:49.6 crew 2 steps over kerb into hatch'
LF='0:24 CM climbing, crew 2 mounting|0:31 three on the ladder|0:38 all 4 on the ladder|0:43.3 CM lead boot onto the wing|0:46.0 CM crosses kerb into hatch|0:56.6 crew 4 crosses into hatch'
if [ "${STEP:-all}" != mp4 ]; then
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/pose6 1.6,9,21,38,44.1,49.6)
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/posef 24,31,38,43.3,46.0,56.6)
  for c in game close; do
    rm -rf $W/cy_$c
    nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose6 --engine CYCLES --samples 48 --cam $c --out $W/cy_$c
    python3 $S/make_strip.py $W/cy_$c $B/proofs/crew_boarding_strip_${c}cam_393x852_cycles.png "$L"
  done
  for wh in 375x667 393x852; do
    rm -rf $W/cy_f$wh
    nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/posef --engine CYCLES --samples 48 --cam focus --focus $BF --dist $BFD --w ${wh%x*} --h ${wh#*x} --out $W/cy_f$wh
    python3 $S/make_strip.py $W/cy_f$wh $B/proofs/crew_boarding_strip_focuscam_${wh}_cycles.png "$LF"
  done
fi
if [ "${STEP:-all}" != strip ]; then
  # anim sampled every 1/12 s, encoded at 24 fps => 2x speed, ~36 s clip; follow cam (smoothed crew centroid), 540x960 Workbench
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/poseall --every 0.083333)
  rm -rf $W/mp4f
  nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/poseall --engine ${MP4_ENGINE:-WORKBENCH} --samples 16 --cam follow --sigma 2.0 --fw 14 --w 540 --h 960 --out $W/mp4f
  nice -n 19 ffmpeg -y -loglevel error -framerate 24 -i $W/mp4f/f_%04d.png -vf "drawtext=text='crew_boarding.glb  2x speed':x=10:y=10:fontcolor=white:fontsize=18" -c:v libx264 -pix_fmt yuv420p -crf 22 -movflags +faststart $B/proofs/crew_boarding_preview_2x.mp4 \
   || nice -n 19 ffmpeg -y -loglevel error -framerate 24 -i $W/mp4f/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 -movflags +faststart $B/proofs/crew_boarding_preview_2x.mp4
fi
ls -la $B/proofs
