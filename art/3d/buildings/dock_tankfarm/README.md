# Cargo Space Dock + Tank Farm concept master

A high-detail 3D concept master for the Planet Stack **Cargo Space Dock** and its **Tank Farm**. It is styled to match
**Mine concept B (sleek high-tech)**: white shielded hulls, graphite structure, satin metal and cyan light strips, with the same weathered finish
(lunar dust on lower and upward-facing surfaces, grime, edge wear, panel seams). Everything sits above ground: no caves, no buried modules,
no regolith cover. There are no glass domes and no real logos, only invented stencils (CSD-1, GC-1, JC-2, SWG-2, RAD-1/2, LOX-1/2, LH2-1/2, HE3-1, PS-1, PSCU container numbers).

| | |
|---|---|
| Triangles (master, `Mine` collection) | **516,990** (2,200 objects + the `Cam_Target` empty) |
| Master GLB | `dock_tankfarm_master.glb`, 3,293,248 B, meshopt + quantization (`gltfpack -cc -kn -km -ke -vpf`), **no Draco**, one node per part. Review asset only: it keeps the master's clearcoat and emissive-strength material extensions. md5 `26b8990600624d4dd6569c072894b08a` |
| **Game GLB** | `dock_tankfarm_game.glb`, **181,288 B (0.17 MB)**, **27,679 triangles and 12 draw calls with every tier visible** (base 18,077 tris / 4 draws). Materials `SHM_Paint`, `SHM_Metal`, `SHM_GlowCyan`, `SHM_GlowWhite` from `../_shared/shared_materials.json`. Extensions: `EXT_meshopt_compression` and `KHR_mesh_quantization` only. Plain metallic/roughness, no transmission/clearcoat/ior, no images or textures. Colour comes from `COLOR_0` vertex colours. No astronauts. md5 `882c8e273e4b9125091f87e6fe5cf62d` |
| Units / axes / origin | 1 m, Y up. The dock front (rolling door, container yard) faces +Z. The **origin is the station focus**: on the yard pad, on the hall/door axis. The tank farm extends to +X. |
| Footprint | X −24.8…48.0 m (power mast to the launch-pad pipe end), Z −36.3…16.9 m (solar masts behind to the road entry in front). Hall crown 13.2 m, sign top ~12.6 m, mast tops ~16.6 m. |
| Scale | astronaut = 1.8 m (three in the review renders only; Stage collection, never exported) |

## Layout (fits the in-game station framing)
Phone shots use the Game Coder camera spec: perspective, **38° vertical FOV, tilted down 18°, aimed at the `Cam_Target` empty**. `Cam_Target` sits at Blender (0, −4.0, 2.5) = glTF (0, 2.5, 4.0), 4 m in front of the origin at the game's lookY of 2.5 m. It carries `extras {"frame_w": 15}`: **W = 15 m** of station spans the screen width at Cam_Target. The camera distance is d = W / (2·tan 19°·aspect) = **47.22 m** for 393×852 and for the 1179×2556 master, which has the same aspect. With that framing on 393×852, the focus (roof crown and sign down to the yard pad's front curb) sits between y ≈ 100 (HUD) and y ≈ 645, and the ground in front ends above the open sheet at y = 674. `--ct x,y,z` and `--fw W` change it.
- **Focus (centre):** the cargo hall's rolling door (9.2 × 7.4 m opening) with the blue-neon **CARGO SPACE DOCK** sign on the arch cap above it, and the container yard in front.
- **Gantry crane GC-1** spans the yard (rails at x = ±7.2) and rests just in front of the stacks, low enough to leave the sign clear.
- **Container stacks** frame the lane left and right; the He-3 canister and the armoured platinum crate sit at the lane's front edge so they read at phone size.
- **Tank farm** to the right (+X) behind a low L-shaped berm, so it shows in the hero but stays out of the phone frame centre.

## Systems
- **Cargo hall CSD-1:** a 22 × 18 m white shielded arch hall (shield-tile panels, graphite ribs, cyan light strips). A segmented **rolling door** (25 slats, guide rails, cyan edge strips) opens onto a lit interior with racks and three containers. Roof vents, comms dish, roof beacons and the neon sign sit on top.
- **Gantry crane GC-1:** two wheeled legs on surface rails (sleepers, end stops, bumpers), box girder with walkway, low-profile trolley, wire ropes and a spreader carrying a hoisted 20 ft container.
- **Container yard:** 6.06 × 2.44 × 2.59 m containers (white / graphite / pale, corrugated, corner castings, invented PSCU numbers), stacked 1–3 high. Cargo props: a **glowing blue He-3 canister** in a cradle frame, an **armoured platinum crate** (graphite armour, platinum panels, seals), and small crates.
- **Airlock + dust shower:** crew airlock on the hall's right flank (hatch, handwheel, porthole, status lamps), raised grated dust mat over a catch pan, air-shower arch with nozzle bars and blower, rotary boot brush, handrail.
- **Power:** switchgear SWG-2 front-left; a feeder line on graphite masts with a red beacon lands at a wall bushing; far masts and solar masts behind the hall.
- **Heat rejection:** white radiator wing RAD-1 on masts at the hall's left with coolant loops (RAD-2 is Tier_20).
- **Jib crane JC-2 (Tier_08):** slewing jib crane at the hall's front-left corner.
- **Tank farm:** white MLI-jacketed cryo tanks on legs and footpads, each with bands, labels (LOX-1 "LIQUID OXYGEN 90 K", LH2-1 "LIQUID HYDROGEN 20 K", ...), relief valves and vent stacks. A catwalk links the tank tops with a stair tower. The **He-3 cryo sphere HE3-1** has cyan bands (Tier_12). Insulated LOX / LH2 / He-3 headers with handwheel valves run on pipe racks past the **pump skid PS-1** and turn toward the launch pad, ending in a flange with a "TO LAUNCH PAD" plate.
- **Berm:** a low L-shaped regolith berm separating the tank farm from the dock, with a pipe culvert.
- The ground uses the shared cool-grey `M_ground` (with the hill-stripe fix). No tan.

## Files
- `_src/build_dock_tankfarm.py`: the procedural Blender 4.2 build script. It imports `art/3d/mine_concepts/_src/mc_common.py` and re-uses the Life Support helpers.
  `blender -b -P build_dock_tankfarm.py -- --out .. [--quick 1] [--only glb,blend,hero,phone,turn] [--hs 40] [--ts 32] [--ps 48] [--res WxH] [--pres WxH] [--door 0.5] [--hc x,y,z,tx,ty,tz] [--lens 28] [--td 95] [--ct 0,-4,2.5] [--fw 15]`
  `--only glb` writes `dock_tankfarm_master_raw.glb`. Pack it with `gltfpack -i dock_tankfarm_master_raw.glb -o dock_tankfarm_master.glb -cc -kn -km -ke -vpf`.
- `_src/build_game_glb_tiered.py`: game exporter. It culls text, stencils, bolts, ribs, rails, cables and greebles under 0.3 m, disables bevel modifiers, remaps the materials to the 4 merged `SHM_*` materials (swatch colour goes to `COLOR_0`), welds, dissolves planar faces and collapse-decimates (base fitted to `--target 28000` total, tiers and moving parts at `--tierratio 0.7`). Splits out tier, moving-part and marker nodes.
  `blender -b dock_tankfarm_master.blend -P _src/build_game_glb_tiered.py -- --out raw.glb`, then `gltfpack -i raw.glb -o dock_tankfarm_game.glb -cc -kn -ke`
- `_src/make_sheet.py`: builds the contact sheet (`python3 make_sheet.py turntable dock_tankfarm_turntable_sheet.png TITLE SUB hero.png`)
- `dock_tankfarm_master.blend`: full scene (procedural shading, stage, lights, cameras, review astronauts). The door is rendered 50 % open (`--door`).
- `dock_tankfarm_hero_3840x2160.png`: hero render (Cycles, OIDN, AgX), dock and tank farm on grey ground
- `dock_tankfarm_phone_1179x2556.png` and `dock_tankfarm_phone_393x852.png`: in-game station camera view aimed at `Cam_Target`, W = 15 m (3× master, and its Lanczos downscale)
- `dock_tankfarm_game_preview_393x852.png` and `dock_tankfarm_game_preview_hero.png`: the game GLB itself (all tiers visible, door closed) from the station camera (Cam_Target, W = 15 m) and the hero angle (flat preview renders)
- `turntable/turn_000..315.png` and `dock_tankfarm_turntable_sheet.png`: 8 angles at 45° steps, plus the contact sheet

## Game GLB nodes
All under the root `DockTankFarm`. Glows on tier and moving parts are folded into `SHM_Paint` (cyan kept as vertex colour) so each is exactly one draw (Beacon_Lights uses `SHM_GlowWhite`).

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint`, `Base_Metal`, `Base_GlowCyan`, `Base_GlowWhite` | static base, merged by material | 12,489 / 2,816 / 2,668 / 104 | SHM_* | origin |
| `Tier_03` | three extra containers on the yard stacks | 216 | SHM_Paint | (0, 0, 6.31) |
| `Tier_05` | second LOX tank LOX-2 with catwalk posts and header tie-in | 1,798 | SHM_Paint | (27.99, 0, −6.52) |
| `Tier_08` | jib crane JC-2 | 468 | SHM_Paint | (−9.49, 0, −1.02) |
| `Tier_12` | He-3 cryo sphere HE3-1 with legs, bands and drop line | 3,480 | SHM_Paint | (31.50, 0, −11.57) |
| `Tier_20` | second LH2 tank LH2-2, radiator wing RAD-2, two extra container stacks | 2,034 | SHM_Paint | (4.28, 0, −4.51) |
| `Crane_Gantry` | gantry crane (legs, girder, trolley, spreader, hoisted container), pivot on the rail top at the crane's rest position | 1,030 | SHM_Paint | (0, 0.32, 9.00) |
| `Dock_Door` | rolling door, pivot at the top of the opening (door rolls up by scaling local Y) | 336 | SHM_Paint | (0, 7.40, −3.72) |
| `Beacon_Lights` | hall roof beacons + power-mast red lamp | 240 | SHM_GlowWhite | (−9.20, 13.45, −4.90) |

Tier nodes carry `extras` `{"tier": N, "hidden_by_default": true}` (three.js: `userData`). glTF has no hidden flag, so the loader must set `visible = false` on load.

Clips:
- `crane_gantry_move` (6.0 s loop): `Crane_Gantry` translation 4.5 m toward the hall (−Z) by 3.0 s and back, smooth.
- `dock_door_open` (2.5 s, play once / reverse to close): `Dock_Door` scale Y 1 → 0.06 about the top pivot.
- `Beacon_Lights_Blink` (1.5 s loop, step): 0.3 s on, then scale 0.001 for 1.2 s.

Markers (empty nodes, glTF coords):
- `Road_Entry` (0, 0.12, 17.20): where the road meets the yard pad.
- `Crate_Drop` (0, 0.12, 6.00): crane drop spot in the yard lane, in front of the door.
- `Container_Stack` (−4.00, 5.30, 3.00): top of the left front stack.
- `Pipe_LaunchPad` (47.00, 1.20, 8.10): open flange at the end of the launch-pad line.
- `Cam_Target` (0, 2.50, 4.00), `extras {"frame_w": 15}`: station-camera look-at (empty, no draws). Aim the camera at it from 18° down with 38° vertical FOV, at the distance where 15 m spans the screen width.
- `Crew_Path_01..08`: from the airlock hatch over the dust mat and out to the hall front: (9.25, 0.32, 0.28), (9.25, 0.32, 1.60), (9.25, 0.12, 3.70), (8.65, 0.12, 6.00), (5.60, 0.12, 14.30), (2.30, 0.12, 11.90), (0, 0.12, 6.00), (0, 0.12, −2.10).

## Validation (game GLB)
- three.js: `Cam_Target` loads at (0, 2.5, 4) with `userData.frame_w = 15`; all five tiers carry `{tier, hidden_by_default: true}`; clips Beacon_Lights_Blink 1.5 s, crane_gantry_move 6.0 s, dock_door_open 2.5 s.
- `gltf-transform inspect`: 12 meshes / 12 primitives, 4 materials, no textures, 3 animations, extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression] (no Draco).
- Loaded in Node with three.js `GLTFLoader` plus `MeshoptDecoder`: 12 draw calls, 27,679 triangles, 29,331 vertices (all tiers visible), materials SHM_GlowCyan/GlowWhite/Metal/Paint, bbox (−24.75, −0.30, −36.26)…(48.00, 16.59, 16.94).
- Materials contain only `pbrMetallicRoughness` and `emissiveFactor`, with no `KHR_materials_*` extensions.

## Caveats
- The game GLB is a collapse-decimated proxy. Text and stencils are culled except the sign. Sign letters and neon are merged into `Base_GlowCyan`, so the blue neon reads cyan in game. Handrails, stair rails, ropes, power lines and grating are dropped or simplified. Small curved parts get faceted.
- The game door is modelled closed (`Dock_Door` scale 1); the renders show it 50 % open.
- Grime, dust, wear and corrugation are procedural and live only in the .blend and the renders.
- The master GLB is for review, not the game. It still uses the `KHR_materials_clearcoat` and `KHR_materials_emissive_strength` extensions.
- Fuel is LOX + LH2 (no methane anywhere). LH2-1/LH2-2 are MLI-jacketed white tanks but the **same size as the LOX tanks** (r 2.4 m). Real LH2 storage would need about 3× the LOX volume per tonne of fuel, so bigger LH2 tanks are a possible follow-up (it would need re-renders).
- Cyan is used for light strips to match Mine B, and the He-3 canister/sphere glow blue-cyan. STYLE_GUIDE_3D reserves cyan for He-3, so the guide may need updating.
- For framing, the tank farm is about 20–35 m from the hall and the launch-pad line ends at x = 47 m; a real installation would keep cryo tanks much farther from the dock.
