# RC-1 Refinery crane (`crane_refinery_game.glb`)

A slewing tower crane that loads HELIUM-3 boxes (`../cargo_box`) onto FB-05 (`../fb05`). It's a **code-driven rig**: set Slew, Trolley, Hoist and Hook from your own timestamps. The baked `crane_load` clip is optional and exists only for the proof; the joints work without it. Station placement is **not done yet** because the Director is still choosing the road route.

| | |
|---|---|
| File | `crane_refinery_game.glb`: meshopt + quantization, no Draco, no images |
| Budget | **2,552 tris / 2 draws** (SHM_Paint + SHM_GlowCyan), one skinned mesh. Limit ≤3k / ≤3 |
| Root | `Crane_Refinery`. Origin = ground centre of the pedestal, +Y up. At slew 0 the jib points +X |
| Size | 13.7 m tall (A-frame + beacon), jib tip r 11.25 m at y 10, counter-jib 4.6 m, pedestal 3.4 m wide |
| Clip | `crane_load`: 6.0 s, 30 fps, 15 tracks, loops seamlessly (first key = last key). Optional |

## Joints

| Joint | Parent | Channel | Meaning |
|---|---|---|---|
| `Crane_Base` | — | — | static pedestal and mast |
| `Slew` | Crane_Base | `rotation.y` = θ (rad, ±π) | cab, jib and counter-jib turn about the mast (pivot y 1.8) |
| `Trolley` | Slew | `position.x` = r (m, 2.6 … 10.3) | trolley along the jib (y 10) |
| `Hoist` | Trolley | `scale.y` = L (m, 0.6 … 8.3) | the cable hangs from the sheave (y 9.65) and is exactly L m long |
| `Hook` | Trolley | `position.y` = −2.3 + 1 − L, `rotation.y` = box_yaw − θ | hook block plus spreader. Its origin is the spreader underside, where the box's `Hook_Point` attaches. The rotation is a hook rotator: with box_yaw 0, the box stays aligned with the pick pad and the truck |

Hook is a sibling of Hoist, so the cable scale never scales the hook.

## Markers (crane-local, glTF)

| Empty | Position | Use |
|---|---|---|
| `Pick_Point` | (−6.5, 0, −3) | box `Base` on the pick pad (behind-left, away from the game camera) |
| `Drop_Point` | (6.5, 1.9, 3.5) | box `Base` on FB-05 `Bed_Slot_01` when the truck is at `Truck_Park` |
| `Drop_Point_02` | (4.0, 1.9, 3.5) | helper, beyond the spec: FB-05 `Bed_Slot_02` |
| `Truck_Park` | (7.65, 0, 3.5), yaw 0 | helper, beyond the spec: FB-05 root pose while loading (heading +X) |

If the Director's road puts the truck somewhere else, the helpers are only a suggestion. Aim at the truck's own `Bed_Slot_0x` world positions with the solve below.

## Solve (any box `Base` target P, in crane-local coordinates)
```
hook target H = P + (0, box.hook_offset_y = 1.5, 0)
θ = atan2(−H.z, H.x);  r = hypot(H.x, H.z);  L = sheave_y − H.y − hook_drop_m      (sheave_y 9.65, hook_drop_m 0.95)
Slew.rotation.y = θ;  Trolley.position.x = r;  Hoist.scale.y = L;
Hook.position.y = hook_rest_local_y + 1 − L  (= −1.3 − L);  Hook.rotation.y = box_yaw − θ
```
Every constant is in the root extras: `limits`, `sheave_y`, `hook_drop_m`, `slew_y`, `jib_y`, `hook_rest_local_y`, a `joints` formula string, and `crane_load_schedule`. Clamp r and L to the limits. The pick and both drop targets solve with 0 error (verified in three r186).

```js
const c = crane.getObjectByName('Crane_Refinery').userData;
function aim(P, yaw = 0) { const H = P.clone().setY(P.y + 1.5);
  const th = Math.atan2(-H.z, H.x), r = Math.hypot(H.x, H.z), L = c.sheave_y - H.y - c.hook_drop_m;
  slew.rotation.y = th; trolley.position.x = r; hoist.scale.y = L; hook.position.y = c.hook_rest_local_y + 1 - L; hook.rotation.y = yaw - th; }
// carry: hook.add(box); box.position.set(0, -1.5, 0); release: fb.getObjectByName('Bed_Slot_01').attach(box)
```
Ease between poses yourself (smootherstep works well). Drive θ and r with a shared ease so the hook travels in a clean arc.

## crane_load (proof clip, optional)
0 s: hovering over Pick_Point (hook y 5.6). 0.9 s: down at the box. 0.9–1.3 s: latch. 2.1 s: lifted. 3.3 s: slewed and trolleyed over Drop_Point. 4.1 s: lowered onto Bed_Slot_01. 4.1–4.5 s: release. 5.0 s: up. 6.0 s: back over Pick_Point (same as frame 0). **The box rides the hook from 0.9 to 4.5 s.** Parent it at 0.9 s and hand it to the bed slot at 4.5 s. The hook rotator is keyed, so the hook's world yaw stays 0 throughout (verified, max 0 rad).

## Proofs
- `proofs/crane_load_phone_1179x2556.png` and `proofs/crane_load_phone_393x852.png` (Lanczos): the game camera (38° vFOV, 18° pitch) at t = 3.8 s, with the crane lowering a HELIUM-3 box onto FB-05 Bed_Slot_01 while slot 02 is already loaded. The subject sits inside the safe area (y 144–568 at 393×852).
- `proofs/crane_load_phone_strip_393x852.png`: t = 1.3 / 2.7 / 3.8 / 4.5 s.
- `proofs/crane_load_contact.png`: six clip times from a 3/4 view.

Renders: `../_shared_src/render_props_proof.py` (CPU Cycles, 16–24 spp, OIDN, no tiling).

## Rebuild
```
blender -b -P _src/build_crane_refinery.py -- /tmp/crane_raw.glb          # add --noclip for a rig without crane_load
gltfpack -i /tmp/crane_raw.glb -o crane_refinery_game.glb -cc -kn -ke -ac
node ../_shared_src/verify_props.mjs crane crane_refinery_game.glb        # solve error, limits, cable/hook match, rotator, clip loop
```
