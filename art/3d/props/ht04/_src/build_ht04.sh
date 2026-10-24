#!/bin/bash
# HT-04 haul truck: shared prop for the Mine and the Refinery.
# The truck is modelled + rigged + baked inside the Mine build (one source of truth for the body, the fill heap and the
# chute chunks); build_mine.py exports it as its own GLB (--tout). This script runs that build and packs the prop.
#   art/3d/props/ht04/_src/build_ht04.sh [WORKDIR]   -> art/3d/props/ht04/ht04_game.glb (+ WORKDIR/ht04_raw_verify.json)
# Note: the same run also writes WORKDIR/raw.glb (the Mine without the truck); pack that with
# art/3d/buildings/mine/_src/pack_mine.sh if the Mine changed too.
set -e
REPO=$(cd "$(dirname "$0")/../../../../.." && pwd); W=${1:-/tmp/ht04}; mkdir -p "$W"
B=${BLENDER:-/opt/blender-4.2.3-linux-x64/blender}; S=$REPO/art/3d/buildings/mine/_src
cd "$REPO"
"$B" -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P "$S/build_mine.py" -- --arm park --only none --out "$W/gen" \
     --mode game --mout "$W/raw.glb" --tout "$W/ht04_raw.glb" > "$W/build.log" 2>&1
"$S/pack_mine.sh" "$W/ht04_raw.glb" "$W/ht04_base.glb"   # clip prune -> gltfpack -cc -kn -ke -> verify (base body, pre detail pass)
grep -E "WHEEL_R|TRUCK RAW" "$W/build.log"
# 10/23 PM detail pass (autonomy kit, manual cab, treads, chevrons, SHM_Glass), appended at glTF level so joints / IBMs / clips / morph stay exact.
# FB-05 (props/fb05/_src/build_fb05.py) must be built from $W/ht04_base.glb, then run detail_pass.py fb05 on its unpacked output.
GP=${GLTFPACK:-/home/box/apps/gltftools/node_modules/.bin/gltfpack}
"$GP" -i "$W/ht04_base.glb" -o "$W/ht04_base_plain.glb" -noq -kn -ke
python3 "$REPO/art/3d/props/ht04/_src/detail_pass.py" ht04 "$W/ht04_base_plain.glb" "$W/ht04_detail_raw.glb"
"$GP" -i "$W/ht04_detail_raw.glb" -o "$REPO/art/3d/props/ht04/ht04_game.glb" -cc -kn -ke
