# RC-1 Refinery crane + 8-box pallet on a concrete pad (`crane_refinery_game.glb`)

A slewing tower crane in the median of the flatbed road at the Refinery, placed so the real Refinery game camera sees both FB-05 bed slots clear of the mast. It moves HELIUM-3 boxes (`../cargo_box`) between its pallet and FB-05 (`../fb05`). It's a **code-driven rig with no baked clips**: Coder sets Slew, Trolley, Hoist and Hook.

| | |
|---|---|
| File | `crane_refinery_game.glb`: meshopt + quantization, no Draco, no images, **0 clips** |
| Budget | **2,918 tris / 2 draws** (SHM_Paint + SHM_GlowCyan), one skinned mesh, pallet and concrete pad included (the pad is 30 tris on SHM_Paint, no extra draw). Limit ≤3k / ≤3 |
| Root | `Crane_Refinery`. Origin = ground centre of the pedestal, +Y up. At slew 0 the jib points +X |
| World placement (Director layout) | root at **world (311, 0, 17.5)**, yaw 0, in the median between the flatbed lanes z 13 (eastbound) and z 22 (westbound). FB-05 still parks at world (318, 0, 13). (Moved from x 318 after the game-camera check below.) |
| Size | 13.7 m tall, jib tip r 11.25 m at y 10, pedestal 3.4 × 3.4 m (fills the 3.4 m median between berm toes), pallet 5.4 × 3.2 m **west of the mast** at crane-local x −8.75…−3.35 (world 302.25…307.65), on a concrete pad 6.15 × 3.36 × 0.12 m at x −9.15…−3.0, z ±1.68 (world 301.85…308.0, z 15.82…19.18) |

## Joints

| Joint | Parent | Channel | Meaning |
|---|---|---|---|
| `Crane_Base` | — | — | static pedestal, mast, pallet and concrete pad |
| `Slew` | Crane_Base | `rotation.y` = θ (rad, ±π) | cab, jib and counter-jib turn about the mast (pivot y 1.8) |
| `Trolley` | Slew | `position.x` = r (m, 2.6 … 10.3) | trolley along the jib (y 10) |
| `Hoist` | Trolley | `scale.y` = L (m, 0.6 … 8.3) | the cable hangs from the sheave (y 9.65) and is exactly L m long |
| `Hook` | Trolley | `position.y` = −1.3 − L, `rotation.y` = box_yaw − θ | hook block + spreader; origin = spreader underside = box `Hook_Point`. Hook rotator: box_yaw 0 keeps the box long axis on world +X (pallet and truck orientation) |

Hook is a sibling of Hoist, so the cable scale never scales the hook.

## Markers (crane-local glTF → world with the root at (311, 0, 17.5))

| Empty | Crane-local | World | Use |
|---|---|---|---|
| `Pick_Point` | (-4.8, 0.27, -0.725) | (306.2, 0.27, 16.775) | over the pallet = `Pallet_Slot_01` (box `Base`) |
| `Pallet_Slot_01` | (-4.8, 0.27, -0.725) | (306.2, 0.27, 16.775) | bottom layer |
| `Pallet_Slot_02` | (-7.3, 0.27, -0.725) | (303.7, 0.27, 16.775) | bottom layer |
| `Pallet_Slot_03` | (-4.8, 0.27, 0.725) | (306.2, 0.27, 18.225) | bottom layer |
| `Pallet_Slot_04` | (-7.3, 0.27, 0.725) | (303.7, 0.27, 18.225) | bottom layer |
| `Pallet_Slot_05` | (-4.8, 1.77, -0.725) | (306.2, 1.77, 16.775) | top layer, on 01 |
| `Pallet_Slot_06` | (-7.3, 1.77, -0.725) | (303.7, 1.77, 16.775) | top layer, on 02 |
| `Pallet_Slot_07` | (-4.8, 1.77, 0.725) | (306.2, 1.77, 18.225) | top layer, on 03 |
| `Pallet_Slot_08` | (-7.3, 1.77, 0.725) | (303.7, 1.77, 18.225) | top layer, on 04 |
| `Drop_Point` | (5.85, 1.9, -4.5) | (316.85, 1.9, 13) | FB-05 `Bed_Slot_01` with the truck at `Truck_Park` |
| `Drop_Point_02` | (3.35, 1.9, -4.5) | (314.35, 1.9, 13) | FB-05 `Bed_Slot_02` |
| `Truck_Park` | (7, 0, −4.5), yaw 0 | (318, 0, 13), heading +X | FB-05 root while loading (loading spot x 318 on the z 13 lane) |

All slot markers are box `Base` positions (box yaw 0, long axis +X). Slot pitch is 2.5 m in x and 1.45 m in z (≈0.1 m gaps); the top layer sits on the bottom boxes (box height 1.5). Suggested fill order 01→08, pick order 08→01. The pallet is part of the crane GLB (static on `Crane_Base`, no extra draw). Its corner stacking guides are 0.78 m tall, so they hold the bottom layer only.

**Concrete pad (added after 014d751):** a plain slab under the pallet: 0.12 m high, 0.04 m bevel on the top edges, with edge wear as per-face vertex colour (lighter chipped and darker scuffed bevel segments on the long sides, then the shared dust pass). The root extra `concrete_pad` gives its crane-local bbox. The pallet now sits on the pad, so the pallet geometry and every `Pallet_Slot_*` / `Pick_Point` marker moved up by **+0.12 m**: bottom layer y 0.15 → **0.27**, top layer 1.65 → **1.77**. x and z didn't change, and Drop_Point, Drop_Point_02 and Truck_Park are unchanged. The pad stays in the median (z 15.82…19.18, flatbed lane corridors end at 15.8 and start at 19.2), far from the haul road lanes (z 9 and z 0), and clear of the pedestal (x ≥ 309.3).

Every target solves inside the limits with 0 error (three r186): pallet r 4.85 / 7.34, L 6.93 (bottom) / 5.43 (top); Drop_Point r 7.38, L 5.3; Drop_Point_02 r 5.61, L 5.3.

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
Ease θ, r and the hook height with a shared smootherstep. Carry at hook y ≥ 6.2: the box bottom is then 4.7, which clears the FB-05 cab (3.8) and a full pallet (3.27 on the pad). The pallet→truck swing (θ ≈ 3.0 → 0.66 rad) runs over the far side (−Z) of the mast, away from the camera.

## Game-camera check for 014d751 (Refinery bb5eed2 camera: Cam_Target (314.1, 8.5, 3.36), frame_w 30.8)
Camera: QA3D `fitSite` with the Refinery `Cam_Target` at world (314.1, 8.5, 3.36), frame_w 30.8 (38° vFOV, 18° down, d = (frame_w/2)/(tan 19° · aspect)). I checked it at 393×852 and at 375×667. The scene is the current `refinery_game.glb` (md5 e65968d7…) at +320 with tiers hidden, FB-05 at (318, 0, 13), 6 pallet boxes and the receiver. The crane is posed by the solve onto each bed slot (slot 01 already loaded when slot 02 lands). Measured with `_src/gamecam_occlusion.mjs` (BVH raycast, 3×3 per pixel over the landing box):

| Landing box | Before: crane x 318 (affea57) | After: crane x 311 |
|---|---|---|
| Bed_Slot_01, 393×852 | **38.8% hidden: mast 26.9%**, latched spreader 11.3%, FB-05 headboard 0.6% | 16.7%: mast 0, latched spreader 15.7%, headboard 1.0% |
| Bed_Slot_02, 393×852 | 16.3%: mast 0, latched spreader 15.7%, headboard 0.6% | 16.3%: mast 0, latched spreader 15.7%, headboard 0.6% |
| Bed_Slot_01, 375×667 | **37.6% hidden: mast 25.2%**, latched spreader 11.0%, headboard 1.4% | 17.1%: mast 0, latched spreader 15.0%, headboard 2.1% |
| Bed_Slot_02, 375×667 | 17.1%: mast 0, latched spreader 15.2%, headboard 1.9% | 17.1%: mast 0, latched spreader 15.2%, headboard 1.9% |

The Refinery hides 0% in every case. The remaining ~16% is the spreader frame and hook block latched on top of the box, plus FB-05's own bed headboard, both expected. After the move, the crane hides 0% of FB-05 (cab included). Before, the crane hid 13–16% of the truck (1.5–5.2% of the cab), and at slot 02 the mast also covered the slot 01 box already on the bed. The mast stays clear of the slot 02 box up to crane x ≈ 312 (it starts to clip at 312.5), so x 311 keeps about 1.4 m of margin.

## Safe band check (Refinery camera from f4d4a2c: Cam_Target (313.1, 2.08, 5.45), frame_w 34.4)
The Refinery owner re-framed the station camera in f4d4a2c, after the 014d751 check above. The checks below use that GLB (md5 b45b4649…) and its camera. The new safe band is y 165–534 at 393×852 (with the iPhone insets) and y 144–383 at 375×667:

| Frame | Safe band | Concrete pad | Loaded pallet | FB-05 | Box landing on Bed_Slot_01 |
|---|---|---|---|---|---|
| 393x852 | y 165–534 | y 489–506 inside | y 453–502 inside | y 427–487 inside | y 437–459 inside |
| 375x667 | y 144–383 | y 395–412 (**29 px** below) | y 360–408 (**25 px** below) | y 335–392 (**9 px** below) | y 344–366 inside |

- **393×852: everything is inside the band, pad included.**
- **375×667: the pad is 29 px below the band**, with the pallet 25 px and FB-05 9 px below. The landing box is inside. The band's bottom edge reaches the ground at world z ≈ 12.75, but the whole median (z 15.8…19.2: pedestal, pallet, pad) and FB-05's near side are in front of that. No pad or pallet position in the median, clear of the haul lanes (z 9 berm toe to 11.8) and the flatbed lanes, can be inside the band. Fixing it is a camera change in the Refinery `Cam_Target`, not a crane change. Checked with the current GLBs, these single-camera settings fit both bands:
  - Cam_Target z +6.4 → (313.1, 2.08, 11.85), frame_w 34.4: crane/pallet/pad/FB-05 y 310–478 at 393×852 and y 220–383 at 375×667, Refinery top y 218 / 144.
  - Cam_Target z +5.65 → (313.1, 2.08, 11.1), frame_w 36.4: y 319–478 and y 229–383, Refinery top y 228 / 153.
  
  Both settings sit right on the 383 line. For a few px of margin, use about +0.3 m more z.
- Overlays: `proofs/gamecam_safe_band_{393x852,375x667}.png`.

**Occlusion recheck with the pad and the f4d4a2c camera:** the mast hides 0% of either landing box, and the crane hides 0% of the cab and truck. Box hidden: slot 01 16.1% (spreader 13.4%, headboard 2.7%), slot 02 15.5% (spreader 13.3%, headboard 2.3%) at 393×852; slot 01 17.2% (spreader 14.6%, headboard 2.6%), slot 02 16.8% (spreader 14.5%, headboard 2.3%) at 375×667. The Refinery hides 0%.

## Proofs (proof-only crane_load clip, NOT in the shipped GLB)
The renders use the `--proofclip` build: same mesh and markers plus a 12 s crane_load. Cycle 1 lifts `Pallet_Slot_05` onto Bed_Slot_01, landing at 4.1 s. Cycle 2 lifts `Pallet_Slot_06` onto Bed_Slot_02, landing at 10.1 s. Every proof uses the real game camera, now the f4d4a2c Refinery camera (Cam_Target (313.1, 2.08, 5.45), frame_w 34.4), with that Refinery GLB, the flatbed road tiles, FB-05 at Truck_Park and the receiver (`../../crew/receiver`, suggested spot world (316.5, 0, 17.1), yaw 180°, playing `guide`).
- `proofs/gamecam_before_x318_slot0{1,2}_{393x852,375x667}.png`: landing frames, old placement (014d751-era camera (314.1, 8.5, 3.36) / 30.8 and Refinery bb5eed2; kept as the record of that check).
- `proofs/gamecam_after_x311_slot0{1,2}_{393x852,375x667}.png`: landing frames, crane at 311 with the pad, f4d4a2c camera.
- `proofs/gamecam_landing_compare.png`: 3× crops of all 8 landing frames, with the box outlined and the numbers above.
- `proofs/crane_layout_phone_1179x2556.png` and `proofs/crane_layout_phone_393x852.png`: t 4.1 s (box lands on Bed_Slot_01).
- `proofs/crane_layout_phone_strip_393x852.png`: t 0 / 1.3 / 2.7 / 4.1 / 7.5 / 10.1 / 11.0 s.
- `proofs/crane_layout_contact.png`: iso, rear, top-down, pallet close-up (8 boxes on the pad), east side, west.
- `proofs/concrete_pad_closeup.png`: low close-up of the pad, bevel and edge wear under the full pallet.
- `proofs/gamecam_safe_band_{393x852,375x667}.png`: game-camera frames at t 4.1 s with the safe band, plus the pad / pallet / FB-05 / landing-box screen boxes.

Renders: `../_shared_src/render_props_proof.py` (CPU Cycles, 16–24 spp, OIDN, no tiling).

## Rebuild
```
blender -b -P _src/build_crane_refinery.py -- /tmp/crane_raw.glb            # shipped: no clips
gltfpack -i /tmp/crane_raw.glb -o crane_refinery_game.glb -cc -kn -ke       # no -ac (no animation)
node ../_shared_src/verify_props.mjs crane crane_refinery_game.glb          # 8 slots, solve error + limits for every target, 0 clips, cable/hook match
blender -b -P _src/build_crane_refinery.py -- /tmp/crane_proof.glb --proofclip   # renders only
```
