# Cargo Dock layout v2: Refinery | Cargo Dock | Launch Pad (proposal, stills only)

> **Superseded for framing by `../layout_v3/` (10/24): compact dock `cargo_dock_compact_v3.glb`, dock camera frame_w 48.** The v2b camera below was rejected.

Jacob's new order: the **Cargo Dock sits directly right of the Refinery with nothing between them**, and the Launch Pad comes next.
The Cargo Dock stores refined cargo boxes that are not on the ship. **The Lv1 cap is locked at 20 boxes.** No game GLB changed.
All numbers are world glTF metres (+X right, +Z toward the camera).
Models: Cargo Dock `dock_tankfarm_game.glb` **882c8e27** (git 8ca81ac; this is the version that was in the tree at eedd8e5), Refinery 93c44166, bridge **bc081489**, Launch Pad 82131aba, Shipyard c0e9d54e, RC-1 crane plain, FB-05 plain.

## Proposed positions
| Station | Origin X (world) | Z | Footprint X | Edge gap to the left neighbour |
|---|---|---|---|---|
| Refinery (unchanged) | 320 | 0 | 274.0 - 338.25 (bridge bc081489 to 338.25) | - |
| **Cargo Dock** | **373** | **-8** | 348.25 - 421.0 (storage apron 343.7 - 357.7) | **5.45 m** from the bridge edge to the apron (10.0 m to the dock body) |
| **Launch Pad** | **457** | 0 | 427.6 - 486.4 | **6.6 m** from the dock |
| Habitat (gray placeholder, unchanged) | 800 | 0 | 795.5 - 804.5 | - |
| Shipyard (unchanged) | 960 | 0 | 908.0 - 1021.9 | 421.6 m from the pad (transport road) |

- Origin-to-origin spacing: Refinery to Dock **53 m**, Dock to Pad **84 m** (it was 160 m per slot).
- The stations leave the i*160 grid. The game would need a per-station X table, with the Dock at index 3 and the Pad at index 4. That code change is for Coder.
- **Dock z -8** keeps its front (yard pad edge at local z 16.94, which becomes world 8.94) out of the flatbed road band (z 10.2 - 24.8). It also meets Jacob's ≥1 m clear-ground rule (z ≤ 9.2).

## Storage (Lv1 = 20 slots, `cargo_dock_slots_lv1.json`)
- The storage apron sits at Dock-local x -29.3..-15.3, z 1.0..15.6, with a 0.12 m slab. This is free ground left of the yard, between the power mast and RAD-1/yard.
- Layout is 5 columns × 2 rows × 2 high. Each slot is the box `Base` (bottom centre), yaw 0, using the CargoBox 2.4 × 1.5 × 1.34 m.
  - Columns at local x -27.7 / -25.0 / -22.3 / -19.6 / -16.9.
  - Rows at z 14.5 (front) / 12.75 (back).
  - Tiers at y 0.12 / 1.62.
- Numbering:
  - Slot_01-05: front row, low tier, left to right.
  - Slot_06-10: back row, low tier.
  - Slot_11-15: on top of 01-05.
  - Slot_16-20: on top of 06-10.
  - Fill order is 01 to 20.
- In the future dock GLB, these become 20 empties `Slot_01..Slot_20` under one `Storage` node, with one shared CargoBox mesh instanced per filled slot.
- Room to grow: 5 more rows (z 10.95 / 9.2 / 7.45 / 5.7 / 3.95) fit on the same apron at +10 slots per row, 2 high. That is up to 70 slots at 2 high, or 105 at 3 high. Director sets the maximum.

## Stills
- `cargo_dock_layout_v2_topdown.png`: the plan, with stations, the haul road, the FB-05 route plus the pad U-turn, the planned ST-10 transport road, the buried fuel lines, the spacing and the slot-numbering diagram. It is a max-height raster of the actual GLBs at these positions (`_src/hmap.mjs` then `_src/layout.py`).
- `refinery_view_375x667@2x.png`: the Refinery game camera (ct world 318.9, 2.08, 13.55 = local -1.1/2.08/13.55, frame_w 38.25). The dock starts 5.45 m beyond the right edge of this frame, so it is not visible here.
- `refinery_dock_pair_375x667@2x.png`: ct (342, 3, 2), frame_w 72. Refinery plus bridge, then the full storage apron, then the dock, side by side.
- `cargo_dock_storage_full_375x667@2x.png` (750×1334) and `cargo_dock_storage_full_393x852@3x.png` (1179×2556): the **v2b dock camera** (Director fix, 12:09). The whole dock GLB, the full 20-box stack, the SC-1 storage crane and the FB-05 at the dock stop all fit inside the framing band. `cargo_dock_storage_full_framing_guides.png` draws the band, the 5 px limit and the subject bounds on both sizes.
- The game-camera stills come from three.js with the game's camera rule, lights and tone mapping (`_src/game_cam_page.html` + `_src/shot.js`, 375×667 at DPR 2). The road strips are flat proxies.

## Conflict check (numbers from `_src/chk.py` -> `_src/conflict_bands.txt`)
1. **Flatbed route: OK after the dock's z -8 shift.**
   - With the dock at z 0, its yard front (z 16.94) would sit 6.7 m into the z 13 lane band.
   - At z -8 there are zero dock or pad cells in the band from x 340 to 429. The pad's only hit is its own Road_UTurn mesh (h 0.30).
   - The route gets 16 m shorter: tiles x 296-464 (21 × 8 m, was 23), Truck_Stop x 453.5 (was 476.5), pad U-turn centre x 458, r 4.5.
2. **Dock to flatbed hand-off: not solved.** The front storage row (world z 6.5) is 6.5 m off the z 13 lane, and GC-1 (rails at dock-local x ±7.2) cannot reach the apron. A dock crane or a dock stop is needed to put boxes into the slots.
3. **Haul road: OK.** HT-04 stays at x ≤ 321, z 0 / 9 (Refinery U-turn r 4.5 about 316.5, 4.5).
4. **Bridge bc081489: OK.** It ends at x 338.25, 5.45 m clear of the apron.
5. **Launch Pad spacing: OK** (6.6 m to the dock). Pad `Road_Entry` (409, 13) is only a marker in front of the dock; the band is clear.
6. **Fuel line: the pad's end is on the wrong side.** Dock `Pipe_LaunchPad` is at (420, 1.2, 0.1), but the pad's `Pipe_LaunchPad_End` is at (477.3, 0.95, -9.6), on the pad's right. That means a 58 m buried run under the ship. The pad end should move to the pad's left (about x 430).
7. **Transport road exit is blocked at the pad.**
   - The pad's right-side rack/fuel structure (world x 470-482 = pad-local 13-25, z -30..-4, up to 4.3 m), Tier_08 (pad-local x 10.1-16.2, z -27.1..-18.6, 5.2 m), Hose_LOX/LCH4 (to local x 14.3) and `Fuel_Hookup` (460.85, -15.0) all sit inside the ST-10 corridor (ship axis z -13 ± 18, as in `vehicles/ship_transporter` `build_road(half=18)`).
   - These need to retract or move left/front.
8. **Habitat placeholder** (x 795.5-804.5, z ±4.5) overlaps a straight z -13 corridor (z -31..5). The road jogs to z -24 there (corridor -42..-6, 1.5 m clear).
9. **Shipyard door is too narrow.**
   - `Hall_Door` is (940.6, 4.9) with an opening of 10.3 m (L -24.61 / R -14.27 local). The pad ship's legs span 18.5 m (r 9.26) and ST-10 is about 26.6 m wide.
   - Structures in front of the door (x 916-920 / 924-946, z 16-28, up to 9.9 m) leave only about 8-14 m of approach depth (door front z 8.4), not the 36 m corridor.
   - This is for the transport-road and Shipyard owners.
10. **Dock model version.**
    - 882c8e27 is the older LH2 build, with footprint x -24.75..48 and `Pipe_LaunchPad` at local (47, 1.2, 8.1).
    - The live game uses fd286b9 / 7959ae74 (methalox LCH4, x -18.2..39.5, Cam_Target (12, 6, 2) with frame_w 64). With that build, the same X 373 / z -8 still works: the apron at -29.3 sits outside its -18.2 edge, so the apron edge moves 0 m and the dock body gets 6.6 m narrower.

## Dock camera v2b (replaces the f3478cf dock still's ct (359, 3, -1) / frame_w 52, which cropped the dock)
- **ct world (380.95, 1.5, 25.35)**, which is **dock-local (7.95, 1.5, 33.35)**, with **frame_w 74.5**. Game rule: 38° vFOV, 18° pitch, camera on +Z.
  - The look-at point sits out on the road because the framing band's centre is above the screen centre. ct is just the aim point at screen centre.
  - For a CAM_OVERRIDE, use `ct: {x: 7.95, y: 1.5, z: 33.35}, frame_w: 74.5` relative to the dock origin.
- **Subject:** every vertex of the dock GLB (882c8e27, x 348.25-421, up to 16.6 m), the 20 boxes, the apron, the SC-1 crane over all 40 clips (with the carried box), and the FB-05 at `Truck_Stop_Dock`. Bounds are measured on the convex hull of all points (`_src/dump_frame_points.mjs` -> `_src/frame_solve.py`, result `dock_camera_v2.json`).

| Size | Band y | Subject px (x0, y0, x1, y1) | Spare L | Spare R | Spare T | Spare B |
|---|---|---|---|---|---|---|
| 375×667 | 144-383 | 10.2, 202.2, 364.6, 324.8 | **10.2** | **10.4** | **58.2** | **58.2** |
| 393×852 | 165-534 | 8.6, 282.2, 386.0, 416.8 | **8.6** | **7.0** | **117.2** | **117.2** |

- Width is the binding limit: the tightest edge is 7.0 px, at the right edge at 393. The smallest frame_w that still keeps 5 px everywhere is 73.8.

## Storage crane and flatbed dock stop
- **SC-1 storage crane:** `../storage_crane/storage_crane.glb` (3 draws). It stands at world (350.7, 0, 8.5), dock-local (-22.3, 0, 16.5), in front of the stack's centre column. Its footing ends at z 9.2. See `../storage_crane/SPEC.md`.
- **Flatbed dock stop:** `Truck_Stop_Dock`, world (352.6, 0, 13.0), dock-local (-20.4, 0, 21.0), on the loaded lane z 13, heading +X. Both FB-05 bed slots are within reach (r 4.56 / 4.83).
  - This answers conflict 2 above: dock to flatbed hand-off is now solved for Lv1.
  - A crane-reach note remains: future rows beyond the Lv1 rows need SC-2.
- These values are also in `cargo_dock_slots_lv1.json` (`dock_camera_v2`, `storage_crane`, `truck_stop_dock`).
