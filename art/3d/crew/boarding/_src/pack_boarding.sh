#!/bin/bash
# raw GLB -> game GLB: meshopt + quantization (gltfpack, keys kept as authored with -af 0, 10-bit rotations), then the JSON chunk is
# minified (floats rounded to 6 significant digits; binary chunk untouched).  usage: pack_boarding.sh raw.glb out.glb
set -e
G=/home/box/apps/gltftools/node_modules/.bin
$G/gltfpack -i "$1" -o "$2.tmp.glb" -cc -kn -ke -ac -af 0 -ar ${AR:-10} -at ${AT:-16}
python3 "$(dirname "$0")/minify_glb_json.py" "$2.tmp.glb" "$2" && rm -f "$2.tmp.glb"
