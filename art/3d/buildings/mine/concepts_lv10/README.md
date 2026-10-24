# Mine Lv10 concepts (10/24/2026) - concept stills only

These are concept stills for the first big look change: the Mine levels to 50, with a new look every 10 levels.

- Nothing here is a game asset. The game Mine GLB (ef45f6f1), HT-04 (71fe624e), qa3d and qa3d-next are untouched.
- Each concept is built **on top of the current Mine** with the Mine-B style: white paint, graphite and cyan, with weathering (low dust plus grime).
- Both concepts keep:
  - the pit dug into the surface;
  - the plant above ground;
  - the flat grey lunar ground;
  - the tire-track haul road.
- The names on the signs are original, with no real logos. The font is Chakra Petch Bold (OFL), rendered into the stills only.

## A - TYCHO DEEPWORKS (vertical, "go deep")
- A 30 m tapering lattice **headframe** stands over a dug, cyan-floored **shaft** at the back centre. It has:
  - a winder house;
  - twin spinning **sheave wheels** (motion blur);
  - backstays and cyan leg light strips;
  - a red beacon mast;
  - a skip cage mid-hoist (blurred);
  - a lit **TYCHO / DEEPWORKS · SHAFT 10** sign.
- Busier ground level:
  - a terraced **second open pit** at front-left, with cyan rim lights, amber bench lights and an exposed glowing seam;
  - a small pit-side drill mast;
  - an **incline conveyor** from the pit into the hoppers;
  - a **3-bay ore bay** on the right, fed by a second conveyor;
  - floodlights and lit road posts.

## B - ARGENT SEAM WORKS (horizontal, "go wide")
- **Twin rig:** a second slim 26 m derrick sits on the right over its own lit pit. It has a spinning top drive, an **amber** drill-string collar and a beacon.
- A white **gantry** spans both haul lanes. It carries:
  - the ore conveyor from rig 2 to the hoppers (cyan chevrons and riding ore, blurred);
  - the lit **ARGENT SEAM / He-3 WORKS · LEVEL 10** billboard.
- Busier ground level:
  - a covered **ore bay** at front-left with glowing rich-ore piles;
  - a wide, shallow, amber-lit **second pit** with an excavator arm;
  - a comms mast and dish;
  - twin tanks;
  - floodlights.
- Silhouette: A is one tall spike; B is a broad, busy skyline with warmer amber accents.

## Files
| file | what |
|---|---|
| mine_lv10_{current,A,B}_393x852.png | Cycles, game station camera exactly as qa3d-next frames the Mine (frame_w 39.9, Cam_Target y 5.6, 38 deg vFOV, 18 deg down) |
| mine_lv10_{current,A,B}_375x667.png | same camera recipe at 375x667 |
| mine_lv10_compare_game_{393x852,375x667}.png | current / A / B side by side |
| mine_lv10_{current,A,B}_hero_1920x1080.png | hero close-up, one shared 3/4 camera (26 mm at (-32,-50,20) -> (4,3,15.5)); all buildings inside frame |
| mine_lv10_compare_hero_1920x1100.png | current / A / B heroes |
| _check/mask_*.png, _check/edge_check.json | edge check: unlit mask of everything standing > 0.45 m (ground, road and deposits drop out) |
| _src/lv10_concept.py, _src/sheets.py | scene builder (`--variant current/A/B --shots game,hero,mask,proj,hproj --sizes`) and sheets |

## Edge check (minimum 5 px from every edge): all pass
The lowest margin is 18 px (A, right edge, at 393). The analytic projection (`--shots proj`) agrees.

| frame | L | R | T | B | pass |
|---|---|---|---|---|---|
| current_393x852 | 63 | 65 | 232 | 399 | True |
| A_393x852 | 36 | 18 | 90 | 398 | True |
| B_393x852 | 28 | 24 | 172 | 392 | True |
| current_375x667 | 64 | 64 | 153 | 309 | True |
| A_375x667 | 36 | 23 | 23 | 307 | True |
| B_375x667 | 29 | 23 | 99 | 301 | True |

## Render
- Blender 4.2.3, Cycles CPU: 160 samples for game frames and 128 for hero frames.
- OIDN denoising, AgX Medium High Contrast, motion blur with shutter 0.8.
- Lighting matches mine/_src/proof_phone.py: Sun 4.0 at angle 3 deg, world (0.03, 0.035, 0.045), regolith 0.16 grey.
- Inputs are the unpacked Mine and HT-04 GLBs (`gltfpack -noq`), because Blender has no meshopt decoder.
- Every heavy render was run under `flock /tmp/planet_stack_heavy.lock nice -n 19 ... -t 4`.

## md5
```
ebcf7c48 mine_lv10_A_375x667.png
5a4dee5d mine_lv10_A_393x852.png
8db683d5 mine_lv10_A_hero_1920x1080.png
d35ca1db mine_lv10_B_375x667.png
e26c1b8d mine_lv10_B_393x852.png
0fad3a41 mine_lv10_B_hero_1920x1080.png
4030bf5e mine_lv10_compare_game_375x667.png
853c7944 mine_lv10_compare_game_393x852.png
0097ba1e mine_lv10_compare_hero_1920x1100.png
0043ab06 mine_lv10_current_375x667.png
8f29c0ea mine_lv10_current_393x852.png
bc5a1215 mine_lv10_current_hero_1920x1080.png
```
