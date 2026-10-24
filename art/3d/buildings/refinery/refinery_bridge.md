# CV-3 Refinery Box Bridge — `refinery_bridge.glb` (v3)

v3 is a truss gantry at a 32° yaw, slid +X past the dump bay. It works like this:
1. A clad south lift tower stands **east of the RB-1 hopper / intake**.
2. The span crosses **only flatbed lane E** to an open lowerator in the flatbed median, toward the Cargo Dock.
3. The lowerator lowers each box and turns it to yaw 0.
4. A **ground conveyor** in the median runs it 17.3 m west to the pickup table, inside RC-1 reach.

In the Refinery game view, no part of the bridge overlaps the dump bay, Truck_Dump, the hopper or the intake. Most of the span and the lowerator run off the right edge, which the Director allowed (the right band is waived for the bridge only).

This file stands on its own. Do not merge it into `refinery_game.glb`.

## Placement
- The root node `Refinery_Bridge` is **already at Refinery-local (14.81, 0, 12.13), yaw 0**.
- Parent the GLB scene to the Refinery root with **no extra offset**. In world terms that is (334.81, 0, 12.13) when the Refinery sits at (320, 0, 0).
- Bridge axes are the same as Refinery axes.
- Centres (Refinery coords):
  - South tower: (11.6, 7.0).
  - Lowerator: (17.63, 17.5).
- Span: tower to tower 12.10 m, truss 10.13 m, yaw 32°. The truss underside is at 7.25 and the top at 11.9.
- Footprints (Refinery x/z):
  - South tower footing: x 8.91..14.29, z 4.31..9.69. It sits between the U-turn and lane E (lane edge z 10.2), and is clear of the Refinery geometry, which ends at x ≈ 8 there.
  - Lowerator footing: x 16.03..19.23, z 15.9..19.1. This is in the median (15.8..19.2).
  - Ground conveyor + pickup slab: x -1.3..16.43, z 16.35..18.65 (median).
- Clearance:
  - The span crosses **only flatbed lane E** (z 10.2..15.8). The lowest bridge vertex over it, across all clip samples, is **y 7.27**.
  - Nothing of the bridge is inside or over RD-1 outbound z 0, the U-turn, inbound z 9, the HT-04 dump pose (bed up 5.75) or flatbed W.
  - HT-04 sweep (route + dump pose, +0.5 m margin): 0 vertices inside. The nearest bridge part is 3.23 m away horizontally.

## Crane pickup (RC-1 at world (311, 0, 17.5); not moved)
- `Pickup_Point` is the box base on the table:
  - Refinery (0.3, 1.0, 17.5)
  - World (320.3, 1.0, 17.5)
  - Crane-local (9.3, 1.0, 0)
- Box yaw is 0 (long axis +X).
- RC-1 solve: θ 0, r 9.3 m (trolley range 2.6–10.3), L 6.2 m. This is in reach.
- Every bridge part above y 3 is ≥ 21.3 m from the mast. Only the table, the west end of the conveyor, the end stop, the lamp (y 2.53) and the control box sit inside the jib radius, all under the hook path.
- Markers (each has `refinery_xyz` in its extras):
  - `Box_Infeed` (11.6, 1.2, 7.0)
  - `Bridge_Entry` (11.22, 8.1, 7.24)
  - `Bridge_Exit` (17.63, 8.1, 17.5)
  - `Lowerator_Bottom` (17.63, 1.42, 17.5)
  - `Pickup_Point`

## Clips
- **`box_convey`**, 38.0 s loop. Three cargo boxes, each 12.667 s apart, at 1.5 m/s with 1 s eased starts and stops. Timeline for one box:
  - 0–5.61 s: rise, hidden in the south shaft.
  - 5.61–14.68 s: cross the bridge.
  - 14.68–20.13 s: lowerator descent.
  - 20.13–21.33 s: turntable yaw -58°→0°.
  - 21.33–33.89 s: ground conveyor west, 17.3 m, arriving at the pickup.
  - 33.89–36.89 s: dwell.
  - Hidden from 36.94 s.
  - Coder: when RC-1 latches, hide the bridge box, or start the crane cycle at 33.89 s plus the box offset.
- **`box_path`**, 33.9 s, no loop. A single box (Box_1, scrubbable): time = progress × duration. It uses the same event times and ends on `Pickup_Point` at yaw 0. Box_2 and Box_3 are scaled to 0.
- **`roller_spin`**, 0.4 s loop. 28 roller bones: span at 1.2 m pitch, ground conveyor at 1.2 m, table at 0.4 m. Surface speed is about 1.41 m/s.

## Budget
- 4,676 tris, 4 draws: `Bridge_Static` and `Bridge_Moving` with SHM_Paint + SHM_GlowCyan each.
- 82,780 B.
- Extensions: KHR_mesh_quantization and EXT_meshopt_compression only. No Draco, images, textures, transmission, clearcoat or ior.

## Game view (Cam_Target (313.1, 2.08, 13.55), frame_w 37.5)
The dump bay outline is the screen bounds of these elements:
- the HT-04 reverse-in and tipping volume (x -7.25..4.73, bed up 5.75)
- the RB-1 hopper, intake and sizer (Refinery x 2..10.5, z -6.5..4.5)
- the Dump_Dust puff

The outline is `proofs/refinery_bridge_dumpbay_check.json`, drawn orange in the proofs.

| | 393×852 | 375×667 |
|---|---|---|
| dump bay outline (px) | x 193–353, y 348–411 | x 184–334, y 261–319 |
| bridge vertices inside | 0 | 0 |
| closest gap | 6.5 px | 7.9 px |
| bridge spare top / bottom / left | 145.8 / 71.5 / 256.6 | 80.4 / 14.4 / 245.2 |
| **right-edge overflow** (waived) | 95.9 px past the edge, 64 % of sampled vertices off-screen | 96.0 px, 64 % |
| union with Refinery + crane, top / bottom / left | 64.2 / 71.5 / 78.1 | 10.2 / 14.4 / 73.4 |

On screen you see the left part of the south tower at the right edge, the start of the span, and the ground conveyor bringing boxes in from the right edge along the median to the pickup table.

## Source
- Build: `blender -b -P _src/build_bridge.py -- raw.glb [--box /tmp/cargo_box_plain.glb]`. The env vars `BR_SX` and `BR_SZ` move the south tower; defaults are 11.6 and 7.0. Make the box input with `gltfpack -i art/3d/props/cargo_box/cargo_box_game.glb -o /tmp/cargo_box_plain.glb -noq -kn -ke`.
- Pack: `gltfpack -i raw.glb -o refinery_bridge.glb -cc -kn -ke -af 10`.
- Proofs: `_src/render_bridge_proofs.py` (`--phone` for the game camera, `--clip box_convey|box_path`).
  - `proofs/refinery_bridge_393x852.png` and `_375x667.png`: box_convey at t 28 s, with band lines and the dump bay outline.
  - `_before_after.png`: v2 (5ecf708) vs v3 at both sizes, 2× size.
  - `_closeup_4k.png` is **still the v1 image**. A v3 4K close-up is queued until the shared box is free (QA until about 1:50 AM PT).
