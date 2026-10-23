# Refinery station concept master

The Planet Stack **Refinery** is its **own station**, one swipe right of the Mine (order Mine, Refinery, Dock; stations 160 m apart).
The shared HT-04 haul truck (`art/3d/props/ht04/ht04_game.glb`) drives in from the Mine along a haul road that enters from the **left edge**, tips into the
RB-1 intake bin and drives back out the left edge. From the bin the ore splits into a **HELIUM-3 line** (cyan) and a **fuel line, LOX + LCH4** (orange; no LH2
product, no tanker). Fuel leaves on the buried pipeline **PL-1** heading right (+X) to the pad; HELIUM-3 leaves as dewars on a rack, loaded into the ship's cargo
at pickup. Same style as Mine concept B and the Life Support / Dock masters: white shielded hulls, graphite structure, cyan light strips and a weathered
finish. Everything sits above ground except the buried pipeline. The ground is the shared cool-grey `M_ground`. Labels are invented stencils only (RB-1,
BF-1, SP-1, BE-1, SV-1, KN-1/2, CP-1, CT-1..4, DC-1/2, FS-1, CR-1, MS-1, RX-1, WC-1, EL-1/2, SB-1, LQ-1, RAD-1, LOX-1..3, LCH4-1, PL-1, CM-1, A-1), with no real logos.

The build is fully standalone: it reads no Mine markers, layout or GLB (`REFINERY_ANCHOR`, `Path_Dump` and the Mine-relative hairpin are gone).

| | |
|---|---|
| Master | `refinery_master.blend` (1,638 objects, **357,764 tris** incl. the placed HT-04, Blender 4.2, procedural shading) |
| Master GLB | `refinery_master.glb`, 2,290,300 B, md5 `6b29cab5f92baea9cd46dcc6764852d9`, `gltfpack -cc -kn -km` (meshopt + quantization, no Draco). Review asset, not for the game |
| **Game GLB** | `refinery_game.glb`, **224,812 B**, md5 `e65968d7f1b567c1155e0ff90e42854a`. **26,566 tris and 13 draws with every tier visible** (budget 30k / 15) |
| Game GLB format | `EXT_meshopt_compression` + `KHR_mesh_quantization` only (no Draco). 3 shared materials `SHM_Paint`, `SHM_GlowCyan`, `SH_GlowRed`, each only `pbrMetallicRoughness` + `emissiveFactor` (no transmission / clearcoat / ior / emissive_strength), no images or textures. Colour comes from `COLOR_0` vertex colours. **No truck geometry** (only the `Truck_*` markers), no astronauts. `strings refinery_game.glb \| grep -i lh2` is empty (same for the master GLB) |
| Units / axes / origin | 1 m, Y up. **Origin = `Truck_Dump`** (HT-04 centre while tipping). No rotation: place it like any station, `position.set(i*GAP, 0, 0)` |
| Station camera | **`Cam_Target` glTF (−5.90, 8.50, 3.36)**, extras `frame_w` **30.8**, `fov_y_deg` 38, `pitch_down_deg` 18, `distance_m_393x852` 96.96. Camera on +Z looking down −Z |
| Footprint (glTF) | refinery x −21…7, z −33…+3, top 14.8 m (DC-2 beacon). Haul road x −46…3.55, z −0.5…+11.8 |

## Process
Intake (white):
1. **HT-04** (shared prop) comes in from the left edge, U-turns in front of the intake, reverses 4 m to `Truck_Dump` (the GLB origin) and tips over the bin rim.
2. **RB-1 intake bin**: steel bin with grizzly bars (node `Intake_Grate`, clip `intake_shake`), wheel stop and water-spray bar. The dust skirt is only on the far (+Y Blender) side
   and the back, so from the station camera nothing of the bin stands in front of the tipping truck (Coder QA3D 10/23). The RB-1 plate sits low on the bin front (z 0.85).
3. **BF-1 belt feeder** meters ore out of the bin bottom up to **SP-1 splitter**, a flop gate with two chutes (cyan He-3, orange fuel).

HELIUM-3 line (cyan) = **Tier_03 / Tier_08 / Tier_12**:
- **BE-1 bucket elevator** + covered gallery conveyor (`Conveyor_He3`) over the fuel row.
- **SV-1 sieve** keeps fines < 100 µm (He-3 is implanted in the fine grains).
- **KN-1 sealed rotary kiln**, ~700 °C (`Kiln_Drum`, clip `kiln_spin`); **Tier_08 = second kiln KN-2**.
- Gas hood + **CP-1** compressor → **CT-1..4 cold traps** strip H2O, CO2, N2 and H2. CO2 + H2 go over the pipe rack to SB-1 ("CO2 + H2 > SB-1").
- **DC-1 cryo distillation column** separates He-3 from He-4; **Tier_12 = bigger column DC-2**.
- **FS-1** fills the dewars on the **HELIUM-3 dewar rack** ("HELIUM-3 / DEWARS READY FOR SHIP PICKUP", `He3_Output`); **Tier_03 = second dewar rack**.
- Tailings conveyor from the kiln discharge to the tailings pile.

Fuel line (orange), **LOX + LCH4** = **Tier_05 / Tier_20**:
- **CR-1 crusher** → **MS-1 magnetic separator** (ilmenite concentrate).
- **RX-1 H2 reduction reactor**, 900–1000 °C: FeTiO3 + H2 → Fe + TiO2 + H2O, slag / iron bin under it. **WC-1** condenser knocks out the water.
- **EL-1 electrolyzer**: 2 H2O → 2 H2 + O2. H2 is recycled to RX-1 and fed to SB-1. **Tier_05 = second electrolyzer EL-2**.
- **SB-1 Sabatier reactor**: CO2 + 4 H2 → CH4 + 2 H2O (CO2 from the He-3 cold traps; the water goes back to EL-1).
- **LQ-1 liquefier** (O2 → LOX 90 K, CH4 → LCH4 112 K) with the **RAD-1** radiator wing.
- **LOX-1 / LCH4-1** cryo tanks (`Fuel_Output`); **Tier_20 = LOX-2 + LOX-3**.
- **PL-1 fuel pipeline head** (`Pipe_TankFarm`): LOX + LCH4 risers with valves drop into a small vault and go **below grade**; marker posts + a trench strip
  show the **buried PL-1** heading right (+X) to `Pipeline_Exit` and on to the Dock / pad. No tanker, no hose cart.

Support:
- **CM-1 control module** with airlock A-1, dust mat and dust shower arch, and a crew stair to the pipe rack.
- Pipe rack + catwalk (H2 / CO2 crossover), power masts with red beacons, switchgear.

## Layout (station frame)
- Station frame = the build's final coords with no rotation (Blender (x, y, z) = glTF (x, z, −y)). Screen right = +X.
- RB-1 and the tipping truck sit in the foreground on the right; the two process rows rise behind them (glTF z −3…−33). The open apron on the left
  (x −21…−4) carries the two haul lanes.
- This is the back side compared with the old Mine-station view, so most process stencils face away from the camera. The game GLB culls stencils
  anyway; the HT-04 decal reads correctly.
- The process rows are built in line coordinates and placed by `_rowM` (mirror in X, **row scale 0.85**), then mirrored in Y (historic).

### Haul road RD-1 (`rd_haul_road`, part of `Base_Paint`, RoadCol vertex colours, never decimated)
- **Inbound lane at glTF z +9**, heading +X from the left edge (x −46 = world 274, where the 11th 8 m `haul_road_seg` tile ends). This is the same Z as the Mine road that leaves the Mine's right edge
  (Mine `Road_Entry` (13.5, 0, 9) heading +X), so a straight road joins them across the 160 m gap.
- U-turn in front of the intake: centre (−4, 0, 4.5), radius 4.5 m, apex x 0.5 (bin starts at x 3.7).
- Stop at `Truck_Path_07` heading −X, then **reverse 4 m** straight along +X to `Truck_Dump`.
- **Outbound lane at glTF z 0**, from the wheel stop (x 3.55) out the left edge to x −46 heading −X.
- Lane surfaces: inbound y 0.025, outbound y 0.045; the ground is cut 3 cm under the road.
- **Strip join (x −34 → −46):** both lanes ease to the `haul_road_seg` x0 profile and colours (surface 0.045, crown 0.065,
  tracks ±1.45 at 0.026, berm crest ±1.65, toe ±1.8, track colours #797c81/#7d8085 on z 9 and #7d8085/#7a7d82 on z 0).
  Measured at x −45.99: every height within 2 mm of the strip. Before: inbound surface 0.025 vs 0.045 (2 cm step), tracks #8d9094,
  and the road ran to −48 so it overlapped the last tile by 2 m (z-fighting on z 0). `Truck_Path_01` / `Truck_Exit` unchanged (`RD_MK` −46).
  The rut is a doubled vertex at 1.5 m so the profile matches the strip's vertex count; visually unchanged in frame.

### Fit (393×852, station camera, every vertex projected, all tiers visible)
Target band: HUD bottom ~141 + 24 = 165 to sheet top 674 − 34 = 640, centre ~402. Target x 40…353.

| Part | x px | y px |
|---|---|---|
| Refinery + bin (no road, no PL-1 marker posts) | **44.6…353.4** (centre ~199) | **276.6…522.5** (centre ~400) |
| RB-1 bin | 306.9…350.4 | 457.2…522.5 |
| HT-04 tipping at `Truck_Dump` (proof render) | 223.2…353.4 | 464.3…519.0 |
| Tier_03 (dewar rack 2) | 59.6…87.4 | **387.5…407.3** |
| Tier_05 (EL-2) | 146.9…175.2 | **427.4…455.2** |
| Tier_08 (KN-2) | 169.6…259.4 | **372.8…425.7** |
| Tier_12 (DC-2, the station top) | 69.0…98.3 | **279.9…422.5** |
| Tier_20 (LOX-2/3) | 50.3…114.2 | **386.8…461.3** |

On 1179×2556 the same boxes scale ×3. The road runs off the left edge, and the PL-1 marker posts run off the right edge (x up to 401) toward the pad, as intended.

Flat distance from `Cam_Target` (glTF XZ, pivot / farthest vertex): Tier_03 34.8 / 35.6 m, Tier_05 18.5 / 19.5, Tier_08 27.8 / 30.2, Tier_12 30.3 / 31.8,
Tier_20 20.5 / 22.5. Tier_05/08/20 are within frame_w (30.8 m); **Tier_03 (+4.8 m) and Tier_12 (+1 m) are a little over** but fully in frame.

## Files
- `_src/build_refinery.py`: the procedural Blender 4.2 build. It imports `art/3d/mine_concepts/_src/mc_common.py` (the concept B helpers and stage).
  `blender -b -P _src/build_refinery.py -- --out . [--quick 1] [--only glb,blend,hero,phone,turn,diagram] [--ps 64] [--ct x,y,z --fw W] [--ht04 PATH [--ht04frame N]] [--truck none]`
  - `--ht04 art/3d/props/ht04/ht04_game.glb` hides the old master truck and places the shared HT-04 with `_src/place_ht04.py`: per its README, root `Truck`
    at the ground point under the truck centre = `Truck_Dump` (0, 0, 0), yaw 180° (cab −X, rear into RB-1), `truck_dump` clip baked at frame 22 (bed ~33° up, load sliding), `fill` 1.0.
    Imported materials get an `HT04_` prefix so the game exporter's own `SHM_*` names stay free.
  - `--only glb` writes `refinery_master_raw.glb` (scratch). Pack it with `gltfpack -i refinery_master_raw.glb -o refinery_master.glb -cc -kn -km`.
  - `--only phone` renders from the station camera (`--ct` Blender coords, default −5.9, −3.36, 8.5; `--fw` 30.8), prints `FIT` / `FIT_TIER`, and writes
    `refinery_phone_<w>x<h>_callouts.json` (projected anchor per module).
- `_src/build_game_glb_tiered.py`: the game exporter (`--target 27000`). It prints `FIT393`, `TIERDIST` and `CAM_TARGET`.
  `blender -b refinery_master.blend -P _src/build_game_glb_tiered.py -- --out raw.glb`, then `gltfpack -i raw.glb -o refinery_game.glb -cc -kn -ke`.
- `_src/make_callouts.py`: `python3 _src/make_callouts.py refinery_phone_1179x2556.png refinery_phone_1179x2556_callouts.json refinery_phone_callouts_1179x2556.png`.
- `refinery_phone_393x852.png`, `refinery_phone_1179x2556.png`: station camera, master scene + shared HT-04 tipping at `Truck_Dump` (Cycles 64 samples).
- **`refinery_phone_callouts_1179x2556.png`**: labelled callout proof (cyan HELIUM-3 line incl. Tier_03/08/12, orange LOX + LCH4 line incl. Tier_05/20 and PL-1, white intake + HT-04).
- **Stale (older camera / layout, not re-rendered):** `refinery_station_game_393x852.png`, `refinery_intake_truck_closeup.png`, `refinery_intake_truck_top.png`,
  `refinery_hero_3840x2160.png`, `turntable/`, `refinery_turntable_sheet.png`, `refinery_process_diagram.png`.

## Game GLB nodes
All under the root `Refinery` (extras: origin, road and layout notes, `draws_all_tiers` 13). gltfpack puts each mesh on an unnamed child of its named node.

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint` / `Base_GlowCyan` / `Base_GlowRed` | static base merged by material (road in Paint) | 15,969 / 901 / 394 | SHM_Paint / SHM_GlowCyan / SH_GlowRed (kiln + reactor glow, red lamps) | origin |
| `Intake_Grate` | RB-1 grizzly bars | 204 | SHM_Paint | (5.00, 1.54, 0) |
| `Kiln_Drum` | KN-1 rotary drum (axis along X) | 610 | SHM_Paint | (−3.69, 2.21, −26.92) |
| `Conveyor_He3` | ore lumps on the He-3 gallery belt | 732 | SHM_Paint | (3.25, 7.55, −8.35) |
| `Conveyor_Fuel` | ore lumps on the fuel belt | 396 | SHM_Paint | (5.35, 0.45, −6.90) |
| `Beacon_Lights` | red beacons | 328 | SH_GlowRed | (−11.71, 0, −21.30) |
| `Tier_03` | HELIUM-3: second dewar rack | 1,964 | SHM_GlowCyan | (−18.82, 0, −28.97) |
| `Tier_05` | fuel: second electrolyzer EL-2 | 586 | SHM_Paint | (−9.23, 0, −14.85) |
| `Tier_08` | HELIUM-3: second rotary kiln KN-2 | 912 | SHM_Paint | (−4.02, 0, −24.40) |
| `Tier_12` | HELIUM-3: bigger cryo column DC-2 | 824 | SHM_Paint | (−17.21, 0, −24.80) |
| `Tier_20` | fuel: LOX-2 and LOX-3 tanks | 2,738 | SHM_Paint | (−16.57, 0, −14.18) |

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
| `Cam_Target` | (−5.90, 8.50, 3.36) | | `frame_w` 30.8 |
| `He3_Output` | (−15.76, 0.10, −29.65) | | HELIUM-3 dewar rack (ship cargo pickup) |
| `Fuel_Output` | (−16.57, 0.10, −19.15) | | LOX-1 / LCH4-1 |
| `Pipe_TankFarm` | (−13.85, 0, −18.62) | 0 | PL-1 pipeline head: LOX + LCH4 go below grade here and run **buried along +X** (z −18.62) toward the Dock / pad |
| `Pipeline_Exit` | (15.90, 0, −18.62) | 0 | buried PL-1 leaves the Refinery footprint, continuing +X |
| `Crew_Path_01..07` | (−7.3, 0.1, −20.95), (−8.0, 0.1, −20.95), (−10.7, 0.1, −19.55), (−12.5, 5.45, −21.6), (−17.1, 0.1, −19.75), (1.0, 0.1, −20.35), (2.0, 0.1, −5.0) | | airlock → intake |

## Validation
- Packed game GLB: 13 draws, 26,566 tris, extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression], 0 images / textures, material keys only
  name / pbrMetallicRoughness / emissiveFactor, 5 clips, no truck nodes besides the `Truck_*` markers. `strings refinery_game.glb | grep -i lh2` → empty.
- Master build: `RELAYOUT moved 1112 neg 0`, `BELOW_GROUND` only `tf_lox` / `tf_lch4` at −0.34 (the intended buried PL-1 risers). Phone `FIT_TIER` all OK.
- Every proof was read at full size (and the truck / bin crop at 1179 checked: the tipping HT-04 is fully visible, nothing of the bin in front of it).

## Caveats
- The view is the back side of the old approved Mine-station view (needed so the bin + truck are in front and the road leaves left).
- The game GLB is a decimated proxy; stencils, handrails and grating are culled. Process rows are at 0.85 scale.
- Tier_03 / Tier_12 are 4.8 / 1 m farther from `Cam_Target` than frame_w (still fully in frame).
