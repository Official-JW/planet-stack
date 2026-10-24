# HELIUM-3 cargo box (`cargo_box_game.glb`)

**This is not a new design.** It's the existing starter-ship HELIUM-3 / ³He crate (the `crate()` function plus the CrateHe3A/B/C instances in `art/3d/ship/starter_ship/build_starter_ship.py`, crate size 2.3 × 1.3 × 1.5 m). That's the most recent HELIUM-3 crate, last rendered Oct 23 2026. I rebuilt it at game LOD with the same layout and colours: #e8edf5 body, #3a4258 bands, lid and plates, #2a3245 skids, #9aa3ad handles, a cyan glow strip, "HELIUM-3" and "³He" LED lettering, and an amber hazard band. The only additions are the `Base` and `Hook_Point` empties.

| | |
|---|---|
| File | `cargo_box_game.glb`: meshopt + quantization, no Draco, no images |
| Budget | **400 tris / 2 draws** (SHM_Paint + SHM_GlowCyan) |
| Root | `CargoBox`. Origin = `Base` (bottom centre). Long axis +X, labelled faces ±Z |
| Size | 2.3 × 1.5 (h) × 1.3 m. Bbox x ±1.2 (handles), y 0…1.5, z ±0.67 |
| Clips / joints | none (rigid prop) |

## Markers

| Empty | Position | Use |
|---|---|---|
| `Base` | (0, 0, 0) | goes on `FB-05 Bed_Slot_01/02`, or on the crane's `Pick_Point` / `Drop_Point` |
| `Hook_Point` | (0, 1.5, 0) | top centre, latched to the crane's `Hook` joint |

Root extras: `size_m` [2.3, 1.5, 1.3], `hook_offset_y` 1.5.

## three.js
```js
// carry on the crane: keep the box hanging under the hook
hook.add(box); box.position.set(0, -box.userData.hook_offset_y, 0); box.rotation.set(0, 0, 0);
// set down on the truck
slot.attach(box); box.position.set(0, 0, 0); box.rotation.set(0, 0, 0);
```

## Proofs
- `proofs/cargo_box_contact.png`: front, back and top views.
- On the truck and the crane: `../fb05/proofs/fb05_contact.png` and `../crane_refinery/proofs/`.

## Rebuild
```
blender -b -P _src/build_cargo_box.py -- /tmp/cargo_box_raw.glb
gltfpack -i /tmp/cargo_box_raw.glb -o cargo_box_game.glb -cc -kn -ke
node ../_shared_src/verify_props.mjs box cargo_box_game.glb
```
