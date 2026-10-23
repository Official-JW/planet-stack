# Life Support (LS-01) concept master

A high-detail 3D concept master for the Planet Stack **Life Support** building. It is styled to match
**Mine concept B (sleek high-tech)**: glossy white and graphite panels, satin metal, cyan light strips, and clean rounded
shapes, with the same weathered finish (lunar dust on lower and upward-facing surfaces, grime, edge wear, panel seams).
Everything is original. There are no real logos, only invented stencils (LS-01, PM-1/2, SWG-1, R-1, EL-1, O2-1/2, M-1, C-1, H2O-1..3, RAD-0..2, SA-1/2, FPU-1).

| | |
|---|---|
| Triangles (exported building, `Mine` collection) | **248,973** (996 objects) |
| Master GLB | `life_support_master.glb`, 1.67 MB (Draco, 996 nodes), 1 m units, Y up, front faces +Z, origin at base center on the ground (bbox Y min ≈ -0.005) |
| In-game GLB (target ≤ 0.9 MB) | `life_support_game.glb`, **0.54 MB**, full detail: the master run through `gltf-transform optimize --compress draco --simplify false` (meshes joined per material, base colors packed into a 128×4 palette texture, same origin/axes/bbox) |
| Footprint | ≈ 38.7 m (X) × 27.8 m (Z), mast tops at 15.5 m |
| Scale | astronaut = 1.8 m (stage only, not in the GLB) |

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
  `blender -b -P build_life_support.py -- --out .. [--quick 1] [--only glb,blend,turn,hero] [--ks 0,1] [--hs 48] [--ts 40] [--res WxH]`
- `_src/make_sheet.py`: builds the contact sheet (`python3 make_sheet.py turntable life_support_turntable_sheet.png TITLE SUB hero.png`)
- `life_support_master.blend`: full scene with procedural shading, stage, lights and cameras
- `life_support_master.glb`: building only (geometry and base colors, one node per part)
- `life_support_game.glb`: in-game candidate (joined, palette, Draco), 0.54 MB
- `life_support_hero_3840x2160.png`: hero render (Cycles, 48 spp, OIDN, AgX Punchy)
- `turntable/turn_000..315.png`: 8 angles at 45° steps, 1000 px, 40 spp
- `life_support_turntable_sheet.png`: contact sheet (8 angles plus the hero), same layout as the Mine concepts

## In-game plan (0.9 MB budget)
`life_support_game.glb` already fits at 0.54 MB with full detail. Measured alternatives from the same master: simplify 0.75 gives 0.47 MB,
0.6 gives 0.41 MB, 0.4 gives 0.32 MB. If the phone triangle budget matters more than file size, use simplify 0.4–0.6 and/or drop the
grating bars, bolts and rail posts (the main triangle sinks), then bake the procedural grime/dust/wear into a small atlas if the
budget allows (about 0.3 MB left over).

## Caveats
- About 249k triangles is heavy for phones even though the file fits the 0.9 MB budget. See the plan above.
- The game GLB has not been loaded in qa3d or the game yet. It uses KHR_draco_mesh_compression, which the loader must support.
- The GLB carries geometry and flat base colors only. Grime, dust, wear, radiator ribs and solar cells are procedural shaders that live only in the .blend.
- The stage terrain comes from `mc_common.build_stage`, which currently includes the in-progress hills/crater edits.
- For framing, FPU-1 sits about 65 m away. A real installation would put it about 1 km away behind terrain or a berm (the sign says so).
- Cyan is used for light strips to match the chosen Mine B look. STYLE_GUIDE_3D reserves cyan for He-3, so the guide may need updating.
- The turntable frames were rendered before the hull stencils were renamed M-1/M-2 to PM-1/PM-2 (to avoid clashing with melt vessel M-1). The label can't be read at 1000 px. The hero, .blend and GLBs have the final labels.
