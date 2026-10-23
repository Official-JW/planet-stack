# Refinery station concept master

The Planet Stack **Refinery** is its **own station**, one swipe right of the Mine (order Mine, Refinery, Dock; stations 160 m apart).
The HT-04 haul truck drives in from the Mine along a haul road that enters from the **left edge**, tips into the RB-1 intake bin and drives back out
the left edge. From the bin the ore splits into a **He-3 line** and a **fuel line (LOX / LH2 only, no methane)**. Same style as Mine concept B and the
Life Support / Dock masters: white shielded hulls, graphite structure, cyan light strips and a weathered finish. Everything sits above ground: no caves,
no glass domes, no tan. The ground is the shared cool-grey `M_ground`. Labels are invented stencils only (RB-1, BF-1, SP-1, BE-1, SV-1, KN-1/2, CP-1,
CT-1..4, DC-1/2, FS-1, CR-1, MS-1, RX-1, WC-1, EL-1/2, LQ-1, RAD-1, LOX-1..3, LH2-1, CM-1, A-1, HT-04), with no real logos.

The build is fully standalone: it reads no Mine markers, layout or GLB (`REFINERY_ANCHOR`, `Path_Dump` and the Mine-relative hairpin are gone).

| | |
|---|---|
| Master | `refinery_master.blend` (1,616 objects, **340,178 tris**, Blender 4.2, procedural shading) |
| Master GLB | `refinery_master.glb`, 2,220,712 B, md5 `e007974cd9bc288b94e9a2164f6a28f3`, `gltfpack -cc -kn -km` (meshopt + quantization, no Draco). Review asset, not for the game |
| **Game GLB** | `refinery_game.glb`, **224,044 B (0.21 MB)**, md5 `d1178fd768121029aaa577ff1abc0919`. **26,560 tris and 13 draws with every tier visible** (budget 30k / 15) |
| Game GLB format | `EXT_meshopt_compression` + `KHR_mesh_quantization` only (no Draco). 3 shared materials `SHM_Paint`, `SHM_GlowCyan`, `SH_GlowRed`, each only `pbrMetallicRoughness` + `emissiveFactor` (no transmission / clearcoat / ior / emissive_strength), no images or textures. Colour comes from `COLOR_0` vertex colours. No astronauts, no truck |
| Units / axes / origin | 1 m, Y up. **Origin = `Truck_Dump`** (HT-04 centre while tipping). No rotation: place it like any station, `position.set(i*GAP, 0, 0)` |
| Station camera | **`Cam_Target` glTF (−5.00, 1.00, 3.36)**, extras `frame_w` **36**, `fov_y_deg` 38, `pitch_down_deg` 18, `distance_m_393x852` 113.33. Camera on +Z looking down −Z |
| Footprint (glTF) | refinery x −21…7, z −33…+3, top 14.8 m (DC-2 beacon). Haul road x −48…3.55, z −0.5…+11.8 |

## Process
Intake (white flow arrows in the diagram):
1. **T, HT-04 truck** comes in from the left edge, U-turns in front of the intake, reverses 4 m to `Truck_Dump` (the GLB origin) and tips its bed 50° over the rim of the bin.
2. **RB-1 intake bin**: steel bin with grizzly bars (node `Intake_Grate`, clip `intake_shake`), dust skirt, wheel stop and water-spray dust bar. The wheel stop is at x 3.55; the tail lip (z 1.63) clears the rim top (z 1.57) at the 50° tip.
3. **BF-1 belt feeder** meters ore out of the bin bottom up to **SP-1 splitter**, a flop gate with two chutes (cyan He-3, orange fuel). The vibrating grizzly VG-1 from the first layout was dropped to keep the intake compact.

He-3 line (cyan):
- **H1 BE-1 bucket elevator** lifts the He-3 feed 7.6 m. A covered **gallery conveyor** (`Conveyor_He3`) carries it over the fuel row on two towers.
- **H2 SV-1 sieve** keeps fines < 100 µm (He-3 is implanted in the fine grains).
- **H3 KN-1 sealed rotary kiln**, ~700 °C, electric, with an orange heat glow (`Kiln_Drum`, clip `kiln_spin`).
- **H4 gas hood + CP-1 compressor** collect and compress the released volatiles.
- **H5 CT-1..4 cold traps** strip H2O, CO2, N2 and H2. The H2 goes over the pipe rack to the fuel line ("H2 > FUEL").
- **H6 DC-1 cryo distillation column** separates He-3 from He-4.
- **H7 FS-1 filling station** fills the **glowing blue He-3 canisters** on the rack (`He3_Output`).
- **H8 tailings**: a conveyor takes the spent regolith from the kiln discharge to the tailings pile.

Fuel line (orange):
- **F1 CR-1 crusher** → **F2 MS-1 magnetic separator** (ilmenite concentrate).
- **F3 RX-1 H2 reduction reactor**, 900–1000 °C: FeTiO3 + H2 → Fe + TiO2 + H2O. **F3b slag / iron bin** under it.
- **F4 WC-1 condenser** knocks the water out of the gas stream.
- **F5 EL-1 electrolyzer**: 2 H2O → 2 H2 + O2. The H2 is recycled to RX-1 on an overhead loop.
- **F6 LQ-1 LOX/LH2 liquefier** with the **RAD-1** radiator wing.
- **F7 LOX-1 / LH2-1** cryo tanks (`Fuel_Output`) → **F8 "TO TANK FARM"** LOX + LH2 header ending in a flange (`Pipe_TankFarm`).

Support:
- **CM-1 control module** with airlock A-1, dust mat and **dust shower** arch, and a crew stair to the pipe rack.
- **X: pipe rack + catwalk** carries the H2 crossover.
- Power masts with red beacons, switchgear cabinet, a drop to the kiln and a drop to the electrolyzer.


## Layout (station frame)
- Station frame = the build's final coords with no rotation (Blender (x, y, z) = glTF (x, z, −y)). Screen right = +X.
- RB-1 and the tipping truck sit in the foreground on the right; the two process rows rise behind them (glTF z −3…−33). The open apron on the left
  (x −21…−4) carries the two haul lanes.
- This is the back side compared with the old Mine-station view, so most process stencils face away from the camera. The game GLB culls stencils
  anyway; the HT-04 decal reads correctly.
- The process rows are built in line coordinates and placed by `_rowM` (mirror in X, **row scale 0.85**), then mirrored in Y (historic).

### Haul road RD-1 (`rd_haul_road`, part of `Base_Paint`, RoadCol vertex colours, never decimated)
- **Inbound lane at glTF z +9**, heading +X from the left edge (x −48). This is the same Z as the Mine road that leaves the Mine's right edge
  (Mine `Road_Entry` (13.5, 0, 9) heading +X), so a straight road joins them across the 160 m gap.
- U-turn in front of the intake: centre (−4, 0, 4.5), radius 4.5 m, apex x 0.5 (bin starts at x 3.7).
- Stop at `Truck_Path_07` heading −X, then **reverse 4 m** straight along +X to `Truck_Dump`.
- **Outbound lane at glTF z 0**, from the wheel stop (x 3.55) out the left edge to x −48 heading −X.
- Lane surfaces: inbound y 0.025, outbound y 0.045; the ground is cut 3 cm under the road.

### Fit (393×852, station camera, every vertex projected, all tiers visible)
Target band: HUD bottom ~141 + 24 = 165 to sheet top 674 − 34 = 640, centre ~402.

| Part | x px | y px |
|---|---|---|
| RB-1 bin + tipping HT-04 (master truck, proof render) | 210…322 | **362…434 (centre ~398)** |
| RB-1 bin (game GLB) | 285…322 | 378…434 |
| Refinery (no road) | 52…322 | 227…468 |
| Tier_03 | 65…90 | 330…348 |
| Tier_05 | 144…169 | 359…384 |
| Tier_08 | 164…245 | 314…362 |
| Tier_12 (DC-2, the station top) | 74…100 | **230…360** |
| Tier_20 | 58…115 | 322…389 |

On 1179×2556 the same boxes scale ×3 (Tier_12 691…1079, Tier_20 967…1166).
The road runs off the left edge as intended (x down to −307).

Flat distance from `Cam_Target` (glTF XZ): Tier_03 35.2 m (farthest vertex 36.0), Tier_05 18.7, Tier_08 27.8, Tier_12 30.7, Tier_20 21.0. All within frame_w (36 m).

Tier_20 (LOX-2/3, 6.7 m tall) can't reach the y 220–240 top on its own without frame_w ≈ 21, which crops the station. The station's tallest part,
Tier_12 (DC-2, 14.5 m), puts the top at y 230 instead; Tier_20's top is at y 322.

## Files
- `_src/build_refinery.py`: the procedural Blender 4.2 build. It imports `art/3d/mine_concepts/_src/mc_common.py` (the concept B helpers and stage) and the HT-04 from the concept B master.
  `blender -b -P _src/build_refinery.py -- --out . [--quick 1] [--only glb,blend,hero,phone,turn,diagram] [--ps 24] [--ct x,y,z --fw W] [--hc x,y,z,tx,ty,tz]`
  - `--only glb` writes `refinery_master_raw.glb` (scratch). Pack it with `gltfpack -i refinery_master_raw.glb -o refinery_master.glb -cc -kn -km`.
  - `--only phone` renders from the station camera (`--ct` Blender coords, default −5, −3.36, 1.0; `--fw` 36) and prints `FIT` / `FIT_TIER`.
- `_src/build_game_glb_tiered.py`: the game exporter (`--target 27000`). It prints `FIT393` screen boxes per node, bin + truck, `TIERDIST` and `CAM_TARGET`.
  `blender -b refinery_master.blend -P _src/build_game_glb_tiered.py -- --out raw.glb`, then `gltfpack -i raw.glb -o refinery_game.glb -cc -kn -ke`.
- `refinery_phone_393x852.png`, `refinery_phone_1179x2556.png`: station camera, master scene (Cycles 24 samples).
- `refinery_station_game_393x852.png`: the game GLB (all tiers) plus the master HT-04 at `Truck_Dump`, same camera, flat Workbench preview.
- `refinery_intake_truck_closeup.png`, `refinery_intake_truck_top.png` (1600×1000): game GLB + HT-04 tipping; red balls = `Truck_Path_01..07` / `Truck_Exit`, yellow = `Truck_Dump`.
- **Stale (still the Mine-station layout):** `refinery_hero_3840x2160.png`, `turntable/`, `refinery_turntable_sheet.png`, `refinery_process_diagram.png`.

## Game GLB nodes
All under the root `Refinery` (extras: origin, road and layout notes, `draws_all_tiers` 13). gltfpack puts each mesh on an unnamed child of its named node.

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint` / `Base_GlowCyan` / `Base_GlowRed` | static base merged by material (road in Paint) | 16,008 / 930 / 344 | SHM_Paint / SHM_GlowCyan / SH_GlowRed (kiln + reactor glow, red lamps) | origin |
| `Intake_Grate` | RB-1 grizzly bars | 204 | SHM_Paint | (5.00, 1.54, 0) |
| `Kiln_Drum` | KN-1 rotary drum (axis along X) | 610 | SHM_Paint | (−3.69, 2.21, −26.93) |
| `Conveyor_He3` | ore lumps on the He-3 gallery belt | 732 | SHM_Paint | (3.25, 7.55, −8.35) |
| `Conveyor_Fuel` | ore lumps on the fuel belt | 396 | SHM_Paint | (5.35, 0.45, −6.90) |
| `Beacon_Lights` | red beacons | 328 | SH_GlowRed | (−11.71, 0, −21.30) |
| `Tier_03` | second He-3 canister rack | 1,964 | SHM_GlowCyan | (−18.82, 0, −28.97) |
| `Tier_05` | second electrolyzer EL-2 | 586 | SHM_Paint | (−9.23, 0, −14.85) |
| `Tier_08` | second rotary kiln KN-2 | 912 | SHM_Paint | (−4.02, 0, −24.40) |
| `Tier_12` | bigger cryo column DC-2 | 824 | SHM_Paint | (−17.21, 0, −24.80) |
| `Tier_20` | LOX-2 and LOX-3 tanks | 2,738 | SHM_Paint | (−16.57, 0, −14.18) |

Tier nodes carry `extras {"tier": N, "hidden_by_default": true}`. glTF has no hidden flag, so the loader must set `visible = false` on load.
Draws with every tier showing: 3 base + 5 moving + 5 tiers = **13**.

Clips (all loop): `kiln_spin` 4.0 s (one turn), `conveyor_he3_run` / `conveyor_fuel_run` 1.0 s, `intake_shake` 0.5 s (play while tipping), `Beacon_Lights_Blink` 1.2 s step.

## Markers (empty nodes, glTF)
`yaw_deg` is about +Y: 0 = heading +X, 90 = −Z, 180 = −X, −90 = +Z.

| Marker | Translation | yaw | Mode / notes |
|---|---|---|---|
| `Truck_Path_01` = `Road_Entry` | (−46, 0, 9) | 0 | forward; inbound lane at the left edge, from the Mine |
| `Truck_Path_02` | (−14, 0, 9) | 0 | forward |
| `Truck_Path_03` | (−4, 0, 9) | 0 | U-turn start (r 4.5) |
| `Truck_Path_04` | (−0.82, 0, 7.68) | 45 | forward |
| `Truck_Path_05` | (0.5, 0, 4.5) | 90 | apex |
| `Truck_Path_06` | (−0.82, 0, 1.32) | 135 | forward |
| `Truck_Path_07` | (−4, 0, 0) | 180 | stop, then reverse 4 m along +X (~1.5 s) |
| **`Truck_Dump`** | **(0, 0, 0)** | 180 | tip (cab −X, rear into RB-1), `intake_shake` |
| `Truck_Exit` = `Road_Exit` | (−46, 0, 0) | 180 | forward along the outbound lane off the left edge |
| `Cam_Target` | (−5.00, 1.00, 3.36) | | `frame_w` 36 |
| `He3_Output` | (−15.76, 0.10, −29.65) | | canister rack |
| `Fuel_Output` | (−16.57, 0.10, −19.15) | | LOX-1 / LH2-1 |
| `Pipe_TankFarm` | (−20.14, 0.94, −18.62) | | "TO TANK FARM" flange (now on the left side; the Dock is to the right) |
| `Crew_Path_01..07` | (−7.3, 0.1, −20.95), (−8.0, 0.1, −20.95), (−10.7, 0.1, −19.55), (−12.5, 5.45, −21.6), (−17.1, 0.1, −19.75), (1.0, 0.1, −20.35), (2.0, 0.1, −5.0) | | airlock → intake |

## Validation
- three.js GLTFLoader + MeshoptDecoder: 13 draws, 26,560 tris, 33,683 verts, materials SHM_GlowCyan / SHM_Paint / SH_GlowRed, 5 clips, `Cam_Target.userData.frame_w` 36, five tiers with `hidden_by_default`. extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression]; 0 images; no material extensions.
- Master build: `RELAYOUT moved 1075 neg 0`, `BELOW_GROUND []`, `RD-1 station road 1128 faces`, `ROADCUT 360`. Phone `FIT_TIER` all OK.
- Every proof was read at full size.

## Caveats
- The view is the back side of the old approved Mine-station view (needed so the bin + truck are in front and the road leaves left).
- The bin + truck sit on the right third of the screen (x 210…322), centred vertically in the band.
- The game GLB is a decimated proxy; stencils, handrails and grating are culled. Process rows are at 0.85 scale.
- `Pipe_TankFarm` is on the far-left (west) end; if the pipe should run to the Dock on the right, the flange needs to move (not done here).
