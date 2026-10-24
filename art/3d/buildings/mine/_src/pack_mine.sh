#!/bin/bash
# raw Blender GLB -> clip-pruned -> deposits split into Deposit_01/02 (2 passes, grid-snapped) -> gltfpack (meshopt + quantization,
# keep named nodes + extras; never Draco) -> deposit materials set BLEND -> verify
set -e
HERE=$(cd "$(dirname "$0")" && pwd); RAW=${1:-/tmp/mine/raw.glb}; OUT=${2:-$HERE/../mine_game.glb}
TOOLS=/home/box/apps/gltftools/node_modules; export NODE_PATH=$TOOLS
B=${RAW%.glb}
node "$HERE/mine_clips.cjs" prune "$RAW" "${B}_pruned.glb"
node "$HERE/split_deposits.cjs" "${B}_pruned.glb" "${B}_split1.glb"
"$TOOLS/.bin/gltfpack" -i "${B}_split1.glb" -o "${B}_pass1.glb" -cc -kn -ke
node "$HERE/split_deposits.cjs" "${B}_pruned.glb" "${B}_split.glb" "${B}_pass1.glb"
"$TOOLS/.bin/gltfpack" -i "${B}_split.glb" -o "${B}_packed.glb" -cc -kn -ke
python3 "$HERE/set_deposit_blend.py" "${B}_packed.glb" "$OUT"
node "$HERE/mine_clips.cjs" verify "$OUT" > "${B}_verify.json"
ls -l "$OUT"; md5sum "$OUT"
