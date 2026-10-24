#!/bin/bash
# QUEUED heavy renders for the crew boarding proofs (Cycles strips + MP4), v3. DO NOT RUN while the render hold is on
# (4:03 AM 10/24/2026: hold back ON for Playtester's full runs on tag 6b2c37b - no Cycles, 4K, turntables or MP4).
# House rule: every heavy job is wrapped as  flock /tmp/planet_stack_heavy.lock nice -n 19 <command> -t 4  (one heavy job box-wide at a time;
# ffmpeg takes -threads 4). Light pose dumps / strip assembly stay at nice -n 19. This script is sequential.
# Usage: bash art/3d/crew/boarding/_src/run_heavy_renders.sh      STEP=strip -> Cycles strips only;  STEP=mp4 -> MP4 only
set -euo pipefail
B=/workspace/planet-stack/art/3d/crew/boarding; S=$B/_src; BL=/opt/blender-4.2.3-linux-x64/blender
GT=/home/box/apps/gltftools; W=/tmp/cb_heavy; mkdir -p $W $B/proofs; LOCK=/tmp/planet_stack_heavy.lock
# pad: committed launch pad 7e02552 (read-only; extracted with git show, unpacked to /tmp, never written back)
PAD=${PAD:-$W/pad_7e02552.glb}
[ -f $PAD ] || (cd /workspace/planet-stack && git show 7e02552:art/3d/buildings/launch_pad/launch_pad_game.glb > $PAD)
# two-stage game camera (crew_boarding.glb nodes; distances from cam_fit_v3.py, plain lookAt, 38 deg vFOV, 18 deg look-down)
F1=3.854,11.05,-10.775;  F2=3.854,15.861,-10.775          # Board_Focus (frame_w 105.9) / Board_Focus_Top (frame_w 16.1)
# switch: C1_Hips world y >= 14 m (crew_climb clip-local 12.792 s, absolute 35.092 s)
nice -n 19 $GT/node_modules/.bin/gltfpack -i $PAD -o $W/pad_plain.glb -noq -kn -km -ke >/dev/null
cp $S/dump_poses.mjs $GT/dp.mjs
L='0:01.6 Cargo Mgr radios crew|0:09 crew walk to pad|0:21 CM at ladder, others queue|0:38 all 4 on the ladder|0:44.1 CM onto the wing|0:49.6 crew 2 on the wing'
LF='0:24 Board_Focus: CM climbing, crew 2 mounting|0:28 Board_Focus: three on the ladder|0:33 Board_Focus: CM nearing 14 m|0:38 Board_Focus_Top: CM at the top|0:44.1 Board_Focus_Top: CM onto the wing|0:49.6 Board_Focus_Top: crew 2 on the wing'
if [ "${STEP:-all}" != mp4 ]; then
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/pose6 1.6,9,21,38,44.1,49.6)
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/pose1 24,28,33)
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/pose2 38,44.1,49.6)
  for c in game close; do
    rm -rf $W/cy_$c
    flock $LOCK nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose6 --engine CYCLES --samples 48 --cam $c --out $W/cy_$c
    python3 $S/make_strip.py $W/cy_$c $B/proofs/crew_boarding_strip_${c}cam_393x852_cycles.png "$L"
  done
  for wh in 375x667 393x852; do
    if [ $wh = 375x667 ]; then D1=273.52; D2=41.58; BAND=144,383; else D1=333.38; D2=50.68; BAND=184,489; fi
    rm -rf $W/cy_f$wh; mkdir -p $W/cy_f$wh
    flock $LOCK nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose1 --engine CYCLES --samples 48 --cam focus --focus $F1 --dist $D1 --w ${wh%x*} --h ${wh#*x} --out $W/cy_f$wh --pattern a_%04d.png
    flock $LOCK nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/pose2 --engine CYCLES --samples 48 --cam focus --focus $F2 --dist $D2 --w ${wh%x*} --h ${wh#*x} --out $W/cy_f$wh --pattern b_%04d.png
    for i in 0 1 2; do mv $W/cy_f$wh/a_000$i.png $W/cy_f$wh/f_000$i.png; mv $W/cy_f$wh/b_000$i.png $W/cy_f$wh/f_000$((i+3)).png; done
    BAND=$BAND python3 $S/make_strip.py $W/cy_f$wh $B/proofs/crew_boarding_strip_focus2stage_${wh}_cycles.png "$LF"
  done
fi
if [ "${STEP:-all}" != strip ]; then
  # anim sampled every 1/12 s, encoded at 24 fps => 2x speed; follow cam (smoothed crew centroid), 540x960
  (cd $GT && nice -n 19 env NODE_PATH=$GT/node_modules node dp.mjs $B/crew_boarding.glb $W/poseall --every 0.083333)
  rm -rf $W/mp4f
  flock $LOCK nice -n 19 $BL -b -t 4 -P $S/render_proofs.py -- --pad $W/pad_plain.glb --poses $W/poseall --engine ${MP4_ENGINE:-WORKBENCH} --samples 16 --cam follow --sigma 2.0 --fw 14 --w 540 --h 960 --out $W/mp4f
  flock $LOCK nice -n 19 ffmpeg -threads 4 -y -loglevel error -framerate 24 -i $W/mp4f/f_%04d.png -vf "drawtext=text='crew_boarding.glb  2x speed':x=10:y=10:fontcolor=white:fontsize=18" -c:v libx264 -pix_fmt yuv420p -crf 22 -movflags +faststart $B/proofs/crew_boarding_preview_2x.mp4 \
   || flock $LOCK nice -n 19 ffmpeg -threads 4 -y -loglevel error -framerate 24 -i $W/mp4f/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 -movflags +faststart $B/proofs/crew_boarding_preview_2x.mp4
fi
ls -la $B/proofs
