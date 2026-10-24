# Cargo Dock layout v4: 20 Lv1 boxes under the hall, moved by GC-1 overhead crane

Jacob's change (relayed by Director, 10/24 1:45 PM): all 20 Lv1 boxes are stored under the main dock hall's big gantry crane (GC-1), and that crane moves the **real CargoBox** between the FB-05 flatbed at the dock truck stop and the slots, both ways. SC-1 and the side apron go unless needed. They are not needed, so both are retired.

**Director approved (10/24 2:25 PM):** the stop at world (362.4, 0, 13) and the raised GC-1 runway over the loaded lane.

**GC-1 re-keyed to heavy timing (10/24 2:29 PM):** 22.0 s per box. Motion: easeInOutSine travel, a 0.25 m/s landing and take-up creep, and a damped sway settle at pick and set. The bridge rest moved to z 12.4. Peaks: bridge 5.4 m/s, hook 3.8 m/s (they were 12.9 and 12).

The exact FB-05 dwell is in `SPEC_GC1.md` (Dwell) and in the JSON `dwell`:
- Store: 31.4 s standing, 38.064 s arrive→depart.
- Load: 42 s standing, 48.664 s arrive→depart.
- GC-1 moves 2.73 boxes/min against ≤ 0.84 boxes/min of mining supply.

Everything else stays as in v3 (cae8f39): dock at world x 360 (origin 360, 0, -8), Launch Pad at 457, camera ct (369.5, 1.5, 8.6) frame_w 48, tank farm behind the hall.

## Reach answer (does GC-1 reach the truck stop at world 386.5, 0, 13?)
**No.** Measured on the v3 GLB, dock-local (= world − (360, 0, −8)):
- The stop is local (26.5, 0, 21). The v3 gantry's rails are at x ±7.2 and the trolley reaches x ±5.2, so the stop is **19.3 m east of the rail line and 21.3 m beyond the hook's x reach**.
- Along z, the gantry's ground rails run z −2.7..14.6, so the hook reaches z ≈ 11.2 at most. That is **9.8 m short** of the loaded lane (z 21).
- Ground rails cannot be extended past local z 17.2 (1 m clear strip + road band world z 10.2–24.8).

Options checked:
| Option | Verdict |
|---|---|
| Keep the stop at 386.5 | needs a > 30 m bridge girder across x; no |
| Extend the ground rails across the loaded lane | puts dock ground geometry in the road band; breaks the road rules |
| Turn GC-1 90° (rails along x) | big change to the look Jacob likes; hits the airlock |
| Yard spur so trucks drive under the hall | changes the flatbed route |
| **Elevated runway over the lane + move the stop under it (chosen)** | minimal: no ground geometry in the band, same route, same lane |

**Chosen (minimal) option:**
1. GC-1 becomes an overhead bridge crane on an **elevated runway** (beams at x ±7.2, rail top 9.75) that runs z 2.0..22.9 local and **cantilevers 6.5 m over the loaded lane** from its last column at z 16.4. Columns stay out of the road band and the 1 m clear strip; the lowest overhead part over the road is 6.77 m (knee brace), beams 8.89 m+.
2. The dock **truck stop slides 24.1 m west along the same loaded lane** to **world (362.4, 0, 13)**, so both bed slots sit under the runway. The flatbed route and lanes are unchanged; only the stopping point moves. (The game's Truck_Stop_Dock / FB stop needs updating to 362.4. Not sent to anyone, per instructions.)

## Files
| File | What |
|---|---|
| `cargo_dock_overhead_v4.glb` | dock GLB v4, md5 see the commit report / `cargo_dock_slots_lv1_v4.json` `dock_glb_md5` |
| `cargo_dock_slots_lv1_v4.json` | 20 slots (local + world), stop, picks, rig, clip table, timeline, **dwell + throughput**, road, verify results |
| `SPEC_GC1.md` | GC-1 rig, runway, the 80 clips (timings + easing), limits checked, Lv5 stub |
| `verify_v4.json` | full output of `_src/verify_v4.mjs` |
| `cargo_dock_v4_375x667@2x.png`, `cargo_dock_v4_393x852@3x.png` | **queued, not rendered yet** (box held for the crew GLB, 10/24 2:23 PM). Game-camera stills: 18 stored, Store_A_Slot_19 mid-travel (t 11.1 of the 22 s clip), B still on the bed |
| `gc1_pick_travel_set_strip_375x667@2x.png` | **queued**. Store_A_Slot_19 (22 s clip) at t 2.8 / 6.0 / 8.6 / 11.1 / 17.2 / 19.2, full res |
| `_src/overhead_dock.mjs` | builds v4 from `../layout_v3/cargo_dock_compact_v3.glb` (9fb1ddbe) |
| `_src/v4_layout.mjs` | all v4 numbers (rig, runway, slots, clip keys) shared by builder / JSON / verifier |
| `_src/dwell_v4.mjs` | FB-05 dwell + throughput from the game's own flatbed kinematics (imported by make_slots_v4) |
| `_src/make_slots_v4.mjs`, `_src/verify_v4.mjs`, `_src/render_v4.sh`, `_src/index_v4.html`, `_src/compose_v4.py` | slots JSON, checks, stills |

Build: `node _src/overhead_dock.mjs ../layout_v3/cargo_dock_compact_v3.glb cargo_dock_overhead_v4.glb` (gltf-transform + meshoptimizer; `_src/node_modules` → `/home/box/apps/gltftools/node_modules`).

## What changed in the GLB (v3 → v4)
- **GC-1** (`Crane_Gantry` mesh + `crane_gantry_move`) → `GC_Rig`: one skinned mesh (`GC_Mesh`, 1 draw) with joints GC_Bridge → GC_Trolley → GC_Hook → `Hook_Attach`, plus 80 clips. Legs, bogies, ground rails, spreader and the generic 20 ft container are removed; girders, end carriages, cab, trolley house, stencil and lamps are the v3 faces, unchanged.
- **Runway + 6 columns** merged into the static Base meshes (0 extra draws).
- **Lv1 generic container stacks removed** (the 4 stacks at x ±4, z 3 / 9.6). The 20 CargoBox slots take their place.
- **Storage grid**: 2 blocks at x ±4.25, 5 rows z 3.8 / 5.6 / 7.4 / 9.2 / 11.0 (pitch 1.8), 2 tiers (base y 0.12 / 1.62). Box bbox 2.4 × 1.5 × 1.34, long axis +X, yaw 0. Boxes sit on the yard pad between the hall front (z −3.5) and the He3 / Pt props (z ≥ 12.6). The central lane, drop box, crew path and airlock stay clear.
  - Fill order: Slot_01..05 left low (hall → front), 06..10 right low, 11..15 left top, 16..20 right top. Load out is LIFO.
- New empties: `Truck_Stop_Dock`, `Pick_A`, `Pick_B`, `Slot_01..20`, `GC_Bridge2_Stub` (Lv5).
- `Container_Stack` marker → top of Slot_15 (−4.25, 3.12, 11.0). Scene extras: `game_nodes` pivot `Crane_Gantry` replaced by `GC_Bridge`, new markers added, new `layout_v4` block.
- **`Tier_03`** (Lv3 extra containers) sat on top of the removed stacks and would float. It now stands on the ground in the freed right area (old apron side): three containers at x 20.5 / 23.5 / 26.5, z 6.0 (bbox x 19.3..27.7, z 3.0..9.0).
- `Tier_08` (JC-2 jib, Lv8) is unchanged. Its arm ends at z 1.76, 0.24 m in front of the runway's hall-end stop (z 2.0). No overlap, but re-check if JC-2 is ever re-placed.
- `Tier_20`: same note as v3 (re-place before Lv20). Its yard stacks at x ≤ −9.18 are clear of the left runway (x −7.5).

## Draw calls (Lv1)
**7**: 4 Base + Beacon + Dock_Door + GC_Mesh. v3 was 11 (7 dock + 3 SC-1 + 1 apron). Boxes and the truck are the same as before.

## Camera (unchanged rule, ct (369.5, 1.5, 8.6), frame_w 48)
| Size | Band y | Subject px (x0, y0, x1, y1) | Spare L / R / T / B | Box width px |
|---|---|---|---|---|
| 375×667 | 144–383 | 7.9, 166.1, 289.9, 360.8 | 7.9 / 85.1 / 22.1 / 22.2 | 17.5–19.4 |
| 393×852 | 165–534 | 8.3, 241.9, 309.7, 454.4 | 8.3 / 83.3 / 76.9 / 79.6 | 18.6–20.2 |

Subject = Lv1 dock + runway, FB-05 at the new stop, 20 boxes, and the GC-1 envelope (bridge, trolley, hook, carried box) over all 80 clips. All margins ≥ 5 px, boxes ≥ 8 px. The right spare grew because the apron/SC-1 are gone and the truck moved west. frame_w is kept at 48 as asked.

## Road
No dock ground geometry at local z > 17.2 (world z > 9.2). Over the loaded lane there is only the runway cantilever (≥ 6.77 m). The runway ends at world z 14.9, before the empty-lane band.
