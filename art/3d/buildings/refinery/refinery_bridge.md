# CV-3 Refinery Box Bridge — `refinery_bridge.glb` (v5.2)

v5.2 makes the carriage visibly attached and lifts the dark areas. Timings, camera and the box route are unchanged from v5.1.
- **Guide shoe:** two C-clamps on the carriage (bone `Lift_Carriage`) wrap the full-height mast, 0.9 m apart vertically. Each wraps the carriage face, the camera face and a back return. The clamps are open on the −z side, where the west-rail ties and the ground conveyor's north rail land. A bracket joins the shoe to the carriage corner.
- **Rack strip:** a steel guide/rack strip (y 0.9–9.0) runs on the mast's carriage face, and the shoe rides 2.2 cm off it.
- **Hoist cable:** a sheave sits under the head beam, with a cable down to the shoe top. Its top vertices are skinned to `Bridge_Base` and its bottom vertices to `Lift_Carriage`, so it stretches with the carriage at no extra draw.
- **Far-right post: no shoe.** That post stops at y 7.1 under a bearing cap, but the carriage travels from y 8.1 down to 1.42. A clamp could not stay on the post at the top or pass the cap, so the far-right post is left without a shoe.
- **Lighter underside:** the deck pan is now satin, and the guide beams and the under-strip are now light white. The floor beams went from graphite to mid graphite.
- **Tower opening:** the span opening in the tower now has light reveals (jambs and head) and a cyan glow strip under the head. No new materials.
- **Budget:** +156 tris (3,908), still 4 draws.


v5.1 is the Director's option B retime of v5. Geometry and camera are unchanged. The heavy lift now moves slowly: the box and carriage come down the visible lowerator at **≤ 1.0 m/s, eased in and out**. The hidden rise is shorter to keep the 33.887 s arrival, and `box_convey` is now **44 s** so the single carriage is back at the top before each next box.


v5 is the Director's option A: **the box rides end-on (yaw 90, long axis along z) the whole way and turns to yaw 0 only on the pickup turntable.**
1. The box turns end-on while hidden in the south lift shaft, then rises (9.06 s, hidden).
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
`box_path` keeps the 33.887 s arrival. `box_convey` is stretched to 44 s for the slow lift.

Timeline for one box (both clips):

| stretch | time (s) | length | peak speed |
|---|---|---|---|
| `rise` (hidden in the south shaft) | 0–9.059 | 6.9 m | 0.86 m/s |
| `bridge` (end-on) | 9.059–18.313 | 12.38 m | 1.5 m/s |
| `lower` (on the carriage) | 18.313–25.993 | 6.68 m | **1.0 m/s**, held 19.31–24.99 s (box base y 7.6 → 1.9) |
| `ground_conveyor` (end-on) | 25.993–32.8 (unchanged) | 8.71 m | 1.5 m/s |
| `table_turn` | 32.8–33.8 | 90° → 0° smoothstep | 135°/s at mid-turn |
| `settle` | 33.8–33.887 | | |
| `dwell` | 33.887–36.887 | | |

- Every move eases over 1 s (cubic ramp), so speed never jumps. The largest box acceleration is 2.25 m/s².
- `lift_carriage`: down with the box 18.313–25.993 s at ≤ 1.0 m/s. It waits at the bottom until the box has rolled clear, then returns up empty 27.44–30.667 s, eased, peak 3.0 m/s.
- RC-1: start the cycle at 33.89 s plus the box offset. It latches 0.9–1.3 s into the cycle (34.79–35.19 s), so the turn is done 0.99 s before the latch.

- **`box_convey`**, **44.0 s** loop. Three boxes, 14.667 s apart. Each box is hidden at the infeed for the first 0.25 s and again from 36.937 s. The first and last keys match on every channel, so the loop is clean.
- **`box_path`**, 33.9 s, no loop. A single box (Box_1, scrubbable): time = progress × duration. It ends on `Pickup_Point` at yaw 0. The carriage moves with it, and Box_2 and Box_3 are scaled to 0.
- **`roller_spin`**, 0.4 s loop. 18 roller bones, surface speed about 1.41 m/s.

### Single-carriage cycle (also in the `carriage_cycle` extras)
Box N+1 must start its timeline **at least 14.64 s** after box N. The breakdown:
- **Wait for the box, 2.286 s.** The carriage must be at the top from the moment the box comes within 0.05 m (in plan) of the carriage deck (16.027 s) until the box is centred and the descent starts (18.313 s).
- **Descent, 7.680 s.**
- **Roll-off, 1.447 s.** This runs until the box is 0.05 m clear of the carriage.
- **Empty return, 3.227 s.** The carriage is free at 30.667 s.

`box_convey` uses 14.667 s, which leaves 0.027 s of slack.

If boxes come faster than this:
- Hold the next box on the **span conveyor**, with its centre at least **2.68 m back from the lift centre**: at or before Refinery (10.42, 8.1, 15.23), base y 8.1.
- Keep it there until the previous box's carriage is back at the top (30.667 s on that box's timeline), then resume its timeline.
- Never let a box onto the lowerator while the carriage is below the top.
- Further boxes can queue behind it on the span, at least 2.9 m centre to centre (the box is 2.75 m long along the span, plus a gap), or wait hidden in the south shaft.

## Clip check (`proofs/refinery_bridge_clipcheck.json`)
The check runs every frame at 30 Hz over the full 33.9 s `box_path` and over the 44 s `box_convey` loop (all three boxes):
- Each box's OBB is fitted per frame to its skinned vertices.
- Each OBB is tested against every real triangle within 0.5 m: static mesh, rollers, lift carriage and the other boxes.
- Distances are exact triangle-to-OBB. Geometry below the box base + 3 cm counts as support.

Results:
- **0 frames touching.**
- **0 frames with a box over the open shaft without the carriage under it.**
- **Minimum clearance 0.119 m.** It occurs at t 19.7 s, as the box starts down the lowerator beside the west end of the truss (y ≈ 7.25).
- Per-segment minimum clearance (m):

  | rise | bridge | lower | ground_conveyor | table_turn | settle |
  |---|---|---|---|---|---|
  | 0.186 | 0.139 | 0.119 | 0.148 | 0.351 | ≥ 0.5 |
- Support never rises above the box base (max −0.005 m). The tilted box is rested on the chute, so it never sinks in.
- Carriage vs static (carriage, shoes and cable): minimum 0.021 m. This is the shoe's back return passing the mast panel bands. The shoes and cable are also tested against every box, and the box clearances are unchanged from v5.1.
- The largest yaw step is 4.45°/frame, during `table_turn` only.

## Budget
- 3,908 tris, 4 draws: `Bridge_Static` and `Bridge_Moving` with SHM_Paint + SHM_GlowCyan each.
- 72,916 B.
- Extensions: KHR_mesh_quantization and EXT_meshopt_compression only. No Draco, images, textures, transmission, clearcoat or ior.

## Game view (Cam_Target (313.1, 2.08, 13.55), frame_w 37.5; camera unchanged)
All numbers are edge-sampled over every clip sample (re-measured for v5.2: unchanged from v5.1) (`proofs/refinery_bridge_dumpbay_check.json`). The dump bay outline is drawn orange in the proofs.

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
  - `proofs/refinery_bridge_393x852.png` and `_375x667.png`: box_convey at t 22 s (box on the carriage, mid-descent), with band lines and the dump bay outline. **v5.2: Eevee, 24 samples.** Cycles was on hold during the Playtester runs.
  - `_before_after.png`: v5.1 vs v5.2, Eevee, t 22, lift crops at 2×.
  - `_clipcheck.json`: the 30 Hz box-vs-geometry clip check (box_path and box_convey).
  - `_closeup_4k.png`: **still v5.1** (no shoes or cable, old underside). The v5.2 re-render is queued until the heavy-render hold lifts. v5.1 (ea5b99f) 3840×2160 Cycles close-up, 64 samples, OIDN. It shows box_convey at t 22 s with Box_1 on the lift carriage mid-descent, the −32° span into the south tower, and Box_3 on the pickup turntable. Camera `--cam 32,13,33,331.8,-13.8,5.6 --lens 45`.
