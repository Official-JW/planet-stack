# Launch crew boarding animation (Art Assistant 3)

Crew-only animation of the 4 crew boarding the starter ship at the Launch Pad. Place the GLB root at the launch pad origin
(same space as `art/3d/buildings/launch_pad/launch_pad_game.glb`; glTF Y-up, 1 unit = 1 m). It contains no pad geometry.

| file | what |
|---|---|
| `crew_boarding.glb` | 4 skinned crew (`C1_`…`C4_` joints, 18 joints each), 1 material `SHM_Paint` (vertex colour), 4 draws, 3,049 tris per crew (12,196 total), meshopt + KHR_mesh_quantization, no images/Draco/transmission/clearcoat/ior |
| clips | `crew_call` 3.000 s → `crew_walk_to_pad` 19.300 s → `crew_climb` 36.200 s (play back to back; 58.50 s total). Keys at 15 Hz, linear |
| `Board_Focus` | empty node (no camera baked): ease the camera to it over 1.2 s and hold. Position (3.854, 3.017, −10.775), distance 109.7 m, 38° vFOV, 18° look-down, game yaw; settings in its `extras` and in the timing JSON `board_focus` |
| `CREW_BOARDING_TIMING.md` / `crew_boarding_timing.json` | per-crew phase times, every rung grab/step, hatch landing (mantle + walk-in) plants, Board_Focus camera numbers, measured checks |
| `proofs/crew_boarding_strip_gamecam_393x852_workbench.png` | 6 key frames at the game camera (38° vFOV, 18° look-down, Cam_Target (0,4,-0.7), frame_w 78.25) |
| `proofs/crew_boarding_strip_close_393x852_workbench.png` | the same 6 times, close camera on the crew (crew are ~9 px tall at the game camera) |
| `proofs/crew_boarding_strip_focuscam_375x667_workbench.png` / `..._393x852_workbench.png` | Board_Focus camera at 6 climb/landing times; dashed lines = HUD-free band (144–383 at 375x667, scaled 184–489 at 393x852) |
| `proofs/*.json` | measured checks: climber clearance, landing vs Art Assistant 2's WIP pad (`landing_check_vs_wip_pad.json`, `aa2_landing_clear_output.json`), Board_Focus fits |
| `crew_boarding_proof.blend` | **v1 (c2d33fc) proof scene, not refreshed for v2**: v2 lands on Art Assistant 2's uncommitted option-1 pad, which is not embedded here. Refresh once that pad is committed |
| `_src/` | build + verify + render scripts (see below) |

Hide/show: after `inside_hatch` each crew Root is scaled to 1e-4 and holds; game code can also just hide `Crew_k` nodes.

## Rebuild
```
cd _src
blender -b -t 4 -P extract_suit.py -- --variant A --budget 0.68 --out /tmp/suit_A68.npz     # suit from crew_pass3.py (AA2 pass-3 snapshot)
python3 build_boarding.py /tmp/suit_A68.npz /tmp/br.glb /tmp/bt.json --walk-step 2 --climb-step 2 --no-lsq --rung-pair-s 1.0 --climb-gap 3.4 --mantle-scale 0.9 \
    --focus 3.854,3.017,-10.775 --focus-extras "$(cat board_focus_extras.json)"
./pack_boarding.sh /tmp/br.glb ../crew_boarding.glb       # gltfpack -cc -kn -ke -ac -af 0 -ar 10 -at 16 + JSON minify
# measured checks (pose dump every 1/30 s from 22.3 s): clearance.py, deck_check.py (vs WIP pad tris), cam_fit.py, AA2 landing_clear.mjs, then:
python3 finalize_timing.py /tmp/bt.json vb.json cl.json dc.json camfit_375x667.json camfit_393x852.json lc.json ../crew_boarding_timing.json
python3 make_timing_sheet.py ../crew_boarding_timing.json ../CREW_BOARDING_TIMING.md
# verify in three r186 (clips, draws, contacts vs build reference):
cp verify_boarding.mjs /home/box/apps/gltftools/vb.mjs && cd /home/box/apps/gltftools && NODE_PATH=$PWD/node_modules node vb.mjs <glb> [ref.json]
```
Proofs: `dump_poses.mjs` (three CPU skinning) → `render_proofs.py` (Blender) → `make_strip.py`. Heavy Cycles strips + MP4: `run_heavy_renders.sh` (queued only — render hold until Art & Animation gives the go).

Suit source: Art Assistant 2's pass-3 crew.py snapshot (`_src/crew_pass3.py`, md5 8016ecce62a705fe874d7c1c4a6191d6, mtime 2026-10-23 23:43:59 PT), variant A for all four.
The live `art/3d/ship/starter_ship/crew.py` was never edited.
