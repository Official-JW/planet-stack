# Refinery station concept master

The Planet Stack **Refinery** is its **own station**, one swipe right of the Mine (order Mine, Refinery, Dock; stations 160 m apart).
The shared HT-04 haul truck (`art/3d/props/ht04/ht04_game.glb`) drives in from the Mine along a haul road that enters from the **left edge**, tips into the
RB-2 tipping hopper (DB-2 dump bay) and drives back out the left edge. From the bin the ore splits into a **HELIUM-3 line** (cyan) and a **fuel line, LOX + LCH4** (orange; no LH2
product, no tanker). Fuel leaves on the buried pipeline **PL-1** heading right (+X) to the pad; HELIUM-3 leaves as dewars on a rack, loaded into the ship's cargo
at pickup. Same style as Mine concept B and the Life Support / Dock masters: white shielded hulls, graphite structure, cyan light strips and a weathered
finish. Everything sits above ground except the buried pipeline. The ground is the shared cool-grey `M_ground`. Labels are invented stencils only (DB-2, RB-2,
AF-1, SZ-1, CV-0, CB-1, SP-1, BE-1, SV-1, KN-1/2, CP-1, CT-1..4, DC-1/2, FS-1, CR-1, MS-1, RX-1, WC-1, EL-1/2, SB-1, LQ-1, RAD-1, LOX-1..3, LCH4-1, PL-1, CM-1, A-1), with no real logos.

The build is fully standalone: it reads no Mine markers, layout or GLB (`REFINERY_ANCHOR`, `Path_Dump` and the Mine-relative hairpin are gone).

| | |
|---|---|
| Master | `refinery_master.blend` (10/23 22:41 rebuild with `_src/intake_db2.py`, incl. stage and the placed HT-04, Blender 4.2, procedural shading) |
| Master GLB | `refinery_master.glb` (10/23 23:17, DB-2 / intake upgrade + shared HT-04), 3,137,720 B, md5 `b301255d3d1c8aad709535e32f06a546`, 397,420 tris, `gltfpack -cc -kn -km -vpf` (meshopt + quantization, float positions because of the 370 m stage; no Draco), then clearcoat / transmission / ior stripped from the JSON (no images). Review asset, not for the game |
| **Game GLB** | `refinery_game.glb`, **265,392 B**, md5 `93c44166ecc39031966a9be130dfc093` (10/24 00:40: road ruts / tread / dust in vertex colour + Base_Paint skin merge, see *Road paint + draw merge* at the end). **29,356 tris and 13 draws with every tier visible**, so with HT-04 + FB-05 at 1 draw each the station is 15. CAM_OVERRIDE must be re-keyed. Before: 260,192 B, md5 `ea5ab7af54134c312cdd43f284fac642`, 15 draws |
| Game GLB format | `EXT_meshopt_compression` + `KHR_mesh_quantization` only (no Draco). 4 shared materials `SHM_Paint`, `SHM_GlowCyan`, `SH_GlowRed`, `SH_Dust` (dust only: `alphaMode` BLEND, alpha from `COLOR_0`.a), each only `pbrMetallicRoughness` + `emissiveFactor` (no transmission / clearcoat / ior / emissive_strength), no images or textures. Colour comes from `COLOR_0` vertex colours. **No truck geometry** (only the `Truck_*` markers), no astronauts. `strings refinery_game.glb \| grep -i lh2` is empty (same for the master GLB) |
| Units / axes / origin | 1 m, Y up. **Origin = `Truck_Dump`** (HT-04 centre while tipping). No rotation: place it like any station, `position.set(i*GAP, 0, 0)` |
| Station camera | **`Cam_Target` glTF (−6.90, 2.08, 5.45)**, extras `frame_w` **34.4**, `fov_y_deg` 38, `pitch_down_deg` 18, `distance_m_393x852` 108.29 (refit 10/23 21:05 for the iPhone-inset band, see Fit). Camera on +Z looking down −Z |
| Footprint (glTF) | refinery x −21…7, z −33…+3, top 14.8 m (DC-2 beacon). Haul road x −46…3.55, z −0.5…+11.8 |

## Process
Intake (white):
1. **HT-04** (shared prop) comes in from the left edge, U-turns in front of the intake, reverses 3.5 m to `Truck_Dump` (the GLB origin) and tips over the bin rim.
2. **DB-2 dump bay (10/23 PM upgrade, `_src/intake_db2.py`)**: sloped concrete apron (`db_apron`, falls toward the hopper) with joint lines, dark tyre-wear tracks, painted back-up guides, chevrons, a cyan guide line and a **TIP** stencil (single-sided decal quads, no logos); a concrete wheel stop with an armour cap and a striped bump rail; a full-height guard wall on the far side with a hazard cap and a low striped wall on the camera side so the tipping truck stays visible; three white bollards with cyan bands; a back splash wall with a spray bar and nozzles (H2O feed + valve); a green / amber / red status light (green lit); two flood lights on short posts. Dust: node `Dump_Dust` (pivot (4.1, 1.45, 0), rest scale 0.001 = invisible), 8 smooth puffs decimated to 55 %, own material `SH_Dust` with vertex-alpha falloff (dense core, soft rim). Clip **`dump_dust` 1.5 s, play once at the tip**: smooth Bezier scale 0 → 0.9 (0.25 s) → 1.15 (0.75 s) → 1.35 (1.375 s) → 0 (1.5 s) while drifting 0.75 m up; extras `opacity_curve` [[0,0],[0.2,0.9],[0.9,0.7],[1.5,0]] for the loader to drive `material.opacity` (true fade).
3. **RB-2 tipping hopper**: reinforced steel hopper on a plinth with liners, stiffener ribs, cyan strip and an **armoured lip** (top z 1.57, below the HT-04 bed lip); grizzly (node `Intake_Grate`, 13 graphite bars with armour caps, clip `intake_shake`). Nothing of the hopper stands in front of the tipping truck from the station camera.
4. **AF-1 apron feeder** (motor + finned gearbox housing, white skirts) carries ore out of the hopper bottom into **SZ-1 primary sizer** (hatch with hinges and dogs, top and side vents, motor + belt guard, flywheel node `Sizer_Flywheel`, clip `sizer_spin`), then a covered **transfer chute** onto **CV-0** whose tail pulley housing has grated guards and take-ups. Walkway with handrails and stairs, **CB-1** control box with a lit cyan screen and e-stop, cable tray and pipe runs. CV-0 feeds **SP-1 splitter**, a flop gate with two chutes (cyan He-3, orange fuel) (unchanged).

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
- Pipe rack + catwalk (H2 / CO2 crossover) and switchgear. **The power masts, their cables, beacon masts and power drops are removed (10/23 PM cleanup)**; red beacons remain only on the process units (`Beacon_Lights`).

## Layout (station frame)
- Station frame = the build's final coords with no rotation (Blender (x, y, z) = glTF (x, z, −y)). Screen right = +X.
- RB-2 and the tipping truck sit in the foreground on the right; the two process rows rise behind them (glTF z −3…−33). The open apron on the left
  (x −21…−4) carries the two haul lanes.
- This is the back side compared with the old Mine-station view, so most process stencils face away from the camera. The game GLB culls stencils
  anyway; the HT-04 decal reads correctly.
- The process rows are built in line coordinates and placed by `_rowM` (mirror in X, **row scale 0.85**), then mirrored in Y (historic).

### Haul road RD-1 (`rd_haul_road`, part of `Base_Paint`, RoadCol vertex colours, never decimated)
- **Inbound lane at glTF z +9**, heading +X from the left edge (x −46 = world 274, where the 11th 8 m `haul_road_seg` tile ends). This is the same Z as the Mine road that leaves the Mine's right edge
  (Mine `Road_Entry` (13.5, 0, 9) heading +X), so a straight road joins them across the 160 m gap.
- U-turn in front of the intake: centre (−3.5, 0, 4.5), radius 4.5 m, apex x 1.0 (bin starts at x 3.7).
- Stop at `Truck_Path_07` heading −X, then **reverse 3.5 m** straight along +X to `Truck_Dump` (3.35 m is the minimum: shorter and the truck's rear corner sweeps the bin rim).
- **Outbound lane at glTF z 0**, from the wheel stop (x 3.55) out the left edge to x −46 heading −X.
- Lane surfaces: inbound y 0.025, outbound y 0.045; the ground is cut 3 cm under the road.
- **Strip join (x −34 → −46):** both lanes ease to the `haul_road_seg` x0 profile and colours (surface 0.045, crown 0.065,
  tracks ±1.45 at 0.026, berm crest ±1.65, toe ±1.8, track colours #797c81/#7d8085 on z 9 and #7d8085/#7a7d82 on z 0).
  Measured at x −45.99: every height within 2 mm of the strip. Before: inbound surface 0.025 vs 0.045 (2 cm step), tracks #8d9094,
  and the road ran to −48 so it overlapped the last tile by 2 m (z-fighting on z 0). `Truck_Path_01` / `Truck_Exit` unchanged (`RD_MK` −46).
  The rut is a doubled vertex at 1.5 m so the profile matches the strip's vertex count; visually unchanged in frame.
- **Flatbed band trim (10/23 20:50):** the RD-1 berm along the z 9 lane reached into the flatbed lane (world z 13, x 308–319.4; z 10.4–11.4, up to 0.28 m).
  It is clamped (`FLATBED_TRIM` in `build_refinery.py`, 65 vertices) so **nothing from the Refinery sits above y 0.02 within z 11.0–24.0** (flatbed lanes z 13 / 22,
  crane median z 15.3–18.7). Checked by clipping every triangle of the GLB to z 11–24: **0 violations**. `art/3d/props/flatbed_road/` and `crane_refinery` untouched.

### Truck timing (HT-04: 8.33 m/s straights, 4 m/s turns, accel 3 / brake 4 m/s², reverse ≤ 3 m/s, eased)
Every `Truck_*` marker carries `s_m` (distance along the route) and `next_leg` (JSON: `to`, `type`, `length_m`, `v_max`, `dir`, `t_s`); the root carries `truck_times`.

| Leg | Type | Length | Time |
|---|---|---|---|
| Path_01 → 02 | straight | 32.0 m | 3.84 s |
| Path_02 → 03 | straight (brake into the turn) | 10.5 m | 1.54 s |
| Path_03 → 04 → 05 → 06 | arc r 4.5 | 3 × 3.534 m | 3 × 0.88 s |
| Path_06 → 07 | arc r 4.5, to a stop | 3.534 m | 1.38 s |
| Path_07 → Truck_Dump | reverse | 3.5 m | 2.04 s |
| Truck_Dump | tip (`truck_dump`, + `dump_dust` at the tip) | | 3.00 s |
| Truck_Dump → Truck_Exit | straight | 46.0 m | 6.91 s |

Inbound (01 → 07) 9.42 s. **Arrive (U-turn start, Path_03) to leave (Truck_Dump) = 4.03 + 2.04 + 3.00 = 9.08 s**, about 1 s over the ≈ 8 s target: the reverse cannot be shortened below ~3.35 m (bin rim), and the turn radius stays ≥ 4.5 m.

### Fit (Coder's safe area, 10/23 20:58: everything, every tier visible, inside y 165–534 at 393×852 and y 144–383 at 375×667, 0 px side margin)
Solved by projecting every vertex of the packed GLB (station = everything except the haul road / PL-1 posts outside x −16…40) plus HT-04 envelopes
(9.2 × 3.2 m; 6 m tall with the bed up at `Truck_Dump`, 3.6 m at every U-turn marker): smallest frame_w, then a pan along the camera's up axis.
Measured on the packed `refinery_game.glb` (`/workspace/aa_ps/check.mjs`):

| | 393×852 (band y 165–534) | 375×667 (band y 144–383) | 1179×2556 |
|---|---|---|---|
| Station + truck envelopes (fit) | x 8…393, **y 227…470** | x 5…370, **y 151…376** | ×3 of 393 |
| All named nodes + tiers | x 73…340, y 230…429 | x 74…324, y 154…336 | x 219…1021, y 689…1287 |
| Whole GLB incl. road | x −270…393, y 227…470 | x −262…368, y 151…376 | y 680…1411 |
| Tier_03 (dewar rack 2) | 79…105, y 331…350 | 81…104, y 248…264 | y 994…1049 |
| Tier_05 (EL-2) | 161…187, y 361…387 | 155…178, y 274…297 | y 1084…1161 |
| Tier_08 (KN-2) | 181…263, y 315…364 | 173…248, y 232…277 | y 946…1093 |
| Tier_12 (DC-2, the station top) | 89…116, y 230…362 | 89…114, y 154…275 | y 689…1085 |
| Tier_20 (LOX-2/3) | 73…131, y 324…391 | 74…127, y 239…301 | y 971…1173 |
| Dump_Dust at peak scale 1.3 (21:21 rebuild) | 302…347, y 381…433 | 287…330, y 291…340 | |

The road runs off the left edge to x −46 (by design); nothing else leaves the frame. The station is smaller on screen than before (frame_w 30.8 → 34.4), because the 375×667 band is the binding one.

## Files
- `_src/build_refinery.py`: the procedural Blender 4.2 build. It imports `art/3d/mine_concepts/_src/mc_common.py` (the concept B helpers and stage).
  `blender -b -P _src/build_refinery.py -- --out . [--quick 1] [--only glb,blend,hero,phone,turn,diagram] [--ps 64] [--ct x,y,z --fw W] [--ht04 PATH [--ht04frame N]] [--truck none]`
  - `--ht04 art/3d/props/ht04/ht04_game.glb` hides the old master truck and places the shared HT-04 with `_src/place_ht04.py`: per its README, root `Truck`
    at the ground point under the truck centre = `Truck_Dump` (0, 0, 0), yaw 180° (cab −X, rear into RB-2), `truck_dump` clip baked at frame 22 (bed ~33° up, load sliding), `fill` 1.0.
    Imported materials get an `HT04_` prefix so the game exporter's own `SHM_*` names stay free.
  - `--only glb` writes `refinery_master_raw.glb` (scratch). Pack it with `gltfpack -i refinery_master_raw.glb -o refinery_master.glb -cc -kn -km -vpf`, then strip `KHR_materials_clearcoat` from the JSON chunk.
  - `--only hero --hs 16 --notile 1 --hc -26,-16,20,-3,14,2` and `--only turn --ts 16 --notile 1 --tt -3,14,3 --td 44` (now also the script defaults).
  - `--only phone` renders from the station camera (`--ct` Blender coords, default −6.90, −5.45, 2.08; `--fw` 34.4), prints `FIT` / `FIT_TIER`, and writes
    `refinery_phone_<w>x<h>_callouts.json` (projected anchor per module).
- `_src/build_game_glb_tiered.py`: the game exporter (`--target 27000`). It prints `FIT393`, `TIERDIST` and `CAM_TARGET`.
  `blender -b refinery_master.blend -P _src/build_game_glb_tiered.py -- --out raw.glb --baseratio 0.3548` (`--baseratio` pins the Base decimation so untouched parts decimate exactly as before; `--dustratio` 0.55), then `gltfpack -i raw.glb -o refinery_game.glb -cc -kn -ke`.
- `_src/make_callouts.py`: `python3 _src/make_callouts.py refinery_phone_1179x2556.png refinery_phone_1179x2556_callouts.json refinery_phone_callouts_1179x2556.png`.
- `refinery_phone_393x852.png`, `refinery_phone_1179x2556.png` (10/23 21:10): station camera, master scene + shared HT-04 tipping at `Truck_Dump` (Cycles CPU, 16 samples, OIDN, no tiling).
- `refinery_station_game_393x852.png`, `refinery_station_game_1179x2556.png`: the **game GLB** + shared HT-04 from the station camera (`_src/render_game_proofs.py`).
- `refinery_intake_truck_closeup.png`: the dump bay close-up, HT-04 tipping with `Dump_Dust` mid-clip (10/23 21:22, no path balls; `render_game_proofs.py --only closeup` draws none, add `--balls 1` to show them); `refinery_intake_truck_top.png`: top-down of the same.
- **`refinery_truck_path_diagram.png`**: top-down route with legs, times, `s_m` and yaw arrows (`python3 _src/path_diagram.py refinery_game.glb refinery_intake_truck_top.png refinery_truck_path_diagram.png`).
- **`refinery_phone_callouts_1179x2556.png`**: labelled callout proof (cyan HELIUM-3 line incl. Tier_03/08/12, orange LOX + LCH4 line incl. Tier_05/20 and PL-1, white intake + HT-04).
- **`refinery_hero_3840x2160.png`** (10/23, concept B high-detail, Cycles CPU 16 samples, OIDN, no tiling): current layout with the shared HT-04 tipping. **`turntable/turn_000..315.png`** (8 × 45°, 1000 px) and **`refinery_turntable_sheet.png`** (`python3 _src/make_sheet.py turntable refinery_turntable_sheet.png TITLE SUB refinery_hero_3840x2160.png`), made the same way as the Dock's.
- **Stale (older layout, not re-rendered):** `refinery_process_diagram.png`.

## Game GLB nodes
All under the root `Refinery` (extras: origin, road and layout notes, `draws_all_tiers` 13 (was 15), `truck_times`). gltfpack puts each mesh on an unnamed child of its named node.

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint` / `Base_GlowCyan` / `Base_GlowRed` | static base merged by material (road in Paint) | 17,160 / 982 / 328 | SHM_Paint / SHM_GlowCyan / SH_GlowRed (kiln + reactor glow, red lamps) | origin |
| `Intake_Grate` | RB-2 grizzly bars | 218 | SHM_Paint | (5.00, 1.54, 0) |
| `Kiln_Drum` | KN-1 rotary drum (axis along X) | 610 | SHM_Paint | (−3.69, 2.21, −26.92) |
| `Conveyor_He3` | ore lumps on the He-3 gallery belt | 732 | SHM_Paint | (3.25, 7.55, −8.35) |
| `Conveyor_Fuel` | ore lumps on the fuel belt | 396 | SHM_Paint | (5.35, 0.45, −6.90) |
| `Dump_Dust` | dust billow over the hopper (8 smooth puffs, vertex-alpha falloff; clip `dump_dust`, rest scale 0.001) | 1,378 | SH_Dust | (4.10, 1.45, 0) |
| `Sizer_Flywheel` | SZ-1 sizer flywheel (axis along glTF Z; clip `sizer_spin`) | 236 | SHM_Paint | (9.02, 1.30, 1.01) |
| `Beacon_Lights` | red beacons | 234 | SH_GlowRed | (−11.14, 0, −21.30) |
| `Tier_03` | HELIUM-3: second dewar rack | 1,964 | SHM_GlowCyan | (−18.82, 0, −28.97) |
| `Tier_05` | fuel: second electrolyzer EL-2 | 586 | SHM_Paint | (−9.23, 0, −14.85) |
| `Tier_08` | HELIUM-3: second rotary kiln KN-2 | 912 | SHM_Paint | (−4.02, 0, −24.40) |
| `Tier_12` | HELIUM-3: bigger cryo column DC-2 | 824 | SHM_Paint | (−17.21, 0, −24.80) |
| `Tier_20` | fuel: LOX-2 and LOX-3 tanks | 2,740 | SHM_Paint | (−16.57, 0, −14.27) |

Tier nodes carry `extras {"tier": N, "hidden_by_default": true}`. glTF has no hidden flag, so the loader must set `visible = false` on load.
Draws with every tier showing: 3 base + 7 moving + 5 tiers = **15**.

Clips (all loop): `kiln_spin` 4.0 s (one turn), `conveyor_he3_run` / `conveyor_fuel_run` 1.0 s, `intake_shake` 0.5 s (play while tipping), `sizer_spin` 2.0 s (one turn, linear, seamless), `dump_dust` 1.5 s (play once at the tip; not a loop), `Beacon_Lights_Blink` 1.2 s step.

## Markers (empty nodes, glTF)
`yaw_deg` is about +Y: 0 = heading +X, 90 = −Z, 180 = −X, −90 = +Z.

| Marker | Translation | yaw | Mode / notes |
|---|---|---|---|
| `Truck_Path_01` = `Road_Entry` | (−46, 0, 9) | 0 | s 0; inbound lane at the left edge, from the Mine; → 02 straight 32 m, 3.84 s |
| `Truck_Path_02` | (−14, 0, 9) | 0 | s 32.0; → 03 straight 10.5 m, 1.54 s |
| `Truck_Path_03` | (−3.5, 0, 9) | 0 | s 42.5; U-turn start (r 4.5); → 04 arc 3.534 m, 0.88 s |
| `Truck_Path_04` | (−0.318, 0, 7.682) | 45 | s 46.034; → 05 arc, 0.88 s |
| `Truck_Path_05` | (1.0, 0, 4.5) | 90 | s 49.569; apex; → 06 arc, 0.88 s |
| `Truck_Path_06` | (−0.318, 0, 1.318) | 135 | s 53.103; → 07 arc to a stop, 1.38 s |
| `Truck_Path_07` | (−3.5, 0, 0) | 180 | s 56.637; stop, then **reverse 3.5 m** along +X, 2.04 s |
| **`Truck_Dump`** | **(0, 0, 0)** | 180 | s 60.137; tip 3 s (cab −X, rear into RB-2), `intake_shake` + `dump_dust`; → Exit straight 46 m, 6.91 s |
| `Truck_Exit` = `Road_Exit` | (−46, 0, 0) | 180 | s 106.137; handoff to the Mine (outbound lane off the left edge) |
| `Cam_Target` | (−6.90, 2.08, 5.45) | | `frame_w` 34.4 |
| `He3_Output` | (−15.76, 0.10, −29.65) | | HELIUM-3 dewar rack (ship cargo pickup) |
| `Fuel_Output` | (−16.57, 0.10, −19.15) | | LOX-1 / LCH4-1 |
| `Pipe_TankFarm` | (−13.85, 0, −18.62) | 0 | PL-1 pipeline head: LOX + LCH4 go below grade here and run **buried along +X** (z −18.62) toward the Dock / pad |
| `Pipeline_Exit` | (15.90, 0, −18.62) | 0 | buried PL-1 leaves the Refinery footprint, continuing +X |
| `Crew_Path_01..07` | (−7.3, 0.1, −20.95), (−8.0, 0.1, −20.95), (−10.7, 0.1, −19.55), (−12.5, 5.45, −21.6), (−17.1, 0.1, −19.75), (1.0, 0.1, −20.35), (2.0, 0.1, −5.0) | | airlock → intake |

## Validation
- Packed game GLB (10/24 00:06, marker posts): 15 draws, 29,356 tris, extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression], 0 images / textures, material keys only
  name / pbrMetallicRoughness / emissiveFactor, 7 clips, no truck nodes besides the `Truck_*` markers. `strings refinery_game.glb | grep -i lh2` → empty.
- Master build: `RELAYOUT moved 1112 neg 0`, `BELOW_GROUND` only `tf_lox` / `tf_lch4` at −0.34 (the intended buried PL-1 risers). Phone `FIT_TIER` all OK.
- Every proof was read at full size (and the truck / bin crop at 1179 checked: the tipping HT-04 is fully visible, nothing of the bin in front of it).

## Caveats
- The view is the back side of the old approved Mine-station view (needed so the bin + truck are in front and the road leaves left).
- The game GLB is a decimated proxy; stencils, handrails and grating are culled. Process rows are at 0.85 scale.
- Arrive-to-leave is 9.08 s, not ≈ 8 s (see Truck timing).

## DB-2 / intake upgrade (10/23 PM)
Only the dump bay and the intake (hopper, grizzly, feeder, sizer, CV-0 tail) changed; tanks, tower, kiln, downstream conveyors, markers, `Cam_Target` (−6.90, 2.08, 5.45) / `frame_w` 34.4 and Tier nodes are unchanged.
- Haul road: no vertex above y 0.02 in glTF z 11–24 (none at all there).
- Override fit (Cam_Target 313.1, 2.08, 13.55, frame_w 37.5, `_ros_ip.mjs check`): 393×852 envelope min spare **22.9 px** (top 64.2 / bottom 67.3 / left 47.6 / right 22.9); 375×667 min spare **10.18 px** (top 10.2 / bottom 10.3 / left 43.1 / right 29.1) — same as before the upgrade.
- Proofs (all in `proofs/`, game GLB + shared HT-04, Cycles 24 samples): bay close-up `refinery_intake_before_3840x2160.png` (HEAD c53013e GLB) / `refinery_intake_after_3840x2160.png` (empty bay); override camera `refinery_station_override_before_{393x852,375x667}.png` / `refinery_station_override_{393x852,375x667}.png`, the same at 2x (`*_before2x_*`, `*_after2x_*`); side-by-side with the safe band drawn and a bay crop: `refinery_dumpbay_before_after_393x852.png` / `_375x667.png`; tip moment with dust mid-clip `refinery_truck_dump_moment.png`.
- Hero `refinery_hero_3840x2160.png`, `turntable/` and `refinery_turntable_sheet.png` re-rendered 10/23 23:00-23:26 from the upgraded master (no marker balls).
- In game the green lens rides on `SHM_GlowCyan` (reads cyan-white); amber and red lenses are unlit paint. Small rails, nozzles, posts and stencil text are culled from the game GLB (present in the master).

## PL-1 marker posts (10/24 00:06)
The 7 buried-pipeline marker posts `plm0..plm6` are now **white with one cyan glow band near the top** (were RF_Red). Done as a game-GLB patch
(`_src/patch_marker_posts.py`: 168 post vertices recoloured to the station white in Base_Paint, a 4-sided band y 0.66–0.73 per post added to Base_GlowCyan, +56 tris,
**0 extra draws**, same materials, clips, nodes and extras), so the rest of the decimated station is untouched. `build_refinery.py` has the same change at the source
(`plm{k}_pole` WHITE_S, new `plm{k}_band` CYANL), so a full rebuild matches. `refinery_master.glb` / `.blend` and the hero/turntable renders still show red posts (not rebuilt).
Proofs: `proofs/refinery_markerposts_before_393x852.png` / `_after_393x852.png` (station camera) and `proofs/refinery_markerposts_before_closeup_1600x1000.png` / `_after_closeup_1600x1000.png`.


## Road paint + draw merge (10/24 00:40, `../_shared/road/_src/paint_station_roads.py refinery IN OUT --skin-merge Conveyor_Fuel,Conveyor_He3`)
- **Road:** 1,463 of 1,599 existing road vertices recoloured (COLOR_0 only, haul_road_seg palette): ruts with tread alternation where rows are ≤ 0.6 m apart (near the bay, median row spacing 0.48 m), mid-tone ruts on the coarse rows, worn shoulders, crown polish, dusty edges. No new geometry.
- **-2 draws:** the conveyor belt meshes (`Conveyor_Fuel`, `Conveyor_He3`, both SHM_Paint) are merged into `Base_Paint` as **one SkinnedMesh** (joints `Base_Paint`, `Conveyor_Fuel`, `Conveyor_He3`; IBM = inv(joint world) x Base_Paint world). The clips still drive the same named nodes, so `conveyor_fuel_run` / `conveyor_he3_run` move exactly as before (checked to ~2 mm under three r186). Note for Coder: `Conveyor_Fuel` / `Conveyor_He3` now have no mesh children (they are bones), and `Base_Paint`'s mesh is a SkinnedMesh (the loader already sets `frustumCulled = false` on skinned meshes). Look, camera and `Cam_Target` unchanged. Non-skinned merges were not clean (different clips, the Beacon blink, GlowCyan vs GlowRed, code-toggled tiers). More headroom if needed: `Intake_Grate`, `Kiln_Drum`, `Sizer_Flywheel` can join the same skin (-1 draw each).
- Proofs: `proofs/refinery_road_{before,after}_393x852.png` (Cycles 16 samples, HT-04 on `Truck_Path_02`), `proofs/refinery_road_{before,after}_close_1600x900.png` (Workbench).
