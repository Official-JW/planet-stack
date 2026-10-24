#!/bin/bash
# Planet Stack - crew role renders, queued. Every Blender step takes the shared heavy lock on its own (crew GLB renders can
# slip in between steps).  bash run_renders.sh [smoke|portrait|game|lineup|glb|all]   (run from anywhere)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/.." && pwd)"
BL=/home/box/apps/blender-4.2.3-linux-x64/blender; GP=/home/box/apps/gltftools/node_modules/.bin/gltfpack
LOCK=/tmp/planet_stack_heavy.lock; RAW="$ROOT/proofs/_raw"; mkdir -p "$RAW" "$ROOT/proofs/game" "$ROOT/cards" "$ROOT/glb"
heavy() { flock "$LOCK" nice -n 19 "$BL" -b -t 4 -P "$HERE/render_roles.py" -- --threads 4 "$@"; }
step="${1:-all}"
if [[ $step == smoke || $step == all ]]; then      # Workbench: new tools in hand, clipping check (seconds)
  heavy --mode preview --engine WORKBENCH --roles captain,co_captain,engineer,botanist,welder,machinist --out "$RAW/preview"
fi
if [[ $step == portrait || $step == all ]]; then   # 10 card portraits, 840x864 (2x of the 420x432 card window)
  heavy --mode portrait --samples 96 --out "$RAW/portrait"
  python3 "$HERE/cards3x.py" "$RAW/portrait" "$ROOT/cards"
fi
if [[ $step == game || $step == all ]]; then       # 375x667 game-camera proof, ~20 px figures, front + back
  heavy --mode game --samples 64 --spacing 2.2 --out "$RAW/game"
  python3 "$HERE/compose.py" game "$RAW/game" "$ROOT/proofs/game"
fi
if [[ $step == lineup || $step == all ]]; then     # full-res lineup 3200x1200
  heavy --mode lineup --samples 96 --out "$RAW/lineup"
  python3 "$HERE/compose.py" lineup "$RAW/lineup" "$ROOT/proofs/lineup_roles_3200x1200.png"
fi
if [[ $step == glb || $step == all ]]; then        # role-kit GLB: Tool_<role> + Badge_<role>, meshopt + quantised
  flock "$LOCK" nice -n 19 "$BL" -b -t 4 -P "$HERE/export_kit.py" -- "$RAW/role_kit_raw.glb"
  "$GP" -i "$RAW/role_kit_raw.glb" -o "$ROOT/glb/role_kit.glb" -c
fi
echo "RUN_RENDERS DONE $step"
