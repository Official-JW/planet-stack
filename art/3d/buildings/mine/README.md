# Mine station: in-game build (concept B + HT-04 truck)

The in-game **Mine** for Planet Stack, built from the approved **concept B (sleek high-tech)** master and the **HT-04** haul truck. The **Refinery is part of the Mine station**: it is a separate GLB placed at the `REFINERY_ANCHOR` empty, and trucks dump into its intake bin.

| | |
|---|---|
| **Game GLB** | `mine_game.glb`, **179,192 B (0.18 MB)**, md5 `0dcb9ef5048f828a2b43223bde1ee646` |
| Triangles / draws | **24,132 triangles, 11 draw calls with every tier visible** (11 meshes × 1 primitive) |
| Format | meshopt + quantization (`gltfpack -cc -kn -ke`). Extensions: `EXT_meshopt_compression` and `KHR_mesh_quantization` only. **No Draco.** |
| Materials | `SHM_Paint` and `SHM_GlowCyan` (`../_shared/shared_materials.json`). Plain metallic/roughness plus emissiveFactor. No transmission, clearcoat or ior. Colour is in `COLOR_0` vertex colours. **No images or textures** and no TEXCOORD. |
| Units / axes | 1 m, Y up. The origin is concept B's world origin. The camera side is +Z. |
| Bounds (glTF) | (−15.55, −0.24, −13.22) … (22.38, 21.78, 19.17). The +X / +Z growth is the access road leaving `Road_Entry`; it runs off the phone frame on the right. |
| No astronauts | The concept-B astronaut is removed. |
| Budget | Mine ≤ 25k tris / ≤ 12 draws / ≤ 550 KB. **Combined Mine + Refinery** ≤ 1.2 MB / 50k tris / 25 draws, so the Refinery has **≤ 1.02 MB, ≤ 25,868 tris and ≤ 14 draws** left. |

## Files
- `mine_game.glb`: the game asset.
- `mine_phone_1179x2556.png` (Cycles master) and `mine_phone_393x852.png` (its Lanczos downscale): the station camera view. The ground uses the shared cool-grey `M_ground` (material unchanged; only the render terrain under the road is cut ≤ a few cm so it never pokes through). The renders show the full concept-B shading. The refinery is not in these renders; the anchor area west of the rig is empty ground.
- `mine_tiers_393x852.png`: tier check, the same station camera with **every tier visible** (Cycles, 24 samples, rendered at 393×852). Made with `--mode tiers --mout DIR`, which also writes `tier_boxes.json`.
- `_src/mine_layout.py`: the station re-layout applied on top of the concept-B scene (see Layout changes), including the graded haul road (`graded_roads`, `M_road_graded`).
- `_src/build_mine.py`: does the camera fit, renders the phone shots, and builds the game GLB. That covers the material remap, tiers, culling, the per-group bake and decimation to budget, the truck armature and skin, the arm poses, the clearance checks, the clips, the markers and the export.
- `_src/mine_clips.cjs`: `prune` trims each clip to its own nodes and moving channels. `verify` writes a JSON report with tris, draws, extensions, images, clip targets and foreign targets, nodes and skins.
- `_src/pack_mine.sh`: runs prune → gltfpack → verify.
- `_src/phone_downscale.py`: makes the 393×852 from the 1179×2556 master (PIL Lanczos).

Rebuild (from the repo root, Blender 4.2):
```
B=/opt/blender-4.2.3-linux-x64/blender; S=art/3d/buildings/mine/_src
$B -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P $S/build_mine.py -- --arm park --only none --out /tmp/mine/gen --mode game --mout /tmp/mine/raw.glb --w 37
$S/pack_mine.sh /tmp/mine/raw.glb art/3d/buildings/mine/mine_game.glb
$B -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P $S/build_mine.py -- --arm park --only none --out /tmp/mine/gen --mode phone --mout art/3d/buildings/mine --ps 64 --w 37
python3 $S/phone_downscale.py art/3d/buildings/mine
```
`--w W` forces the frame width (the shipped build uses `--w 37`, locked by Director so the Refinery fits). Without it, the script picks the smallest W from 30 to 40 m that fits the focus. `--cy Y` sets the focus-box centre on 393×852 (default **460**, the middle of Director's 280–640 band).

## Station camera (Game Coder spec)
Perspective, **38° vertical FOV, tilted down 18°, aimed at `Cam_Target`**.
- **W = 37 m**: `Cam_Target` carries `extras {"frame_w": 37, "fov_y_deg": 38, "pitch_down_deg": 18, "distance_m": 116.48}`.
- **Distance** d = (W/2) / (tan 19° · 393/852) = **116.48 m**. The same value holds for 393×852 and for the 1179×2556 master, because the aspect ratio is the same.
- **`Cam_Target`** sits at glTF **(0.09, 10.36, 1.00)**, which is Blender (0.09, −1.0, 10.36). It is high above the pad on purpose: with W and d fixed, raising the aim point is what moves the station *down* the screen (it was (−0.11, 2.65, 1.00), which put the station at y 242–508).
- **Fit:** W is fixed at 37. The target is solved so the focus box is centred at y 460 on 393×852 and centred in x. The focus box holds:
  - the rig
  - the conveyor head
  - the parked truck
  - the silo
  - the haul loop to its graded edge at the east apex (the berm is open there for the access road) and to the south berm toes
  - a 3.2 × 3.2 × 3 m refinery intake-bin envelope at `REFINERY_ANCHOR`

  The fitted box is **x 26…367, y 322…598 px** (x margin check 4–96 %, y 100–650). **Director asked for y≈280–640, but at W = 37 the distance is fixed (116.48 m), so the station's on-screen height is fixed at ~276 px and cannot stretch to 360 px; moving `Cam_Target` only slides it.** 322–598 is that span centred in the 280–640 band (42 px short at each end). Reaching 280–640 would need W ≈ 28, which cuts off the Refinery and the east hairpin.

## Game GLB nodes
Everything sits under the root `Mine`. gltfpack puts each mesh on an **unnamed child node** of its named node; that child carries the quantization offset and scale. Find meshes under the named node with `traverse`. The names, pivots and extras are on the named nodes.

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint` | static base merged by material: pads, rig skirt, hopper, conveyor frame, silo base, graded roads (2,280 tris, not decimated), deposits, rocks | 9,962 | SHM_Paint | origin |
| `Base_GlowCyan` | all static cyan glow: light strips, He-3 seam crystals | 3,926 | SHM_GlowCyan | origin |
| `Rig` | bore head and crown block, the moving part of the rig (clip `dig`) | 635 | SHM_Paint | (−7.5, 8.65, −3.6) |
| `Conveyor` | belt-surface ore lumps (clip `conveyor_run`) | 160 | SHM_Paint | (−0.85, 2.55, −2.65), the tail end C0 |
| `Silo` | ore silo | 782 | SHM_Paint | (10.0, 0, −4.5), base centre |
| `Truck` | HT-04: armature root, **pivot at the ground centre** under the truck, faces **+X** | 5,847 (one skinned mesh `Truck_Mesh`) | SHM_Paint | (4.7, 0, 4.5) = `Path_Load` |
| `Tier_03…20` | see Tiers | | | |

**Truck joints** (one skin, 18 joints, rest rotations are identity; local offsets are relative to the parent):
- `Truck_Chassis` (0, 0, 0)
  - `Truck_Bed` at the **rear hinge** (−3.3, 1.72, 0); it tips about local Z, rear down.
    - `Truck_Load` (1.7, 0.27, 0): the ore heap. **Its rest pose is a full bed.**
  - `Truck_Ram_L` / `Truck_Ram_R`: the bed rams, each with a `_Stage2` and `_Rod` telescoping section.
  - `Truck_Arm` (shoulder) → `Truck_Arm_Fore` (elbow) → `Truck_Arm_Scoop` (wrist).
  - `Truck_Wheel_01..06`

**Side naming:** `_L` is the truck's left, which is glTF −Z when the truck faces +X. `_R` is the right, +Z.
- Wheels 01–03 are on the **left**, rear → middle → front (x −2.7, −1.35, +2.4).
- Wheels 04–06 are on the **right**, rear → middle → front.

## Clips
| Clip | Length | Loop | Targets (only these) | What it does |
|---|---|---|---|---|
| `dig` | 3.0 s | loop | `Rig` translation | The bore head lowers 0.6 m and comes back up (cosine). |
| `conveyor_run` | 1.0 s | loop | `Conveyor` translation | The lumps move one 0.9 m lump spacing along the belt, linear, so the loop is seamless. |
| `truck_drive` | 1.0 s | loop | `Truck_Wheel_01..06` rotation | Wheel spin, one full turn per second (≈ 5.3 m/s at r 0.85 m). Move the `Truck` node yourself along the `Path_*` markers. |
| `truck_load` | 0.8 s | once | `Truck_Load` scale | The heap grows from (0.75, 0.02, 0.75) to 1, i.e. empty to full, under the conveyor chute at `Path_Load`. |
| `truck_dump` | 3.0 s | once | `Truck_Bed` rotation, `Truck_Load` scale, rams (rotation, plus stage and rod translation) | The bed goes **0 → 50 → 0°** with ease in-out (smoothstep up and down). The load stays full to 18°, is gone by 42° on the way up, and stays empty on the way down. The rams track the bed. It reads fine at **1.5× speed** (2.0 s). |
| `truck_scoop` | 1.2 s | once | `Truck_Arm`, `Truck_Arm_Fore`, `Truck_Arm_Scoop` rotation | From the stowed pose:<br>• 0–0.47 s: reach 2.8 m out to the truck's **right** and down to the deposit.<br>• 0.47–0.67 s: curl the scoop and lift.<br>• 0.67–1.2 s: swing back. **Ends on the stowed pose.** |

**Sequence rules (game side):**
- **Scoop**, then the arm returns to stow (the end of `truck_scoop`), and only then the **bed tips**.
- **Never drive with the bed raised**: play `truck_drive` / move the truck only when `truck_dump` is finished (bed at 0°).
- The order at the dump: drive to `Path_Dump_Approach` → reverse to `Path_Dump` → `truck_dump` → drive off.
- The loaded state comes from `truck_load` at `Path_Load`, or from the scoop at a spur. After a dump, `Truck_Load` stays at scale 0 until the next `truck_load`.

## Tiers
**Frame rule (Director): every tier must land inside the station frame.** Checked by projecting every vertex of each tier with the station camera on 393×852 (all tiers visible), and in `mine_tiers_393x852.png`:

| Tier | x px | y px | In frame (y 100–650) |
|---|---|---|---|
| `Tier_03` | 181–228 | 472–486 | yes |
| `Tier_05` | 194–269 | 432–516 | yes |
| `Tier_08` | 44–111 | 423–494 | yes |
| `Tier_12` | 267–326 | 405–498 | yes |
| `Tier_20` | 82–153 | 295–381 | yes |

Every tier node has `extras {"tier": N, "hidden_by_default": true}` (three.js `userData`). glTF has no hidden flag, so the loader must set `visible = false` on load. Each tier is one draw.

| Node | Adds | Tris | Material | Pivot (glTF) |
|---|---|---|---|---|
| `Tier_03` | conveyor light kit: cyan running lights on both trough walls, plus head and tail beacons | 208 | SHM_GlowCyan | (0.84, 0, 0.39) |
| `Tier_05` | second pod hopper east of the first, plus a pneumatic feed tube onto the conveyor | 1,370 | SHM_Paint | (3.6, 0, −4.36) |
| `Tier_08` | radiator wing behind the rig power module (6 panels, mast, coolant pipe) | 272 | SHM_Paint | (−12.09, 0, −7.65) |
| `Tier_12` | second, taller ore silo behind the first, plus a transfer bridge and beacon | 686 | SHM_Paint | (10.6, 0, −9.11) |
| `Tier_20` | Mk II bore crown: bigger crown housing, twin emitter pods and a tall mast | 284 | SHM_Paint | (−7.5, 0, −3.59) |

Base 13,888 + moving 7,424 + tiers 2,820 = 24,132 tris.

## Markers (empties, glTF coords; yaw is about +Y, 0 = truck faces +X)
- **`REFINERY_ANCHOR`**: world transform **position (−13.84, 0, 5.50), rotation +90° about Y** (quaternion (0, 0.7071, 0, 0.7071)), scale 1. That is Blender (−13.84, −5.5, 0), +90° about Z.
  - It is **the Refinery GLB origin**.
  - Its local **+Z points along the truck heading (+X world)**, i.e. toward the truck's rear when the truck is at `Path_Dump`.
  - The intake bin front should sit **1.2 m** along local +Z (`extras.intake_front_offset_m`).
  - Place the Refinery with `refinery.position/quaternion = anchor.getWorldPosition/Quaternion`.
- **`Path_Dump`** (−9.0, 0, 5.5), yaw 0: the truck centre for dumping. The bed hinge is 3.3 m behind the centre, so the bed tips toward the anchor. It is 12.1 m from the conveyor head and loading point, and 17 m from the rig. The dump stub runs west past the rig's south side.
- **`Path_Dump_Approach`** (−5.0, 0, 5.5), yaw 0: stop here heading +X, then reverse 4 m to `Path_Dump`.
- **`Path_Load`** (4.7, 0, 4.5), yaw 0: under the conveyor discharge chute (`extras.chute_glTF` (3.1, 4.35, 4.5)). This is the truck's rest position.
- **`Path_01..15`**: the haul loop clockwise from the load bay. Each has `extras.yaw_deg`.
  - North line: x 5 → 8 (z 4.5).
  - East hairpin: centre (9, 9), r 4.5.
  - South straight: z 13.5, x 7.75 → −4.25.
  - West hairpin: centre (−5, 9.5), r 4.
  - Back east to (−5.25, 5.51), which joins the dump stub and the north line.

  | Marker | Position | Yaw |
  |---|---|---|
  | Path_01 | (5, 0, 4.5) | 0 |
  | Path_02 | (8, 0, 4.5) | 0 |
  | Path_03 | (11.18, 0, 5.06) | −28.9 |
  | Path_04 | (13.25, 0, 7.51) | −70.7 |
  | Path_05 | (13.16, 0, 10.72) | −112.5 |
  | Path_06 | (10.95, 0, 13.05) | −154.3 |
  | Path_07 | (7.75, 0, 13.5) | 180 |
  | Path_08 | (4.75, 0, 13.5) | 180 |
  | Path_09 | (1.75, 0, 13.5) | 180 |
  | Path_10 | (−1.25, 0, 13.5) | 180 |
  | Path_11 | (−4.25, 0, 13.5) | 180 |
  | Path_12 | (−7.35, 0, 12.74) | 144 |
  | Path_13 | (−8.97, 0, 10.0) | 97.2 |
  | Path_14 | (−8.08, 0, 6.95) | 50.4 |
  | Path_15 | (−5.25, 0, 5.51) | 3.6 |
- **Scoop spurs:** at each, stop and play `truck_scoop`, which reaches to the truck's right. These are stops on the loop, not separate roads.
  - **`Path_Spur_01`** (8.5, 0, 4.5), yaw 0, for **`Dep_01`** (8.65, −0.01, 8.65): the main He-3 seam, r 2.2 m.
  - **`Path_Spur_02`** (−1.0, 0, 13.5), yaw 180, for **`Dep_02`** (−1.2, −0.01, 10.4): the tap deposit, r 1.05 m.
- **`Road_Entry`** (13.5, 0, 9.0), yaw −90 (heading +Z): the east apex of the loop, where the graded **access road** joins. The road leaves heading +Z (toward the camera), bends east between two craters and runs off the right edge of the phone frame (it ends at about glTF x 22, z 16.4). Position unchanged.
- **`Crew_Path_01..07`**: (−9.4, 0.64, 0.2) at the rig operator pod deck → (−9.0, −0.01, 1.9) → (−5.6, 0, 2.7) → (−2.2, 0, 2.3) → (1.6, 0, −0.2) → (5.6, 0, −1.0) → (8.6, 0, −1.4) at the silo.
- **`Cam_Target`** (0.09, 10.36, 1.00), `frame_w` 37. See Station camera. **This is the only marker that moved.**

## Layout changes vs the concept-B master
These live in `_src/mine_layout.py`. The B look, palette and parts are otherwise unchanged.
- **Receiving hopper removed:** the DUMP 01 receiving hopper and its lift tube are gone. Trucks now dump into the **Refinery intake** at `REFINERY_ANCHOR`, west of the rig.
- **Head-end support replaced:** the head-end cantilever pylon and boom stood in the new road. A column with a knee brace under the trough, north of the road, replaces them.
- **Haul road re-laid:** it is now a loop (load bay → east hairpin → south straight → west hairpin → back), plus a dump stub west to the refinery, plus an access road at `Road_Entry`. The centre lines (and every `Path_*` marker) are unchanged.
- **Graded regolith road** (replaces the flat dark decal stripe). Built in `mine_layout.graded_roads` as real geometry, three meshes `haul_road_loop` / `haul_road_dump` / `haul_road_access`:
  - **Cross-section:** a 4.0 m graded running surface (the HT-04 is 3.82 m over the tyres; the old 3.2 m stripe was narrower than the truck) with a 2 cm crown, then a **low berm on each side**: foot at ±2.0 m, crest **25 cm** high at ±2.35 m, toe buried at ±2.8 m.
  - **Tyre marks:** a 2 cm rut with a darker vertex colour at ±1.5 m, the HT-04 wheel track.
  - **Colour** is in a `RoadCol` corner colour attribute (no images): track `#a4a7ac` (a little lighter than the regolith), tyre marks `#878a8f`, berm crest `#939499`, toe `#82858a`, with ±5 % low-frequency variation. The render material `B_HaulRoadGraded` multiplies it by fine gravel noise and bump; the game GLB copies it into `COLOR_0` of `Base_Paint`.
  - **Junctions:** berms flatten wherever they cross another road's running surface (loop ↔ dump stub at the west hairpin, loop ↔ access road at `Road_Entry`), so both junctions are open. Berms also flatten next to station parts (head column foot, rig feet, the two deposits) so nothing is buried.
  - The stub surface sits 2 cm under the loop where they overlap (no z-fighting). Pebbles and boulders on the road were removed (36). In the render scene the terrain under the road is cut 3 cm below the road surface wherever it bulged through (20 ground vertices); `M_ground` itself is untouched.
  - Roads skip the planar dissolve and the decimation (they would smear the ruts and berms): 2,280 tris.
- **Deposits moved:** they are inside the loop so the truck scoops them from the road. `Path_Spur` is now a stop, not a side road.
- **Arm:** the game uses the arm stow `park` (forward over the cab corner, clear of the tipping bed). The scoop reach was changed so the elbow stays raised. **The master `b_sleek_hightech_master.blend` was not edited and still shows the concept's rim stow.** The game pose is generated by the script (`--arm park`).
- **Text dropped:** stencils and labels are culled from the game GLB.
- **Fuel:** the station's fuel is **LOX / LH2**. Concept B has no methane labels or tanks and the game GLB has no text, so there is nothing methane-related anywhere.

## Validation
- **`gltf-transform inspect`:**
  - 11 meshes / 11 primitives, 24,132 triangles
  - 2 materials, no textures
  - 6 animations
  - extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression]
- **`mine_clips.cjs verify`:** every clip targets only its own nodes, with **0 foreign targets**:
  - `dig` → Rig
  - `conveyor_run` → Conveyor
  - `truck_drive` → the 6 wheels
  - `truck_load` → Truck_Load
  - `truck_dump` → bed, load and rams
  - `truck_scoop` → the arm chain

  Tier extras, marker names (no `.001` duplicates) and the single skin (18 joints) were also checked.
- **Clearance**, checked in Blender with the clip poses evaluated on the real mesh parts (BVH overlap + nearest-distance):
  - Stowed arm vs bed rim at bed **0° / 25° / 50°**: 0 overlaps, minimum gaps **0.200 / 0.595 / 1.309 m**.
  - `truck_scoop`, every 2nd frame (19 poses): 0 overlaps with every other truck part (bed, load, chassis and cab, rams, wheels). Points within 0.45 m of the shoulder are excluded, because that is the ball joint inside the turret. The minimum gap is **0.062 m** (scoop vs chassis at 0.13 s). The lowest arm point is z 0.73 m (truck-local) at full reach, out over the deposit beside the road.
  - The bed rams are posed from the bed angle every frame (base swings, stage and rod extend). The arm-ram piston of the concept was dropped from the game build, because it clipped the turret during the scoop.

## Caveats
- The game GLB is a baked, decimated proxy. Small curved parts are faceted; procedural dust, grime and wear live only in the .blend and the renders.
- All metals are folded into `SHM_Paint`, with their grey kept in the vertex colour, to reach 11 draws.
- `Truck` is one skinned mesh. The ram and arm pistons are rigidly skinned, one joint each.
- Blender prints "mesh not valid" export warnings for Rig, Tier_05 and Truck_Mesh, which are the joined, decimated meshes. The packed GLB loads and inspects cleanly, and the renders and clearance checks look right.
- Cyan is used for light strips (concept B) and for the He-3 crystals.
