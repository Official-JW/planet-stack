# HT-04 haul truck — shared prop (Mine + Refinery)

`ht04_game.glb`: 67,344 B, md5 `16eccb4d34c33b2d5093744fadead804`, **3,859 tris, 1 draw** (one skinned mesh `Truck_Mesh`,
material `SHM_Paint`, colours in COLOR_0, no textures). It uses EXT_meshopt_compression + KHR_mesh_quantization (gltfpack -cc -kn -ke) and no Draco.
The budget is ≤ 4k tris and ≤ 3 draws. The no-scoop body has no arm.

## Root, origin and axes
- The root node is `Truck`, an armature/skin root. It sits at the **origin = the ground point under the truck centre**: x is between the
  front axle and the rear tandem, z is the centreline, and y = 0 is the tyre contact plane.
- **Forward = +X (glTF) = yaw 0**, up = +Y, and the truck's left = −Z. The rest rotation is identity and the scale is 1 (true metres).
- **Placing it:** copy a `truck_pose` marker's world transform onto `Truck` (position = marker position, rotation = marker
  rotation, i.e. yaw about +Y). The Mine's `Path_Load`, `Path_Load_Approach`, `Path_XX` and `Road_Entry`, and the Refinery's truck markers,
  all use this convention (yaw 0 = heading +X).
- At the Mine's `Path_Load` (glTF 4.7, 0, 4.5), the bed centre sits exactly under the chute.

## Wheels (code-driven, no baked spin)
- There are 6 wheels, each its own joint: `HT04_Wheel_FL` / `HT04_Wheel_FR` (front axle, x +2.4), `HT04_Wheel_ML` / `HT04_Wheel_MR`
  (rear tandem, x −1.35) and `HT04_Wheel_RL` / `HT04_Wheel_RR` (x −2.7).
  - L is at z −1.5 (truck left) and R is at z +1.5. The axle height is y 0.85.
- **Spin axis = the joint's local +X.** In the rest pose it points to the truck's left (glTF −Z). The joint rest rotation is
  (0, 0.7071, 0, 0.7071).
  - A **positive** rotation about local X rolls the truck **forward** (+X).
  - Use `angle += distance_travelled / wheel_radius`, applied as `rest_rotation * rotX(angle)`.
- **Wheel radius (rolling radius at the tyre tread): 0.853 m.** It is in the root extras as `wheel_radius`, with
  `wheel_axle_height` 0.85.
- **No clip animates any wheel joint.**

## Fill morph
- `Truck_Mesh` has `morphTargetInfluences[0]` = target **`fill`** (with morph normals).
- **Official remap:** `influence = 0.5 + 0.5 * (fill_pct / 100) ** 0.8` for fill_pct > 0, and `influence = 0` at 0 % (empty, after a dump).
- Shapes, in metres above the ground:

  | influence | apex | relative to the rim top (3.38) |
  | --- | --- | --- |
  | 0 | 2.87 | hidden below the near rim |
  | 0.5 (first load) | 3.55 | +0.17, crowning just over the rim |
  | 1 (full) | 4.23 | **+0.85**, a conical heap |

## Clips (30 fps; each targets only its own joints)
| clip | length | joints | use |
| --- | --- | --- | --- |
| `chute_pour` | 1.2 s seamless loop | Truck_Pour_01..07 (7 chunks, alternating He-3 cyan / regolith), Truck_Dust_01..04 (dust puffs that fade by scale) | loop while parked under a chute and raise `fill` by code |
| `truck_load_rich` | 1.0 s | Truck_Rich_01..05 | rich (tapped-deposit) load drops in; pair with the Mine's `Rich_Pop` |
| `truck_dump` | 3.0 s | Truck_Bed, Truck_Load, Truck_Ram_L/R (+_Stage2, _Rod) | bed tips and the load slides out; set `fill` to 0 after it |
| `truck_drive` | 1.0 s seamless loop | Truck_Bed only | small suspension rattle of the bed while driving; **no wheel spin** (see Wheels). Don't play it together with `truck_dump` |

All chunks and dust sit hidden inside the bed (heap base) in the rest pose.

## Anchors
- `Fill_Arc`: an empty that is a child of `Truck`, at truck-local glTF **(2.2, 4.6, 0)**, 0.9 m over the cab light bar. It is the UI anchor
  for the slim cyan fill-% arc and moves with the truck.

## Build
- `_src/build_ht04.sh [WORKDIR]` runs the Mine build, which is the single source for the body, the heap and the chute chunks
  (`art/3d/buildings/mine/_src/build_mine.py`, which exports the truck via `--tout`).
- The script then packs `ht04_game.glb` with `art/3d/buildings/mine/_src/pack_mine.sh` (clip prune → gltfpack → verify JSON).
- The truck budget is `BUD['Truck']` = 3950 in build_mine.py. The heap and chunks are exempt from decimation, and the rest of the body is decimated to fit.
