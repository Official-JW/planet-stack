# GC-1 overhead bridge crane (layout v4, Lv1): rig, clips, limits

GC-1 is the big gantry crane on the dock hall front that Jacob likes. In v4 it keeps its look (twin white box girders, end carriages, cab, trolley house with cyan trim, warn lamps, "GC-1 40 t" stencil), but it now runs as an **overhead bridge crane on an elevated runway**. It does every Lv1 cargo move with the **real CargoBox** (`site/box.glb`, the same model FB-05 carries and SC-1 handled). SC-1 and its apron are retired.

## Rig (inside `cargo_dock_overhead_v4.glb`, node `GC_Rig` under `DockTankFarm`)
```
GC_Rig (0,0,0)
 ├─ GC_Bridge      translation z = bridge position (rest 9.0, range 3.8..21.0)
 │   └─ GC_Trolley translation (x, 11.5, 0): trolley x (rest 0, range -5.2..5.2)
 │       └─ GC_Hook translation (0, hook_y - 11.5, 0): rest hook_y 7.0, carry 6.0
 │           └─ Hook_Attach  (0,0,0). Parent the CargoBox here at (0,-1.5,0) -> its Hook_Point (0,1.5,0) sits on Hook_Attach.
 ├─ GC_Mesh        one skinned SHM_Paint mesh (1 draw), 672 verts / 352 tris, joints [GC_Bridge, GC_Trolley, GC_Hook]
 └─ GC_Bridge2_Stub (0, 9.75, 3.8) extras {tier 5, cap_t 40}: Lv5 second bridge marker
```
- Skin weights are rigid (1 joint per vertex). Bridge: girders, end carriages, cab, lamps, trolley rails. Trolley: trolley frame, house, drum. Hook: new graphite/cyan hook block (0.9 × 0.45 × 0.6) + steel hook. The four ropes run from the drum (y 11.2, trolley joint) to the block top (hook joint), so they stretch with the hook.
- Bind pose = rest pose (bridge z 9, trolley x 0, hook 7.0). No rotation channels on any joint, so the box yaw is always 0.
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

## Clips (80, 8.0 s each)
Names are `Store_{A|B}_Slot_NN` (bed → slot) and `Load_{A|B}_Slot_NN` (slot → bed). Each clip has 3 translation channels (GC_Bridge, GC_Trolley, GC_Hook) on shared key times. Easing is **smoothstep per segment**, baked as CUBICSPLINE with zero tangents, which evaluates exactly to 3s²−2s³. Clip extras: `duration_s`, `events {pick 1.95, set 5.75}`, `from`, `to`.

| Segment | t (s) | Motion |
|---|---|---|
| approach | 0.00–1.40 | bridge + trolley from rest to over the pick; hook 7.0 → carry 6.0 |
| lower | 1.40–1.90 | hook down to the pick (bed 3.40, or slot 1.62/3.12 for Load) |
| pick hold | 1.90–2.05 | **pick event 1.95**: parent the box to Hook_Attach |
| hoist | 2.05–2.55 | hook up to carry 6.0 (box base 4.5) |
| travel | 2.55–5.15 | bridge z + trolley x to over the target, hook at carry |
| set lower | 5.15–5.70 | hook down into the slot / onto the bed |
| set hold | 5.70–5.85 | **set event 5.75**: release the box at the target |
| up | 5.85–6.35 | hook back to carry |
| return | 6.35–8.00 | back to rest (z 9.0, x 0, hook 7.0) |

Box rule for the game: before 1.95 the box sits at the start (bed for Store, slot for Load). From 1.95 to 5.75 it is a child of Hook_Attach at (0,-1.5,0). From 5.75 it sits at the target. One truck (2 boxes) = Store_A_Slot_N then Store_B_Slot_N+1 = 16 s. Loading out is the reverse: Load_A_Slot_N then Load_B_Slot_N-1 (LIFO).

Peak speeds with these timings (smoothstep peak = 1.5 × distance / time): bridge up to 12.9 m/s on the rest→stop approach, 9.9 m/s on the longest travel (z 21 → 3.8); hook up to 12 m/s on a tier-1 set. That reads arcade-fast. If it looks too quick in game, play the clips with `timeScale` < 1 (events scale with it) rather than re-baking.

## Limits checked (`_src/verify_v4.mjs`, three.js playback of all 80 clips at 60 Hz)
- Hook_Attach error at the pick and set events (and the hold edges): **max 3.8e-7 m** (< 1e-6, same limit as SC-1). Box yaw 0° (no rotation channels).
- Carried box during travel: ≥ 2.88 m over stored boxes (fill order, LIFO for Load), ≥ 2.71 m over any dock geometry (0.1 m height raster), ≥ 1.24 m over FB-05. Side gap to neighbour boxes while lowering into a slot: 0.46 m. Tier-2 sets always land on a stored tier-1 box (0 unsupported).
- Gap to the other box on the bed while lowering/hoisting: 0.10 m (bbox 2.4 m; true 2.3 m box gives 0.20 m). That is FB-05's own bed spacing, the same as with SC-1.
- Empty hook block over the truck / bed boxes: ≥ 2.60 m except at its own pick.
- Bridge sweep: girders (bottom 9.93) and cab (bottom 8.15) clear all static dock geometry under their sweep by ≥ 0.975 m.

## Lv5 second crane (cap 40)
`GC_Bridge2_Stub` marks a **second bridge + trolley on the same runway** (Director: a second bridge, not a jib). It parks at the hall end (bridge z 3.8). Open points for Lv5, not built: the two bridges cannot pass, so GC-1 keeps every truck move and GC-2 only works the hall-side rows (a hand-off rule is TBD). The runway is long enough for both (z 2.0..22.9).
