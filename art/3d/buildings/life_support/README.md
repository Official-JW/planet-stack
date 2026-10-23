# Life Support (LS-01) concept master

A high-detail 3D concept master for the Planet Stack **Life Support** building. It is styled to match
**Mine concept B (sleek high-tech)**: glossy white and graphite panels, satin metal, cyan light strips, and clean rounded
shapes, with the same weathered finish (lunar dust on lower and upward-facing surfaces, grime, edge wear, panel seams).
Everything is original. There are no real logos, only invented stencils (LS-01, PM-1/2, SWG-1, R-1, EL-1, O2-1/2, M-1, C-1, H2O-1..3, RAD-0..2, SA-1/2, FPU-1).

| | |
|---|---|
| Triangles (master, `Mine` collection) | **264,277** (1,125 objects) |
| Master GLB | `life_support_master.glb`, 1.49 MB, meshopt + quantization (`gltfpack -cc -kn -km`), **no Draco**, one node per part. Review asset only: it keeps the master's clearcoat/transmission/ior material extensions. |
| **Game GLB** | `life_support_game.glb`, **197,880 B (0.19 MB)**, **23,795 triangles and 11 draw calls with every tier visible** (base 17,999 tris / 4 draws). Materials `SHM_Paint`, `SHM_Metal`, `SHM_GlowCyan`, `SHM_GlowWhite` from `../_shared/shared_materials.json`. Extensions: `EXT_meshopt_compression` and `KHR_mesh_quantization` only. Plain metallic/roughness, no transmission/clearcoat/ior, no textures. Colour comes from `COLOR_0` vertex colours. Single-sided. No astronaut. Tier nodes, moving parts and markers: see *Game GLB nodes* below. md5 `e8427ec46e93fa04b4d1a7468644d992` |
| Units / axes / origin | 1 m, Y up. The front (airlock) faces +Z. The **origin is the station focus**: on the ground, on the PM-1 / airlock axis. The game camera aims at `Cam_Target` (see markers). The bbox is not centred because the plants sit behind the modules. |
| Footprint | X −10.7…10.5 m (21 m wide), depth from 11.9 m in front of the origin to 42.3 m behind it (solar masts). Mast tops are at 15.5 m. |
| Scale | astronaut = 1.8 m (review renders only; it is in the Stage collection and is never exported) |

## Layout (fits the in-game station framing)
The in-game station camera (`qa3d/main.js`: fov 38° vertical, 18° down, look-at 2.5 m above the origin, distance 47.2 m for a 393×852 portrait) sees about 15 m of width at the origin. It sees about 12 m at the porch and about 20 m at the back. The station is laid out for that framing:
- **Focus (centre):** PM-1 and PM-2 (shortened to 7.2 m and 6.4 m) and the airlock and dust porch. The canopy is narrowed to 6.6 m. SWG-1 sits front-left and the compact CO2 skid front-right, both inside the frame.
- **O2 and H2O lines frame the modules.** White-jacketed lines with wide colour bands (green O2, blue H2O) run forward down a central pipe spine. They split behind PM-2 and ride T-post racks at 3 m along both flanks into PM-1's end caps (tags "O2" and "H2O").
- **Pushed back:** the O2 plant (left) and water plant (right) start about 9 m behind PM-2, and their tall parts (reactor tower, tanks, RAD-1 and RAD-2) show above the hulls. The solar masts are 40 m back, and FPU-1 and its berm are far off-frame.
- **Simplified for phone size:** the hull labels are re-spaced between seam rings, the vent stacks are shortened, and the guy footprints are tightened. RAD-0 is lowered. The power trays are graphite-only, so they don't read as a red line.
- The ground and hills use the shared `M_ground` (`M_Regolith`) from `mine_concepts/_src/mc_common.py` (imported read-only; the build asserts it). The boulders and dust are re-toned to grey. There is no tan.

## Systems (left to right in the hero)
- **Power hookup:** the reactor feeder (cable tray on stanchions) comes from fission unit **FPU-1**. FPU-1 sits behind its own ring berm with
  four white radiator wings, a beacon mast and a "KEEP OUT 1 km" sign, and the tray runs off toward the horizon. The feeder lands in switchgear **SWG-1**
  ("REACTOR FEED 1.2 kV", HV mark). Distribution conduits run up the headwall and into trays to the O2 and H2O plants.
- **O2 extraction:** ilmenite regolith feed bin, then an inclined screw conveyor, then a feed hopper with a lock valve on a braced tower,
  then MLI-insulated **H2-reduction reactor R-1** (hot port, heater leads), with a slag chute and skip. Water vapour goes to the **electrolysis unit EL-1** (with H2
  return) and on to spherical tanks **O2-1 / O2-2**. Large white radiator **RAD-1** with coolant loops sits behind the plant.
- **Pressurized modules (above ground, nothing buried):** two parallel horizontal modules, **PM-1 "PROCESS / ECLSS"** in front and **PM-2 "STORES / CONTROL"**
  behind, joined by a pressurized tunnel. They have no glass and no domes. Each hull wears a thick jacket of white shield segments (water-wall/polyethylene for radiation and
  micrometeoroids) with graphite seam rings, cyan light rings and end-cap service hatches. They sit on graphite cradles with footpads and have flank handrails. The hull crown carries
  cabin radiator **RAD-0**, vents, a beacon mast and a comms dish. The large "LS-01 / LIFE SUPPORT" stencil is on PM-1's shoulder.
- **Entry / dust control:** airlock **A1** (hatch, handwheel, porthole, status lamps) plus suitports **SP-1/SP-2**. A porch
  canopy (white shield-tile roof) shades a raised grated dust mat over a catch pan, with a ramp and handrails, an air-shower arch with nozzle bars and a blower, a rotary boot/glove
  brush station, a tool rack, and a work light.
- **CO2 scrubbing:** a skid with scrubber beds **A–D** (actuators, status lamps), header and blower, and insulated cabin-air ducts from the
  headwall. Two guyed **vent stacks** with red lamps. The CO2 transfer line runs out "TO TANK FARM".
- **Water recovery:** ice-regolith feed hopper, then melt/sublimation vessel **M-1**, then finned **condenser C-1**, then filtration skid
  **F-1..4**, then recycling and potable tanks **H2O-1..3** (sight glasses, catwalk, ladder, greywater return). Large white radiator **RAD-2** sits behind it.
- **Solar backup:** arrays **SA-1/SA-2** on 15 m masts (sun-tracking panels, combiners, cable drops).

## Files
- `_src/build_life_support.py`: the procedural Blender 4.2 build script. It imports `art/3d/mine_concepts/_src/mc_common.py`.
  `blender -b -P build_life_support.py -- --out .. [--quick 1] [--only glb,blend,turn,hero,phone] [--hs 48] [--ts 40] [--ps 48] [--res WxH] [--pres WxH]`
  `--only glb` writes `life_support_master_raw.glb`. Pack it with `gltfpack -i life_support_master_raw.glb -o life_support_master.glb -cc -kn -km`.
- `_src/build_game_glb_tiered.py`: **current game exporter**. Same culling and palette remap as below, but splits out tier, moving-part and marker nodes; base decimated to fit `--target 24000` total, tiers at `--tierratio 0.45`.
  `blender -b life_support_master.blend -P _src/build_game_glb_tiered.py -- --out raw.glb`, then `gltfpack -i raw.glb -o life_support_game.glb -cc -kn -ke`
- `_src/build_game_glb.py`: previous single-node game exporter (kept for reference). It culls text, stencils, lamps, wires and greebles under 0.3 m, remaps the materials to the 4 merged `SHM_*` materials (swatch colour goes to `COLOR_0`), welds, dissolves planar faces, joins and collapse-decimates to 17k or fewer triangles, then splits by material.
  `blender -b life_support_master.blend -P _src/build_game_glb.py -- --out raw.glb`, then `gltfpack -i raw.glb -o life_support_game.glb -cc`
- `_src/make_sheet.py`: builds the contact sheet (`python3 make_sheet.py turntable life_support_turntable_sheet.png TITLE SUB hero.png`)
- `life_support_master.blend`: full scene (procedural shading, stage, lights, cameras)
- `life_support_phone_1179x2556.png` and `life_support_phone_393x852.png`: in-game camera view (aimed at `Cam_Target`, frame_w 34, 3× master and its Lanczos downscale), default tier state
- `life_support_game_preview_393x852.png`: the game GLB itself (all tiers visible) from the same camera (flat preview render, plain grey ground)
- `life_support_hero_3840x2160.png`: hero render (Cycles, OIDN, AgX Punchy)
- `turntable/turn_000..315.png` and `life_support_turntable_sheet.png`: 8 angles at 45° steps, plus the contact sheet

## Game GLB nodes
All under the root `LifeSupport`. Glows on tier parts are folded into `SHM_Paint` (cyan kept as vertex colour) so each tier is exactly one draw.

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `LS_Paint`, `LS_Metal`, `LS_GlowCyan`, `LS_GlowWhite` | static base, merged by material | 11,905 / 5,158 / 874 / 32 | SHM_* | origin |
| `Tier_03` | third radiator wing RAD-2 (4 panels, posts, manifolds, coolant loop) | 1,626 | SHM_Paint | (5.58, 0, −22.79) |
| `Tier_05` | second O2 storage sphere O2-2 with legs, pads, band, girder | 1,436 | SHM_Paint | (−3.30, 0, −28.60) |
| `Tier_08` | CO2 scrubber beds C and D (+ their ribs, valves, actuators) | 598 | SHM_Paint | (5.29, 0, 6.25) |
| `Tier_12` | third water tank H2O-3 | 952 | SHM_Paint | (7.40, 0, −23.40) |
| `Tier_20` | both solar masts SA-1/SA-2 with arrays, gimbals, combiners, cables | 690 | SHM_Paint | (0, 0, −39.31) |
| `Fan_Scrubber` | CO2 blower fan, pivot at the hub, spins about local +X | 284 | SHM_Paint | (3.13, 0.70, 4.75) |
| `Beacon_Lights` | roof beacon + two vent-stack lamps | 240 | SHM_GlowWhite | (−3.00, 8.17, 1.40) |

Tier nodes carry `extras` `{"tier": N, "hidden_by_default": true}` (three.js: `userData`). glTF has no hidden flag, so the loader must set `visible = false` on load.
Clips: `Fan_Scrubber_Spin` (1.0 s loop, 1 rev/s, quaternion), `Beacon_Lights_Blink` (1.5 s loop: 0.3 s on, then scale 0.001 for 1.2 s).
Markers (empty nodes): `Airlock_Door` (0, 1.70, 7.86, centre of the hatch's outer face, facing +Z), `Crew_Path_01..05` from the hatch out over the dust mat and ramp to open ground (z 8.4, 9.6, 11.4, 13.2, 15.5 on x = 0), `Pipe_TankFarm` (6.60, 0.60, 11.80, open flange at the end of the CO2 transfer line, facing +Z), `Cam_Target` (0, 2.50, -12.50; empty only, extras `{"frame_w": 34}`): the in-game camera aims here from -Z+up at 18 deg pitch, 38 deg vertical FOV, distance (W/2)/(tan 19 deg x 393/852) = 107.03 m. Every tier is within 34 m (3D) of it.

## Validation (game GLB)
Loaded in Node with three.js `GLTFLoader` plus `MeshoptDecoder` (three r17x from npm). Result: 11 meshes / 11 draw calls, 23,795 triangles, 30,318 vertices (all tiers visible), materials SHM_GlowCyan/GlowWhite/Metal/Paint, extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression], no images or textures.

## Caveats
- The game GLB is a collapse-decimated proxy. Small curved parts get faceted, and the dust-mat grating becomes a flat dark slab. It reads cleanly from the game camera; see the preview.
- Grime, dust, wear, radiator ribs and solar cells are procedural and live only in the .blend and the renders.
- The master GLB is for review, not the game. It still uses clearcoat, transmission and ior extensions.
- The stage terrain comes from `mc_common.build_stage` (with the in-progress hills edits), re-skinned grey here.
- For framing, FPU-1 sits about 65 m away. A real installation would put it about 1 km away behind terrain or a berm (the sign says so).
- Cyan is used for light strips to match the chosen Mine B look. STYLE_GUIDE_3D reserves cyan for He-3, so the guide may need updating.
