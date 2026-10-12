# Room art handoff: Shipyard + Engineering base rooms
- Format: same as ART_SPEC layered floors.
  - Files: `floors/floor_<art>.{json,webp,_layers.webp,_needs_stock.webp}`, @2x/@3x.
  - 16 frames at 12 fps, loop. WebP q95. One layers page each, ≤2048 px.
- Size: 360x120, pivot (0,120), except **ship_assembly: 360x240, pivot (0,240), takes 2 floor slots**. It has no `_needs_stock` variant.
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
- None of these ids are referenced in game.js yet.

## Shelved
- `hab_quarters` is shelved in `art/moon/_shelved/hab_quarters/`. Do not ship it.
