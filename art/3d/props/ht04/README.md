# HT-04 haul truck — shared prop (Mine + Refinery)

`ht04_game.glb`: **134,096 B, md5 `4222799b2801d40f26a313a62c42b43e`, 10,560 tris, 1 draw** (10/24 01:10 ore v3: load lifted to sRGB (100,97,92), see *Ore v3* below; 01:00 v2 was 134,292 B / md5 `5ba7c9da...`; ore v2: deposit-grey dumped pile, see *Ore v2* below; 00:40 v1 was 134,588 B / md5 `62c32238...` / 10,536 tris; 10/24 00:40 truck_pass: regolith ore + glass merged into the paint, see *Ore load / 1 draw* below; 10/23 PM detail pass was 124,876 B / 8,308 tris / 2 draws, md5 `5e5c9fe1...`; before that 67,344 B / 3,859 tris / 1 draw). One skinned mesh `Truck_Mesh`,
materials `SHM_Paint` + `SHM_Glass` (see Detail pass), colours in COLOR_0, no textures). It uses EXT_meshopt_compression + KHR_mesh_quantization (gltfpack -cc -kn -ke) and no Draco.
The budget was ≤ 4k tris and ≤ 3 draws; the detail pass takes it to ~8.3k tris (approved scope: "trucks lack detail"), draws stay ≤ 3. The no-scoop body has no arm.

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

## Detail pass (10/23 PM, Jacob: "autonomous vehicles, but they have cabs cause they can be manually driven")
`_src/detail_pass.py` (shared by HT-04 and FB-05; `python3 detail_pass.py ht04|fb05 IN_PLAIN.glb OUT_RAW.glb`, then `gltfpack -cc -kn -ke`) appends geometry at
glTF level to the existing skinned mesh, so **node names, joints, rest pose / IBMs, wheel joints, the `fill` morph and every clip are unchanged** (verified with three r186).
- Autonomy kit: roof sensor mast + spinning-lidar puck, stereo camera bar, GNSS dome, whip antenna (top y 4.21), cyan status light bar, corner lidar pucks, side camera pods, front lidar + radar panel, rear camera.
- Manual cab: door seams + gaskets + handles, amber grab handles, 3-rung ladder with amber nosing (x 1.12), mirrors with glass, tinted windshield + side/door glass, wipers, roof hatch and panel lines.
- Running gear: 14-pitch slanted tyre tread blocks, hub cap + cyan LED ring + 6 lug nuts, mud flaps with chevrons, hazard-chevron front and rear bumpers, tail lights; light dust weathering low on the paint.
- Paint geometry rides on `SHM_Paint` (COLOR_0, 100 % weight on one joint, zero `fill` deltas). The glass is a **2nd primitive, material `SHM_Glass`**
  (baseColor 0.018/0.03/0.05, metallic 0, roughness 0.1, opaque, no COLOR_0; zero `fill` target) = **+1 draw**. three loads the mesh node as a Group with 2 SkinnedMeshes
  (both carry `morphTargetDictionary.fill`, so the loader's fill traversal drives both).
- bbox grows from (−3.60…3.69, 0…3.79, ±1.90) to (−3.70…3.75, −0.02…4.21, ±1.95).
- Build: `_src/build_ht04.sh` now packs the base body to `$W/ht04_base.glb` and runs the detail pass into `ht04_game.glb`.
- Proofs: `proofs/ht04_detail_closeup_3840x2160.png`, `proofs/ht04_detail_front.png`, `proofs/ht04_detail_rear.png`, `proofs/trucks_before_393x852.png` / `proofs/trucks_after_393x852.png` (game camera 38° / 18°). Renderer: `_src/render_truck_proof.py`.


## Ore load / 1 draw (10/24 00:40, `_src/truck_pass.py --ore --merge-glass`)
Director: the load must not read as cyan gems (crystals are the paid currency). Now:
- **Bed heap (`Truck_Load`, `fill` morph):** per-face regolith palette matching the Mine deposit rock (#3f3d3b 42 %, #47443f, #373531, #504c46; 5 % faint vein faces #2f5a63), plus **26 rounded, matte rock lumps** (noisy icospheres, r 0.15-0.27 m, flattened) skinned to `Truck_Load`. Every lump vertex carries the heap's `fill` delta (IDW from the 4 nearest heap-top vertices), so the lumps stay seated at every fill value (proof `proofs/ore_after_fill025_060_1600x450.png`).
- **`chute_pour` / `truck_load_rich` chunks** (`Truck_Pour_01..07`, `Truck_Rich_01..05`): the 20-tri faceted icosahedra are replaced by rounded grey rocks with the same bind centre / size; He-3 and rich chunks keep 1-2 faint cyan veins only. Dust chunks unchanged.
- **Glass merged:** the SHM_Glass primitive is appended to the paint primitive with COLOR_0 = glass base x 1.25 (dark tinted windows, now matte-ish SHM_Paint roughness). Material `SHM_Glass` is gone: **1 primitive, 1 draw**.
- Names, joints, IBMs, `fill` morph, clips (`chute_pour`, `truck_drive`, `truck_dump`, `truck_load_rich`) unchanged; only three's auto `mesh_0_1` child disappears. Tris 8,308 -> 10,536 (+2.2k for the lumps; still well inside the prop budget).
- Proofs (Workbench, render hold): `proofs/ore_before_close_1600x900.png` / `proofs/ore_after_close_1600x900.png` (fill 1, `chute_pour` frame 18), phone view on the Mine `Path_Load`: `../../buildings/mine/proofs/mine_road_before_393x852.png` / `mine_road_after_393x852.png`.

## Ore v2 (10/24 01:00, `_src/truck_pass.py --ore --merge-glass`; proof `proofs/ore_v2_fill_vs_deposit_1600x1240.png`)

Director notes on v1 (near-black/blue, shards through the walls at 60%, vertical cliff sides at 100%) fixed:
- **Colour:** heap, 26 surface rocks and the chute_pour / truck_load_rich chunks use the Mine deposit rock's actual COLOR_0, linear u8 **(13,12,11)** (SHM_DepositRock, white base), x per-face shade 0.92-1.09. No veins, no cyan/blue anywhere in the load (check: max(B - R) over 2,470 load verts = -1). In the Workbench proof both the deposit and the ore read dark grey side by side; the in-game tone follows the scene lighting exactly as the deposits do.
- **Shape:** the `fill` morph's full target is an analytic dumped pile: crown = rim edge + tan(33°) x soft-min distance to the bed walls (soft 0.22 -> rounded crown, y≈3.90 vs rim 3.30-3.38), so it slopes down to all four walls at ~33° repose. Basis is the old flat bed floor; heap rebuilt as a 27x11 grid (520 tris, replaces 496). Rocks ride the pile surface via per-vertex morph deltas.
- **Spikes:** the morph only moves y, and every heap/rock vertex is clamped in x/z inside the bed box (x -3.24..0.04, |z| ≤ 1.21; walls -3.30/0.10, ±1.28) and y ≥ floor. Verified by sampling: in-build 21 fills and post-pack 51 fills x 1,675 load verts -> **0 violations**, worst overshoot 0.0002 m (quantisation).
- Names, joints, IBMs, morph name, clips, 1 primitive / SHM_Paint unchanged. Tris 10,536 -> 10,560.

## Ore v3 colour (10/24 01:10, `../_shared_src/regolith_grey_v3.py ht04`; proof `proofs/ore_v3_fill_vs_deposit_1600x1240.png`, game frame `../../buildings/mine/proofs/mine_ht04_full_game_375x667.png`)

Director: (13,12,11) read as coal. The whole load (heap, 26 rocks, chute_pour / truck_load_rich chunks; every vertex skinned to Truck_Load / Truck_Pour_* / Truck_Rich_*) is lifted together with the Mine deposits and conveyor lumps:
- target **sRGB (100, 97, 92)** -> COLOR_0 is linear: **(0.1274, 0.1195, 0.1070)** = u8 ~(32.5, 30.5, 27.3); stored u8 (31..34, 29..32, 26..29), i.e. the v2 shade steps compressed + a positional hash, clamped to +-6 %; R >= G > B on every vertex (0 blue / cyan verts of 2,974 load verts). Mean = sRGB (100, 97, 92).
- Neutral-light check (Workbench FLAT, Standard view): ore renders sRGB (101, 98, 93), Deposit (102, 99, 94).
- Geometry, morph, joints, clips, nodes, material, tris (10,560) and draws (1) unchanged: the triangle set (positions + fill target + joints) is identical to v2 (gltfpack only re-orders vertices).
