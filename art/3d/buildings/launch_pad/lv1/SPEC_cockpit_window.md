# Cockpit window band CW-1: runtime glow switch (for Coder)

- **File:** `art/3d/buildings/launch_pad/launch_pad_game_lv1ship.glb`, md5 `1042e76793da1f97a9837a4a823873f0` (committed 10/25/2026), 15 draws.
  See `CHANGES_lv1ship_1042e767.md`.
- **Source:** `_src/lp_cockpit_window.py`, built with `build_launch_pad.py ... --cockpit 1 [--cockpit_glow 1|0]`.
- **Approved** by A&A at 10/24 14:54 PT: the band at z 25.95..27.15 and the vertex-colour switch, which adds no draw calls.

## Geometry
- 4 panes, each 0.58 m wide × 1.20 m tall. The glass covers ship-local glTF y 25.95..27.15 (pad z, up).
  - The panes sit on the two hull facets that carry cargo door CD-1, at bearings 257.49°, 268.13°, 281.87° and 292.51° in the pad frame.
  - They face the game camera (+Z glTF). In the 375×667 game view each pane is about 5.8 px tall; at 393×852 it is about 6.0 px.
- The frames use LP_ShipGraphite (#2b2f35), 7 cm wide and 2.5 cm proud of the hull. The glass is recessed 2 cm inside the frame.
- Everything is part of the `Ship_Placeholder` mesh (material SHM_Stainless), so the windows add no draw calls.
- `Cockpit_Window` is an empty, a child of `Ship_Placeholder`, at local (0.334, 26.55, 3.82) = world (457.334, 26.55, -9.18).
  - Its extras are: `on_hex`, `off_hex`, `default: "on"`, `panes: 4`, and `glass_boxes_ship_local_gltf` (a JSON string with the same boxes as below).
- `Engine_Ring_Mount` is an empty, a child of `Ship_Placeholder`, at local (0, 2.9, 0) = world (457, 2.9, -13).
  - It marks the base centre of the ship (aft skirt bottom), for swapping in the A&A aft skirt or engine ring. Its extras hold `skirt_r_m` and `dome_bottom_z_pad`.

## Pane boxes
Each box is an axis-aligned min/max that already includes a 1 cm margin.
- **Ship-local** is glTF in the `Ship_Placeholder` node frame. The node sits at translation (0, 0, -13).
- **World** = ship-local + (457, 0, -13). Layout v2: pad origin 457, and the ship stands at pad-local glTF z -13.

| Pane | Bearing | Ship-local min | Ship-local max | World min | World max |
|---|---|---|---|---|---|
| 1 | 257.49° | (-1.151, 25.94, 3.766) | (-0.551, 27.16, 3.893) | (455.849, 25.94, -9.234) | (456.449, 27.16, -9.107) |
| 2 | 268.13° | (-0.427, 25.94, 3.857) | (0.173, 27.16, 3.984) | (456.573, 25.94, -9.143) | (457.173, 27.16, -9.016) |
| 3 | 281.87° | (0.513, 25.94, 3.727) | (1.098, 27.16, 3.951) | (457.513, 25.94, -9.273) | (458.098, 27.16, -9.049) |
| 4 | 292.51° | (1.211, 25.94, 3.511) | (1.795, 27.16, 3.736) | (458.211, 25.94, -9.489) | (458.795, 27.16, -9.264) |

## Colours
COLOR_0 is stored as UNSIGNED_BYTE normalized, in linear values (glTF).

| State | sRGB hex | Linear | COLOR_0 uint8 |
|---|---|---|---|
| ON (warm interior glow, the default in the file) | `#ffb46a` | (1.0, 0.4564, 0.1441) | (255, 116, 37) |
| OFF (dark glass) | `#141b22` | (0.0070, 0.0110, 0.0160) | (2, 3, 4) |
| Frame (never recolour) | `#2b2f35` LP_ShipGraphite | (0.0242, 0.0284, 0.0356) | (6, 7, 9) |

## How to match the pane vertices
1. Take the `Ship_Placeholder` mesh child. gltfpack quantised it, so apply the mesh child's local matrix (the dequant transform) to each POSITION.
   That gives ship-local coordinates. In three.js, use `v.applyMatrix4(meshChild.matrix)`.
2. A vertex is a pane vertex only when BOTH of these are true:
   - **(a)** it lies inside one of the 4 boxes above, with 1 mm tolerance;
   - **(b)** its COLOR_0 equals the current pane colour (ON (255, 116, 37) or OFF (2, 3, 4)), within ±1 per channel in uint8.
   - Both tests are needed because the graphite frame's inner edge shares the box faces. In the file, 168 vertices are inside the boxes: 96 are glass and 72 are frame (6, 7, 9).
3. **Glow vertex count: 96** (4 panes × 24 vertices, unshared flat faces). All 96 are inside the boxes; none lie outside them.
   The mesh has 9,356 vertices in total.
4. To switch, write the other colour into those 96 indices and set `needsUpdate` on the colour attribute.
   - Cache the indices once at load, so later switches don't need the colour test.
   - SHM_Stainless is a lit material, so ON reads as amber paint rather than true emission. Bloom or emissive is up to the game shader.
   - If true emission is needed, the fallback is a separate 1-primitive `Cockpit_Window` mesh node, which makes 16 draws. That needs the Director's OK.
