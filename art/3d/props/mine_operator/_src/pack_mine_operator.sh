#!/bin/bash
# build raw GLB -> gltfpack (meshopt + quantization, keep named nodes + extras + all animation tracks; never Draco) -> verify
set -e
HERE=$(cd "$(dirname "$0")" && pwd); RAW=${1:-/tmp/op/raw.glb}; OUT=${2:-$HERE/../mine_operator_game.glb}
TOOLS=/home/box/apps/gltftools/node_modules
python3 "$HERE/build_mine_operator.py" "$RAW"
"$TOOLS/.bin/gltfpack" -i "$RAW" -o "$OUT" -cc -kn -ke -ac
ln -sfn "$TOOLS" "$HERE/node_modules"; node "$HERE/verify_mine_operator.mjs" "$OUT"; rm -f "$HERE/node_modules"
ls -l "$OUT"; md5sum "$OUT"
