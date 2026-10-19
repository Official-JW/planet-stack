# Room art handoff: Shipyard + Engineering base rooms
- Format: same as ART_SPEC layered floors.
  - Files: `floors/floor_<art>.{json,webp,_layers.webp,_needs_stock.webp}`, @2x/@3x.
  - 16 frames at 12 fps, loop. WebP q95. One layers page each, ≤2048 px.
- Size: 360x120, pivot (0,120), except **ship_assembly: 360x240, pivot (0,240), takes 2 floor slots** (see stacking note below).
- Labels ≥10.5 px @3x. Never ship `_masters/`.

## Final floor order (Game Director)
1. **Habitat:** Living Quarters (`living_quarters`, existing v3 pods), Hospital (`hospital`), Café (`moon_cafe`), Supply Depot (`market`, in `mine/floors/`), Roof.
2. **Shipyard:** Refinery (`refinery`), Assembly (`ship_assembly`, 2 slots), Parts (`ship_parts`), Fuel (`ship_fuel`), Launch Tower.
3. **Engineering:** CNC (`eng_cnc`), CAD (`eng_cad`), CAM (`eng_cam`), Print (`eng_print`), Chem (`eng_chem`), Prop (`eng_prop`), Penthouse.
- Roofs, Launch Tower and Penthouse are not part of this batch.

## Accents
- Shipyard: assembly #ff6a3d, parts #e8885a, fuel #ffb4a0.
- Engineering: cnc #d4e04a, cad #c0e86a, cam #e8d84a, print #b8e04a, chem #a8e080, prop #e8e070.

## Sizes (bytes, @2x + @3x, 4 files each)
| Floor | Bytes |
|---|---|
| ship_assembly | 186,108 |
| ship_parts | 228,620 |
| ship_fuel | 201,012 |
| eng_cnc | 193,554 |
| eng_cad | 168,439 |
| eng_cam | 173,969 |
| eng_print | 202,978 |
| eng_chem | 203,672 |
| eng_prop | 230,101 |
| **Total** | **1,788,453** |

- Sheets: `art/moon/shipyard_rooms.png`, `art/moon/engineering_rooms.png`.
- In `game-1215.js` (PREVIEW · 12:15) these ARE wired: `ship_assembly`, `eng_cnc` (and the other `eng_*` rooms), `roof_habitat`, `roof_engineering`, `refinery`, plus packs `shipyard_rooms` / `engineering_rooms`.
- Still unwired as art-only: Launch Tower and Engineering Penthouse (not in this batch).

## Shelved
- `hab_quarters` is shelved in `art/moon/_shelved/hab_quarters/`. Do not ship it.

## Shipyard tiers (L10–L50)
- Files: `floors/tiers/floor_<id>_t{10..50}.{json,webp,_layers.webp}`, @2x/@3x.
- Overlays are cumulative, use the same format as the Life Support tiers, and each has one layers page.
- ship_assembly overlays are 360x240, pivot (0,240).
- Tiers:
  - **assembly:** UT NDT carriage, X-ray booth, orbital welder, laser seams, gold.
  - **parts:** RFID portal, scan drone, pick gantry, rack lights, gold.
  - **fuel:** LN2 subcooler, gas detection, VJ transfer line, tank halo, gold.
- Bytes (@2x+@3x): assembly 511,116; parts 333,184; fuel 425,434; total 1,269,734.
- Sheets: `ship_assembly_tiers.png`, `ship_parts_tiers.png`, `ship_fuel_tiers.png`.
- Generator: `artgen/tiers2/shipyard_tiers.py`.

## Packs (later-loading, `art/moon/packs/`, root "." = art/moon, same format as mine_later_*.json)
- `shipyard_rooms.json`: bases and L10–L50 tiers for ship_assembly, ship_parts, ship_fuel and refinery.
- `engineering_rooms.json`: the six eng_* bases and their L10–L50 tiers.
- `habitat_rooms.json`: hospital and moon_cafe bases and tiers, plus living_quarters tiers only. The starter living_quarters base is not repacked.
- hab_quarters is shelved and is in no pack.

## ship_assembly two-slot stacking
- It occupies 2 consecutive floor slots and is drawn once, as a 360x240 image with pivot (0,240) at the bottom-left of the lower slot.
- Its tiers are also 360x240 overlays and use the same anchor.
- `floor_ship_assembly_needs_stock.webp` (360x240) now exists. It is the same dimmed room with the crate icon centred.
- Treat the upper slot as occupied and draw nothing in it.
- L10 fix: the NDT carriage now rides a short rail at x 148–210 on the hull crown, so it no longer covers the HULL SECTION 04 · CRADLE tag.

## Engineering tiers (L10–L50)
- Same format as the Shipyard tiers: `floors/tiers/floor_eng_<id>_t{10..50}.*`, cumulative, 16 frames at 12 fps, one layers page each, 360x120, pivot (0,120).
- Tiers:
  - **cnc:** tool presetter, coolant chiller, mist extraction, light curtain, gold.
  - **cad:** render node, plotter, cable tray, glowing review wall, gold.
  - **cam:** tool presetter, chip bin, 6-bar air drop, glowing sim screen, gold.
  - **print:** O₂ monitor, HEPA extract, argon line, chamber lights, gold.
  - **chem:** hood service valves (gas/vac/air), safety shower, hood exhaust, sash lights, gold.
  - **prop:** PT rack, high-speed camera, deluge, shock diamonds, gold.
- Bytes (@2x+@3x): cnc 450,360; cad 384,546; cam 338,152; print 301,976; chem 295,147; prop 219,178; total 1,989,359.
- Sheets: `art/moon/eng_<id>_tiers.png`. Generator: `artgen/tiers2/eng_tiers.py`.

## L50 badge placement
- In Engineering (all 6) and Shipyard Parts and Fuel, the L50 badge is a compact medal with a MASTERED plaque beside it.
- It sits on clear wall with at least 4 px clearance at @3x from screens, labels and equipment.
- Centres in pt:
  - cnc (214,36), cad (74,40), cam (210,40), print (276,62), chem (190,32), prop (292,69).
  - parts (296,31), with a smaller r 6.4 medal to fit above the crates; fuel (174,46).
- Room changes made to clear space:
  - print: O₂ monitor moved to x 314.
  - prop: PT rack moved into the test cell.
  - chem: L10 is now hood service valves, replacing the gas manifold.
- Assembly keeps its full-size badge at (40,58).

## Living Quarters tiers (L10–L50), base `living_quarters` (HAB-04) unchanged
- Accent is peach #f0a070, taken from the shelved hab_quarters.
- Files: `floors/tiers/floor_living_quarters_t{10..50}.*`, 360x120, pivot (0,120), 16 frames at 12 fps, one layers page each.
- Tiers:
  - L10: CO₂ monitor and pod vent grilles.
  - L20: cycle ergometer.
  - L30: cabin air loop duct and hazard edge.
  - L40: staggered peach pod glow (the hab_quarters motion) and strips.
  - L50: gold trim, gold pod frames, and the badge on the locker faces at (313,80), clear of screens and labels.
- Bytes (@2x+@3x): 469,371. Sheet: `art/moon/living_quarters_tiers.png`. Generator: `artgen/tiers2/lq_tiers.py`.

## Pack sizes (@3x / @2x bytes)
- shipyard_rooms: 1,874,960 / 1,177,188.
- engineering_rooms: 1,952,427 / 1,209,645.
- habitat_rooms: 1,623,331 / 984,283.

## Supply Depot tiers (L10–L50)
- Base `floor_market` (DEP-05) is unchanged.
- Accent is emerald #24d08a, distinct from Café sage #9cc76a.
- Files follow the mine/ convention:
  - `mine/@2x|@3x/floors/tiers/floor_market_t{10..50}.{json,webp,_layers.webp}`
  - masters in `mine/_masters/floors/tiers/`
- Format: 360x120, pivot (0,120), 16 frames at 12 fps, one layers page each.
- Tiers:
  - L10: RFID gate over the inbound conveyor.
  - L20: check-weigh readout.
  - L30: 2 t monorail hoist over the racks and hazard edge.
  - L40: emerald rack-edge lights and strips.
  - L50: gold trim and compact badge at (242,61), r 6.4, on clear wall between the manifest screen and the conveyor and above the forklift mast's highest point.
- Bytes: @3x 150,369; @2x 99,428; total 249,797.
- Pack: `packs/supply_depot_later_tiers.json` (root "mine", later-loading). `supply_depot.json` is unchanged; its `floor_market*` pattern does not include `tiers/`.
- Sheet: `art/moon/supply_depot_tiers.png`. Generator: `artgen/tiers2/depot_tiers.py`.
