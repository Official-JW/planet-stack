# RC-1 Refinery crane + 8-box pallet (`crane_refinery_game.glb`)

A slewing tower crane in the median of the flatbed road at the Refinery. It moves HELIUM-3 boxes (`../cargo_box`) between its pallet and FB-05 (`../fb05`). It's a **code-driven rig with no baked clips**: Coder sets Slew, Trolley, Hoist and Hook.

| | |
|---|---|
| File | `crane_refinery_game.glb`: meshopt + quantization, no Draco, no images, **0 clips** |
| Budget | **2,888 tris / 2 draws** (SHM_Paint + SHM_GlowCyan), one skinned mesh, pallet included. Limit ≤3k / ≤3 |
| Root | `Crane_Refinery`. Origin = ground centre of the pedestal, +Y up. At slew 0 the jib points +X |
| World placement (Director layout) | root at **world (318, 0, 17.5)**, yaw 0, in the median between the flatbed lanes z 13 (eastbound) and z 22 (westbound) |
| Size | 13.7 m tall, jib tip r 11.25 m at y 10, pedestal 3.4 × 3.4 m (fills the 3.4 m median between berm toes), pallet 5.4 × 3.2 m at x 3.35…8.75 |

## Joints

| Joint | Parent | Channel | Meaning |
|---|---|---|---|
| `Crane_Base` | — | — | static pedestal, mast and pallet |
| `Slew` | Crane_Base | `rotation.y` = θ (rad, ±π) | cab, jib and counter-jib turn about the mast (pivot y 1.8) |
| `Trolley` | Slew | `position.x` = r (m, 2.6 … 10.3) | trolley along the jib (y 10) |
| `Hoist` | Trolley | `scale.y` = L (m, 0.6 … 8.3) | the cable hangs from the sheave (y 9.65) and is exactly L m long |
| `Hook` | Trolley | `position.y` = −1.3 − L, `rotation.y` = box_yaw − θ | hook block + spreader; origin = spreader underside = box `Hook_Point`. Hook rotator: box_yaw 0 keeps the box long axis on world +X (pallet and truck orientation) |

Hook is a sibling of Hoist, so the cable scale never scales the hook.

## Markers (crane-local glTF → world with the root at (318, 0, 17.5))

| Empty | Crane-local | World | Use |
|---|---|---|---|
| `Pick_Point` | (4.8, 0.15, −0.725) | (322.8, 0.15, 16.775) | over the pallet = `Pallet_Slot_01` (box `Base`) |
| `Pallet_Slot_01` | (4.8, 0.15, −0.725) | (322.8, 0.15, 16.775) | bottom layer |
| `Pallet_Slot_02` | (7.3, 0.15, −0.725) | (325.3, 0.15, 16.775) | bottom layer |
| `Pallet_Slot_03` | (4.8, 0.15, 0.725) | (322.8, 0.15, 18.225) | bottom layer |
| `Pallet_Slot_04` | (7.3, 0.15, 0.725) | (325.3, 0.15, 18.225) | bottom layer |
| `Pallet_Slot_05` | (4.8, 1.65, −0.725) | (322.8, 1.65, 16.775) | top layer, on 01 |
| `Pallet_Slot_06` | (7.3, 1.65, −0.725) | (325.3, 1.65, 16.775) | top layer, on 02 |
| `Pallet_Slot_07` | (4.8, 1.65, 0.725) | (322.8, 1.65, 18.225) | top layer, on 03 |
| `Pallet_Slot_08` | (7.3, 1.65, 0.725) | (325.3, 1.65, 18.225) | top layer, on 04 |
| `Drop_Point` | (−1.15, 1.9, −4.5) | (316.85, 1.9, 13) | FB-05 `Bed_Slot_01` with the truck at `Truck_Park` |
| `Drop_Point_02` | (−3.65, 1.9, −4.5) | (314.35, 1.9, 13) | FB-05 `Bed_Slot_02` |
| `Truck_Park` | (0, 0, −4.5), yaw 0 | (318, 0, 13), heading +X | FB-05 root while loading (loading spot x 318 on the z 13 lane) |

All slot markers are box `Base` positions (box yaw 0, long axis +X). Slot pitch is 2.5 m in x and 1.45 m in z (≈0.1 m gaps); the top layer sits on the bottom boxes (box height 1.5). Suggested fill order 01→08, pick order 08→01. The pallet is part of the crane GLB (static on `Crane_Base`, no extra draw). Its corner stacking guides are 0.78 m tall, so they hold the bottom layer only.

Every target solves inside the limits with 0 error (three r186): pallet r 4.85 / 7.34, L 7.05 (bottom) / 5.55 (top); Drop_Point r 4.64, L 5.3; Drop_Point_02 r 5.79, L 5.3.

## Solve (any box `Base` target P, crane-local)
```
hook target H = P + (0, box.hook_offset_y = 1.5, 0)
θ = atan2(−H.z, H.x);  r = hypot(H.x, H.z);  L = sheave_y − H.y − hook_drop_m      (sheave_y 9.65, hook_drop_m 0.95)
Slew.rotation.y = θ;  Trolley.position.x = r;  Hoist.scale.y = L;
Hook.position.y = hook_rest_local_y + 1 − L  (= −1.3 − L);  Hook.rotation.y = box_yaw − θ
```
The constants are in the root extras: limits, `sheave_y`, `hook_drop_m`, `slew_y`, `jib_y`, `hook_rest_local_y`, and a `joints` formula string.

```js
const c = crane.getObjectByName('Crane_Refinery').userData;
function aim(P, yaw = 0) { const H = P.clone().setY(P.y + 1.5);
  const th = Math.atan2(-H.z, H.x), r = Math.hypot(H.x, H.z), L = c.sheave_y - H.y - c.hook_drop_m;
  slew.rotation.y = th; trolley.position.x = r; hoist.scale.y = L; hook.position.y = c.hook_rest_local_y + 1 - L; hook.rotation.y = yaw - th; }
// carry: hook.add(box); box.position.set(0, -1.5, 0); release: fb.getObjectByName('Bed_Slot_01').attach(box)
```
Ease θ, r and the hook height with a shared smootherstep. Carry at hook y ≥ 6.2: the box bottom is then 4.7, which clears the FB-05 cab (3.8) and a full pallet (3.15). The pallet→truck swing (θ 0.15 → 1.82 rad) passes over the cab, not the mast.

## Proofs (proof-only crane_load clip, NOT in the shipped GLB)
The renders use `--proofclip`, a build with the same mesh and markers plus a 6 s crane_load clip. It lifts the top box at `Pallet_Slot_05` and lowers it onto `Drop_Point_02` (Bed_Slot_02). I used slot 02 for the proof because, in the game camera, Bed_Slot_01 sits behind the mast; slot 01 is pre-loaded. Scene: flatbed road tiles (z 13 / 22), FB-05 at Truck_Park, 6 boxes on the pallet, and the receiver (`../../crew/receiver`) in the median at crane-local (−6, 0, −0.4), playing `guide`.
- `proofs/crane_layout_phone_1179x2556.png` and `proofs/crane_layout_phone_393x852.png`: game camera (38° vFOV, 18° pitch) at t 3.8 s, box being lowered onto the bed. The subject is inside the safe area y 144–568.
- `proofs/crane_layout_phone_strip_393x852.png`: t 0 / 1.3 / 2.7 / 3.8 / 4.5 s.
- `proofs/crane_layout_contact.png`: iso, rear, top-down, pallet close-up (8 boxes), east side, west.

Renders: `../_shared_src/render_props_proof.py` (CPU Cycles, 16–24 spp, OIDN, no tiling).

## Rebuild
```
blender -b -P _src/build_crane_refinery.py -- /tmp/crane_raw.glb            # shipped: no clips
gltfpack -i /tmp/crane_raw.glb -o crane_refinery_game.glb -cc -kn -ke       # no -ac (no animation)
node ../_shared_src/verify_props.mjs crane crane_refinery_game.glb          # 8 slots, solve error + limits for every target, 0 clips, cable/hook match
blender -b -P _src/build_crane_refinery.py -- /tmp/crane_proof.glb --proofclip   # renders only
```
