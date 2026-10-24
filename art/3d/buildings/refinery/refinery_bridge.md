# CV-3 Refinery Box Bridge — `refinery_bridge.glb` (v5)

v5 is the Director's option A: **the box rides end-on (yaw 90, long axis along z) the whole way and turns to yaw 0 only on the pickup turntable.**
1. The box turns end-on while hidden in the south lift shaft, then rises (12.4 s, hidden).
2. It crosses the −32° span lengthwise. The span is 2.7 m between the guides (box + 0.15 m a side). The walkway was dropped to make room.
3. It rides a **moving lift carriage** down the open two-post lowerator in the **flatbed median at Refinery (9.0, 17.5)**. The frame is 2.08 × 3.16 m (box + 0.15 m a side).
4. It rolls west, still end-on, along the 2.7 m-wide **ground conveyor** to the **3.05 m pickup turntable**.
5. The table turns it 90°→0° in 1 s (ease in/out), and it settles on `Pickup_Point` inside RC-1 reach.

The whole lowerator is on screen. The span runs back to the right, crossing **only flatbed lane E**, to the clad south tower off the right edge. No part of the bridge overlaps the dump bay, Truck_Dump, the hopper or the intake.

This file stands on its own. Do not merge it into `refinery_game.glb`.

## Placement
- The root node `Refinery_Bridge` is **already at Refinery-local (12.28, 0, 12.25), yaw 0**.
- Parent the GLB scene to the Refinery root with **no extra offset**. In world terms that is (332.28, 0, 12.25) when the Refinery sits at (320, 0, 0).
- Bridge axes are the same as Refinery axes.
- Centres (Refinery coords):
  - South tower: (15.561, 7.0).
  - Lowerator: (9.0, 17.5).
- Span: tower to tower 12.38 m, truss 9.13 m, yaw −32°. The truss underside is at 7.25 and the top at 11.9.
- Footprints (Refinery x/z):
  - South tower footing: x 12.87..18.25, z 4.31..9.69.
  - Lowerator footing: x 7.85..10.15, z 15.85..19.15 (median 15.8..19.2).
  - Ground conveyor + table slab: x −1.92..8.18, z 15.9..19.1.
  - Pickup turntable: centre (0.3, 17.5), 3.05 m across.
- Clearance:
  - The span crosses **only flatbed lane E** (z 10.2..15.8). The lowest bridge vertex over it, across all clip samples, is **y 7.249** (≥ 7.22).
  - No bridge part goes below 6.75 in any lane.
  - HT-04 sweep (fresh run, full route + bed-up dump pose, +0.5 m margin): 0 vertices inside. The nearest bridge part is 2.68 m away horizontally.

## Crane pickup (RC-1 at world (311, 0, 17.5); not moved)
- `Pickup_Point` is the box base on the turntable:
  - Refinery (0.3, 1.0, 17.5)
  - World (320.3, 1.0, 17.5)
  - Crane-local (9.3, 1.0, 0)
- Box yaw is 0 (long axis +X).
- RC-1 solve: θ 0, r 9.3 m, L 6.2 m. This is in reach.
- Every bridge part above y 3 is ≥ 16.85 m from the mast.
- Markers (each has `refinery_xyz`):
  - `Box_Infeed` (15.561, 1.2, 7.0)
  - `Bridge_Entry` (15.561, 8.1, 7.0)
  - `Bridge_Exit` (9.0, 8.1, 17.5)
  - `Lowerator_Bottom` (9.0, 1.42, 17.5)
  - `Pickup_Point`

## Clips
The clip lengths and the pickup arrival time are the same as v4.
- **`box_convey`**, 38.0 s loop. Three boxes, 12.667 s apart, at 1.5 m/s on the rollers with 1 s eased starts and stops. Timeline for one box:
  - 0–12.399 s: `rise`, hidden in the south shaft. The box is held scaled to 0 for the first 0.25 s, so gltfpack's 10 Hz resample never shows a growing box.
  - 12.399–21.653 s: `bridge`, 12.38 m, end-on.
  - 21.653–25.993 s: `lower`, 6.68 m on the carriage, up to 2 m/s.
  - 25.993–32.8 s: `ground_conveyor`, 8.71 m west, end-on.
  - 32.8–33.8 s: `table_turn`, 90°→0° smoothstep.
  - 33.8–33.887 s: `settle`.
  - 33.887–36.887 s: `dwell`.
  - Hidden from 36.937 s.
  - `lift_carriage`: down 21.653–25.993 s, back up 27.44–30.667 s (3 m/s). It is at the top again before the next box arrives.
  - Coder: start the RC-1 cycle at 33.89 s plus the box offset. RC-1 latches 0.9–1.3 s into its cycle (34.79–35.19 s), so the turn has finished 0.99 s before the latch.
- **`box_path`**, 33.9 s, no loop. A single box (Box_1, scrubbable): time = progress × duration. It uses the same events and ends on `Pickup_Point` at yaw 0. The carriage moves with it.
- **`roller_spin`**, 0.4 s loop. 18 roller bones. Surface speed is about 1.41 m/s.

## Clip check (`proofs/refinery_bridge_clipcheck.json`)
The check runs every frame at 30 Hz over the full 33.9 s `box_path` and over the 38 s `box_convey` loop (all three boxes):
- Each box's OBB is fitted per frame to its skinned vertices.
- Each OBB is tested against every real triangle within 0.5 m: static mesh, rollers, lift carriage and the other boxes.
- Distances are exact triangle-to-OBB. Geometry below the box base + 3 cm counts as support.

Results:
- **0 frames touching.**
- **Minimum clearance 0.119 m.** It occurs at t 22.6 s, as the box starts down the lowerator beside the west end of the truss (y ≈ 7.25).
- Per-segment minimum clearance (m):

  | rise | bridge | lower | ground_conveyor | table_turn | settle |
  |---|---|---|---|---|---|
  | 0.186 | 0.139 | 0.119 | 0.148 | 0.351 | ≥ 0.5 |
- Support never rises above the box base (max −0.005 m). The tilted box is rested on the chute, so it never sinks in.
- Carriage vs static: minimum 0.034 m, at the bottom stop.
- The largest yaw step is 4.45°/frame, during `table_turn` only.

## Budget
- 3,752 tris, 4 draws: `Bridge_Static` and `Bridge_Moving` with SHM_Paint + SHM_GlowCyan each.
- 69,712 B.
- Extensions: KHR_mesh_quantization and EXT_meshopt_compression only. No Draco, images, textures, transmission, clearcoat or ior.

## Game view (Cam_Target (313.1, 2.08, 13.55), frame_w 37.5; camera unchanged)
All numbers are edge-sampled over every clip sample (`proofs/refinery_bridge_dumpbay_check.json`). The dump bay outline is drawn orange in the proofs.

| | 393×852 | 375×667 |
|---|---|---|
| lowerator right spare | **10.3 px** (box in the lift 11.5) | **8.2 px** (box in the lift 8.5) |
| gap to the dump bay outline | **6.3 px** | **10.6 px** |
| whole Refinery + bridge + crane, top spare | **64.2 px** | **10.2 px** |
| whole Refinery + bridge + crane, bottom spare | **70.9 px** | **13.8 px** |
| bridge vertices inside the dump bay | 0 | 0 |

The v4 edge-sampled numbers, for comparison: 393 gap 3.5 px, lowerator right 1.4 px; 375 lowerator right −0.9 px.

## Source
- Build: `blender -b -P _src/build_bridge.py -- raw.glb [--box /tmp/cargo_box_plain.glb]`. The env vars `BR_LX` (lowerator centre x, default 9.0), `BR_EE` (span end set-back, default 1.6) and `BR_LOWDUMP` (dump the lift-section polygons as JSON). Make the box input with `gltfpack -i art/3d/props/cargo_box/cargo_box_game.glb -o /tmp/cargo_box_plain.glb -noq -kn -ke`.
- Pack: `gltfpack -i raw.glb -o refinery_bridge.glb -cc -kn -ke -af 10`.
- Proofs: `_src/render_bridge_proofs.py` (`--phone` for the game camera, `--clip box_convey|box_path`).
  - `proofs/refinery_bridge_393x852.png` and `_375x667.png`: box_convey at t 28 s, with band lines and the dump bay outline.
  - `_before_after.png`: v4 (613e1c9) vs v5 at both sizes, 2× size.
  - `_clipcheck.json`: the 30 Hz box-vs-geometry clip check (box_path and box_convey).
  - `_closeup_4k.png` is **still the v1 image**. A v5 4K close-up is queued until the shared box is free (QA until about 1:50 AM PT).
