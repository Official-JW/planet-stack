# CV-3 Refinery Box Bridge — `refinery_bridge.glb` (v4)

v4 mirrors v3's span yaw to **−32°** (Director review of 2c30bf1), so the lowerator and the span start are on screen. It works like this:
1. An open lowerator stands in the **flatbed median at Refinery (9.15, 17.5)**, just right of the dump bay outline and **fully inside the game view** at 393×852 and 375×667.
2. The span heads **back to the right** from it, crossing **only flatbed lane E**, to the clad south lift tower at (16.24, 7.0). The tower is between the U-turn / dump bay and lane E, off the right edge.
3. The lowerator lowers each box (slow lift) and turns it to yaw 0.
4. A **ground conveyor** in the median runs it 8.9 m west to the pickup table, inside RC-1 reach.

In the Refinery game view, no part of the bridge overlaps the dump bay, Truck_Dump, the hopper or the intake.

This file stands on its own. Do not merge it into `refinery_game.glb`.

## Placement
- The root node `Refinery_Bridge` is **already at Refinery-local (12.89, 0, 12.37), yaw 0**.
- Parent the GLB scene to the Refinery root with **no extra offset**. In world terms that is (332.89, 0, 12.37) when the Refinery sits at (320, 0, 0).
- Bridge axes are the same as Refinery axes.
- Centres (Refinery coords):
  - South tower: (16.24, 7.0).
  - Lowerator: (9.15, 17.5).
- Span: tower to tower 12.66 m, truss 10.69 m, yaw −32°. The truss underside is at 7.25 and the top at 11.9.
- Footprints (Refinery x/z):
  - South tower footing: x 13.55..18.93, z 4.31..9.69. It sits right of the U-turn and dump bay, short of lane E (lane edge z 10.2). The Refinery has no geometry at x ≥ 10 there.
  - Lowerator footing: x 7.55..10.75, z 15.9..19.1. This is in the median (15.8..19.2). The frame is 2.4 m (legs 0.22 m), and the box's 1.374 m turn radius clears the legs (1.386 m).
  - Ground conveyor + pickup slab: x −1.3..8.15, z 16.35..18.65 (median).
- Clearance:
  - The span crosses **only flatbed lane E** (z 10.2..15.8). The lowest bridge vertex over it, across all clip samples, is **y 7.27**.
  - Nothing of the bridge is inside or over RD-1 outbound z 0, the U-turn, inbound z 9, the dump bay, the HT-04 dump pose (bed up 5.75) or flatbed W.
  - HT-04 sweep (full route + bed-up dump pose, +0.5 m margin): 0 vertices inside. The nearest bridge part is 3.23 m away horizontally.

## Crane pickup (RC-1 at world (311, 0, 17.5); not moved)
- `Pickup_Point` is the box base on the table:
  - Refinery (0.3, 1.0, 17.5)
  - World (320.3, 1.0, 17.5)
  - Crane-local (9.3, 1.0, 0)
- Box yaw is 0 (long axis +X).
- RC-1 solve: θ 0, r 9.3 m (trolley range 2.6–10.3), L 6.2 m. This is in reach.
- Every bridge part above y 3 is ≥ 16.9 m from the mast. Only the table, the west end of the conveyor, the end stop, the lamp (y 2.53) and the control box sit inside the jib radius, all under the hook path.
- Markers (each has `refinery_xyz` in its extras):
  - `Box_Infeed` (16.24, 1.2, 7.0)
  - `Bridge_Entry` (15.86, 8.1, 6.76)
  - `Bridge_Exit` (9.15, 8.1, 17.5)
  - `Lowerator_Bottom` (9.15, 1.42, 17.5)
  - `Pickup_Point`

## Clips
The clip lengths and the pickup arrival time are the same as v3. The shorter ground conveyor is made up by a slower lowerator lift.
- **`box_convey`**, 38.0 s loop. Three cargo boxes, each 12.667 s apart, at 1.5 m/s on the rollers with 1 s eased starts and stops. Timeline for one box:
  - 0–5.61 s: rise, hidden in the south shaft.
  - 5.61–15.05 s: cross the bridge (12.66 m).
  - 15.05–25.38 s: lowerator descent (6.68 m at about 0.71 m/s).
  - 25.38–26.98 s: turntable yaw 58°→0°.
  - 26.98–33.89 s: ground conveyor west, 8.86 m, arriving at the pickup.
  - 33.89–36.89 s: dwell.
  - Hidden from 36.94 s.
  - Coder: when RC-1 latches, hide the bridge box, or start the crane cycle at 33.89 s plus the box offset.
- **`box_path`**, 33.9 s, no loop. A single box (Box_1, scrubbable): time = progress × duration. It uses the same event times (`rise`, `bridge`, `lower`, `turn`, `ground_conveyor`) and ends on `Pickup_Point` at yaw 0. Box_2 and Box_3 are scaled to 0.
- **`roller_spin`**, 0.4 s loop. 21 roller bones: span at 1.2 m pitch, ground conveyor at 1.2 m, table at 0.4 m. Surface speed is about 1.41 m/s.

## Budget
- 4,508 tris, 4 draws: `Bridge_Static` and `Bridge_Moving` with SHM_Paint + SHM_GlowCyan each.
- 79,112 B.
- Extensions: KHR_mesh_quantization and EXT_meshopt_compression only. No Draco, images, textures, transmission, clearcoat or ior.

## Game view (Cam_Target (313.1, 2.08, 13.55), frame_w 37.5)
The dump bay outline is the screen bounds of these elements:
- the HT-04 reverse-in and tipping volume (x −7.25..4.73, bed up 5.75)
- the RB-1 hopper, intake and sizer (Refinery x 2..10.5, z −6.5..4.5)
- the Dump_Dust puff

The outline is `proofs/refinery_bridge_dumpbay_check.json`, drawn orange in the proofs.

| | 393×852 | 375×667 |
|---|---|---|
| dump bay outline (px) | x 193–353, y 348–411 | x 184–334, y 261–319 |
| bridge vertices inside | 0 | 0 |
| closest gap (lowerator left face) | 5.1 px | 9.6 px |
| **lowerator** on screen (px) | x 351–390, y 337–462: **fully in, 3.1 px right spare** | x 336–375, y 248–369: **fully in, 0.1 px right spare** |
| bridge spare top / bottom / left | 145.8 / 71.7 / 256.6 | 80.4 / 14.5 / 245.2 |
| bridge right edge | span and south tower 61.2 px past the edge (53 % of sampled vertices off-screen) | 56.6 px (53 %) |
| union with Refinery + crane, top / bottom / left / right | 64.2 / 71.7 / 78.1 / −61.2 | 10.2 / 14.5 / 73.4 / −56.6 |
| Refinery alone, right spare | 22.9 | 29.0 |

On screen you see the whole lowerator at the right edge, the first part of the span leaving it toward the upper right, and the ground conveyor carrying boxes along the median to the pickup table.

## Source
- Build: `blender -b -P _src/build_bridge.py -- raw.glb [--box /tmp/cargo_box_plain.glb]`. The env vars `BR_LX` (lowerator centre x) and `BR_SZ` (south tower z) default to 9.15 and 7.0. Make the box input with `gltfpack -i art/3d/props/cargo_box/cargo_box_game.glb -o /tmp/cargo_box_plain.glb -noq -kn -ke`.
- Pack: `gltfpack -i raw.glb -o refinery_bridge.glb -cc -kn -ke -af 10`.
- Proofs: `_src/render_bridge_proofs.py` (`--phone` for the game camera, `--clip box_convey|box_path`).
  - `proofs/refinery_bridge_393x852.png` and `_375x667.png`: box_convey at t 28 s, with band lines and the dump bay outline.
  - `_before_after.png`: v3 (2c30bf1) vs v4 at both sizes, 2× size.
  - `_closeup_4k.png` is **still the v1 image**. A v4 4K close-up is queued until the shared box is free (QA until about 1:50 AM PT).
