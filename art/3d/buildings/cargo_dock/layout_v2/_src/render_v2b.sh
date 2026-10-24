set -x
CT=380.95,1.5,25.35,74.5
cd /workspace/dockl
nice -n 19 node shot.js 23917 $CT v2b/full_375.png 375 667 2 "&sc=1&fbx=352.6&fill=20"
nice -n 19 node shot.js 23917 $CT v2b/full_393.png 393 852 3 "&sc=1&fbx=352.6&fill=20"
for T in 1.5 2.95 4.3; do nice -n 19 node shot.js 23917 $CT v2b/clip_$T.png 375 667 2 "&sc=1&fbx=352.6&fill=19&clip=Store_A_Slot_20&ct_t=$T"; done
echo ALLDONE
