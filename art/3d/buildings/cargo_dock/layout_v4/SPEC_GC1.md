# GC-1 overhead bridge crane (layout v4, Lv1): rig, clips, limits

GC-1 is the big gantry crane on the dock hall front that Jacob likes. In v4 it keeps its look (twin white box girders, end carriages, cab, trolley house with cyan trim, warn lamps, "GC-1 40 t" stencil), but it now runs as an **overhead bridge crane on an elevated runway**. It does every Lv1 cargo move with the **real CargoBox** (`site/box.glb`, the same model FB-05 carries and SC-1 handled). SC-1 and its apron are retired.

## Rig (inside `cargo_dock_overhead_v4.glb`, node `GC_Rig` under `DockTankFarm`)
```
GC_Rig (0,0,0)
 ├─ GC_Bridge      translation z = bridge position (rest 12.4, range 3.8..21.0)
 │   └─ GC_Trolley translation (x, 11.5, 0): trolley x (rest 0, range -5.2..5.2)
 │       └─ GC_Hook translation (0, hook_y - 11.5, 0): rest hook_y 7.0, carry 6.0
 │           └─ Hook_Attach  (0,0,0). Parent the CargoBox here at (0,-1.5,0) -> its Hook_Point (0,1.5,0) sits on Hook_Attach.
 ├─ GC_Mesh        one skinned SHM_Paint mesh (1 draw), 672 verts / 352 tris, joints [GC_Bridge, GC_Trolley, GC_Hook]
 └─ GC_Bridge2_Stub (0, 9.75, 3.8) extras {tier 5, cap_t 40}: Lv5 second bridge marker
```
- Skin weights are rigid (1 joint per vertex). Bridge: girders, end carriages, cab, lamps, trolley rails. Trolley: trolley frame, house, drum. Hook: new graphite/cyan hook block (0.9 × 0.45 × 0.6) + steel hook. The four ropes run from the drum (y 11.2, trolley joint) to the block top (hook joint), so they stretch with the hook.
- Bind pose = rest pose (bridge z 12.4, trolley x 0, hook 7.0). The rest moved from z 9.0 to 12.4, the middle of the 3.8..21 work range, so the empty approach and return legs are at most 8.6 m each (they were 12 m). No rotation channels on any joint, so the box yaw is always 0.
- glTF-validator: 0 errors, 1 warning `NODE_SKINNED_MESH_NON_ROOT` (the skinned mesh lives under `DockTankFarm`/`GC_Rig`). three.js handles this (SkinnedMesh bind mode "attached"); the parent transforms are identity.
- Removed from the v3 gantry: legs, bogies, wheels, braces, ties, ladder, cable reel, ground rails, spreader + twistlocks, the generic 20 ft container, and the old `crane_gantry_move` clip.

## Runway (static, merged into `Base_Paint` / `Base_Metal` / `Base_GlowCyan`, 0 extra draws)
- Two white box beams at dock-local x ±7.2 (0.6 wide), y 8.95..9.61, steel rail to **9.75** (end-carriage bottom). They run z **2.0..22.9** (world z -6.0..14.9), with graphite/cyan end stops at both ends.
- Columns (0.6 × 0.6, graphite footing 1.0 × 1.0 × 0.38, cap, inner cyan stripe) at z **2.6, 7.0, 16.4** on both sides. The z 7.0 column keeps 0.73 m from Crew_Path_04→05. The z 2.6 column keeps 0.95 m from the airlock shower posts and 1.55 m from Crew_Path_02→03. Columns at z 8.5..11.4 would cut the crew path, so none are there.
- From the z 16.4 column (footing to z 16.9, inside the 17.2 clear-strip line) the runway **cantilevers 6.5 m over the loaded lane**, with a knee brace each side. Lowest overhead surface over local z > 17.2 is **6.77 m** (knee brace). Beams are at 8.89 m and up. Precedent: SC-1 jib ≥ 6.3 m, refinery bridge. The runway ends at world z 14.9, before the empty-lane band (19.7).

## Stations
| Node | Dock-local | World | Hook_Attach y |
|---|---|---|---|
| `Truck_Stop_Dock` (FB-05 origin, heading +X) | (2.4, 0, 21) | **(362.4, 0, 13)** | — |
| `Pick_A` = Bed_Slot_01 | (1.25, 1.9, 21) | (361.25, 1.9, 13) | 3.40 |
| `Pick_B` = Bed_Slot_02 | (-1.25, 1.9, 21) | (358.75, 1.9, 13) | 3.40 |
| `Slot_01..20` | see `cargo_dock_slots_lv1_v4.json` | | 1.62 (tier 1) / 3.12 (tier 2) |

## Clips (80, 22.0 s each: heavy bridge-crane timing, re-keyed 10/24 2:29 PM)
Clip names are `Store_{A|B}_Slot_NN` (bed → slot) and `Load_{A|B}_Slot_NN` (slot → bed). Each clip has 3 translation channels: GC_Bridge (z), GC_Trolley (x) and GC_Hook (y, plus small x/z sway offsets). They are baked as CUBICSPLINE with exact tangents of the analytic motion (`_src/v4_layout.mjs` `pose()`). Playback in three.js stays within 0.22 mm of the analytic curve, and holds and events are exact. Clip extras: `duration_s` 22, `events {pick 6.0, set 17.2}`, `segments`, `from`, `to`.

Motion style:
- **Bridge and trolley travel** use easeInOutSine.
- **Hook lowers:** a main lower, then the last **0.15 m at a 0.25 m/s landing creep**, then a 0.2 s touchdown to zero speed at contact.
- **Hoists:** the mirror of the lower: a 0.15 m take-up creep at 0.25 m/s off the bed or slot, then the main hoist.
- **Sway:** at carry height before every lower, a short **damped sway settle** runs along the last travel direction. It starts at 0.04 m empty and 0.07 m loaded and is exactly zero before the lower starts, so pick and set accuracy is unchanged.

**Segment table, per box (identical for all 80 clips):**

| Segment | t (s) | dur (s) | Motion |
|---|---|---|---|
| approach | 0.00–2.80 | 2.8 | bridge z + trolley x from rest to over the pick (easeInOutSine); hook 7.0 -> carry 6.0 |
| settle pick | 2.80–3.40 | 0.6 | empty hook damped sway (0.04 m, along the approach) dies out at carry |
| lower | 3.40–5.80 | 2.4 | hook carry -> pick: main lower, then 0.15 m landing creep at 0.25 m/s, 0.2 s touchdown |
| pick hold | 5.80–6.20 | 0.4 | latch; pick event 6 (parent box to Hook_Attach) |
| hoist | 6.20–8.60 | 2.4 | hook pick -> carry 6.0: 0.15 m take-up creep at 0.25 m/s, then main hoist |
| travel | 8.60–13.60 | 5.0 | bridge z + trolley x to over the slot (easeInOutSine), hook at carry 6.0 (box base 4.5) |
| settle set | 13.60–14.60 | 1.0 | loaded damped sway (0.07 m, along the travel) dies out at carry |
| set lower | 14.60–17.00 | 2.4 | hook carry -> slot: main lower, then 0.15 m landing creep at 0.25 m/s |
| set hold | 17.00–17.40 | 0.4 | unlatch; set event 17.2 (unparent box at the target) |
| up | 17.40–19.20 | 1.8 | empty hook target -> carry (easeInOutSine) |
| return | 19.20–22.00 | 2.8 | bridge/trolley/hook back to rest (z 12.4, x 0, hook 7.0), easeInOutSine |

Box rule for the game: before **6.0** the box sits at the start (bed for Store, slot for Load). From 6.0 to **17.2** it is a child of Hook_Attach at (0,-1.5,0). From 17.2 it sits at the target. One truck (2 boxes) is Store_A_Slot_N then Store_B_Slot_N+1, **44 s**. Loading out is the reverse: Load_A_Slot_N then Load_B_Slot_N-1 (LIFO).

**Peak speeds (measured in three.js at 120 Hz over all 80 clips).**
- **Bridge:** 4.8 m/s on the approach and return, **5.4 m/s** on the longest travel (17.2 m). It was 12.9.
- **Trolley:** ≤ 2.4 m/s.
- **Hook:** ≤ **3.8 m/s** on the main part of a full 4.38 m tier-1 lower or hoist (it was 12). The last and first 0.15 m always move at 0.25 m/s.
- **Sway:** ≤ 0.43 m/s.

Real 40 t bridge cranes run slower (about 1–1.5 m/s bridge, 0.1–0.3 m/s hoist). That is not reachable at about 22 s per box: one worst-case cycle covers 34.4 m of bridge travel and about 15 m of hook travel. A full 0.25 m/s lower alone would take 10–17.5 s for each of the four vertical moves. The creep therefore covers only the landing and take-up, where the eye judges weight. If Director wants slower, play the clips with `timeScale` < 1. Events scale with it, and every crane time in the dwell table below stretches by 1/timeScale.

## Dwell at the dock stop (FB-05 arrive → depart), exact
Truck numbers come from the game's own flatbed code (`qa3d-next/main.js` e69ef53: `TV`, `TURN_ACC`, `kin()`), re-run by `_src/dwell_v4.mjs` on the real route (Refinery load x 318 → dock stop x 362.4 → pad unload x 476.5, lane z 13). Crane times come from the clip segments above.
- FB-05 brakes and pulls away at **2.5 m/s²** from **8.33 m/s**. The brake-in is **3.332 s over 13.878 m**, and the pull-away is the same.
- Stop margins use the game's own `TV.settle` of 0.4 s. GC-1 starts 0.4 s after the truck stops. The truck leaves 0.4 s after the last bed contact is clear: box B at carry for a store, the empty hook back at carry for a load.
- The JSON copy is `cargo_dock_slots_lv1_v4.json` → `dwell`. In the tables, t = 0 is the truck stopped at `Truck_Stop_Dock` and negative t is braking in.

**Store (2 boxes, bed → Slot_N, Slot_N+1)**

| t (s) | event |
|---|---|
| -3.332 | arrive: start braking 13.88 m before the stop, 8.33 -> 0 m/s at 2.5 m/s^2 |
| 0.000 | stopped at Truck_Stop_Dock (362.4, 0, 13) |
| 0.400 | stop settle 0.4 s (TV.settle) done; Store_A_Slot_N starts |
| 6.400 | pick A (Bed_Slot_01) |
| 17.600 | set A in Slot_N |
| 22.400 | Store_A ends at rest; Store_B_Slot_N+1 starts |
| 28.400 | pick B (Bed_Slot_02): bed empty |
| 31.000 | box B at carry (base 4.5, clears the FB-05 cab 3.8) |
| 31.400 | depart margin 0.4 s done: pull-away starts |
| 34.732 | back at 8.33 m/s, 13.88 m past the stop |
| 44.400 | GC-1 back at rest (box B set in Slot_N+1 at 39.6); the truck does not wait for this |

**Load (2 boxes, Slot_N, Slot_N-1 → empty bed)**

| t (s) | event |
|---|---|
| -3.332 | arrive: start braking 13.88 m before the stop |
| 0.000 | stopped at Truck_Stop_Dock |
| 0.400 | stop settle 0.4 s done; Load_A_Slot_N starts (crane at rest until the truck has stopped) |
| 17.600 | set A on Bed_Slot_01 |
| 22.400 | Load_A ends; Load_B_Slot_N-1 starts |
| 39.600 | set B on Bed_Slot_02: bed full |
| 41.600 | hook back at carry (6.0, 2.6 m over the box tops) |
| 42.000 | depart margin 0.4 s done: pull-away starts |
| 44.400 | GC-1 back at rest |
| 45.332 | back at 8.33 m/s |

| | store | load |
|---|---|---|
| standing still at the stop | **31.4 s** | **42 s** |
| arrive → depart (brake-in start → back at 8.33 m/s) | **38.064 s** | **48.664 s** |
| added to the FB-05 trip vs driving past (27.76 m takes 3.332 s at 8.33 m/s) | 34.732 s | 45.332 s |
| GC-1 busy (settle + 2 clips) | 44.4 s | 44.4 s |

Legs: Refinery → dock 8.662 s and dock → pad 17.029 s, against 22.36 s straight through. In a store, the truck leaves before GC-1 sets box B (39.6) and returns to rest (44.4). Nothing else uses the bed, so the truck never waits on that.

**Throughput.**
- **GC-1 moves 2.73 boxes/min** (22 s per box, 44 s per 2-box truck), in either direction.
- **Mining supplies at most 0.84 boxes/min** (1 sealed box per HT-04 dump; fastest dump gap = fill floor 15 s (Chute Lv11) + trip 56.62 s = 71.62 s). The hard cap is 1.06 boxes/min (zero fill, one dump per HT-04 trip).
- GC-1 therefore has **3.26× headroom** at the peak (2.57× at the hard cap) and is busy at most 30.7% of the time.
- GC-1 finishes a 2-box truck in 44.4 s, well before the next FB-05 can arrive (loop ≥ 87.77 s), so **GC-1 is never what halts mining.** Mining stops only when all 20 slots are full (and the pad side cannot take boxes).

**Flatbed vs the Refinery pallet (cap 8).**
- FB-05 loop: 87.77 s with no dock stop, **122.5 s** with a store stop, **133.1 s** with a load stop. The base loop is 2 × 6 s Refinery load + drive out + 4 s walk-out + 2 × 6 s pad unload + drive back, from the live cargo constants.
- At the mining peak, mining needs 143.24 s to make 2 boxes. The loop stays ahead by 20.74 s (store) and 10.14 s (load), so the pallet does not back up.
- **Plainly:** in the theoretical zero-fill case (2 boxes every 113.24 s), back-to-back store stops would fall 9.26 s behind per loop and fill the pallet after about 100 min. That limit is the flatbed's dwell, not GC-1 capacity.

## Limits checked (`_src/verify_v4.mjs`, three.js playback of all 80 clips at 60 Hz)
- 80 clips × 1321 frames (60 Hz over 22 s). Hook_Attach error at the pick and set events (and the hold edges): **max 3.8e-7 m** (< 1e-6, same limit as SC-1). Box yaw 0° (no rotation channels).
- Carried box during travel and the loaded sway settle: ≥ 2.88 m over stored boxes (fill order, LIFO for Load), ≥ 2.71 m over any dock geometry (0.1 m height raster), ≥ 1.24 m over FB-05. Side gap to neighbour boxes while lowering into a slot: 0.46 m. Tier-2 sets always land on a stored tier-1 box (0 unsupported).
- Gap to the other box on the bed while lowering/hoisting: 0.10 m (bbox 2.4 m; true 2.3 m box gives 0.20 m). That is FB-05's own bed spacing, the same as with SC-1.
- Empty hook block over the truck / bed boxes: ≥ 2.60 m except at its own pick.
- Bridge sweep: girders (bottom 9.93) and cab (bottom 8.15) clear all static dock geometry under their sweep by ≥ 0.975 m.

## Lv5 second crane (cap 40)
`GC_Bridge2_Stub` marks a **second bridge + trolley on the same runway** (Director: a second bridge, not a jib). It parks at the hall end (bridge z 3.8). Open points for Lv5, not built: the two bridges cannot pass, so GC-1 keeps every truck move and GC-2 only works the hall-side rows (a hand-off rule is TBD). The runway is long enough for both (z 2.0..22.9).
