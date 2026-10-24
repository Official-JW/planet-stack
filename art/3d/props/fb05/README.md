# FB-05 flatbed hauler (`fb05_game.glb`)

A flatbed sibling of HT-04. It reuses HT-04's cab, chassis, six wheels and SHM_Paint, so the scale and style match exactly. The flatbed carries two HELIUM-3 cargo boxes (`../cargo_box`). It's a rig only: no motion is baked in, and code drives everything.

| | |
|---|---|
| File | `fb05_game.glb`: meshopt + KHR_mesh_quantization, no Draco, no images |
| Budget | **3,500 tris / 1 draw** (SHM_Paint, vertex colours; cyan strips are paint, as on HT-04). Limit ≤4k / ≤3 |
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
