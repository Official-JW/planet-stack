# Cargo Dock layout v3: compact dock, stack and SC-1 beside the hall (Lv1)

This layout replaces the v2b framing from 272e158, which Director rejected: at frame_w 74.5 everything was tiny and the tank farm took up the right third of the screen. The fix tightens the layout and crops nothing. The new frame_w is **48**, down from 74.5.

## What moved
**New dock GLB: `cargo_dock_compact_v3.glb`** (md5 `9fb1ddbe62991edde19e239d9a32b2c6`, 228 KB, glTF-validator 0 errors / 0 warnings).
- It was made by `_src/compact_dock.mjs` from the game dock `882c8e27` (8ca81ac). The old GLBs are untouched.
- The edits are rigid moves of whole mesh islands. No mesh was scaled or warped.

| Part | Change (dock-local metres) |
|---|---|
| Tank farm TF-1: LOX-1, LH2-1, overhead pipe bridge, low rack, valves, right stub, farm lights | moved by **(-20, 0, -42)**, to behind the hall. It now sits at x -3..28, z -36..-52, and the tank tops show above and right of the roof. |
| `Tier_05` (LOX-2) and `Tier_12` | moved with the farm, by the same offset |
| Power mast | moved by **(+10, 0, -14)**, to the hall's back-left corner (x -14.8..-13.2, z -23.4..-26.6) |
| Big L-pipe | The riser leg (x 11..17, Refinery feed) is unchanged. The horizontal leg is shortened to end at **x 17.2**, its end cap closing there. |
| `Pipe_LaunchPad` marker | (47, 1.2, 8.1) -> (27, 1.2, -33.9). The pad fuel line now leaves from the moved farm. |
| `Cam_Target` | (9.5, 1.5, 16.6), extras frame_w 48. This is the v3 camera below. |
| Hall, yard, gantry, door, beacons, crew path, Road_Entry, Crate_Drop, Container_Stack, Tier_03/08 | unchanged |

- The dock footprint without tiers is now **x -14.9..28, z -52.2..16.94**. In v2 it was x -24.8..48.
- **`Tier_20` is not moved in the shipped GLB, which keeps md5 9fb1ddbe.** It is one mesh (`mesh_11`) with three parts. Before the Lv20 tier is shown, re-place it as follows (dock-local metres, positions as in the v3 GLB):

| Tier_20 part | Now (bbox x, z) | Lv20 placement |
|---|---|---|
| RAD-2 second radiator wing + loop (outboard of RAD-1) | x -18.9..-14.52, z -21.07..-5.70, h 7.05 | **stays**. At Lv20 it is the dock's left edge, world 341.1, and is 6.85 m from the Refinery and more from the bridge, so it passes the 5 m rule. |
| Yard container stacks (stack 31 two-high, stack 32) | x -11.62..-9.18, z -0.63..12.04 | **stays** (yard front-left) |
| LH2-2 tank + `lh22_drop` pipe (farm row B) | x 22.03..27.45, z -18.2..-3.54 (would float behind the apron) | **move by (-20, 0, -42)**, the farm offset, to x 2.03..7.45, z -60.2..-45.54. That puts it back in its designed row-B slot next to LOX-2 (Tier_05) and Tier_12, which already moved by the same offset. |

  - Exact rule: move the islands of `mesh_11` whose bbox centre is at x > 15.8 by (-20, 0, -42), and leave the rest. `node _src/compact_dock.mjs dock_882c.glb OUT.glb --tier20` does exactly that. It writes a variant (md5 `77dc612bc5adf3941d7988320dd88b51`, validator 0/0) that differs from 9fb1ddbe only in Tier_20. It is not committed; build it when the Lv20 tier is wired.
  - Tier visibility is unchanged; Lv1 hides all `Tier_*`.

## World placement (all y 0)
| Item | v3 world | v2 world |
|---|---|---|
| Refinery | x 320 (unchanged) | 320 |
| **Cargo Dock origin** | **(360, 0, -8)** | (373, 0, -8) |
| Storage apron (0.12 m slab) | x 377.6..391.6, z -7..7.6 (dock-local x 17.6..31.6, z 1..15.6) | x 343.7..357.7 |
| **SC-1 crane** | **(384.6, 0, 8.5)** (dock-local 24.6, 0, 16.5), footing z up to 9.2 | (350.7, 0, 8.5) |
| **Flatbed dock stop `Truck_Stop_Dock`** | **(386.5, 0, 13)**, loaded lane z 13, heading +X. Pick_A 385.35, Pick_B 382.85. | (352.6, 0, 13) |
| Launch Pad origin | **x 457, unchanged** (pad x 427.6..486.4). Pad Truck_Stop 453.5, U-turn r 4.5 at (458, 17.5), road tiles x 296..464 (21 x 8 m), all as in v2. | x 457 |

Only the Dock moved (373 -> 360). The Launch Pad and all road data stay at their v2 values. A 13:30 draft had moved the pad to 430; Director rejected that. The stills were re-rendered with the pad at 457 and came out byte-identical (the pad is outside the frame at both sizes), so their md5s are unchanged.

The 20 slots keep the same numbering, the same 5 x 2 x 2 grid, the same fill order and the same box. Columns are at dock-local x 19.2 / 21.9 / 24.6 / 27.3 / 30.0, rows at z 14.5 (front) / 12.75, tiers at y 0.12 / 1.62. See `cargo_dock_slots_lv1_v3.json`. The future rows (z 10.95..3.95) are free ground now that the farm has moved. Per Director, they get a second SC-1, not a longer jib.

## Checks
- **Refinery bridge:** the dock's left edge is at 345.1 and the bridge's right edge at 338.25, so the gap is **6.85 m** (≥ 5 m). The nearest parts are the stair railing and the moved mast.
- **Clear strip:** dock ground geometry reaches z 8.94, the apron 7.6 and the crane footing 9.2. All are ≤ 9.2, so the 1 m strip before the road band (z 10.2..24.8) is kept.
- **Flatbed route:** east on z 13 from the load point at x 318 to the dock stop at 386.5, then on to the pad Truck_Stop at 453.5, the U-turn at x 458 (outer edge 462.5, inside the tiles to 464), and west on z 22. Along z 13 between the dock stop and the pad stop, the road band (z 10.2..24.8) holds no dock or pad geometry above 0.3 m, and dock geometry stops at z 8.94. At rest the SC-1 jib is at y 6.3 or higher, above FB-05's 3.79 m.
  - The FB-05 body at the stop spans x 381.4..390.2, z 11.1..14.9.
  - The crane envelope reaches z 16.0, which is clear of the empty lane (band from z 19.7).
  - From the Dock's right edge (crane/apron, x 392.1) to the Launch Pad's left edge (427.6) is **35.5 m**. The nearest real geometry is 36.2 m apart in the height map, so nothing overlaps. The pad's right edge stays at x 486.4.
  - The buried fuel line runs from `Pipe_LaunchPad` (world 387, -41.9) to the pad receiver (477.3, -9.6), which is about 96 m (57 m in v2).
- **No overlaps:** in the 0.5 m height map (`_src/cfg_world_v3.json` + `_src/hmap.mjs`), the apron and the crane zone (dock-local x 17.5..34, z -1..17) contain no dock geometry.
- **SC-1 re-bake:** md5 `fad409cc8230f1250bb6e9b7bfb79b3a`, 3 draws, 464 tris, 40 clips. Run with `verify_storage_crane.mjs` against the v3 dock height map:
  - pick and set error < 1e-6 m, yaw 0;
  - the carried box clears stored boxes by 0.98 m, the FB-05 cab by 0.31 m and the pillar by 0.99 m;
  - neither the carried box nor the jib ever passes over dock geometry.

## Dock camera v3 (`dock_camera_v3.json`)
**ct (369.5, 1.5, 8.6) world** (dock-local 9.5, 1.5, 16.6), **frame_w 48**. Rule: 38° vFOV, 18° pitch, d = (fw/2)/(tan19°·aspect), ct at the screen centre.
- For a main.js CAM_OVERRIDE, the ct offset from the dock origin is (9.5, 1.5, 16.6) with frame_w 48. The same values are in the new GLB's `Cam_Target`.
- The subject is the Lv1 dock (no tiers), the 20-box stack, the apron, the SC-1 envelope over all 40 clips including the carried box, and FB-05 at the stop.

| Size | Band y | Subject px (x0, y0, x1, y1) | Spare L / R / T / B |
|---|---|---|---|
| 375×667 | 144–383 | 7.9, 166.1, 367.1, 360.8 | **7.9 / 7.9 / 22.1 / 22.2** |
| 393×852 | 165–534 | 8.3, 241.9, 384.0, 454.4 | **8.3 / 9.0 / 76.9 / 79.6** |

The edge margins are spare px from the screen edges (x) and from the band lines (y). All are ≥ 5. Left = dock railing, right = SC-1 jib.

**Readability at 375 (CSS px):**
- each box is **19.2–20.7 px** wide (≥ 8); 21.3 px at 393;
- SC-1 is **63 px** tall (66 at 393);
- the jib reads 15–59 px long depending on slew;
- scale is 7.8 px/m at ct.

In v2b the crane was about 43 px tall and the boxes about 12 px wide.

## Files
- `cargo_dock_compact_v3.glb`: the new dock (see above).
- `cargo_dock_storage_v3_375x667@2x.png`, `cargo_dock_storage_v3_393x852@3x.png`: full stills, 20 boxes, SC-1 at rest, FB-05 at the stop.
- `storage_crane_pick_swing_set_strip_v3_375x667@2x.png`: Store_A_Slot_20 at t 1.50 / 2.95 / 4.30, 19 stored, with x2 details.
- `cargo_dock_storage_v3_framing_guides.png`: yellow = band, orange = 5 px limit, green = subject bounds.
- `cargo_dock_layout_v3_topdown.png`: top-down plan with world positions, gaps, roads, apron, SC-1 reach and the slot plan.
- `cargo_dock_slots_lv1_v3.json` (slots, crane, stop, camera) and `dock_camera_v3.json`.
- `_src/`: `compact_dock.mjs` (GLB edit), `make_slots_v3.py`, `layout_v3.py` + `cfg_world_v3.json` + `hmap.mjs` (plan), `dump_pts_v3.mjs` + `frame_solve_v3.py` + `metrics.py` (camera), `game_cam_page_v3.html` + `render_v3.sh` + `compose_v3.py` (stills).
