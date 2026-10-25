# Cargo Dock v4 → Coder handoff (layout 887a609: Dock at x 480)

Not committed. Written 10/25 01:4x PT.

## GLB
- Path: `art/3d/buildings/cargo_dock/layout_v4/cargo_dock_overhead_v4.glb` (commit 921f631)
- md5 `c16d8565bef3cea94aa51784de8ba865`, 579,680 B. meshopt + quantization.
- Slots/clip JSON: `art/3d/buildings/cargo_dock/layout_v4/cargo_dock_slots_lv1_v4.json` (md5 `2791e6a8c4d5c460deca6f98ddbb1b43`).
  Its `*_world` values are for the old placement (Dock at x 360). For x 480, add +120 to every world x.
- Placement: root at world **(480, 0, −8)**. The v4 layout puts the Dock 8 m behind the station line so the truck stop lands on the z 13 lane.

## Truck_Stop_Dock
- Node `Truck_Stop_Dock`, Dock-local (2.4, 0, 21) → world **(482.4, 0, 13)** with the root at (480, 0, −8).
- Heading +X (yaw 0, direction (1, 0, 0)), on the loaded lane z 13. No pull-off.
- Its extras still say world (362.4, 0, 13); that is the old layout, so ignore it.
- Picks: `Pick_A` (1.25, 1.9, 21) = Bed_Slot_01 and `Pick_B` (−1.25, 1.9, 21) = Bed_Slot_02. The box Base goes there, and the hook attaches 1.5 m higher.
- Road band: no Dock ground geometry at local z > 17.2 (world z > 9.2). Only the runway cantilever passes over the z 13 lane, at y ≥ 6.77.

## Dwell (truck stationary at Truck_Stop_Dock)
- **Store** (unload 2 boxes into Slot_N, N+1): **31.4 s**.
  - 0.4 s settle, Store_A 0.4–22.4, Store_B from 22.4. Box B reaches carry at 31.0, then a 0.4 s margin and pull-away.
  - The crane is busy until 44.4 s; the truck doesn't wait for it.
- **Load** (2 boxes from Slot_N, N−1 onto the empty truck): **42.0 s**.
  - 0.4 s settle, Load_A 0.4–22.4, Load_B 22.4–44.4. The hook is back at carry at 41.6 s, then a 0.4 s margin and pull-away.
- Braking 3.332 s / 13.88 m in and pull-away 3.332 s / 13.88 m out (v 8.33, 2.5 m/s²).
- The JSON's `dwell.source.route` leg times were worked out for the old order (Dock 360, Pad 480). Re-derive the legs for Refinery 318 → Dock 482.4 (164.4 m) → Pad stop 636.5 (154.1 m).

## Clips (82)
- `Store_{A|B}_Slot_NN`, bed → slot, 40 clips, **22.0 s** each. A = Bed_Slot_01, B = Bed_Slot_02.
- `Load_{A|B}_Slot_NN`, slot → bed, 40 clips, **22.0 s** each.
- Events inside every Store/Load clip: **pick 6.0 s**, **set 17.2 s**. Key times are 0, 2.8, 3.4, 5.8, 6.2, 8.6, 13.6, 14.6, 17, 17.4, 19.2, 22.
- Parent the CargoBox to `Hook_Attach` at (0, −1.5, 0) between pick and set. Before pick and after set it sits at the bed slot or the storage slot.
- `Beacon_Lights_Blink` **1.5 s** loop. `dock_door_open` **2.5 s**, play once / reverse.
- Joints are on the Dock's own mixer (`GC_Rig`: GC_Bridge z → GC_Trolley x → GC_Hook y → Hook_Attach). Hide `Tier_*` by default. `GC_Bridge2_Stub` is Lv5 only.

## Storage branch (which clip pair to play at the stop)
- 20 slots under the GC-1 runway: blocks L/R (local x ∓4.25), rows local z 3.8 / 5.6 / 7.4 / 9.2 / 11, tiers y 0.12 / 1.62.
  - Fill order: Slot_01..05 left low (hall → front), 06..10 right low, 11..15 left top, 16..20 right top.
- **Loaded truck (2 boxes on the bed) and storage has room (count ≤ 18):**
  - Play **Store_A_Slot_{n+1}** then **Store_B_Slot_{n+2}** (n = boxes stored).
  - Dwell 31.4 s, then the truck goes on empty.
- **Empty truck and storage has ≥ 2 boxes:**
  - Play **Load_A_Slot_{n}** then **Load_B_Slot_{n−1}** (LIFO, 20 → 01).
  - Dwell 42.0 s, then the truck goes on loaded.
- Otherwise there's no stop at the Dock: drive through on the lane.

## Camera (Art, 01:29)
The v4 still sits to the left: about 8 px of margin on the left and 85 px on the right at 375. Move the camera centre x from 489.5 to about 484.6 (Dock + 4.6 m) to centre it, keeping frame width 48.
