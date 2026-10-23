# Cargo Space Dock + Tank Farm concept master

A high-detail 3D concept master for the Planet Stack **Cargo Space Dock** and its **Tank Farm**. It is styled to match
**Mine concept B (sleek high-tech)**: white shielded hulls, graphite structure, satin metal and cyan light strips, with the same weathered finish
(lunar dust on lower and upward-facing surfaces, grime, edge wear, panel seams). Everything sits above ground: no caves, no buried modules,
no regolith cover. There are no glass domes and no real logos, only invented stencils (CSD-1, GC-1, JC-2, SWG-2, RAD-1/2, LOX-1/2, LCH4-1/2, HE3-1, PS-1, PSCU container numbers).

| | |
|---|---|
| Triangles (master, `Mine` collection) | **529,500** (2,248 objects + the `Cam_Target` empty) |
| Master GLB | `dock_tankfarm_master.glb`, 3,394,564 B, meshopt + quantization (`gltfpack -cc -kn -km -ke -vpf`), **no Draco**, one node per part. Review asset only: it keeps the master's clearcoat and emissive-strength material extensions. md5 `689ab09630633494ae92fc947a15bd80` |
| **Game GLB** | `dock_tankfarm_game.glb`, **183,184 B (0.17 MB)**, **27,682 triangles and 12 draw calls with every tier visible** (base 17,542 tris / 4 draws). Materials `SHM_Paint`, `SHM_Metal`, `SHM_GlowCyan`, `SHM_GlowWhite` from `../_shared/shared_materials.json`. Extensions: `EXT_meshopt_compression` and `KHR_mesh_quantization` only. Plain metallic/roughness, no transmission/clearcoat/ior, no images or textures. Colour comes from `COLOR_0` vertex colours. No astronauts. md5 `7959ae74c3ef106095bbdbab492c9820` |
| Units / axes / origin | 1 m, Y up. The dock front (rolling door, container yard) faces +Z. The **origin is the station focus**: on the yard pad, on the hall/door axis. The tank farm extends to +X. |
| Footprint | X −18.2…39.5 m (feeder power mast to the buried-line vault), Z −36.3…16.9 m (solar masts behind to the road entry in front). Hall crown 13.2 m, sign top ~12.6 m, LCH4 vessel tops 16.2 m (vents ~17.8 m). |
| Scale | astronaut = 1.8 m (three in the review renders only; Stage collection, never exported) |

## Layout (fits the in-game station framing)
Phone shots use the Game Coder camera spec: perspective, **38° vertical FOV, tilted down 18°, looking down glTF −Z, aimed at the `Cam_Target` empty**. `Cam_Target` sits at Blender (12.0, −2.0, 6.0) = glTF (12.0, 6.0, 2.0), centred between the hall's left edge and the vault at the right end of the launch-pad line. It carries `extras {"frame_w": 64}`: **W = 64 m** spans the screen width at Cam_Target. The camera distance is d = (W/2) / (tan 19°·aspect) = **201.48 m** for 393×852 and for the 1179×2556 master (same aspect). On 393×852 the **whole dock (hall, power mast, radiator, crane, yard, tank farm, pipe racks and the buried-line vault) sits inside x ≈ 23–369** (master, all Mine-collection geometry; game GLB with all tiers on: about x 22–372), centred, and **y ≈ 318–495**, inside the y 100–650 band and clear of the sheet at y 674. `--ct x,y,z` and `--fw W` change it.
- To fit inside x 18–375 the layout was compacted: the feeder power mast moved from x −24 to −17.4 (just left of RAD-1), and the launch-pad headers now end at x ≈ 39.5 in a **buried-line vault** (they used to run on the surface to x 48). The far surface line is replaced by buried-pipeline marker posts (Stage only).
- **Tier screen boxes (393×852, game GLB, all tiers on):** Tier_03 x 85–154 y 411–467; Tier_05 x 245–277 y 371–446; Tier_08 x 44–87 y 383–455; Tier_12 x 225–263 y 398–464; Tier_20 x 44–310 y 331–481 (LCH4-2 plus RAD-2 on the left). Every tier is fully inside the frame, so the camera doesn't need to move when one is bought. Moving parts: Crane_Gantry x 68–170, Dock_Door x 97–153, Beacon_Lights x 24–181.
- **Focus (centre):** the cargo hall's rolling door (9.2 × 7.4 m opening) with the blue-neon **CARGO SPACE DOCK** sign on the arch cap above it, and the container yard in front.
- **Gantry crane GC-1** spans the yard (rails at x = ±7.2) and rests just in front of the stacks, low enough to leave the sign clear.
- **Container stacks** frame the lane left and right; the He-3 canister and the armoured platinum crate sit at the lane's front edge so they read at phone size.
- **Tank farm** close to the hall's right (+X): front row LOX-1, He-3 sphere HE3-1 (in front of the LOX gap) and LOX-2, with the two big LCH4 (liquid methane) tanks in the row behind, set into the gaps so they show over the front row. A low berm runs along its front.

## Systems
- **Cargo hall CSD-1:** a 22 × 18 m white shielded arch hall (shield-tile panels, graphite ribs, cyan light strips). A segmented **rolling door** (25 slats, guide rails, cyan edge strips) opens onto a lit interior with racks and three containers. Roof vents, comms dish, roof beacons and the neon sign sit on top.
- **Gantry crane GC-1:** two wheeled legs on surface rails (sleepers, end stops, bumpers), box girder with walkway, low-profile trolley, wire ropes and a spreader carrying a hoisted 20 ft container.
- **Container yard:** 6.06 × 2.44 × 2.59 m containers (white / graphite / pale, corrugated, corner castings, invented PSCU numbers), stacked 1–3 high. Cargo props: a **glowing blue He-3 canister** in a cradle frame, an **armoured platinum crate** (graphite armour, platinum panels, seals), and small crates.
- **Airlock + dust shower:** crew airlock on the hall's right flank (hatch, handwheel, porthole, status lamps), raised grated dust mat over a catch pan, air-shower arch with nozzle bars and blower, rotary boot brush, handrail.
- **Power:** switchgear SWG-2 front-left; a feeder line on graphite masts (nearest mast at x −17.4 with a red beacon) lands at a wall bushing; far masts and solar masts behind the hall.
- **Heat rejection:** white radiator wing RAD-1 on masts at the hall's left with coolant loops (RAD-2 is Tier_20).
- **Jib crane JC-2 (Tier_08):** slewing jib crane at the hall's front-left corner.
- **Fuel is methalox: LOX + liquid methane (LCH4).** There is no LH2 anywhere. Fuel arrives from the Refinery (the station to the left) by **buried pipeline**: it surfaces in the **FROM REFINERY riser vault** between the hall and the tank farm (marker `Pipe_Refinery`), with insulated risers into LOX-1 and LCH4-1.
- **Tank farm:** white MLI-jacketed cryo tanks. LOX-1/2 are r 2.4 m (about 173 m³), shell 1.9–10.0 m, vessel top 11.1 m. **LCH4-1/2 are the big tanks (they keep the earlier "bigger tank" pass): r 3.6 m (7.2 m diameter, 1.5× LOX) on a taller 4.0 m skirt, shell 4.0–14.6 m, vessel top 16.2 m, about 520 m³ each**, with thick graphite stiffener bands and a wide 1.3 m graphite MLI insulation belt with cyan pinstripes. All tanks stand on skirts and plinths, each with bands, labels (LOX-1 "LIQUID OXYGEN 90 K", LCH4-1 "LIQUID METHANE 112 K", ...), relief valves and vent stacks. A catwalk links the tank tops with a stair tower. The **He-3 cryo sphere HE3-1** has cyan bands (Tier_12). Insulated LOX / LCH4 / He-3 headers with handwheel valves run on pipe racks past the **pump skid PS-1**, turn toward the front and go underground in a graphite **buried-line vault** with a "TO LAUNCH PAD" plate (marker `Pipe_LaunchPad`).
- **Berm:** a low regolith berm along the tank farm's front (to x 33.4) and dock-side corner.
- **Lighting:** a shadowless `GapFill` area light over the dock–farm gap removes the hard black wedge the hall's shadow used to cast on the ground there.
- The ground uses the shared cool-grey `M_ground` from mc_common.py (hill-stripe fix, plus the cb5bf5a soft-patch / mid-scale / pebble update). No tan. The renders here use the cb5bf5a version.

## Files
- `_src/build_dock_tankfarm.py`: the procedural Blender 4.2 build script. It imports `art/3d/mine_concepts/_src/mc_common.py` and re-uses the Life Support helpers.
  `blender -b -P build_dock_tankfarm.py -- --out .. [--quick 1] [--only glb,blend,hero,phone,turn] [--hs 40] [--ts 32] [--ps 48] [--res WxH] [--pres WxH] [--door 0.5] [--hc x,y,z,tx,ty,tz] [--lens 28] [--td 95] [--ct 12,-2,6] [--fw 64] [--fill 2200]`. `--only proj [--ctlist x,y,z,W;...] [--overlap lch41,lch42]` prints phone-camera screen boxes per node (plus TankRow / Hall) and bbox overlaps without rendering.
  `--only glb` writes `dock_tankfarm_master_raw.glb`. Pack it with `gltfpack -i dock_tankfarm_master_raw.glb -o dock_tankfarm_master.glb -cc -kn -km -ke -vpf`.
- `_src/build_game_glb_tiered.py`: game exporter. It culls text, stencils, bolts, ribs, rails, cables and greebles under 0.3 m, disables bevel modifiers, remaps the materials to the 4 merged `SHM_*` materials (swatch colour goes to `COLOR_0`), welds, dissolves planar faces and collapse-decimates (base fitted to `--target 28000` total, tiers and moving parts at `--tierratio 0.7`). Splits out tier, moving-part and marker nodes.
  `blender -b dock_tankfarm_master.blend -P _src/build_game_glb_tiered.py -- --out raw.glb`, then `gltfpack -i raw.glb -o dock_tankfarm_game.glb -cc -kn -ke`
- `_src/render_game_preview.py`: flat Workbench preview of the game GLB with vertex colours (`blender -b -P render_game_preview.py -- --glb raw.glb --out DIR`; use the unpacked raw.glb because Blender can't decode meshopt). It prints per-node screen boxes.
- `_src/make_sheet.py`: builds the contact sheet (`python3 make_sheet.py turntable dock_tankfarm_turntable_sheet.png TITLE SUB hero.png`)
- `dock_tankfarm_master.blend`: full scene (procedural shading, stage, lights, cameras, review astronauts). The door is rendered 50 % open (`--door`).
- `dock_tankfarm_hero_3840x2160.png`: hero render (Cycles, OIDN, AgX), dock and tank farm on grey ground. **Stale:** from fb99e50 (old LH2 labels, old layout with the mast at x −24 and the surface line to x 48); re-render pending.
- `dock_tankfarm_phone_1179x2556.png` and `dock_tankfarm_phone_393x852.png`: in-game station camera view aimed at `Cam_Target`, W = 64 m (3× master, and its Lanczos downscale)
- `dock_tankfarm_game_preview_393x852.png` and `dock_tankfarm_game_preview_hero.png`: the game GLB itself (all tiers visible, door closed) from the station camera (Cam_Target, W = 64 m) and the hero angle (flat preview renders)
- `turntable/turn_000..315.png` and `dock_tankfarm_turntable_sheet.png`: 8 angles at 45° steps, plus the contact sheet. **Stale:** they predate the LCH4 relabel and the compacted layout (they still show LH2 labels, the mast at x −24 and the surface line to x 48); re-render pending. The phone renders and game previews are current.

## Game GLB nodes
All under the root `DockTankFarm`. Glows on tier and moving parts are folded into `SHM_Paint` (cyan kept as vertex colour) so each is exactly one draw (Beacon_Lights uses `SHM_GlowWhite`).

| Node | What it is | Tris | Material | Pivot (glTF, m) |
|---|---|---|---|---|
| `Base_Paint`, `Base_Metal`, `Base_GlowCyan`, `Base_GlowWhite` | static base, merged by material | 11,372 / 3,222 / 2,844 / 104 | SHM_* | origin |
| `Tier_03` | three extra containers on the yard stacks | 216 | SHM_Paint | (0, 0, 6.31) |
| `Tier_05` | second LOX tank LOX-2 with catwalk posts and header tie-in | 1,796 | SHM_Paint | (22.99, 0, −6.77) |
| `Tier_08` | jib crane JC-2 | 468 | SHM_Paint | (−9.49, 0, −1.02) |
| `Tier_12` | He-3 cryo sphere HE3-1 with legs, bands and drop line | 3,468 | SHM_Paint | (19.80, 0, −0.50) |
| `Tier_20` | second LCH4 tank LCH4-2, radiator wing RAD-2, two extra container stacks | 2,586 | SHM_Paint | (8.05, 0, −4.83) |
| `Crane_Gantry` | gantry crane (legs, girder, trolley, spreader, hoisted container), pivot on the rail top at the crane's rest position | 1,030 | SHM_Paint | (0, 0.32, 9.00) |
| `Dock_Door` | rolling door, pivot at the top of the opening (door rolls up by scaling local Y) | 336 | SHM_Paint | (0, 7.40, −3.72) |
| `Beacon_Lights` | hall roof beacons + power-mast red lamp | 240 | SHM_GlowWhite | (−9.20, 13.45, −4.90) |

Tier nodes carry `extras` `{"tier": N, "hidden_by_default": true}` (three.js: `userData`). glTF has no hidden flag, so the loader must set `visible = false` on load.

Clips:
- `crane_gantry_move` (6.0 s loop): `Crane_Gantry` translation 4.5 m toward the hall (−Z) by 3.0 s and back, smooth.
- `dock_door_open` (2.5 s, play once / reverse to close): `Dock_Door` scale Y 1 → 0.06 about the top pivot.
- `Beacon_Lights_Blink` (1.5 s loop, step): 0.3 s on, then scale 0.001 for 1.2 s.

Markers (empty nodes, glTF coords; glTF Z = −Blender Y):
- `Road_Entry` (0, 0.12, 17.20): where the road meets the yard pad.
- `Crate_Drop` (0, 0.12, 6.00): crane drop spot in the yard lane, in front of the door.
- `Container_Stack` (−4.00, 5.30, 3.00): top of the left front stack.
- `Pipe_LaunchPad` (37.70, 0.66, 7.30): top of the buried-line vault where the LOX / LCH4 / He-3 line to the launch pad goes underground.
- `Pipe_Refinery` (14.50, 0.60, −12.60): FROM REFINERY riser vault where the buried fuel line from the Refinery surfaces.
- `Cam_Target` (12.00, 6.00, 2.00), `extras {"frame_w": 64}`: station-camera look-at (empty, no draws). Aim the camera at it from 18° down with 38° vertical FOV, at the distance where 64 m spans the screen width.
- `Crew_Path_01..08`: from the airlock hatch over the dust mat and out to the hall front: (9.25, 0.32, 0.28), (9.25, 0.32, 1.60), (9.25, 0.12, 3.70), (8.65, 0.12, 6.00), (5.60, 0.12, 14.30), (2.30, 0.12, 11.90), (0, 0.12, 6.00), (0, 0.12, −2.10).

## Validation (game GLB)
- three.js: `Cam_Target` loads at (12, 6, 2) with `userData.frame_w = 64`; all five tiers carry `{tier, hidden_by_default: true}`; clips Beacon_Lights_Blink 1.5 s, crane_gantry_move 6.0 s, dock_door_open 2.5 s.
- `gltf-transform inspect`: 12 meshes / 12 primitives, 4 materials, no textures, 3 animations, extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression] (no Draco).
- Loaded in Node with three.js `GLTFLoader` plus `MeshoptDecoder`: 12 draw calls, 27,682 triangles, 29,359 vertices (all tiers visible), materials SHM_GlowCyan/GlowWhite/Metal/Paint, bbox (−18.15, −0.30, −36.26)…(39.51, 17.82, 16.94).
- Materials contain only `pbrMetallicRoughness` and `emissiveFactor`, with no `KHR_materials_*` extensions.

## Caveats
- The game GLB is a collapse-decimated proxy. Text and stencils are culled except the sign. Sign letters and neon are merged into `Base_GlowCyan`, so the blue neon reads cyan in game. Handrails, stair rails, ropes, power lines and grating are dropped or simplified. Small curved parts get faceted.
- The game door is modelled closed (`Dock_Door` scale 1); the renders show it 50 % open.
- Grime, dust, wear and corrugation are procedural and live only in the .blend and the renders.
- The master GLB is for review, not the game. It still uses the `KHR_materials_clearcoat` and `KHR_materials_emissive_strength` extensions.
- Fuel is LOX + LCH4 (no LH2 anywhere). The LCH4 tanks are 3× the LOX volume. A methalox load (O/F ≈ 3.6 by mass) needs only about 0.8× the LOX volume of methane, so treat the extra as buffer storage; they could shrink if realism wins over readability.
- With frame_w = 64 the whole dock fits but is small on a phone (the hall is about 140 css px wide, a 1.8 m astronaut about 11 css px tall on 393×852). Fitting everything in x 18–375 is the trade-off; a smaller `--fw` makes the dock bigger but crops the tank farm or the hall.
- Cyan is used for light strips to match Mine B, and the He-3 canister/sphere glow blue-cyan. STYLE_GUIDE_3D reserves cyan for He-3, so the guide may need updating.
- For framing, the tank farm starts about 3 m from the hall's right wall (LOX-1 shell edge at x ≈ 14.2 m) and the launch-pad line goes underground at x ≈ 37.7 m; a real installation would keep cryo tanks much farther from the dock.
