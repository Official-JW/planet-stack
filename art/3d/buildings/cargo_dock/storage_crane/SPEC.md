# SC-1 Cargo Dock storage crane: spec for Coder

`storage_crane.glb` (md5 d74ab995..., built by `_src/build_storage_crane.py`) is an original low-poly slewing jib crane. It moves cargo boxes from the parked FB-05 flatbed into the Lv1 storage slots (Slot_01..Slot_20).

- Style: the dock's white / navy / orange / cyan palette, with soft vertical vertex-colour gradients.
- Materials: `SHM_Paint`, `SHM_Metal` and `SHM_GlowCyan`, the same names and values as the dock.
- Mesh: one skinned mesh with 3 primitives, so **3 draws** and 464 tris. No textures. glTF-validator reports 0 errors and 1 warning (the skinned mesh is not a root node; this is harmless in three.js).

## Placement
| What | World (layout v2) | Dock-local (dock at 373, 0, -8) |
|---|---|---|
| Crane root `StorageCrane` (pillar base, yaw 0) | (350.7, 0, 8.5) | (-22.3, 0, 16.5) |
| Footing pad | x 350.0..351.4, z 7.8..**9.2** | keeps the 1 m clear strip in front of the road band (z ≥ 10.2) |
| **Flatbed dock stop `Truck_Stop_Dock`** | **(352.6, 0, 13.0)**, heading +X on the loaded lane z 13 | (-20.4, 0, 21.0) |
| `Pick_A` = FB-05 `Bed_Slot_01` box Base | (351.45, 1.9, 13.0) | |
| `Pick_B` = FB-05 `Bed_Slot_02` box Base | (348.95, 1.9, 13.0) | |

The flatbed stops at `Truck_Stop_Dock` on its way east (Refinery load x 318, then this stop, then the pad Truck_Stop at 453.5) whenever boxes go to storage instead of the ship. Both bed slots are reachable from this one stop, so the truck does not need to creep forward.

The crane GLB also carries `Truck_Stop_Dock`, `Pick_A`, `Pick_B` and `Slot_01..Slot_20` as empties in crane-local coordinates. For each slot, the empty sits where the CargoBox Base goes (yaw 0), matching `../layout_v2/cargo_dock_slots_lv1.json`. A future dock GLB can carry the same Slot nodes; the values are identical.

## Rig (node: what drives it)
- `SC_Base`: static parts (pad, pillar).
- `SC_Slew` at (0, 6.3, 0): **rotation.y = slew θ**. At θ = 0 the jib points world +X (rest).
- `SC_Trolley`, child of the slew joint: **position = (r, 0.5, 0)**, where r is the radius from the pillar axis.
  - Trolley travel is about 1.9–6.95 m.
  - The rest radius is 4.0.
  - The jib underside is at y 6.8.
- `SC_Hook`, child of the trolley: **position.y = hook_y − 6.8** and **rotation.y = −θ**.
  - The counter-rotation keeps the box at world yaw 0 for any slew angle.
  - The rope is skinned between the trolley and the hook, so it stretches.
- `Hook_Attach`, child of the hook joint: where the box's `Hook_Point` goes. Parent the box here with local position (0, −1.5, 0) and identity rotation.

Angle convention (crane-local): θ = atan2(−dz, dx) and r = hypot(dx, dz) to the target. Always take the **shortest** path between angles.

## Clips (40 baked, 6.0 s each, 30 fps LINEAR samples of smoothstep segments)
Clip names are `Store_A_Slot_01..20` (picking from Bed_Slot_01) and `Store_B_Slot_01..20` (from Bed_Slot_02). Every clip starts and ends at the rest pose, so clips chain back to back. Two boxes take 12 s; do A first, then B.

| Segment | t (s) | Motion |
|---|---|---|
| approach | 0.00–1.00 | slew and trolley from rest to over the pick point, hook at carry height (5.6) |
| lower | 1.00–1.50 | hook down to `Hook_Point` (y 3.4) |
| **pick event** | **1.55** | parent the box to `Hook_Attach` |
| grab hold | 1.50–1.65 | |
| hoist | 1.65–2.15 | up to carry height (box Base 4.1) |
| swing | 2.15–3.75 | slew and trolley to over the slot |
| set | 3.75–4.30 | lower to slot Base y + 1.5 |
| **set event** | **4.35** | un-parent the box and snap it to the Slot transform (error < 1e-6 m) |
| up | 4.45–4.90 | hook back to carry height |
| return | 4.90–6.00 | back to rest |

The event times and the segment table are also in the root extras (`timeline_s`, `pick_t`, `set_t`) and in each animation's extras (`pick`, `slot`).

For a procedural drive instead of the baked clips, use the per-slot parameters in the root extras `slots[]` (or on each `Slot_NN` empty's extras): `slew_deg`, `radius_m`, `hook_y_m`, `hook_local_y_m`. Pick values are in `pick.A` / `pick.B`. Feed them through the same segment table, with smoothstep easing u²(3−2u).

Example values:
- Pick A: θ −80.54°, r 4.562, hook_y 3.4.
- Slot_01: θ 159.68°, r 5.759, hook_y 1.62.
- Slot_20: θ 34.78°, r 6.574, hook_y 3.12.

Fill order is Slot_01 to Slot_20:
- 01–05: front low tier.
- 06–10: back low tier.
- 11–15: front top tier.
- 16–20: back top tier.

## Checked (`_src/verify_storage_crane.mjs`, all 40 clips at 60 Hz)
- Hook_Attach matches the pick point at t 1.55 and the slot at t 4.35 to within 1e-6 m. Box yaw stays at 0°.
- While swinging, the carried box clears:
  - stored boxes by ≥ 0.98 m;
  - the FB-05 cab (top 3.79) by ≥ 0.31 m;
  - the pillar by ≥ 0.99 m.
- The jib and counter-jib (r ≤ 7.46 / 2.6, y ≥ 6.3) do not reach the bridge (x 338.25, 12.4 m away) or the dock mesh.
- The whole crane envelope (all clips plus the carried box) stays inside the dock camera, ct (380.95, 1.5, 25.35) with frame_w 74.5:
  - 375×667: crane px x 10.2–81.6, y 273.9–316.9. Band 144–383, so spare is L 10.2, T 129.9, B 66.1.
  - 393×852: crane px x 8.6–83.9, y 362.4–408.4. Band 165–534, so spare is L 8.6, T 197.4, B 125.6.

## Limits and notes
- **Reach covers Lv1 only** (r ≤ 6.95). The future rows in the layout (world z 2.95..−4.05) need r of about 8–13. That needs a longer jib (SC-2) or a second crane when Director raises the cap.
- The crane does not touch the existing dock GLB (882c8e27). In the layout it is a separate prop, like the 0.12 m storage apron slab.
- Stills: `stills/storage_crane_pick_swing_set_strip_375x667@2x.png` shows `Store_A_Slot_20` at t 1.50 / 2.95 / 4.30 with 19 boxes stored, with ×3 detail crops. The single frames are `stills/sc1_*`. They were rendered with three.js headless using the game camera rule.
