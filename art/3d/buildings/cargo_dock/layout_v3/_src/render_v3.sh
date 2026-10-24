set -x
CT=369.5,1.5,8.6,48
E="&sc=1&scg=crane_sc1_v3.glb&dock=dock_v3.glb&dx=360&px=430&slots=slots_v3.json&fbx=386.5"
cd /workspace/dockl
nice -n 19 node shot.js 23917 $CT v3/r/full_375.png 375 667 2 "$E&fill=20"
nice -n 19 node shot.js 23917 $CT v3/r/full_393.png 393 852 3 "$E&fill=20"
for T in 1.5 2.95 4.3; do nice -n 19 node shot.js 23917 $CT v3/r/clip_$T.png 375 667 2 "$E&fill=19&clip=Store_A_Slot_20&ct_t=$T"; done
echo ALLDONE
