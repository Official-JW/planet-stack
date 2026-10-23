#!/bin/sh
# Build launch_pad_game.glb per Game Coder rules (SH_* palette, merge-by-material, <=30k tris, meshopt + quantization, NO Draco).
# Needs gltfpack (npm i gltfpack). Run from this _src dir.
set -e
B=${BLENDER:-/opt/blender-4.2.3-linux-x64/blender}; GP=${GLTFPACK:-gltfpack}
T=$(mktemp -d)
"$B" -b -P build_launch_pad.py -- --out "$T" --only game
"$GP" -cc -kn -ke -i "$T/launch_pad_game_raw.glb" -o ../launch_pad_game.glb
rm -rf "$T"
