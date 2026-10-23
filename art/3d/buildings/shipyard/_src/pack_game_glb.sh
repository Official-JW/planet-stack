#!/bin/sh
# Build shipyard_game.glb per Game Coder rules (SH_* palette, merge-by-material, <=30k tris, meshopt + quantization, NO Draco).
# Needs gltfpack (npm i gltfpack). Run from this _src dir. Node/clip/marker names: GAME_NAMES dict at the top of build_shipyard.py.
# -kn keeps named nodes (tiers, Crane_Jib, Hall_Door(+_L/_R), Beacon_Lights, markers), -ke keeps extras {"tier": N, "hidden_by_default": true}.
set -e
B=${BLENDER:-/opt/blender-4.2.3-linux-x64/blender}; GP=${GLTFPACK:-gltfpack}
T=$(mktemp -d)
"$B" -b -P build_shipyard.py -- --out "$T" --only game
"$GP" -cc -kn -ke -i "$T/shipyard_game_raw.glb" -o ../shipyard_game.glb
rm -rf "$T"
