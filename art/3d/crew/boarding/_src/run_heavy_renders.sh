#!/bin/bash
# QUEUED heavy renders for the crew boarding proofs (Cycles strips + MP4). Run only when the machine is free
# (house rule: nice -n 19, -t 4, one render at a time - this script runs everything sequentially).
# Usage: bash art/3d/crew/boarding/_src/run_heavy_renders.sh            (from anywhere; ~1.2 h at 4 threads, mostly the MP4)
#        STEP=strip bash ...   -> only the Cycles strips;  STEP=mp4 bash ... -> only the MP4
set -euo pipefail
B=/workspace/planet-stack/art/3d/crew/boarding; S=$B/_src; BL=/opt/blender-4.2.3-linux-x64/blender
GT=/home/box/apps/gltftools; W=/tmp/cb_heavy; mkdir -p $W $B/proofs
PAD=${PAD:-/workspace/planet-stack/art/3d/buildings/launch_pad/launch_pad_game.glb}   # read-only: only unpacked to /tmp, never written
nice -n 19 $GT/node_modules/.bin/gltfpack -i $PAD -o $W/pad_plain.glb -noq -kn -km -ke >/dev/null
cp $S/dump_poses.mjs $GT/dp.mjs
L='0:01.6 Cargo Mgr radios crew|0:09 crew walk to pad|0:19.5 CM at ladder, others queue|0:30 CM climbing|0:53 CM mantles into hatch|1:06 crew 4 climbing'
if [ "${STEP:-all}" != mp4 ]; then
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/pose6 1.6,9,19.5,30,53,66)
  for c in game close; do
    rm -rf $W/cy_$c
    nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose6 --engine CYCLES --samples 48 --cam $c --out $W/cy_$c
    python3 $S/make_strip.py $W/cy_$c $B/proofs/crew_boarding_strip_${c}cam_393x852_cycles.png "$L"
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
