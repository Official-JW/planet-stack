# Mine station: in-game build (concept B + HT-04 truck)

The in-game **Mine** for Planet Stack, built from the approved **concept B (sleek high-tech)** master and the **HT-04** haul truck. **The Refinery is its own station** (one swipe right; station order Mine, Refinery, Dock, 160 m apart). The Mine has no Refinery parts, no dump stub and no `REFINERY_ANCHOR`; trucks leave along the haul road stub off the frame's **right** edge (`Road_Entry`).

The HT-04 has **no scoop arm**. It only fills under the conveyor chute at `Path_Load` (fill is code-driven by percent), then drives off on its own. **The truck is not in `mine_game.glb` any more:** it is the shared prop `art/3d/props/ht04/ht04_game.glb` (3,859 tris, 1 draw; body, `fill` morph, `truck_dump`, `truck_drive`, `chute_pour`, `truck_load_rich`, `Fill_Arc`, code-driven wheels). The game drops its root onto the Mine's truck markers (`Path_Load` etc.) and the Refinery's. See `art/3d/props/ht04/README.md`.

| | |
|---|---|
| **Game GLB** | `mine_game.glb`, **125,708 B (0.13 MB)**, md5 `68e07c01c0e8025a73f81c8e15484553` |
| Triangles / draws | **18,286 triangles, 10 draw calls with every tier visible** (10 meshes × 1 primitive; no truck) |
| Format | meshopt + quantization (`gltfpack -cc -kn -ke`). Extensions: `EXT_meshopt_compression` and `KHR_mesh_quantization` only. **No Draco.** No morph targets, no skins (the truck and its `fill` morph are in the ht04 prop). |
| Materials | `SHM_Paint` and `SHM_GlowCyan` (`../_shared/shared_materials.json`). Plain metallic/roughness plus emissiveFactor. No transmission, clearcoat or ior. Colour is in `COLOR_0` vertex colours. **No images or textures** and no TEXCOORD. |
| Units / axes | 1 m, Y up. The origin is concept B's world origin. The camera side is +Z. |
| Bounds (glTF) | (−15.55, −2.04, −13.22) … (26.0, 21.78, 16.3). The +X growth is the haul road stub leaving `Road_Entry`; it runs off the phone frame on the right. |
| No astronauts | The concept-B astronaut is removed. |
| Budget | Mine station **30k tris / 15 draws including the future operator prop (~3k tris, 2 draws)**, so the Mine itself is held to **≤ 27k tris / ≤ 13 draws**: it uses **18,286 / 10**; with the shared HT-04 at `Path_Load` (3,859 / 1) the station is 22,145 / 11. |

## Files
- `mine_game.glb`: the game asset.
- `truck_fill_strip_393.png`: **fill proof in the FULL 393×852 station frame**: 4 frames at fill 10 / 33 / 66 / 100 % (official remap), `chute_pour` running in the 10 / 33 / 66 frames, each with a 3× inset of the truck (cyan box = inset area). Rendered from the game meshes: the Mine GLB plus the shared `ht04` prop with its root on `Path_Load` (`_src/proof_fill.py --mode strip --truck` + `_src/proof_strip.py`). It also shows the haul trail: worn tyre tracks from `Path_Load` round the east hairpin to `Road_Entry` and out along the +X stub off the right edge.
- `truck_fill_strip_1179.png`: the same 4 frames at 1179×2556 (insets 3× of the 393 scale).
- `mine_phone_1179x2556.png` (Cycles master, 64 samples) and `mine_phone_393x852.png` (its Lanczos downscale): the station camera view. The ground uses the shared cool-grey `M_ground` (material unchanged; only the render terrain under the road is cut ≤ a few cm so it never pokes through). The renders show the full concept-B shading. The truck in the renders has no arm.
- `mine_tiers_393x852.png`: tier check, the same station camera with **every tier visible** (Cycles, 24 samples, rendered at 393×852). Made with `--mode tiers --mout DIR`, which also writes `tier_boxes.json`.
- `_src/mine_layout.py`: the station re-layout applied on top of the concept-B scene (see Layout changes), including the graded haul road (`graded_roads`, `M_road_graded`): the loop plus the +X stub.
- `_src/build_mine.py`: does the camera fit, renders the phone shots, and builds the game GLB. That covers the material remap, tiers, culling, the per-group bake and decimation to budget, the truck armature, skin and fill morph, the clips, the markers and the export. It writes two GLBs: the Mine (`--mout`, no truck) and the HT-04 prop (`--tout`, default `<mout dir>/ht04_raw.glb`; packed by `art/3d/props/ht04/_src/build_ht04.sh`).
- `_src/mine_clips.cjs`: `prune` trims each clip to its own nodes and moving channels. `verify` writes a JSON report with tris, draws, extensions, images, clip targets and foreign targets, nodes and skins.
- `_src/pack_mine.sh`: runs prune → gltfpack → verify.
- `_src/phone_downscale.py`: makes the 393×852 from the 1179×2556 master (PIL Lanczos).
- `_src/proof_fill.py`: imports the pruned raw GLB (Blender has no meshopt decoder), sets the phone camera from `Cam_Target` extras and renders the fill frames with the official remap (`--mode strip --rx 393|1179`), `chute_pour` and the rich drop. `_src/proof_strip.py` lays out the strip with the 3× insets.

Rebuild (from the repo root, Blender 4.2):
```
B=/opt/blender-4.2.3-linux-x64/blender; S=art/3d/buildings/mine/_src
$B -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P $S/build_mine.py -- --arm park --only none --out /tmp/mine/gen --mode game --mout /tmp/mine/raw.glb --tout /tmp/mine/ht04_raw.glb
$S/pack_mine.sh /tmp/mine/raw.glb art/3d/buildings/mine/mine_game.glb
$S/pack_mine.sh /tmp/mine/ht04_raw.glb art/3d/props/ht04/ht04_game.glb
$B -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P $S/build_mine.py -- --arm park --only none --out /tmp/mine/gen --mode phone --mout art/3d/buildings/mine --ps 64
python3 $S/phone_downscale.py art/3d/buildings/mine
$B -b -P $S/proof_fill.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw_pruned.glb --out /tmp/mine/proof --ps 32 --mode strip --rx 393
$B -b -P $S/proof_fill.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw_pruned.glb --out /tmp/mine/proof --ps 24 --mode strip --rx 1179 --pcts 10,33,66,100
python3 $S/proof_strip.py /tmp/mine/proof 393 art/3d/buildings/mine/truck_fill_strip_393.png
python3 $S/proof_strip.py /tmp/mine/proof 1179 art/3d/buildings/mine/truck_fill_strip_1179.png
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
| `Base_Paint` | static base merged by material: pads, rig skirt, hopper, conveyor frame, silo base, graded roads (loop + +X stub, not decimated), rocks | 10,179 | SHM_Paint | origin |
| `Base_GlowCyan` | all static cyan glow: light strips | 3,710 | SHM_GlowCyan | origin |
| `Rig` | bore head and crown block, the moving part of the rig (clip `dig`) | 635 | SHM_Paint | (−7.5, 8.65, −3.6) |
| `Conveyor` | belt-surface ore lumps (clip `conveyor_run`) | 160 | SHM_Paint | (−0.85, 2.55, −2.65), the tail end C0 |
| `Silo` | ore silo | 782 | SHM_Paint | (10.0, 0, −4.5), base centre |
| `Tier_03…20` | see Tiers | | | |

### HT-04 truck (shared prop)
The truck, its joints, the `fill` morph (official remap `influence = 0.5 + 0.5 * (fill_pct / 100) ** 0.8` for fill_pct > 0 and 0 at 0 %; apex 0.17 m over the rim at 0.5 and **0.85 m over the rim top (4.23 vs 3.38 m) at 1**), the truck clips and `Fill_Arc` all live in **`art/3d/props/ht04/`** (README there). Place its root `Truck` (ground centre, +X forward = yaw 0) on `Path_Load` (4.7, 0, 4.5), yaw 0: the bed centre is then exactly under the chute mouth. Wheels are code-driven (`HT04_Wheel_*`, spin about local X, `wheel_radius` 0.853 m in the root extras).

## Clips
| Clip | Length | Loop | Targets (only these) | What it does |
|---|---|---|---|---|
| `dig` | 3.0 s | loop | `Rig` translation | The bore head lowers 0.6 m and comes back up (cosine). |
| `conveyor_run` | 1.0 s | loop | `Conveyor` translation | The lumps move one 0.9 m lump spacing along the belt, linear, so the loop is seamless. |
| `chute_pour`, `truck_load_rich`, `truck_dump`, `truck_drive` | | | | In `ht04_game.glb` (see its README). |

**Removed:** `truck_scoop` (no arm), the wheel-spin `truck_drive` (wheels are code-driven now) and the timed `truck_load` (the fill is the `fill` morph now; there is no debug preview clip).

**Sequence rules (game side):**
- **Load:** arrive heading +X at `Path_Load_Approach`, reverse 4.3 m straight to `Path_Load`, then play `chute_pour` (loop) while tweening the fill 0 → 100 % (2 min at Lv1). A rich tap plays `truck_load_rich` over the pour and adds +25 %. At 100 % stop `chute_pour` and drive off forward along `Path_01..` to `Road_Entry`, then off the right edge.
- **Never drive with the bed raised**: move the truck only when `truck_dump` is finished (bed at 0°).
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

Base 13,889 + moving 1,577 (Rig, Conveyor, Silo) + tiers 2,820 = 18,286 tris (the truck's 3,859 are in the ht04 prop).

## Markers (empties, glTF coords; yaw is about +Y, 0 = truck faces +X)
- **`Path_Load`** (4.7, 0, 4.5), yaw 0: the truck's load / rest pose. The **bed centre sits exactly under the chute mouth**: `extras.bed_centre_glTF` (3.1, 1.99, 4.5) and `extras.chute_glTF` (3.1, 4.35, 4.5) share x and z (checked in the build: 0.000 m apart).
- **`Path_Load_Approach`** (9.0, 0, 4.5), yaw 0: on the north line, 4.3 m east of `Path_Load`. On return the truck drives forward (heading +X) past the chute to here, stops, and **reverses 4.3 m straight along −X** into `Path_Load`. Both sit on the straight part of the north line (z 4.5 for x ≥ 0), so the reverse is a straight line.
- **`Operator_Deck`** (14.0, 0, 1.2), rotation identity (the deck front faces +Z, toward the camera): the root for `art/3d/props/mine_operator/mine_operator_game.glb` (2,584 tris, 2 draws; not part of this GLB). On 393×852 the deck's box is **x 332–371, y 442–501**. The operator is **20 px tall standing at the rail and 16.5 px seated** (Director minimum 12 px; nothing is scaled). Clearances: the +X road stub (berm toe to berm toe, y 515–546) is 14 px below it; the Dep_01 tap-circle centre (294, 530) is 48 px from the box (26 px beyond the 22 px radius); the truck at `Path_Load` (box x 196–292) is 40 px to the left.
- **`Fill_Arc`** moved into the ht04 prop: it is a child of the truck root at truck-local (2.2, 4.6, 0), so with the truck on `Path_Load` it sits at (6.9, 4.6, 4.5), next to `Rich_Pop`.
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
- **Haul exit (for the Refinery's left-edge entry):** the stub's centre line is **z = 9.0, yaw 0 (heading +X)**, running from `Road_Entry` (13.5, 0, 9.0) to its end at **(26.0, 0, 9.0)**. It crosses the 393×852 right edge at x ≈ 16.6 m. Road: **4.0 m graded running surface**, berm crests at ±2.35 m, berm toes at ±2.8 m (5.6 m toe to toe), tyre tracks 0.4 m wide centred ±1.45 m. Stations are 160 m apart, so in Refinery coordinates the stub end is at x 26 − 160 = −134 on the same z if the stations share z.
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
  - **Tyre tracks (worn trail, 10/23):** two 0.4 m wide, 3 cm deep ruts centred ±1.45 m (the HT-04 tyre lines), in a darker vertex colour, on the loop and the +X stub alike, so the trail reads continuously from `Path_Load` round the east hairpin, through `Road_Entry` and off the right edge.
  - **Colour** is in a `RoadCol` corner colour attribute (no images): track `#a4a7ac` (a little lighter than the regolith), tyre tracks `#6c6f74`, berm crest `#939499`, toe `#82858a`, with ±5 % low-frequency variation. The render material `B_HaulRoadGraded` multiplies it by fine gravel noise and bump; the game GLB copies it into `COLOR_0` of `Base_Paint`.
  - **Junctions:** berms flatten wherever they cross another road's running surface (loop ↔ stub at `Road_Entry`), so the junction is open. With the dump stub gone, **the west hairpin berm is closed again** (no road needs it). Berms also flatten next to station parts (head column foot, rig feet) so nothing is buried. Around `Dep_01` / `Dep_02` the berms are fully open within 2.5 m of the marker (see Deposit clearance).
  - The stub surface sits 2 cm under the loop where they overlap (no z-fighting). Pebbles and boulders on the road were removed (36). In the render scene the terrain under the road is cut 3 cm below the road surface wherever it bulged through (52 ground vertices); `M_ground` itself is untouched.
  - Roads skip the planar dissolve and the decimation (they would smear the ruts and berms).
- **Deposits moved:** they are inside the loop. The drill taps them; ore only ever reaches the truck through the chute.
- **Deposit clearance (game fix):** in-game, the concept's deposit heap mound (`deposit` / `deposit_small`, the "crater" over Dep_01), its He-3 seam crystals and the spilled ore chips covered the game-drawn deposit glow disc and gem. `build_mine.py` now deletes every concept deposit-art mesh whose centre is within 6 m of `Dep_01` / `Dep_02` (67 objects: `deposit*`, `seam_crystal*`, and the `spill_rock/he3/pt*` ore chips), plus loose `pebble`s within 2.8 m. This happens after the layout and before the merge. `mine_layout.graded_roads` adds obstacle rings so no berm rises within 2.5 m of either marker. As a result, **nothing stands within 2.5 m of either Dep marker except the flat graded running surface (≤ 6 cm)**, which the fixed `Path_*` centre lines put there, and the truck parked at `Path_Load` (fender 2.33 m from `Dep_01`; it is the moving actor). The `Dep_*` extras `glow` now reads "drawn by the game (no deposit mesh in the GLB; clear ground within 2.5 m)". (That fix kept every name; the later 10/23 passes changed the truck, clips, markers and aim as described above.)
- **Text dropped:** stencils and labels are culled from the game GLB.
- **Fuel:** the station's fuel is **LOX / LH2**. Concept B has no methane labels or tanks and the game GLB has no text, so there is nothing methane-related anywhere.

## Validation
- **`mine_clips.cjs verify`** (`_src/pack_mine.sh`):
  - 10 meshes / 10 primitives, **18,286 triangles, 10 draws**, 0 images/textures, extensionsUsed = [EXT_meshopt_compression, KHR_mesh_quantization]
  - 2 clips, each targets only its own node, **0 foreign targets**: `dig` → Rig, `conveyor_run` → Conveyor (the 4 truck clips are in `ht04_game.glb`)
  - no skin and no morph (the truck moved to `art/3d/props/ht04/`); markers kept: `Path_Load`, `Path_Load_Approach`, `Road_Entry`, `Rich_Pop`, `Operator_Deck`, `Cam_Target`, `Path_01..15`, `Dep_01/02`, `Crew_Path_01..07`
  - nodes vs the previous build: removed `Path_Dump`, `Path_Dump_Approach`, `Path_Spur_01/02`, `REFINERY_ANCHOR`, `Truck_Arm`, `Truck_Arm_Fore`, `Truck_Arm_Scoop`; added `Path_Load_Approach`, `Rich_Pop`, `Operator_Deck`; the `Truck` subtree (and `Fill_Arc`) moved out to the ht04 prop. Every other node and marker position is unchanged, except `Cam_Target` (re-aim) and `Road_Entry`'s yaw.
- **Fill read** in the full phone frame: `truck_fill_strip_393.png` / `_1179.png` (game mesh, station camera, official remap). The pile crowns the rim from the first percent; 0 % (after a dump) reads empty.
- **Load pose:** the build prints `LOADCHECK`; the bed centre and the chute discharge are 0.000 m apart in plan.

## Caveats
- `mine_phone_*.png` (Cycles master) predates the 10/23 tyre-track pass and the new pile; the game GLB and `truck_fill_strip_*.png` show the current road and fill.
- The haul loop's west hairpin stays: it is the turnaround that lets a returning truck (in from `Road_Entry`) come round to `Path_Load_Approach` heading +X and reverse under the chute. It is part of the continuous loop, with no stubs or open berms off it.
- The game GLB is a baked, decimated proxy. Small curved parts are faceted; procedural dust, grime and wear live only in the .blend and the renders.
- All metals are folded into `SHM_Paint`, with their grey kept in the vertex colour, to reach 10 draws.
- `Truck` is one skinned mesh. The ram pistons are rigidly skinned, one joint each. The pour / rich chunks are on truck joints, so they ride with the truck: only play those clips while it is parked at `Path_Load`.
- Blender prints "mesh not valid" export warnings for Rig and Tier_05 (and the truck mesh in the prop build), which are the joined, decimated meshes. The packed GLB loads and inspects cleanly, and the renders and clearance checks look right.
- Cyan is used for light strips (concept B) and for the He-3 crystals.
