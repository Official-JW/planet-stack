# Mine station: in-game build (concept B + HT-04 truck)

The in-game **Mine** for Planet Stack, built from the approved **concept B (sleek high-tech)** master and the **HT-04** haul truck. **The Refinery is its own station** (one swipe right; station order Mine, Refinery, Dock, 160 m apart). The Mine has no Refinery parts, no dump stub and no `REFINERY_ANCHOR`; trucks leave along the haul road stub off the frame's **right** edge (`Road_Entry`).

The HT-04 has **no scoop arm**. It only fills under the conveyor chute at `Path_Load` (fill is code-driven by percent), then drives off on its own. **The truck is not in `mine_game.glb` any more:** it is the shared prop `art/3d/props/ht04/ht04_game.glb` (3,859 tris, 1 draw; body, `fill` morph, `truck_dump`, `truck_drive`, `chute_pour`, `truck_load_rich`, `Fill_Arc`, code-driven wheels). The game drops its root onto the Mine's truck markers (`Path_Load` etc.) and the Refinery's. See `art/3d/props/ht04/README.md`.

| | |
|---|---|
| **Game GLB** | `mine_game.glb`, **126,476 B (0.13 MB)**, md5 `33737ff698161c274d0fda22cd7ee53a` (10/23 20:20 build) |
| Triangles / draws | **18,270 triangles, 10 draw calls with every tier visible** (10 meshes × 1 primitive; no truck) |
| Format | meshopt + quantization (`gltfpack -cc -kn -ke`). Extensions: `EXT_meshopt_compression` and `KHR_mesh_quantization` only. **No Draco.** No morph targets, no skins (the truck and its `fill` morph are in the ht04 prop). |
| Materials | `SHM_Paint` and `SHM_GlowCyan` (`../_shared/shared_materials.json`). Plain metallic/roughness plus emissiveFactor. No transmission, clearcoat or ior. Colour is in `COLOR_0` vertex colours. **No images or textures** and no TEXCOORD. |
| Units / axes | 1 m, Y up. The origin is concept B's world origin. The camera side is +Z. |
| Bounds (glTF) | (−15.55, −0.14, −14.72) … (26.0, 21.78, 11.8). The +X growth is the two parallel haul lanes (outbound z 9, return z 0) running off the phone frame on the right to x 26; +Z 11.8 is the outbound lane's front berm toe. |
| No astronauts | The concept-B astronaut is removed. |
| Budget | Mine station **30k tris / 15 draws including the future operator prop (~3k tris, 2 draws)**, so the Mine itself is held to **≤ 27k tris / ≤ 13 draws**: it uses **18,270 / 10**; with the shared HT-04 at `Path_Load` (3,859 / 1) the station is 22,129 / 11. |

## Files
- `mine_game.glb`: the game asset.
- `truck_fill_strip_393.png`: **fill proof in the FULL 393×852 station frame**: 4 frames at fill 10 / 33 / 66 / 100 % (official remap), `chute_pour` running in the 10 / 33 / 66 frames, each with a 3× inset of the truck (cyan box = inset area). Rendered from the game meshes: the Mine GLB plus the shared `ht04` prop with its root on `Path_Load` (`_src/proof_fill.py --mode strip --truck` + `_src/proof_strip.py`). It also shows the haul trail: the haul lanes (re-rendered 10/23 20:30 on the new bay).
- `truck_fill_strip_1179.png`: the same 4 frames at 1179×2556 (insets 3× of the 393 scale).
- `mine_phone_393x852.png` / `mine_phone_1179x2556.png` (10/23 PM): **phone proofs from the game mesh** (pruned raw GLB + the HT-04 prop on `Path_Load`, full load), station camera from `Cam_Target`, tiers hidden. Cycles CPU, 16 samples, no denoiser, no tiling (`_src/proof_phone.py`). The ground is a flat proof plane; the game draws its own ground and the deposit glow, so neither shows here.
- `mine_tiers_393x852.png` / `mine_tiers_375x667.png`: the same with **every tier visible**, at both of Coder's safe-area sizes.
- `_src/mine_layout.py`: the station re-layout applied on top of the concept-B scene (see Layout changes), including the two-lane graded haul road (`graded_roads`, `M_road_graded`) and its exact centre lines `OUT_LEGS` / `RET_LEGS` (straights and the R 4.5 m U-turn), the re-laid conveyor, the moved silo and the moved `Dep_01`, which the build also turns into the `Path_Out_*` / `Path_Ret_*` markers.
- `haul_paths_topdown.png` (1600×1200, 40 px/m): **top-down haul path diagram** over an orthographic render of the game mesh (truck on `Path_Load`): every `Path_Out_*` / `Path_Ret_*` marker with its yaw arrow, each leg with its length, the dashed 1.5 m reverse, the eased per-leg times, the `Dep_01/02` tap circles, the `Operator_Deck` footprint and the 393×852 frame's right edge at ground level.
- `_src/proof_paths.py`: makes that diagram (Blender pass for the base render, then python3/PIL for the overlay from `raw_info.json`).
- `_src/build_mine.py`: does the camera fit, renders the phone shots, and builds the game GLB. That covers the material remap, tiers, culling, the per-group bake and decimation to budget, the truck armature, skin and fill morph, the clips, the markers and the export. It writes two GLBs: the Mine (`--mout`, no truck) and the HT-04 prop (`--tout`, default `<mout dir>/ht04_raw.glb`; packed by `art/3d/props/ht04/_src/build_ht04.sh`).
- `_src/mine_clips.cjs`: `prune` trims each clip to its own nodes and moving channels. `verify` writes a JSON report with tris, draws, extensions, images, clip targets and foreign targets, nodes and skins.
- `_src/pack_mine.sh`: runs prune → gltfpack → verify.
- `_src/haul_times.py`: the eased trip-time model (8.33 m/s straights, 4.0 m/s turns, accel 3.0 / brake 4.0 m/s², reverse ≤ 3.0 m/s). The build prints the per-leg times and writes them to `raw_info.json` (`haul.times`).
- `_src/proof_phone.py`: the phone proofs above (`--at MARKER --fill F --tiers 0|1 --sizes WxH,...`).
- `_src/phone_downscale.py`: makes the 393×852 from the 1179×2556 master (PIL Lanczos).
- `_src/proof_fill.py`: imports the pruned raw GLB (Blender has no meshopt decoder), sets the phone camera from `Cam_Target` extras and renders the fill frames with the official remap (`--mode strip --rx 393|1179`), `chute_pour` and the rich drop. `_src/proof_strip.py` lays out the strip with the 3× insets.

Rebuild (from the repo root, Blender 4.2):
```
B=/opt/blender-4.2.3-linux-x64/blender; S=art/3d/buildings/mine/_src
$B -b -P art/3d/mine_concepts/_src/concept_b_sleek.py -P $S/build_mine.py -- --arm park --only none --out /tmp/mine/gen --mode game --mout /tmp/mine/raw.glb --tout /tmp/mine/ht04_raw.glb
$S/pack_mine.sh /tmp/mine/raw.glb art/3d/buildings/mine/mine_game.glb
$B -b -P $S/proof_phone.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw.glb --out art/3d/buildings/mine --name mine_phone --tiers 0 --sizes 393x852,1179x2556 --ps 16
$B -b -P $S/proof_phone.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw.glb --out art/3d/buildings/mine --name mine_tiers --tiers 1 --sizes 393x852,375x667 --ps 16
$B -b -P $S/proof_fill.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw_pruned.glb --out /tmp/mine/proof --ps 32 --mode strip --rx 393
$B -b -P $S/proof_fill.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw_pruned.glb --out /tmp/mine/proof --ps 24 --mode strip --rx 1179 --pcts 10,33,66,100
python3 $S/proof_strip.py /tmp/mine/proof 393 art/3d/buildings/mine/truck_fill_strip_393.png
python3 $S/proof_strip.py /tmp/mine/proof 1179 art/3d/buildings/mine/truck_fill_strip_1179.png
$B -b -P $S/proof_paths.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw_pruned.glb --out /tmp/mine/paths_base.png
python3 $S/proof_paths.py /tmp/mine/paths_base.png /tmp/mine/raw_info.json art/3d/buildings/mine/haul_paths_topdown.png
```
The HT-04 prop is unchanged by this pass (no repack: `art/3d/props/ht04/ht04_game.glb` as committed). The camera fit is automatic (see Station camera).

## Station camera (Game Coder spec)
Perspective, **38° vertical FOV, tilted down 18°, aimed at `Cam_Target`**.
- **Aim (10/23 PM):** **W = 33.8 m**, `Cam_Target` glTF **(0.85, 6.0, 2.36)** (Blender (0.85, −2.36, 6.0)), extras `{"frame_w": 33.8, "fov_y_deg": 38, "pitch_down_deg": 18, "distance_m": 106.4}`.
- **Distance** d = (W/2) / (tan 19° · aspect); 106.4 m at 393×852 and 1179×2556 (`Cam_Target` is a look-at point; code recomputes d per aspect, as QA3D does).
- **Fit (`build_mine.py cam_fit`, after the tiers are built):** Coder's exact tier safe area, **y 144–568 at 393×852 and y 144–383 at 375×667, 0 px side margin**. W is scanned from 22 m in 0.2 m steps and the target height is bisected until every tier vertex sits inside both bands with a 3 px margin and the focus (rig, conveyor, parked truck, silo, bay) stays above y 660. The 375×667 band is the binding one.
- **Result (all tiers visible):** see the Tiers table; focus box on 393×852 x 23…370, y 231…530.

## Game GLB nodes
Everything sits under the root `Mine`. gltfpack puts each mesh on an **unnamed child node** of its named node; that child carries the quantization offset and scale. Find meshes under the named node with `traverse`. The names, pivots and extras are on the named nodes.

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint` | static base merged by material: pads, rig skirt, hopper, conveyor frame, silo base, graded roads (outbound + return lanes, not decimated), rocks | 10,036 | SHM_Paint | origin |
| `Base_GlowCyan` | all static cyan glow: light strips | 3,702 | SHM_GlowCyan | origin |
| `Rig` | bore head and crown block, the moving part of the rig (clip `dig`) | 635 | SHM_Paint | (−7.5, 8.65, −3.6) |
| `Conveyor` | belt-surface ore lumps on the re-laid belt (clip `conveyor_run`) | 294 | SHM_Paint | (−0.83, 2.56, −2.62), the tail end C0 |
| `Silo` | ore silo (moved 1.5 m back, clear of the U-turn) | 784 | SHM_Paint | (10.0, 0, −6.0), base centre |
| `Tier_03…20` | see Tiers | | | |

### HT-04 truck (shared prop)
The truck, its joints, the `fill` morph (official remap `influence = 0.5 + 0.5 * (fill_pct / 100) ** 0.8` for fill_pct > 0 and 0 at 0 %; apex 0.17 m over the rim at 0.5 and **0.85 m over the rim top (4.23 vs 3.38 m) at 1**), the truck clips and `Fill_Arc` all live in **`art/3d/props/ht04/`** (README there). Place its root `Truck` (ground centre, +X forward = yaw 0) on `Path_Load` (11.0, 0, 9.0), yaw 0: the bed centre is then exactly under the chute mouth. Wheels are code-driven (`HT04_Wheel_*`, spin about local X, `wheel_radius` 0.853 m in the root extras).

## Clips
| Clip | Length | Loop | Targets (only these) | What it does |
|---|---|---|---|---|
| `dig` | 3.0 s | loop | `Rig` translation | The bore head lowers 0.6 m and comes back up (cosine). |
| `conveyor_run` | 1.0 s | loop | `Conveyor` translation | The lumps move one 0.9 m lump spacing along the belt, linear, so the loop is seamless. |
| `chute_pour`, `truck_load_rich`, `truck_dump`, `truck_drive` | | | | In `ht04_game.glb` (see its README). |

**Removed:** `truck_scoop` (no arm), the wheel-spin `truck_drive` (wheels are code-driven now) and the timed `truck_load` (the fill is the `fill` morph now; there is no debug preview clip).

**Sequence rules (game side):**
- **Load:** arrive heading +X at `Path_Load_Approach`, reverse 1.5 m straight to `Path_Load`, then play `chute_pour` (loop) while tweening the fill 0 → 100 % (2 min at Lv1). A rich tap plays `truck_load_rich` over the pour and adds +25 %. At 100 % stop `chute_pour` and drive off forward along the outbound lane (`Path_Out_01` = `Road_Entry` → `Path_Out_02` at x 26), off the right edge.
- **Never drive with the bed raised**: move the truck only when `truck_dump` is finished (bed at 0°).
- **Never drive while `chute_pour` or `truck_load_rich` is running**: the chunks are on truck joints and would ride along.

## Tiers
**Safe area (Coder, exact): y 144–568 at 393×852 and y 144–383 at 375×667, 0 px side margin, camera from `Cam_Target`.** Checked on the packed `mine_game.glb` by projecting every tier vertex (`/workspace/aa_ps/check.mjs`), and in `mine_tiers_393x852.png` / `mine_tiers_375x667.png`:

| Tier | 393×852 x | 393×852 y (144–568) | 375×667 x | 375×667 y (144–383) | 1179×2556 y | OK |
|---|---|---|---|---|---|---|
| `Tier_03` | 174–299 | 436–450 | 166–287 | 343–356 | 1309–1349 | yes |
| `Tier_05` | 195–267 | 383–474 | 186–254 | 294–379 | 1150–1421 | yes |
| `Tier_08` | 23–95 | 375–452 | 25–93 | 286–357 | 1125–1355 | yes |
| `Tier_12` | 264–327 | 352–450 | 250–309 | 264–356 | 1055–1351 | yes |
| `Tier_20` | 63–141 | **231**–325 | 61–135 | **148**–238 | 692–975 | yes |

Every tier node has `extras {"tier": N, "hidden_by_default": true}` (three.js `userData`). glTF has no hidden flag, so the loader must set `visible = false` on load. Each tier is one draw.

| Node | Adds | Tris | Material | Pivot (glTF) |
|---|---|---|---|---|
| `Tier_03` | conveyor light kit: cyan running lights on both trough walls, plus head and tail beacons (follows the re-laid belt) | 208 | SHM_GlowCyan | (3.97, 0, 2.82) |
| `Tier_05` | second pod hopper east of the first, plus a pneumatic feed tube onto the conveyor | 1,370 | SHM_Paint | (4.0, 0, −3.64) |
| `Tier_08` | radiator wing behind the rig power module (6 panels, mast, coolant pipe) | 272 | SHM_Paint | (−12.09, 0, −7.65) |
| `Tier_12` | second, taller ore silo behind the first, plus a transfer bridge and beacon | 685 | SHM_Paint | (10.6, 0, −10.61) |
| `Tier_20` | Mk II bore crown: bigger crown housing, twin emitter pods and a tall mast | 284 | SHM_Paint | (−7.5, 0, −3.59) |

Base 13,738 + moving 1,713 (Rig, Conveyor, Silo) + tiers 2,819 = 18,270 tris (the truck's 3,859 are in the ht04 prop).

## Markers (empties, glTF coords; yaw is about +Y, 0 = truck faces +X)
- **Haul layout (10/23 PM redesign): two parallel lanes, one U-turn, a 1.5 m reverse.** Outbound (loaded) on **z 9 heading +X**, return (empty) on **z 0 heading −X**, both dead straight from x 12.5 to the strip at **x 26**. The load bay is the west end of the z 9 lane (x 5.5 → 12.5) under the re-laid conveyor chute. The empty truck comes in on z 0, makes one **left U-turn of R 4.5 m** (centre (12.5, 0, 4.5); the 9 m lane spacing fixes R = 4.5, so an 8 m radius does not fit here) onto z 9 heading +X, stops at `Path_Load_Approach` and **reverses 1.5 m** under the chute. Then it drives off forward, dead straight. No S-bends, no lane crossing. The reverse is needed because the conveyor crosses the U-turn about 4 m up, too low for a loaded heap (4.23 m) driving under it; the empty truck (3.5 m) clears it. See `haul_paths_topdown.png`.
- Every haul marker is a `truck_pose` empty with `extras.yaw_deg` (= the node's rotation about +Y; 0 = +X, 180 = −X, −90 = +Z toward the camera), `extras.s_m` (distance along its route) and `extras.next_leg` (JSON: `{"type": "straight", "length_m"[, "reverse": true]}`, `{"type": "arc", "turn": "left", "radius_m": 4.5, "centre_glTF", "sweep_deg", "length_m"}` or `{"type": "handoff", "to"}`). Follow the leg as given (straight, or the arc about `centre_glTF`).
- **Trip times** (eased model `_src/haul_times.py`: 8.33 m/s on straights, 4.0 m/s in the turn, accel 3.0 / brake 4.0 m/s², reverse ≤ 3.0 m/s):

  | Route | Marker | Position (glTF) | Yaw | Next leg | Length | Time |
  |---|---|---|---|---|---|---|
  | out | `Path_Load` | (11.0, 0, 9.0) | 0 | straight +X | 1.50 m | 1.00 s (0 → 3.0 m/s) |
  | out | `Path_Out_01` (= `Road_Entry`) | (12.5, 0, 9.0) | 0 | straight +X | 13.50 m | 2.19 s (3.0 → 8.33 m/s) |
  | out | `Path_Out_02` | (26.0, 0, 9.0) | 0 | handoff: strip inbound lane z 9 | | |
  | | | | | | **out 15.0 m** | **3.19 s** |
  | ret | `Path_Ret_01` | (26.0, 0, 0) | 180 | straight −X | 13.50 m | 1.90 s (8.33 → 4.0) |
  | ret | `Path_Ret_02` | (12.5, 0, 0) | 180 | arc left, centre (12.5, 0, 4.5), 90° | 7.07 m | 1.77 s (4.0) |
  | ret | `Path_Ret_03` | (8.0, 0, 4.5) | −90 | arc left, centre (12.5, 0, 4.5), 90° | 7.07 m | 2.27 s (4.0 → 0) |
  | ret | `Path_Load_Approach` | (12.5, 0, 9.0) | 0 | **reverse** −X to `Path_Load` (`reverse_m` 1.5) | 1.50 m | 1.32 s |
  | | | | | | **return 29.1 m** | **7.26 s** |

  The return is 7.26 s, a quarter-second over the ~7 s target: the turn speed (4 m/s through 14.1 m of U-turn) dominates, and the U radius is fixed at 4.5 m by the 9 m lane spacing.
- **`Path_Load`** (11.0, 0, 9.0), yaw 0: the load / rest pose. The **bed centre is exactly under the chute mouth**: `extras.bed_centre_glTF` (9.4, 1.99, 9.0) and `extras.chute_glTF` (9.4, 4.35, 9.0) (build `LOADCHECK` dxy 0.000).
- **`Path_Load_Approach`** (12.5, 0, 9.0), yaw 0: end of the U-turn; stop, reverse 1.5 m along −X.
- **`Operator_Deck`** (−4.5, 0, 6.5), rotation identity (deck front faces +Z): root for `art/3d/props/mine_operator/mine_operator_game.glb` (not in this GLB). Moved west, clear of every road; its footprint box on 393×852 is about x 114–150, y 466–513.
- **`Fill_Arc`**: in the ht04 prop, a child of the truck root at truck-local (2.2, 4.6, 0).
- **`Rich_Pop`** (9.4, 4.88, 9.0): the money-pop anchor for the rich load, 1.6 m over the bed rim under the chute (valid while the truck is parked at `Path_Load`).
- **`Dep_01`** (3.5, 0, 12.5), the main He-3 seam (r 2.2 m), moved 10/23 PM to open ground in front of the bay's west end (the U-turn island spot was hidden behind the parked truck on screen; it is now at about (230, 537) px on 393×852), and **`Dep_02`** (−1.2, −0.01, 10.4), the tap deposit (r 1.05 m, about (171, 527) px). The game draws the deposit glow. **No floating crystals:** the concept's He-3 seam crystals over the deposits are deleted in the game build (and a later pass removes any He-3 crystal/gem/shard mesh left), and the antenna tip sphere that floated over the headframe after the antenna rod was culled is dropped too. There is no scoop: `extras.tap` reads "the drill taps it: the next load comes down the chute rich -> play truck_load_rich at Path_Load".
- **Haul edge:** both lanes end at **x 26.0**, outbound z 9 (yaw 0) and return z 0 (yaw 180), flush with the 8 m strip (unchanged from `219e774`: heights within 2 mm, strip colours; `_src/mine_layout.py` `SEAM_*`; proof `../_shared/road/haul_road_seams_proof.png`). On 393×852 the frame's right edge is at about x 17–18 m, so the last ~8 m of both lanes and the join are off screen. Lane profile: 4.0 m graded surface, berm crests ±2.35 m, toes ±2.8 m, tyre tracks 0.4 m wide at ±1.45 m.
- **`Road_Entry`** (12.5, 0, 9.0), yaw 0: = `Path_Out_01`, where the loaded truck leaves the bay.
- **`Crew_Path_01..07`**: (−9.4, 0.64, 0.2) at the rig operator pod deck → (−9.0, −0.01, 1.9) → (−5.6, 0, 2.7) → (−2.2, 0, 2.3) → (1.0, 0, 1.6) → (5.0, 0, −0.2) → (8.6, 0, −2.9) at the moved silo.
- **`Cam_Target`** (0.85, 6.0, 2.36), `frame_w` 33.8. See Station camera. `Path_Out_03/04` and `Path_Ret_04..08` are gone (fewer legs).

## Layout changes vs the concept-B master
These live in `_src/mine_layout.py`. The B look, palette and parts are otherwise unchanged.
- **Receiving hopper removed:** the DUMP 01 receiving hopper and its lift tube are gone. Trucks haul to the Refinery station (off the right edge) and dump there.
- **No scoop arm (10/23):** `build_mine.py` deletes the HT-04's loading arm (28 objects: pedestal, turret, shoulder, booms, rams, hoses, scoop and its ore) right after the layout, so it is gone from the renders, the game mesh, the skin and the camera fit. The suspension `swing_arm`s stay.
- **Head-end support replaced:** the head-end cantilever pylon and boom stood in the new road. A column with a knee brace under the trough, north of the road, replaces them.
- **Haul road re-laid (10/23 PM redesign):** two parallel straight lanes (z 9 out, z 0 return) from x 12.5 to x 26, joined by one R 4.5 m U-turn at the west end (x 8 → 12.5); the bay continues the z 9 lane west to x 5.5, just behind the parked truck's tail. The old S-curve, the x 19.5 crossing, the z 13.5 straight and the U-turn round the old `Dep_01` are gone.
- **Conveyor re-laid:** it now runs from the pod hopper tail to a new discharge chute at (9.4, 4.35, 9.0) over the bay (trough, walls, strips, belt, hoops, tail pylon, head/tail housings, head column at 58 % along). It crosses the U-turn about 4 m up (the empty truck is 3.5 m).
- **Silo moved 1.5 m back** (Blender +y, glTF z −6.0) so its plinth clears the U-turn.
- **Graded regolith road** (replaces the flat dark decal stripe). Built in `mine_layout.graded_roads` as real geometry, two meshes `haul_road_out` / `haul_road_return`:
  - **Cross-section:** a 4.0 m graded running surface (the HT-04 is 3.82 m over the tyres; the old 3.2 m stripe was narrower than the truck) with a 2 cm crown, then a **low berm on each side**: foot at ±2.0 m, crest **25 cm** high at ±2.35 m, toe buried at ±2.8 m.
  - **Tyre tracks (worn trail, 10/23):** two 0.4 m wide, 3 cm deep ruts centred ±1.45 m (the HT-04 tyre lines), in a darker vertex colour, on both lanes, so the trail reads continuously from the bay off the right edge, and back round the U-turn to the bay.
  - **Colour** is in a `RoadCol` corner colour attribute (no images): track `#a4a7ac` (a little lighter than the regolith), tyre tracks `#6c6f74`, berm crest `#939499`, toe `#82858a`, with ±5 % low-frequency variation. The render material `B_HaulRoadGraded` multiplies it by fine gravel noise and bump; the game GLB copies it into `COLOR_0` of `Base_Paint`.
  - **Junctions:** berms flatten wherever they cross another road's running surface (the U-turn meets both lanes at x 12.5), so the junctions are open. Berms also flatten next to station parts (head column foot, rig feet) so nothing is buried. Around `Dep_01` / `Dep_02` the berms are fully open within 2.5 m of the marker (see Deposit clearance).
  - The return surface sits 2 cm under the outbound one where they overlap (no z-fighting). Pebbles and boulders on the road were removed (36). In the render scene the terrain under the road is cut 3 cm below the road surface wherever it bulged through (142 ground vertices); `M_ground` itself is untouched.
  - Roads skip the planar dissolve and the decimation (they would smear the ruts and berms).
- **Deposits moved:** `Dep_01` in front of the bay's west end, `Dep_02` west of it. The drill taps them; ore only ever reaches the truck through the chute.
- **Deposit clearance (game fix):** in-game, the concept's deposit heap mound (`deposit` / `deposit_small`, the "crater" over Dep_01), its He-3 seam crystals and the spilled ore chips covered the game-drawn deposit glow disc and gem. `build_mine.py` now deletes every concept deposit-art mesh whose centre is within 6 m of `Dep_01` / `Dep_02` (67 objects: `deposit*`, `seam_crystal*`, and the `spill_rock/he3/pt*` ore chips), plus loose `pebble`s within 2.8 m. This happens after the layout and before the merge. `mine_layout.graded_roads` adds obstacle rings so no berm rises within 2.5 m of either marker. As a result, **nothing stands within 2.5 m of either Dep marker except the flat graded running surface (≤ 6 cm)**, which the fixed `Path_*` centre lines put there, and the truck parked at `Path_Load` (fender 2.33 m from `Dep_01`; it is the moving actor). The `Dep_*` extras `glow` now reads "drawn by the game (no deposit mesh in the GLB; clear ground within 2.5 m)". (That fix kept every name; the later 10/23 passes changed the truck, clips, markers and aim as described above.)
- **Text dropped:** stencils and labels are culled from the game GLB.

## Validation
- **`mine_clips.cjs verify`** (`_src/pack_mine.sh`):
  - 10 meshes / 10 primitives, **18,270 triangles, 10 draws**, 0 images/textures, extensionsUsed = [EXT_meshopt_compression, KHR_mesh_quantization]. No Draco, no transmission/clearcoat/ior.
  - 2 clips, each targets only its own node, **0 foreign targets**: `dig` → Rig (3.0 s), `conveyor_run` → Conveyor (1.0 s) (the truck clips are in `ht04_game.glb`)
  - markers: `Path_Load`, `Path_Load_Approach`, `Road_Entry`, `Rich_Pop`, `Operator_Deck`, `Cam_Target` (frame_w extras), `Path_Out_01..02`, `Path_Ret_01..03`, `Dep_01/02`, `Crew_Path_01..07`; every `Tier_*` keeps `{"tier": N, "hidden_by_default": true}`.
  - vs `219e774`: removed `Path_Out_03/04`, `Path_Ret_04..08`; moved `Path_Load`, `Path_Load_Approach`, `Road_Entry`, `Rich_Pop`, `Operator_Deck`, `Dep_01`, `Crew_Path_05..07`, `Cam_Target` (W 33 → 33.8).
- **Tier safe area:** `/workspace/aa_ps/check.mjs` (three `GLTFLoader` + `MeshoptDecoder` on the packed GLB) projects every tier vertex at 393×852, 375×667 and 1179×2556: all inside (Tiers table).
- **Haul clearances (4.0 m surface / 5.6 m toes):** `Dep_01` tap circle (r 2.2) is 0.3 m from the bay surface's west corner and clear of every berm (2.5 m obstacle ring); `Dep_02` is 6.7 m from the bay; the `Operator_Deck` footprint is 8.6 m from the nearest road. The U-turn's inner surface edge is 2.5 m from its centre (bare ground island).
- **Load pose:** the build prints `LOADCHECK`; the bed centre and the chute discharge are 0.000 m apart in plan.
- **Fill read:** `truck_fill_strip_393.png` / `_1179.png` (game mesh, station camera, official remap).

## Caveats
- The return is **7.26 s**, slightly over the ~7 s target (see the trip table). Getting under 7 s needs a faster turn speed (≈4.6 m/s) or a lane spacing over 9 m.
- The empty truck drives under the conveyor in the U-turn (about 4 m clearance vs 3.5 m truck). The loaded truck never does: it leaves dead straight on z 9.
- The game GLB is a baked, decimated proxy. Small curved parts are faceted; procedural dust, grime and wear live only in the .blend and the renders.
- All metals are folded into `SHM_Paint`, with their grey kept in the vertex colour, to reach 10 draws.
- `Truck` is one skinned mesh. The ram pistons are rigidly skinned, one joint each. The pour / rich chunks are on truck joints, so they ride with the truck: only play those clips while it is parked at `Path_Load`.
- Blender prints "mesh not valid" export warnings for Rig and Tier_05 (and the truck mesh in the prop build), which are the joined, decimated meshes. The packed GLB loads and inspects cleanly, and the renders and clearance checks look right.
- Cyan is used for light strips (concept B). There are no He-3 crystal meshes in the game GLB.
