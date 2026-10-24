# Crew walk-blockers: `colliders.json`

Data for crew pathing. Crew walk around buildings and never through a model. **423 colliders** in 148 object groups, plus **18 walk gaps**. Units are world glTF metres: +X right, +Z toward the game camera, Y up. Geometry is Lv1, with every `Tier_*` node hidden.

Proof: `proofs/colliders_topdown.png`, at full res. The top strip is an overview at 2 px/m and the station panels below are at 12 px/m. It is drawn over the road plan (1df3e3d), the layout_v3 flatbed lanes and U-turn, and the GLB walkable surfaces.

## How to use it

- `colliders[]` entries each carry an oriented `box` with `cx`, `cz`, `hx`, `hz`, `yaw_deg`, `y_min` and `y_max`.
  - `hx` and `hz` are half-extents and already include the **0.3 m pad**.
  - `yaw_deg` is three.js `rotation.y`. Local +X maps to world (cos yaw, −sin yaw).
  - `y_min` and `y_max` are the geometry height range over that footprint.
- `hull` is optional. It is a convex polygon of `[x, z]` points in world space, padded. When an entry has one, use it instead of the box. The hulls cover round tanks, columns and rounded ends (96 entries).
- `group` marks one connected object. Large or concave objects are split into convex parts until each box is ≥ 70% filled (≥ 78% for parts over 20 m²).
- `kind` is one of `structure`, `prop`, `linear` (pipe, fence, rail or berm segment), `round`, `pit` (dug below ground) or `placeholder`.
- `near` names the closest marker node.
- `dynamic` is set on the ship entries (`launch_pad_ship_*`). They block only while the ship is on the pad.
- `walk_gaps[]` uses the same box convention, with **no** pad. A point inside a gap is always walkable, even inside a collider.
  - `cuts` lists the colliders that a gap opens.
  - Crew-spot and door gaps (`kind: corridor`) run from 0.5 m behind the marker out to clear ground. `clear_from_m` is the distance at which clear ground starts.
  - `cab_door` gaps are 1.2 × 1.2 m step-out pads on both sides of the HT-04 / FB-05 cab, at each truck stop pose. The cab door is at truck-local x 2.6 m, and the body half-width is 2.0 m.
- `road_overlaps[]` lists colliders that touch the approved road bands.

## Method (`_src/`)

1. `raster.mjs` uses Node three.js with the Meshopt decoder, following the dock team's `hmap.mjs` pattern. It only reads the GLBs. Each GLB is placed at its world position and every triangle is sampled at ≤ 0.1 m. A 0.2 m cell **blocks** when any sample falls in the **crew body band y 0.35–2.0 m**:
   - anything lower counts as a step, slab or road you walk on (the pad apron at 0.25–0.3 m, for example);
   - anything higher counts as overhead and does not block (bridge deck at 7.25 m, crane jibs, gantry beam, pipe racks), so only legs, piers and footings block;
   - a cell whose only geometry is below −0.35 m is marked as a pit.
   - Cranes have their hook and hoist hidden, since those move. The bridge `Box_1-3` boxes are hidden too. The ship is rasterized on its own.
2. `fit.py` does the fitting:
   - a 3×3 closing joins thin walls;
   - enclosed holes are filled when they are roofed (≥ 60% of cells covered above 2 m, as in halls, container stacks and the AL-2 airlock), have no walking-level floor (berm crest, tank tops), or are under 4 m². Open enclosures with a floor stay open, such as the pad interior and the dock gantry yard;
   - objects less than 0.6 m apart are grouped, because nothing fits through once both sides are padded;
   - each group gets a min-area oriented box (convex hull plus rotating calipers), with recursive splitting as above;
   - a hull is added when the box fill is under 0.86 and the hull fill is ≥ 0.85;
   - every shape gets the 0.3 m pad.
   - The gaps and checks come last.
3. `debug_png.py` draws the proof.

Rerun: `cd _src && nice -n 19 node raster.mjs cfg.json /tmp/coll_r && nice -n 19 python3 fit.py /tmp/coll_r && nice -n 19 python3 debug_png.py /tmp/coll_r`. It runs on the CPU in about 1 min, with no Blender and no lock.

## Sources

Station positions:

- `art/3d/vehicles/ship_transporter/proofs/transport_road_plan.json` @ **1df3e3d**. This is the road v2 the Director approved at 13:31, with the v3 station table.
  - Positions: Life Support 0, Mine 160, Refinery 320, Launch Pad 457, Shipyard 960, Habitat 1068, Engineering 1120.
  - 3c7df36 is the same road but still had the Habitat at x 800, inside the road corridor.
- Cargo Dock, SC-1, RC-1 and the flatbed lanes come from `cargo_dock/layout_v3` @ **cae8f39**: dock at (360, −8), SC-1 at (384.6, 8.5), RC-1 at (311, 17.5).

| item | GLB | md5 | entries | position source |
|---|---|---|---|---|
| life_support | `qa3d/models/life_support_adfaac9.glb` | e8427ec4 | 98 | road plan @ 1df3e3d (road v2 approved) station_x_table (x 0, z 0); GLB = the one qa3d-next loads (models/life_support_adfaac9.glb via <base href=../qa3d/>) |
| mine | `art/3d/buildings/mine/mine_game.glb` | ef45f6f1 | 14 | road plan @ 1df3e3d (road v2 approved) station_x_table (x 160, z 0) |
| refinery | `art/3d/buildings/refinery/refinery_game.glb` | 93c44166 | 50 | road plan @ 1df3e3d (road v2 approved) station_x_table (x 320, z 0) |
| refinery_bridge | `art/3d/buildings/refinery/refinery_bridge_v5_3.glb` | 5d862767 | 2 | bridge v5.3 GLB root is pre-translated to Refinery-local (12.28, 0, 12.25); added under the Refinery station at world (320, 0, 0) per its own placement_world |
| crane_rc1 | `art/3d/props/crane_refinery/crane_refinery_game.glb` | 755815ec | 5 | cargo_dock layout_v3 cae8f39 cfg_world_v3 RC-1 (311, 17.5) = qa3d-next CRANE_ART crane [-9, 17.5] from Refinery x 320, yaw 0 |
| cargo_dock | `art/3d/buildings/cargo_dock/layout_v3/cargo_dock_compact_v3.glb` | 9fb1ddbe | 50 | cargo_dock layout_v3 cae8f39 (dock at x 360, z -8; overrides road plan v2's 373) |
| crane_sc1 | `art/3d/buildings/cargo_dock/storage_crane/storage_crane.glb` | fad409cc | 1 | cargo_dock layout_v3 cae8f39 cfg_world_v3 SC-1 (384.6, 8.5), yaw 0 |
| launch_pad | `art/3d/buildings/launch_pad/launch_pad_game.glb` | 82131aba | 69 | road plan @ 1df3e3d (road v2 approved) station_x_table (x 457, z 0); GLB = the committed one qa3d-next loads |
| launch_pad_ship | `art/3d/buildings/launch_pad/launch_pad_game.glb` | 82131aba | 16 | Ship_Placeholder inside the pad GLB (Ship_Center pad-local (0, -13)); dynamic: only while the ship is on the pad |
| shipyard | `art/3d/buildings/shipyard/shipyard_game.glb` | c0e9d54e | 116 | road plan @ 1df3e3d (road v2 approved) station_x_table (x 960, z 0) + its GLB c0e9d54e |

The ship rows read `launch_pad_game.glb` too, keeping only the `Ship_Placeholder` subtree.

## Walk gaps

- `gap_ls_airlock` (Life Support): Airlock_Door: crew door at the back of the covered entrance porch (railings x +-1.5, roof y 4.1, steps to z 11.6). The gap is 4.4 × 1.6 m, with clear ground 3.5 m out. It cuts: life_support_13_prop, life_support_16_prop, life_support_17_prop, life_support_18_prop.
- `gap_mine_operator_deck` (Mine): Operator_Deck (operator crew spot). The gap is 0.9 × 1.2 m, with clear ground 0.0 m out. It cuts: nothing.
- `gap_dock_door` (Cargo Dock): Dock_Door (hall front, faces +Z toward the gantry yard). The gap is 2.8 × 2.0 m, with clear ground 1.9 m out. It cuts: cargo_dock_31_structure.
- `gap_pad_ladder_foot` (Launch Pad): Ladder_Foot: caged ladder to the hatch at y 21.9 (ship on pad). The gap is 0.9 × 1.2 m, with clear ground 0.0 m out. It cuts: launch_pad_ship_12_prop.
- `gap_pad_receiver_home` (Launch Pad): Receiver_Home at the AL-2 airlock door (east face). The gap is 0.9 × 1.2 m, with clear ground 0.0 m out. It cuts: launch_pad_69_prop.
- `gap_pad_receiver_spot` (Launch Pad): Receiver_Spot (faces the FB-05 bed). The gap is 0.9 × 1.2 m, with clear ground 0.0 m out. It cuts: nothing.
- `gap_shipyard_hall_door` (Shipyard): Hall_Door (AH-1 hall, faces +Z). The gap is 2.0 × 2.0 m, with clear ground 1.1 m out. It cuts: shipyard_14_structure.
- `gap_shipyard_hall_door_front` (Shipyard): Hall_Door_Front (forecourt). The gap is 0.9 × 2.0 m, with clear ground 0.0 m out. It cuts: nothing.
- There are 10 cab-door pads at the Mine load, Refinery dump, RC-1 park, SC-1 dock stop and pad truck stop. All are clear except `gap_cab_refinery_rc1_park_R`: the FB-05 right door at RC-1 opens onto the bridge's median conveyor slab, and the gap cuts `refinery_bridge_02_structure`. The left (driver) door is clear.
- No GLB marks a ramp. The pad note says the ladder is "no ramp". The LS entrance porch steps (y ≤ 0.2) and the pad apron (y 0.25–0.3) are under the band, so they are walkable.

## Road check

The roads must stay walkable. Colliders that touch the approved road bands are listed below. All of them sit in the 3.4 m flatbed median at the Refinery (z 15.8–19.2), and only their edges reach the lane edges:

- `refinery_bridge_02_structure` on flatbed lane E z 13: 2.75 m²
- `crane_rc1_01_prop` on flatbed lane E z 13: 2.12 m²
- `crane_rc1_02_prop` on flatbed lane E z 13: 0.25 m²
- `crane_rc1_03_prop` on flatbed lane E z 13: 0.25 m²
- `refinery_bridge_02_structure` on flatbed lane W z 22: 4.12 m²
- `crane_rc1_01_prop` on flatbed lane W z 22: 3.19 m²
- `crane_rc1_04_prop` on flatbed lane W z 22: 0.5 m²
- `crane_rc1_05_prop` on flatbed lane W z 22: 0.5 m²

The bridge lowerator and ground-conveyor slab has a raw z range of 15.9–19.1, so only its 0.3 m pad crosses the lanes, by 0.2 m. The RC-1 mast footing (raw ±1.8 m about z 17.5) and its four pallet bollards (y 0.9, at z 16.0 and 19.0) reach the lane edges to within one 0.2 m cell, and their pad crosses by up to 0.3 m. The lanes stay open, at 5.6 m wide minus at most 0.3 m on one side. If Coder needs the lanes exactly clear, clip these boxes at z 15.8 and z 19.2.

- The ST-10 transporter road (x 486.4–880.1, 41.2 m graded) has no colliders on it.

## Unresolved

- Habitat: no GLB, collider = road-plan gray box placeholder (1068, 0) 9 x 12 x 9
- Engineering: no GLB, collider = gray box placeholder (1120, 0) 10 x 10 x 8
- Launch Pad Lv1 elevator tower / launch_pad_game_lv1door.glb is uncommitted (other agent): pad uses the committed launch_pad_game.glb 82131aba; its ladder is the ship-side caged ladder (Ladder_Foot gap)
- qa3d-next still loads Shipyard bcbd0934 and the old dock_tankfarm (7959ae74): colliders follow the approved layout GLBs (Shipyard c0e9d54e per the road plan, Dock compact_v3 9fb1ddbe)
- HB-10 Lv10 high bay (road plan proposal) has no GLB and is not Lv1: no collider
