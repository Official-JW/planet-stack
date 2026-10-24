# Launch crew boarding animation (Art Assistant 3)

Crew-only animation of the 4 crew boarding the starter ship at the Launch Pad. Place the GLB root at the launch pad origin
(same space as `art/3d/buildings/launch_pad/launch_pad_game.glb`; glTF Y-up, 1 unit = 1 m). It contains no pad geometry.

| file | what |
|---|---|
| `crew_boarding.glb` | 4 skinned crew (`C1_`…`C4_` joints, 18 joints each), 1 material `SHM_Paint` (vertex colour), 4 draws, 3,049 tris per crew (12,196 total), meshopt + KHR_mesh_quantization, no images/Draco/transmission/clearcoat/ior |
| clips | `crew_call` 3.000 s → `crew_walk_to_pad` 19.300 s → `crew_climb` 50.233 s (play back to back; 72.53 s total). Keys at 15 Hz, linear |
| `CREW_BOARDING_TIMING.md` / `crew_boarding_timing.json` | per-crew phase times and every rung grab/step |
| `proofs/crew_boarding_strip_gamecam_393x852_workbench.png` | 6 key frames at the game camera (38° vFOV, 18° look-down, Cam_Target (0,4,-0.7), frame_w 78.25) |
| `proofs/crew_boarding_strip_close_393x852_workbench.png` | the same 6 times, close camera on the crew (crew are ~9 px tall at the game camera) |
| `crew_boarding_proof.blend` | proof scene (pad unpacked from a read-only copy + posed crew from the GLB), game camera |
| `_src/` | build + verify + render scripts (see below) |

Hide/show: after `inside_hatch` each crew Root is scaled to 1e-4 and holds; game code can also just hide `Crew_k` nodes.

## Rebuild
```
cd _src
blender -b -t 4 -P extract_suit.py -- --variant A --budget 0.68 --out /tmp/suit_A68.npz     # suit from crew_pass3.py (AA2 pass-3 snapshot)
python3 build_boarding.py /tmp/suit_A68.npz /tmp/br.glb /tmp/bt.json --walk-step 2 --climb-step 2 --no-lsq
./pack_boarding.sh /tmp/br.glb ../crew_boarding.glb       # gltfpack -cc -kn -ke -ac -af 0 -ar 10 -at 16 + JSON minify
cp /tmp/bt.json ../crew_boarding_timing.json && python3 make_timing_sheet.py ../crew_boarding_timing.json ../CREW_BOARDING_TIMING.md
# verify in three r186 (clips, draws, contacts vs build reference):
cp verify_boarding.mjs /home/box/apps/gltftools/vb.mjs && cd /home/box/apps/gltftools && NODE_PATH=$PWD/node_modules node vb.mjs <glb> [ref.json]
```
Proofs: `dump_poses.mjs` (three CPU skinning) → `render_proofs.py` (Blender) → `make_strip.py`. Heavy Cycles strips + MP4: `run_heavy_renders.sh`.

Suit source: Art Assistant 2's pass-3 crew.py snapshot (`_src/crew_pass3.py`, md5 8016ecce62a705fe874d7c1c4a6191d6, mtime 2026-10-23 23:43:59 PT), variant A for all four.
The live `art/3d/ship/starter_ship/crew.py` was never edited.
