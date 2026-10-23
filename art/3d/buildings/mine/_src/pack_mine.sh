#!/bin/bash
# raw Blender GLB -> clip-pruned -> gltfpack (meshopt + quantization, keep named nodes + extras; never Draco) -> verify
set -e
HERE=$(cd "$(dirname "$0")" && pwd); RAW=${1:-/tmp/mine/raw.glb}; OUT=${2:-$HERE/../mine_game.glb}
TOOLS=/home/box/apps/gltftools/node_modules; export NODE_PATH=$TOOLS
node "$HERE/mine_clips.cjs" prune "$RAW" "${RAW%.glb}_pruned.glb"
"$TOOLS/.bin/gltfpack" -i "${RAW%.glb}_pruned.glb" -o "$OUT" -cc -kn -ke
node "$HERE/mine_clips.cjs" verify "$OUT" > "${RAW%.glb}_verify.json"
ls -l "$OUT"; md5sum "$OUT"
