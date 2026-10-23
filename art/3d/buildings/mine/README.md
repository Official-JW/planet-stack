# Mine station: in-game build (concept B + HT-04 truck)

The in-game **Mine** for Planet Stack, built from the approved **concept B (sleek high-tech)** master and the **HT-04** haul truck. **The Refinery is its own station** (one swipe right; station order Mine, Refinery, Dock, 160 m apart). The Mine has no Refinery parts, no dump stub and no `REFINERY_ANCHOR`; trucks leave along the haul road stub off the frame's **right** edge (`Road_Entry`).

The HT-04 has **no scoop arm**. It only fills under the conveyor chute at `Path_Load` (fill is code-driven by percent), then drives off on its own.

| | |
|---|---|
| **Game GLB** | `mine_game.glb`, **187,136 B (0.19 MB)**, md5 `72b126ee8a5bd3c5e1c56d16cfbd269a` |
| Triangles / draws | **24,190 triangles, 11 draw calls with every tier visible** (11 meshes × 1 primitive) |
| Format | meshopt + quantization (`gltfpack -cc -kn -ke`). Extensions: `EXT_meshopt_compression` and `KHR_mesh_quantization` only. **No Draco.** One morph target (`fill`, on the truck mesh). |
| Materials | `SHM_Paint` and `SHM_GlowCyan` (`../_shared/shared_materials.json`). Plain metallic/roughness plus emissiveFactor. No transmission, clearcoat or ior. Colour is in `COLOR_0` vertex colours. **No images or textures** and no TEXCOORD. |
| Units / axes | 1 m, Y up. The origin is concept B's world origin. The camera side is +Z. |
| Bounds (glTF) | (−15.55, −2.04, −13.22) … (26.0, 21.78, 16.3). The +X growth is the haul road stub leaving `Road_Entry`; it runs off the phone frame on the right. |
| No astronauts | The concept-B astronaut is removed. |
| Budget | Mine station **30k tris / 15 draws including the future operator prop (~3k tris, 2 draws)**, so the Mine itself is held to **≤ 27k tris / ≤ 13 draws**: it uses 24,190 / 11. |

## Files
- `mine_game.glb`: the game asset.
- `truck_fill_strip_393.png`: **fill proof at phone scale**: the truck crop of the 393×852 station frame at fill 0 / 17 / 33 / 50 / 67 / 83 / 100 %, `chute_pour` and the rich drop (top row 1:1, bottom row the same pixels at 3× nearest). Rendered from the game mesh (`_src/proof_fill.py`).
- `truck_fill_closeup_1179.png`: the same at 1179×2556 scale (4 crops: 0 %, `chute_pour` @ 50 %, `truck_load_rich` @ 75 %, 100 %).
- `mine_phone_1179x2556.png` (Cycles master, 64 samples) and `mine_phone_393x852.png` (its Lanczos downscale): the station camera view. The ground uses the shared cool-grey `M_ground` (material unchanged; only the render terrain under the road is cut ≤ a few cm so it never pokes through). The renders show the full concept-B shading. The truck in the renders has no arm.
- `mine_tiers_393x852.png`: tier check, the same station camera with **every tier visible** (Cycles, 24 samples, rendered at 393×852). Made with `--mode tiers --mout DIR`, which also writes `tier_boxes.json`.
- `_src/mine_layout.py`: the station re-layout applied on top of the concept-B scene (see Layout changes), including the graded haul road (`graded_roads`, `M_road_graded`): the loop plus the +X stub.
- `_src/build_mine.py`: does the camera fit, renders the phone shots, and builds the game GLB. That covers the material remap, tiers, culling, the per-group bake and decimation to budget, the truck armature, skin and fill morph, the clips, the markers and the export.
- `_src/mine_clips.cjs`: `prune` trims each clip to its own nodes and moving channels. `verify` writes a JSON report with tris, draws, extensions, images, clip targets and foreign targets, nodes and skins.
- `_src/pack_mine.sh`: runs prune → gltfpack → verify.
- `_src/phone_downscale.py`: makes the 393×852 from the 1179×2556 master (PIL Lanczos).
- `_src/proof_fill.py`: imports the pruned raw GLB (Blender has no meshopt decoder), sets the phone camera from `Cam_Target` extras and renders the fill stages, `chute_pour` and the rich drop.

Rebuild (from the repo root, Blender 4.2):
```
B=/opt/blender-4.2.3-linux-x64/blender; S=art/3d/buildings/mine/_src
$B -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P $S/build_mine.py -- --arm park --only none --out /tmp/mine/gen --mode game --mout /tmp/mine/raw.glb
$S/pack_mine.sh /tmp/mine/raw.glb art/3d/buildings/mine/mine_game.glb
$B -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P $S/build_mine.py -- --arm park --only none --out /tmp/mine/gen --mode phone --mout art/3d/buildings/mine --ps 64
python3 $S/phone_downscale.py art/3d/buildings/mine
$B -b -P $S/proof_fill.py -- --glb /tmp/mine/raw_pruned.glb --out /tmp/mine/proof --ps 32
```
`--w W` forces the frame width; without it the script picks the smallest W (24–44 m, 0.25 steps) that fits (this gives **33**). `--top_y Y` sets where the Tier_20 mast tip lands on 393×852 (default **230**).

## Station camera (Game Coder spec)
Perspective, **38° vertical FOV, tilted down 18°, aimed at `Cam_Target`**.
- **Mine-only aim (Director 10/23, the Refinery is its own station):** **W = 33 m**, `Cam_Target` glTF **(0.86, 6.26, 1.00)** (Blender (0.86, −1.0, 6.26)), extras `{"frame_w": 33, "fov_y_deg": 38, "pitch_down_deg": 18, "distance_m": 103.89}`. It was W 37 at (0.06, −2.36, 1.00) while the Refinery shared the frame.
- **Distance** d = (W/2) / (tan 19° · 393/852) = **103.89 m**, the same for 393×852 and the 1179×2556 master. `Cam_Target` is a look-at point only.
- **Fit:** the target is solved so the **Tier_20 mast tip lands at y 230** on 393×852 (band 220–240, clear of the HUD bottom at ~141) and the station is centred in x; W is the smallest that keeps x inside 3–97 % and the bottom above y 660 (sheet top 674). The focus holds the rig, conveyor head, parked truck, silo, every game tier envelope (Tier_03…20), the haul loop to its south berm toes, the east apex and the west hairpin toe. The haul road stub is not in the focus: it runs off the right edge.
- **Result (all tiers visible):** x **12…381**, y **230…571** px. Every tier is in frame, and every tier vertex is within 20.4 m (0.62 × frame_w) of `Cam_Target`.

## Game GLB nodes
Everything sits under the root `Mine`. gltfpack puts each mesh on an **unnamed child node** of its named node; that child carries the quantization offset and scale. Find meshes under the named node with `traverse`. The names, pivots and extras are on the named nodes.

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint` | static base merged by material: pads, rig skirt, hopper, conveyor frame, silo base, graded roads (loop + +X stub, not decimated), rocks | 10,173 | SHM_Paint | origin |
| `Base_GlowCyan` | all static cyan glow: light strips | 3,710 | SHM_GlowCyan | origin |
| `Rig` | bore head and crown block, the moving part of the rig (clip `dig`) | 635 | SHM_Paint | (−7.5, 8.65, −3.6) |
| `Conveyor` | belt-surface ore lumps (clip `conveyor_run`) | 160 | SHM_Paint | (−0.85, 2.55, −2.65), the tail end C0 |
| `Silo` | ore silo | 782 | SHM_Paint | (10.0, 0, −4.5), base centre |
| `Truck` | HT-04: armature root, **pivot at the ground centre** under the truck, faces **+X** | 5,910 (one skinned mesh `Truck_Mesh`, morph target `fill`) | SHM_Paint | (4.7, 0, 4.5) = `Path_Load` |
| `Tier_03…20` | see Tiers | | | |

**Truck joints** (one skin, 24 joints, rest rotations are identity; local offsets are relative to the parent):
- `Truck_Chassis` (0, 0, 0)
  - `Truck_Bed` at the **rear hinge** (−3.3, 1.72, 0); it tips about local Z, rear down.
    - `Truck_Load` (1.7, 0.27, 0): the ore pile (carries the `fill` morph). Its rest scale is 1; `truck_dump` scales it to 0 as the bed tips.
  - `Truck_Ram_L` / `Truck_Ram_R`: the bed rams, each with a `_Stage2` and `_Rod` telescoping section.
  - `Truck_Pour_01..04`: chute-pour ore chunks (2 rock, 2 He-3 cyan), driven only by `chute_pour`.
  - `Truck_Rich_01..05`: glowing cyan rich-ore chunks, driven only by `truck_load_rich`.
  - `Truck_Wheel_01..06`
- **No arm:** `Truck_Arm`, `Truck_Arm_Fore` and `Truck_Arm_Scoop` are gone, with the arm's geometry and weights (turret, booms, rams, hoses, scoop).
- At rest the chunk joints sit **inside the bed floor** with their 2 cm chunks (invisible). The clips scale them up only while they fall, and end with them hidden again, so stopping a clip mid-way and resetting (`action.stop()`) hides them.

### Fill (code-driven by percent)
**Choice: one pile mesh with a morph target, not 7 `Fill_00..06` stage meshes** (0 extra draws and no extra nodes; the 7 stages would cost 7 draws, or 1 draw if merged but with 7× the pile tris).
- The morph target is **`fill`** (index 0, `mesh.extras.targetNames = ["fill"]` → three.js `morphTargetDictionary.fill`) on the truck's skinned mesh (the unnamed child of `Truck_Mesh`; find it with `traverse(o => o.isSkinnedMesh)`). `Truck_Mesh.extras.fill_morph` repeats the rule.
- **Influence 0 = fill 0 %**: a thin layer on the bed floor (5 % of the pile height, 82 % of its footprint). **Influence 1 = 100 %**: heaped full, the crown 0.85 m over the bed rim (4.15 m over the ground, 0.2 m under the chute mouth).
- **Mapping: `influence = sqrt(fill_pct / 100)`.** The bed walls hide a low pile from the station camera; with the square root the pile clears the far rim from about **33 %** (it is hidden below that, see `truck_fill_strip_393.png`). Lv1 fill takes 2 min: tween `fill_pct` 0 → 100 over 120 s and set the influence each frame.
- Stage equivalents (if you want to step instead of tween): stage n = 0…6 ↔ fill_pct_min 0, 17, 33, 50, 67, 83, 100 → influence 0, 0.41, 0.57, 0.71, 0.82, 0.91, 1.
- **Dump:** `truck_dump` scales `Truck_Load` to 0 as the bed tips, whatever the influence. After the dump, set the influence back to 0 (fill 0 %) and the dump clip's reset brings `Truck_Load` back to scale 1.

**Side naming:** `_L` is the truck's left, which is glTF −Z when the truck faces +X. `_R` is the right, +Z.
- Wheels 01–03 are on the **left**, rear → middle → front (x −2.7, −1.35, +2.4).
- Wheels 04–06 are on the **right**, rear → middle → front.

## Clips
| Clip | Length | Loop | Targets (only these) | What it does |
|---|---|---|---|---|
| `dig` | 3.0 s | loop | `Rig` translation | The bore head lowers 0.6 m and comes back up (cosine). |
| `conveyor_run` | 1.0 s | loop | `Conveyor` translation | The lumps move one 0.9 m lump spacing along the belt, linear, so the loop is seamless. |
| `truck_drive` | 1.0 s | loop | `Truck_Wheel_01..06` rotation | Wheel spin, one full turn per second (≈ 5.3 m/s at r 0.85 m). Move the `Truck` node yourself along the `Path_*` markers. |
| `chute_pour` | 1.2 s | **loop** | `Truck_Pour_01..04` TRS | Ore chunks drop from the chute mouth (4.35 m) into the bed, one every 0.3 s, each falling 0.47 s (accelerating, with a tumble). Each grows in at the mouth and sinks to nothing at the pile. Frame 36 = frame 0, so it loops seamlessly. Start it when the truck is parked at `Path_Load` and stop it at 100 %. |
| `truck_load_rich` | 1.0 s | once | `Truck_Rich_01..05` TRS | A quick drop of 5 glowing cyan ore chunks (bigger than the pour chunks) from the chute into the bed, staggered over 0.33 s, gone by 1.0 s. **Tween `fill_pct` +25 over the same 1.0 s** for the visible 25 % bump, and spawn the money pop at `Rich_Pop`. |
| `truck_dump` | 3.0 s | once | `Truck_Bed` rotation, `Truck_Load` scale, rams (rotation, plus stage and rod translation) | The bed goes **0 → 50 → 0°** with ease in-out (smoothstep up and down). The load stays full to 18°, is gone by 42° on the way up, and stays empty on the way down. The rams track the bed. It reads fine at **1.5× speed** (2.0 s). Played at the Refinery station. |

**Removed:** `truck_scoop` (no arm) and the timed `truck_load` (the fill is the `fill` morph now; there is no debug preview clip).

**Sequence rules (game side):**
- **Load:** arrive heading +X at `Path_Load_Approach`, reverse 4.3 m straight to `Path_Load`, then play `chute_pour` (loop) while tweening the fill 0 → 100 % (2 min at Lv1). A rich tap plays `truck_load_rich` over the pour and adds +25 %. At 100 % stop `chute_pour` and drive off forward along `Path_01..` to `Road_Entry`, then off the right edge.
- **Never drive with the bed raised**: play `truck_drive` / move the truck only when `truck_dump` is finished (bed at 0°).
- **Never drive while `chute_pour` or `truck_load_rich` is running**: the chunks are on truck joints and would ride along.

## Tiers
**Frame rule (Director): every tier must land inside the station frame.** Checked by projecting every vertex of each tier with the station camera on 393×852 (all tiers visible), and in `mine_tiers_393x852.png`:

| Tier | x px | y px | In frame (HUD bottom ~141, sheet top 674) |
|---|---|---|---|
| `Tier_03` | 170–223 | 431–449 | yes |
| `Tier_05` | 185–269 | 389–483 | yes |
| `Tier_08` | 17–92 | 380–460 | yes |
| `Tier_12` | 267–333 | 361–464 | yes |
| `Tier_20` | 58–139 | **232**–329 | yes (top in the 220–240 band) |

Every tier node has `extras {"tier": N, "hidden_by_default": true}` (three.js `userData`). glTF has no hidden flag, so the loader must set `visible = false` on load. Each tier is one draw.

| Node | Adds | Tris | Material | Pivot (glTF) |
|---|---|---|---|---|
| `Tier_03` | conveyor light kit: cyan running lights on both trough walls, plus head and tail beacons | 208 | SHM_GlowCyan | (0.84, 0, 0.39) |
| `Tier_05` | second pod hopper east of the first, plus a pneumatic feed tube onto the conveyor | 1,370 | SHM_Paint | (3.6, 0, −4.36) |
| `Tier_08` | radiator wing behind the rig power module (6 panels, mast, coolant pipe) | 272 | SHM_Paint | (−12.09, 0, −7.65) |
| `Tier_12` | second, taller ore silo behind the first, plus a transfer bridge and beacon | 686 | SHM_Paint | (10.6, 0, −9.11) |
| `Tier_20` | Mk II bore crown: bigger crown housing, twin emitter pods and a tall mast | 284 | SHM_Paint | (−7.5, 0, −3.59) |

Base 13,883 + moving 7,487 + tiers 2,820 = 24,190 tris.

## Markers (empties, glTF coords; yaw is about +Y, 0 = truck faces +X)
- **`Path_Load`** (4.7, 0, 4.5), yaw 0: the truck's load / rest pose. The **bed centre sits exactly under the chute mouth**: `extras.bed_centre_glTF` (3.1, 1.99, 4.5) and `extras.chute_glTF` (3.1, 4.35, 4.5) share x and z (checked in the build: 0.000 m apart).
- **`Path_Load_Approach`** (9.0, 0, 4.5), yaw 0: on the north line, 4.3 m east of `Path_Load`. On return the truck drives forward (heading +X) past the chute to here, stops, and **reverses 4.3 m straight along −X** into `Path_Load`. Both sit on the straight part of the north line (z 4.5 for x ≥ 0), so the reverse is a straight line.
- **`Operator_Deck`** (14.0, 0, 1.2), rotation identity (the deck front faces +Z, toward the camera): the root for `art/3d/props/mine_operator/mine_operator_game.glb` (2,584 tris, 2 draws; not part of this GLB). On 393×852 the deck's box is **x 332–371, y 442–501**. The operator is **20 px tall standing at the rail and 16.5 px seated** (Director minimum 12 px; nothing is scaled). Clearances: the +X road stub (berm toe to berm toe, y 515–546) is 14 px below it; the Dep_01 tap-circle centre (294, 530) is 48 px from the box (26 px beyond the 22 px radius); the truck at `Path_Load` (box x 196–292) is 40 px to the left.
- **`Rich_Pop`** (3.1, 4.88, 4.5): the money-pop anchor for the rich load, 1.6 m over the bed rim, right under the chute (static, valid while the truck is parked at `Path_Load`).
- **`Path_01..15`**: the haul loop clockwise from the load bay. Each has `extras.yaw_deg`.
  - North line: x 5 → 8 (z 4.5).
  - East hairpin: centre (9, 9), r 4.5.
  - South straight: z 13.5, x 7.75 → −4.25.
  - West hairpin: centre (−5, 9.5), r 4.
  - Back east to (−5.25, 5.51) on the north line, then on to `Path_Load_Approach`.
  - Leaving loaded: `Path_Load` → `Path_01..04` → `Road_Entry` → the +X stub. Returning: `Road_Entry` → `Path_05..15` → `Path_Load_Approach` → reverse into `Path_Load`.

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
- **`Dep_01`** (8.65, −0.01, 8.65), the main He-3 seam (r 2.2 m), and **`Dep_02`** (−1.2, −0.01, 10.4), the tap deposit (r 1.05 m). The game draws the deposit glow. There is no scoop: `extras.tap` reads "the drill taps it: the next load comes down the chute rich -> play truck_load_rich at Path_Load".
- **`Road_Entry`** (13.5, 0, 9.0), **yaw 0 (heading +X)**: the east apex of the loop, where the **haul road stub** leaves straight toward +X and runs off the frame's right edge (it ends at glTF x 26) toward the Refinery station. Position unchanged; yaw was −90 when the access road ran toward the camera.
- **Removed:** `Path_Dump`, `Path_Dump_Approach`, `REFINERY_ANCHOR` (the Refinery is its own station), `Path_Spur_01/02` (no scoop).
- **`Crew_Path_01..07`**: (−9.4, 0.64, 0.2) at the rig operator pod deck → (−9.0, −0.01, 1.9) → (−5.6, 0, 2.7) → (−2.2, 0, 2.3) → (1.6, 0, −0.2) → (5.6, 0, −1.0) → (8.6, 0, −1.4) at the silo.
- **`Cam_Target`** (0.86, 6.26, 1.00), `frame_w` 33: the Mine-only aim. See Station camera. Every other kept marker is unchanged.

## Layout changes vs the concept-B master
These live in `_src/mine_layout.py`. The B look, palette and parts are otherwise unchanged.
- **Receiving hopper removed:** the DUMP 01 receiving hopper and its lift tube are gone. Trucks haul to the Refinery station (off the right edge) and dump there.
- **No scoop arm (10/23):** `build_mine.py` deletes the HT-04's loading arm (28 objects: pedestal, turret, shoulder, booms, rams, hoses, scoop and its ore) right after the layout, so it is gone from the renders, the game mesh, the skin and the camera fit. The suspension `swing_arm`s stay.
- **Head-end support replaced:** the head-end cantilever pylon and boom stood in the new road. A column with a knee brace under the trough, north of the road, replaces them.
- **Haul road re-laid:** it is now a loop (load bay → east hairpin → south straight → west hairpin → back) plus a **straight stub east from `Road_Entry`** (x 13.5 → 26, off the right edge). The old dump stub west to the refinery and the access road toward the camera are gone. The loop centre line (and every `Path_*` marker) is unchanged.
- **Graded regolith road** (replaces the flat dark decal stripe). Built in `mine_layout.graded_roads` as real geometry, two meshes `haul_road_loop` / `haul_road_access` (the +X stub):
  - **Cross-section:** a 4.0 m graded running surface (the HT-04 is 3.82 m over the tyres; the old 3.2 m stripe was narrower than the truck) with a 2 cm crown, then a **low berm on each side**: foot at ±2.0 m, crest **25 cm** high at ±2.35 m, toe buried at ±2.8 m.
  - **Tyre marks:** a 2 cm rut with a darker vertex colour at ±1.5 m, the HT-04 wheel track.
  - **Colour** is in a `RoadCol` corner colour attribute (no images): track `#a4a7ac` (a little lighter than the regolith), tyre marks `#878a8f`, berm crest `#939499`, toe `#82858a`, with ±5 % low-frequency variation. The render material `B_HaulRoadGraded` multiplies it by fine gravel noise and bump; the game GLB copies it into `COLOR_0` of `Base_Paint`.
  - **Junctions:** berms flatten wherever they cross another road's running surface (loop ↔ stub at `Road_Entry`), so the junction is open. With the dump stub gone, **the west hairpin berm is closed again** (no road needs it). Berms also flatten next to station parts (head column foot, rig feet) so nothing is buried. Around `Dep_01` / `Dep_02` the berms are fully open within 2.5 m of the marker (see Deposit clearance).
  - The stub surface sits 2 cm under the loop where they overlap (no z-fighting). Pebbles and boulders on the road were removed (36). In the render scene the terrain under the road is cut 3 cm below the road surface wherever it bulged through (52 ground vertices); `M_ground` itself is untouched.
  - Roads skip the planar dissolve and the decimation (they would smear the ruts and berms).
- **Deposits moved:** they are inside the loop. The drill taps them; ore only ever reaches the truck through the chute.
- **Deposit clearance (game fix):** in-game, the concept's deposit heap mound (`deposit` / `deposit_small`, the "crater" over Dep_01), its He-3 seam crystals and the spilled ore chips covered the game-drawn deposit glow disc and gem. `build_mine.py` now deletes every concept deposit-art mesh whose centre is within 6 m of `Dep_01` / `Dep_02` (67 objects: `deposit*`, `seam_crystal*`, and the `spill_rock/he3/pt*` ore chips), plus loose `pebble`s within 2.8 m. This happens after the layout and before the merge. `mine_layout.graded_roads` adds obstacle rings so no berm rises within 2.5 m of either marker. As a result, **nothing stands within 2.5 m of either Dep marker except the flat graded running surface (≤ 6 cm)**, which the fixed `Path_*` centre lines put there, and the truck parked at `Path_Load` (fender 2.33 m from `Dep_01`; it is the moving actor). The `Dep_*` extras `glow` now reads "drawn by the game (no deposit mesh in the GLB; clear ground within 2.5 m)". (That fix kept every name; the later 10/23 passes changed the truck, clips, markers and aim as described above.)
- **Text dropped:** stencils and labels are culled from the game GLB.
- **Fuel:** the station's fuel is **LOX / LH2**. Concept B has no methane labels or tanks and the game GLB has no text, so there is nothing methane-related anywhere.

## Validation
- **`mine_clips.cjs verify`** (`_src/pack_mine.sh`):
  - 11 meshes / 11 primitives, **24,190 triangles, 11 draws**, 0 images/textures, extensionsUsed = [EXT_meshopt_compression, KHR_mesh_quantization]
  - 6 clips, each targets only its own nodes, **0 foreign targets**: `dig` → Rig, `conveyor_run` → Conveyor, `truck_drive` → 6 wheels, `chute_pour` → Truck_Pour_01..04, `truck_load_rich` → Truck_Rich_01..05, `truck_dump` → bed, load and rams
  - one skin, 24 joints (no `Truck_Arm*`); morph target `fill` present (`targetNames ["fill"]`, 427 moving vertices after gltfpack's vertex split)
  - nodes vs the previous build: removed `Path_Dump`, `Path_Dump_Approach`, `Path_Spur_01/02`, `REFINERY_ANCHOR`, `Truck_Arm`, `Truck_Arm_Fore`, `Truck_Arm_Scoop`; added `Path_Load_Approach`, `Rich_Pop`, `Operator_Deck`, `Truck_Pour_01..04`, `Truck_Rich_01..05`. Every other node and marker position is unchanged, except `Cam_Target` (re-aim) and `Road_Entry`'s yaw.
- **Fill read** at phone scale: `truck_fill_strip_393.png` (game mesh, station camera). The pile clears the bed rim from 33 %; 0 % and 17 % look the same from the station camera.
- **Load pose:** the build prints `LOADCHECK`; the bed centre and the chute discharge are 0.000 m apart in plan.

## Caveats
- The game GLB is a baked, decimated proxy. Small curved parts are faceted; procedural dust, grime and wear live only in the .blend and the renders.
- All metals are folded into `SHM_Paint`, with their grey kept in the vertex colour, to reach 11 draws.
- `Truck` is one skinned mesh. The ram pistons are rigidly skinned, one joint each. The pour / rich chunks are on truck joints, so they ride with the truck: only play those clips while it is parked at `Path_Load`.
- Blender prints "mesh not valid" export warnings for Rig, Tier_05 and Truck_Mesh, which are the joined, decimated meshes. The packed GLB loads and inspects cleanly, and the renders and clearance checks look right.
- Cyan is used for light strips (concept B) and for the He-3 crystals.
