#!/bin/sh
# Build launch_pad_game.glb per Game Coder rules (merged SHM_* materials + vertex colours, <=30k tris, <=15 draws,
# meshopt + quantization, NO Draco, no images). Run from this _src dir. Names: GAME_NAMES at the top of build_launch_pad.py.
# Road_UTurn etc. are handled by the EXEMPT list inside measure_launch_pad_frame.mjs (reported, not skipped).
# -kn keeps named nodes (Pad_Base, hoses, tiers, ship, door, crane joints, markers), -ke keeps extras, -ac keeps constant clip tracks.
set -e
B=${BLENDER:-/opt/blender-4.2.3-linux-x64/blender}
NM=${NODE_PATH:-/home/box/apps/gltftools/node_modules}; GP=${GLTFPACK:-$NM/.bin/gltfpack}
T=${LP_TMP:-$(mktemp -d)}
"$B" -b -t ${THREADS:-4} -P build_launch_pad.py -- --out "$T" --only game
"$GP" -cc -kn -ke -ac -i "$T/launch_pad_game_raw.glb" -o ../launch_pad_game.glb
NODE_PATH="$NM" node verify_launch_pad_glb.mjs ../launch_pad_game.glb ../proofs/launch_pad_game_verify.json
NODE_PATH="$NM" node measure_launch_pad_frame.mjs ../launch_pad_game.glb ../proofs/launch_pad_frame_spare.json > /dev/null && echo "frame spare report: ../proofs/launch_pad_frame_spare.json"
