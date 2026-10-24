# FB-05 flatbed hauler (`fb05_game.glb`)

A flatbed sibling of HT-04. It reuses HT-04's cab, chassis, six wheels and SHM_Paint, so the scale and style match exactly. The flatbed carries two HELIUM-3 cargo boxes (`../cargo_box`). It's a rig only: no motion is baked in, and code drives everything.

| | |
|---|---|
| File | `fb05_game.glb`: meshopt + KHR_mesh_quantization, no Draco, no images |
| Budget | **7,865 tris / 2 draws** (10/23 PM detail pass: SHM_Paint vertex colours + SHM_Glass tinted glass; was 3,500 / 1). Limit ≤8.5k / ≤3 (`verify_props.mjs`) |
| Packed | 91,140 B, md5 `7de100d5f8196d01ca194e31c5d53f7a` |
| Root | `FB05` (armature). Origin is ground centre between the axle groups. **+X forward (yaw 0)**, +Y up, left = −Z |
| Size | 8.8 m long (x −5.09 … +3.69), 3.8 m wide incl. mirrors (z ±1.90), 3.79 m tall, deck top y 1.90 |
| Clips | none |

## Joints

| Joint | Parent | Use |
|---|---|---|
| `FB05_Chassis` | — | whole body (rarely moved; a bob or tilt can go here) |
| `FB05_Wheel_FL` / `FB05_Wheel_FR` | Chassis | front axle, x +2.40, z ∓1.5 |
| `FB05_Wheel_ML` / `FB05_Wheel_MR` | Chassis | mid axle, x −1.35 |
| `FB05_Wheel_RL` / `FB05_Wheel_RR` | Chassis | rear axle, x −2.70 |

The names mirror HT-04's `HT04_Wheel_*` with an `FB05_` prefix. Wheels spin about **local +X**. A positive angle rolls the truck forward (+X). Use `wheel.rotation.x += distance / wheel_radius`, with `wheel_radius = 0.853` from the root extras.

## Markers (empties)

| Empty | Local position (glTF) | Use |
|---|---|---|
| `Bed_Slot_01` | (−1.15, 1.90, 0) | front box: the box `Base` goes here (box yaw 0 = long axis along the truck, label to +Z) |
| `Bed_Slot_02` | (−3.65, 1.90, 0) | rear box |

To load a box, parent it to the slot (`slot.add(box)`) or copy the slot's world matrix onto the box root.

## Root extras
`wheel_radius` 0.853, `wheel_axle_height` 0.85, `deck_top_y` 1.9, `bed_slots`, `capacity_boxes` 2, plus `origin` and `wheels` notes.

## three.js (r186)
```js
loader.setMeshoptDecoder(MeshoptDecoder);
const fb = (await loader.loadAsync('fb05_game.glb')).scene;
const wheels = ['FL','FR','ML','MR','RL','RR'].map(k => fb.getObjectByName('FB05_Wheel_' + k));
const R = fb.getObjectByName('FB05').userData.wheel_radius;
// every frame: fb.position.x += v*dt; wheels.forEach(w => w.rotation.x += v*dt / R);
fb.getObjectByName('Bed_Slot_01').add(box1);
```

## Proofs
- `proofs/fb05_contact.png`: five views with 2× HELIUM-3 on the slots.
- The in-scene phone proof (crane loading the truck) is in `../crane_refinery/proofs/`.

## Rebuild
```
cd art/3d/props/fb05/_src
gltfpack -i ../../ht04/ht04_game.glb -o /tmp/ht04_plain.glb -noq -kn -ke     # unpack (Blender can't read meshopt)
blender -b -P build_fb05.py -- /tmp/ht04_plain.glb /tmp/fb05_raw.glb
gltfpack -i /tmp/fb05_raw.glb -o ../fb05_game.glb -cc -kn -ke
node ../../_shared_src/verify_props.mjs fb05 ../fb05_game.glb
```

## Detail pass (10/23 PM)
Same kit as HT-04 (`../ht04/_src/detail_pass.py fb05`, see `../ht04/README.md`): autonomy sensors, manual-cab details, SHM_Glass, treads, hub detail; rear: chevron bumper with lidar pucks, mud-flap chevron bands, rear camera, deck panel lines. Joints, markers (`Bed_Slot_01/02` unchanged) and root extras unchanged. Rebuild: `build_fb05.py` from the **base** HT-04 (`build_ht04.sh` → `$W/ht04_base.glb`), unpack with `gltfpack -noq -kn -ke`, then `detail_pass.py fb05`, then `gltfpack -cc -kn -ke`.
Proofs: `proofs/fb05_detail_closeup_3840x2160.png`, `proofs/trucks_before_393x852.png` / `proofs/trucks_after_393x852.png`.
