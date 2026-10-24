# Launch crew boarding animation (Art Assistant 3) — v3

Crew-only animation of the 4 crew boarding the starter ship at the Launch Pad. Place the GLB root at the launch pad origin
(same space as `art/3d/buildings/launch_pad/launch_pad_game.glb`; glTF Y-up, 1 unit = 1 m). It contains no pad geometry.
v3 is checked against the **committed** launch pad at `7e02552` (md5 9e44959341d7f57bf1b3bd21b826b940) and also against the current working-tree pad.

| file | what |
|---|---|
| `crew_boarding.glb` | 4 skinned crew (`C1_`…`C4_` joints, 18 joints each), 1 material `SHM_Paint` (vertex colour), **4 draws, 2,693 tris per crew (10,772 total)**, 249,416 B (< 250 KB), meshopt + KHR_mesh_quantization, no images/Draco/transmission/clearcoat/ior |
| clips | `crew_call` 3.000 s → `crew_walk_to_pad` 19.300 s → `crew_climb` 36.200 s (back to back; 58.50 s total). Keys adaptive (dense near the ship / deck, loose far away), linear |
| `Board_Focus` | empty node, **(3.854, 11.05, −10.775)** = mid-ladder point; extras `frame_w` 105.9. Camera target from `crew_climb` start until the height trigger |
| `Board_Focus_Top` | empty node, **(3.854, 15.861, −10.775)** = true centre of the top content (ladder above 14 m + crew + hatch landing); extras `frame_w` 16.1 |
| trigger | switch to `Board_Focus_Top` when `C1_Hips` world Y ≥ 14.0 m (GLB root space): `crew_climb` clip-local 12.792 s / absolute 35.092 s. Alt bone `C1_Head`: 12.293 / 34.593 s. All in both nodes' `extras.trigger` |
| `CREW_BOARDING_TIMING.md` / `crew_boarding_timing.json` | per-crew phase times, rung moves, hatch landing plants, focus nodes + band fits, per-crew `{s, i, side}` for landing_clear_v3.mjs, all measured checks |
| `proofs/crew_boarding_strip_focus2stage_375x667_workbench.png` / `..._393x852_workbench.png` | two-stage game camera (plain lookAt, 38° vFOV, 18° look-down): Board_Focus at 24 / 28 / 33 s, Board_Focus_Top at 38 / 44.1 / 49.6 s; dashed lines = HUD-free band |
| `proofs/aa2_landing_clear_v3_gate_*` | AA2's v3 gate (`/tmp/lp2/landing_clear_v3.mjs`, 14 categories): PASS vs pad 7e02552 and vs the working-tree pad |
| `proofs/aa2_landing_clear_output.json` | AA2's committed v2 `landing_clear.mjs` (7e02552), run unedited |
| `proofs/deck_check_vs_pad_7e02552.json`, `climber_clearance.json`, `board_focus_fit_v3.json`, `board_focus_trigger.json`, `verify_r186.json` | my measured checks (three r186 skinned playback of the shipped GLB) |
| `proofs/crew_boarding_strip_gamecam_…`, `…_close_…` | **v2 images (not re-rendered for v3)** |
| `crew_boarding_proof.blend` | v3 Workbench proof scene: pad 7e02552 (unpacked) + the 4 crew posed at 44.1 s, camera at Board_Focus_Top (393x852, 50.68 m) |
| `_src/` | build + verify + render scripts (see below) |

Camera distances (qa3d-next `fitSite()`: d = (frame_w/2) / (tan 19° · aspect)), from `cam_fit_v3.py`:

| node | 375x667 (band 144–383) | 393x852 (band 184–489) | 393x852 (band 165–534, safe-area) |
|---|---|---|---|
| Board_Focus | 273.52 m, crew 6.1 px, spare top/bottom 152.4 / 5.0 px | 333.38 m, 6.4 px, 203.2 / 16.5 | 333.38 m, 6.4 px, 222.2 / 61.5 |
| Board_Focus_Top | 41.58 m, crew 40.3 px, 5.6 / 5.1 px | 50.68 m, 42.3 px, 51.0 / 16.5 | 50.68 m, 42.3 px, 70.0 / 61.5 |

The fixed mid-ladder Board_Focus with a plain lookAt has to fit the whole 22 m ladder plus the pad-level crew, so climbers are ~6 px tall in stage 1.

Hide/show: after `inside_hatch` each crew Root is scaled to 1e-4 and holds; game code can also just hide `Crew_k` nodes.

## Known v3 issue (not a gate category)
**Climber-to-climber overlap at the ladder top.** The v3 mantle keeps each climber at the top for about 5 s (rail press, slow boot set-downs needed by the still-sole rule). Meanwhile the next climber keeps climbing at the 3.4 s / 4.08 m stagger, so the upper climber's boots and shins pass through the next climber's head and forearms at z 20.4–21.9 m: crew 1/2 at about 43.0–45.3 s, 2/3 at 46.4–48.7 s, and 3/4 at 49.8–52.1 s. Min mesh gap is 0 and 208 frames are under 2 cm (v2: min 6.9 cm). It can't be fixed while keeping both the 3.4 s stagger and the 36.2 s climb. See `crew_boarding_timing.json` → `measured.climber_clearance_note`.

## Rebuild
```
cd _src
nice -n 19 blender -b -t 4 -P extract_suit.py -- --variant A --budget 0.68 --out /tmp/suit_A68.npz     # suit from crew_pass3.py (AA2 pass-3 snapshot)
# key-density point cloud of the pad (Ship_Placeholder tris + analytic ladder) in the pad-local frame:
git -C /workspace/planet-stack show 7e02552:art/3d/buildings/launch_pad/launch_pad_game.glb > /tmp/pad_7e02552.glb
cp pad_points.mjs /home/box/apps/gltftools/ && (cd /home/box/apps/gltftools && nice -n 19 node pad_points.mjs /tmp/pad_7e02552.glb /tmp/padpts.f32)   # 17.7 M points
#   downsample: the shipped GLB was keyed with a 1,185,780-point subset (first point per ~1.2 cm voxel, md5 53805cd8...);
#   the exact voxel size was not recorded - np.unique(np.floor(P / 0.012), axis=0, return_index=True) gives 1,194,979 points (equivalent density)
nice -n 19 python3 build_boarding.py /tmp/suit_A68.npz /tmp/br.glb /tmp/bt.json --walk-step 2 --climb-step 2 --no-lsq --rung-pair-s 1.0 --climb-gap 3.4 --mantle-scale 0.9 \
    --key-tol 0.001 --key-maxgap 4 --key-loose 1.0 --key-pts /tmp/padpts_ds.f32 --key-clips crew_call,crew_walk_to_pad,crew_climb   # focus nodes from board_focus_extras.json (--focus-json)
nice -n 19 ./pack_boarding.sh /tmp/br.glb ../crew_boarding.glb       # gltfpack -cc -kn -ke -ac -af 0 -ar 10 -at 16 + JSON minify (-ar 11 = 261 KB, over the cap)
# gate (AA2, must PASS all 14):  nice -n 19 node /tmp/lp2/landing_clear_v3.mjs ../crew_boarding.glb /tmp/pad_7e02552.glb gate.json
# measured checks: dump_poses.mjs (every 1/30 s from 22.3 s) -> clearance.py, deck_check.py (pad tris from pad_tris.mjs), cam_fit_v3.py POSES 35.092,
#   focus_trigger.mjs (copy into /home/box/apps/gltftools; ESM imports resolve there, NODE_PATH is ignored), AA2 v2 landing_clear.mjs, then:
python3 finalize_timing.py /tmp/bt.json vb.json cl.json dc.json gate.json aa2_v2.json camfit_v3.json trig.json board_focus_extras.json ../crew_boarding_timing.json
python3 make_timing_sheet.py ../crew_boarding_timing.json ../CREW_BOARDING_TIMING.md
```
Proofs: `workbench_strips.sh` (two-stage Workbench strips; light, nice -n 19, -t 4, one Blender job at a time).
Heavy Cycles strips + MP4: `run_heavy_renders.sh`. It's queued only (render hold), and every heavy job in it runs as `flock /tmp/planet_stack_heavy.lock nice -n 19 <command> -t 4`.

Suit source: Art Assistant 2's pass-3 crew.py snapshot (`_src/crew_pass3.py`, md5 8016ecce62a705fe874d7c1c4a6191d6), variant A for all four; v3 glove thickness / curled grip are applied in my copy only.
The live `art/3d/ship/starter_ship/crew.py` was never edited; AA2's pad and scripts were only read (copied to /tmp).
