# Planet Stack: Helium & Platinum Mine (building 2) art spec
Sizes are in logical points. Use `@3x/` when devicePixelRatio > 2, otherwise `@2x/`. Images are full-colour WebP (q92, alpha q100, no palette reduction). `_masters/` holds 6x lossless sources (never ship these). Atlas JSON uses the same format as ../ART_SPEC.md: `meta{images,scale,fps,logicalFrame,pivot,loop}`, `frames{name_i:{page,frame,duration}}`. Accent colour: amber #ff9a2a. He-3 is violet #c8a6ff, and LOADED/OK is green #39ff6a.

## Rover (`rover/`, 90x50, pivot (45,50) bottom centre, faces right; flip X for leftward)
| sheet | frames | fps | loop | notes |
|---|---|---|---|---|
| rover_drive | 14 | 12 | yes | wheels turn 120°/loop, suspension bob ±0.8, low-g dust behind the wheels, empty bed |
| rover_scoop (**106x50 frame**, pivot still (45,50)) | 16 | 12 | no | front arm lowers (f0–6), digs with a dust puff (f5–10), lifts; the bed fills 30%→100% |
| rover_dump | 16 | 12 | no | bed tips 0→36° (f0–6), pours out the rear (f4–11), dust cloud, lowers (f12–15) |
`rover_static` = drive frame 0. The headlight beam and red tail lamp are baked in.

## Rover surface-dig path and dump timing (game logic; the tunnel route below is the main loop)
The ground is the surface line at the Rover Bay door. The rover leaves `SURFACE LOCK A` (the left of the bay, floor x≈10–106) and drives outward with drive @12 fps at 24 pt/s for 3 s. It plays scoop (1.33 s) at the dig site, turns (flip X), and drives back. It reverses so its rear is over `pad/surface_hopper` (60x40, pivot (30,40)), with the rover pivot about 58 pt right of the hopper pivot. Then dump plays: 0 ms start tilt; **330 ms material pours** (spawn the ore tick or hopper fill); 920 ms pour ends; 1330 ms done. Then it drives back to its charging bay. Total loop ≈ 10 s at speed 1. Inside the bay floor, the parked rover is baked into the static art.

## Floors (`floors/`, 360x120, pivot (0,120), layered format exactly like ART_SPEC)
`floor_mine_{rover_bay,crusher,separator,packing}.webp` (static base) + `.json` / `_layers.webp` (16-frame seamless loop @12 fps) + `floor_mine_X_lowpower.webp` (dimmed/desaturated with a red top strip; pause the layers while low power, and the shared fx/floor_low_power can be drawn over it). Labels: MIN-B1, 02, 03, 04. Order from bottom: Rover Bay (garage door, intake hopper with ore, rotary feeder, conveyor, 2 charging bays), Crusher (jaw crusher + flywheel, cone crusher, conveyors, dust), Separator (glowing 700 °C kiln drum, gas line to 2 He-3 tanks, magnetic drum flinging platinum glints), Packing (overhead robot arm, conveyor of boxes whose LEDs turn green after sealing, outbound stack).

## Penthouse (`floors/penthouse_mine`, 360x180, pivot (0,180), layered 16f @12 fps loop)
A domed top that matches penthouse_control. Inside the dome: a mine headframe with 2 counter-rotating sheave wheels and a hoist cage moving on its cable, a He-3 vent stack with violet glow and steam, ore rail cars, and a survey dish. The MIN-OPS room below has a survey map with a moving rover dot, an ore assay chart, He-3/Pt price and next-ship ticker screens, a platinum ingot case, a sample LOADED box and a console. `penthouse_mine_lowpower` is also provided. Draw it on top of the highest floor (bottom edge = that floor's top).

Packing floor and penthouse boxes alternate between the Pt crate and the He-3 canister. Packing floor seal flash: it fires on the LED (box-local (24,11)) of the box crossing x=150, the point where its LED turns green.

## LOADED box (`box/`, 28x24, pivot (14,24))
- `loaded_box` static; `loaded_box_pulse` 12f @12 fps loop = 1.0 s LED cycle (cosine ease).
- `loaded_box_sealed` 16f @12 fps one-shot: lid lowers (f0–4), latches swing shut (f4–8), the amber LED turns green with a flash (f8–10), then settles.
- `loaded_box_stack3` 58x46, pivot (29,46), 12f loop with the 3 LEDs out of phase.
- `loaded_box_hero_3x` (a 3x-larger render, 84x72 logical) + `_masters/box/loaded_box_hero_36x.png`.

## Scene layers (back → front)
1. Sky/globe. 2. **Mid layer** (ground line G): the mine tower, `surface_hopper` (doorstep of the Rover Bay), the Cargo Space Dock, the ship, cranes, the launch tower, astronauts and the cargo mule. 3. **Foreground layer** at G+70 pt, drawn **after** everything else at scale ×1.25 (closer = bigger), with blurred contact shadows (ellipse rx = 0.53×sprite width, ry = 4, black 45%): rover, tunnel, foreground hopper. Parallax: when the camera pans, move the foreground layer 1.15× as fast as the mid layer.

## Mining tunnel (`tunnel/`)
- `tunnel_back` 240x90, pivot (0,30) = left end of the ground line; 8f @8 fps loop (portal floodlights and ramp guide lights). Contents: braced steel-set portal `ADIT-2` with a hazard header, the dark tunnel mouth, a sloping ramp, and the far cut wall.
- `tunnel_front_lip` 240x90, same pivot, static. **Draw it after the rover** so the rover's wheels sink behind the near bank as it descends.
- Ramp in tunnel-local coordinates: top (20,30) → bottom (170,78) (slope 17.7°); the portal mouth is x 160–220.

## rover_tunnel (`rover/rover_tunnel`, 106x64, pivot (45,58), 24f @12 fps, not looped)
- f0–11 **descend**: empty, pitches nose-down 0→17.7° and fades to dark (to 15% brightness) as it enters the mouth.
- f12–23 **emerge**: loaded, reverses up from the dark and levels out.
- The engine moves the pivot along the ramp line: descend = 1.0 s from ramp top to (170,78); hide the rover 0.8 s ("mining"); emerge = 1.0 s back up the ramp.

## Rover route (one loop, about 16 s at speed 1)
| step | sheet | time | path |
|---|---|---|---|
| 1 | rover_drive | 3.0 s | Rover Bay door → tunnel ramp top (foreground layer, 24 pt/s) |
| 2 | rover_tunnel f0–11 | 1.0 s | down the ramp into ADIT-2 |
| 3 | (hidden) | 2.0 s | underground: fill +1 load |
| 4 | rover_tunnel f12–23 | 1.0 s | back up to the ramp top, loaded |
| 5 | rover_drive (flip X) | 3.0 s | ramp top → hopper (stop with the bed over the hopper, rover pivot 58 pt right of the hopper pivot) |
| 6 | rover_dump | 1.33 s | pour starts at 330 ms, ends at 920 ms → ore tick |
| 7 | rover_drive | 2.5 s | hopper → charging bay / back to step 1 |
(`rover_scoop` remains for surface digging events.)

**The Cargo Space Dock, the 4-floor ship, the dock cranes, the crew13 crew and the floodlights moved to `../dock/` (see dock/DOCK_SPEC.md).**

## Globe stops
The globe has 6 stops, 60° apart: Life Support, Mine, Cargo Space Dock, Habitat, Shipyard, Engineering. I checked the existing globe surface strip and `ui_swipe_arc`. Neither bakes in a 72° step (the arc just follows the globe radius), so nothing needed re-exporting. The **tunnel sits on the Mine stop**, in the foreground in front of the tower: tunnel x = tower x + 115, hopper at tower x + 10.

## Packs (manifests in `../packs/*.json`, listing files and bytes per scale)
| pack | @3x | @2x |
|---|---|---|
| mine_preview (one static image; @3x file 780 px wide, @2x 520 px) | 0.11 MB | 0.07 MB |
| mine_starter (Rover Bay + tiers, rover, tunnel, hopper, Pt + He-3 containers, pop-ups) | 2.12 MB | 1.27 MB |
| mine_later_crusher | 0.63 MB | 0.39 MB |
| mine_later_separator | 0.59 MB | 0.38 MB |
| mine_later_packing | 1.02 MB | 0.40 MB |
| mine_later_penthouse | 0.71 MB | 0.43 MB |
| supply_depot | 0.24 MB | 0.15 MB |
| dock (own station, see DOCK_SPEC) | 2.24 MB | 1.33 MB |
Load order: mine_preview → mine_starter → mine_later_* as each floor unlocks. The hero renders are excluded from the packs.

## Floor tiers (`floors/tiers/floor_mine_{rover_bay,crusher,separator,packing}_t{10,20,30,40,50}`)
They use the same layered format and draw order as ../floors/tiers (base → t10 → … cumulative, anchored at floor origin (0,0), 360x120). Static tiers have `layers: []`. Use the same tier-up sequence as ART_SPEC.
- **Rover Bay:** L10 steel trim + charging bay 3; L20 extra lights + auto-guide lane lamps; L30 grizzly pre-screen over the hopper + 2nd conveyor; L40 fusion charger core; L50 gold trim + GOLD FLEET plate + mastery badge.
- **Crusher:** L10 VFD drive cabinet; L20 dust hoods + lights; L30 HPGR roll press; L40 sonic jaw with resonance waves; L50 gold.
- **Separator:** L10 2nd burner; L20 He-3 tank #3 + lights; L30 2nd magnetic separator + flowing gas line; L40 plasma kiln glow with cyan containment rings; L50 gold.
- **Packing:** L10 QC camera; L20 2nd packer arm R-7 + lights; L30 auto-stacker tower; L40 armor-wrap field; L50 gold.
Preview: `mine_tiers.png`. Size added: 0.81 MB @3x / 0.55 MB @2x.

## Bundle size
Whole mine/ folder: 5.44 MB @3x, 3.11 MB @2x (including tiers, preview and Supply Depot). The dock is separate: 2.24 / 1.33 MB.

## Previews
`mine_mockup.png` (two phone screens side by side: `mine_mockup_stop_mine.png` and `mine_mockup_stop_dock.png`), `mine_mockup_pad_closeup.png`, `mine_mockup_foreground_closeup.png`, `loaded_box_hero.png`.
Scripts: /workspace/artgen/mine/ (rover.py, box.py, mfloors.py, penthouse.py, scene.py, ship4.py, ship_export.py, mockup2.py; pad.py/mockup.py are the old ones; run them from that folder).

Masters: every frame of every box and rover sheet is saved in `_masters/{box,rover}/<sheet>_NN.webp` (6x lossless).

## Cargo types (`box/`, both 28x24, pivot (14,24); the same 4 sheets each)
- **Platinum crate** = the LOADED box (`loaded_box*`), now labelled `Pt`.
- **Helium-3 canister** (`he3_canister`, `he3_canister_pulse` 12f loop, `he3_canister_sealed` 16f one-shot, `he3_canister_stack3` 58x46 pivot (29,46), `he3_canister_hero_3x`). It is a horizontal pressure cylinder in a steel cradle frame, mainly blue, with a window showing a **glowing blue core** (it breathes with the pulse). Violet appears only as thin trim (the band rings and valve collar). It has a green LED at (23.8,16.3), a LOADED stencil, an `He-3` tag and blue hazard stripes. In `sealed`, the valve cap drops and the clamps close, then the LED turns from amber to green with a flash while the core ramps up. All masters are saved per frame. Preview: `he3_canister_hero.png` (with a size comparison against the Pt crate).

## Extra pop-up icons (`fx/`, the same format as ../fx/pickup_*: 20x20, pivot (10,10), 8f @12 loop + `_sparkle` 32x32 6f one-shot, same rise tween)
`pickup_ore_spin` (regolith chunk with platinum glints and a blue He-3 fleck), `pickup_miner_spin` (orange mining helmet with headlamp and a green + badge = population/miner gain), `pickup_refined_coin_spin` (gold coin with a cyan refined ring and an "R" hex; use it for refined-cargo income).

## SUPPLY DEPOT (`floors/floor_market*`, 360x120, pivot (0,120), layered 16f @12 loop + `floor_market_lowpower`)
This replaces the Market floor's look. It lives in mine/@3x/floors/; the old ../floors/floor_markets is untouched (the code should point at this file). It has 3 pallet racks of Earth crates (`FROM EARTH · LEO-7`), a forklift drone shuttling a crate with its mast lifting, an inbound conveyor, `DOCK 2`, a manifest screen and a bay-fill screen, and a lit `SUPPLY DEPOT` sign in the header (label DEP-05, accent blue #5ab4ff). There are no prices or coins.

## Rover Bay v2: side-wall cutout garage (supersedes the earlier Rover Bay and bin sections)
- Floor `floors/floor_mine_rover_bay` (layered, 360x120, 16f@12fps, plus lowpower).
- Left wall has a bay cutout at x 0–68, y 42–104. It shows the exterior through the opening, wall thickness (inner jamb face and soffit), a header beam with the rolled-up door drum, a door guide rail, AO, an amber beacon and an orange ROVER BAY sign.
- Two sunk dump pits with a cutaway front:
  - PLATINUM (silver): x 118–192.
  - HELIUM-3 (blue): x 206–280.
  - Rim at FY−3.
- Labels are 10 px heavy stencil on dark plates. They sit on the back wall with baseline y=46, above the rover's highest point (the raised bed tops out near y≈52), so a dumping rover never hides them.
- Icons sit at y≈22: a Pt hex and a He-3 atom.
- `floors/bin_fill_{pt,he3}`: 5 frames (0/25/50/75/100%), attachToFloor (pit x, 104), 74x16. Draw after the floor base and before the rover.
- `rover/rover_bay_dump`: 38 frames @12fps, rover only (90x58, pivot (0,58) = rear-bottom). Covers tilt up, pour and lower.
- `rover/rover_bay_route.json`: per-frame x, tilt, bob and segment for the Pt pit. For He-3, add binX.he3 − binX.pt.
- Timings (s, 12 fps, eased, low-g):

  | step | time (s) | motion |
  |---|---|---|
  | enter | 0–1.8 | ease-out from x −96 to 262, dust |
  | settle | 1.8–2.3 | decaying 1.6 px bounce |
  | reverse | 2.3–3.9 | ease-in-out to binX−4 |
  | settle | 3.9–4.3 | |
  | tipUp | 4.3–5.5 | 0→38° |
  | pour | 5.5–6.5 | |
  | tipDown | 6.5–7.4 | |
  | exit | 7.4–9.0 | reverse out to x −110, ease-in, dust |

- Use rover_drive for the drive and settle steps; play its wheel spin backwards when reversing.
- Rover tint: 0.45 outside, ramping to 1.0 inside over x −40..60.
- Previews: `rover_bay_closeup.png` and `rover_bay_sequence.png` (7 frames).
- Tiers (`floors/tiers/floor_mine_rover_bay_t10..t50`):
  - L10: lane LEDs plus BAY 3 charger.
  - L20: floods plus door strobes (AUTO-GUIDE).
  - L30: grizzly screens on both pits plus a vibrator.
  - L40: FUSION CHARGER glow on the charger.
  - L50: gold trim plus GOLD FLEET.
  - Nothing overlaps the labels or the rover lane.

## Cave v3 (`tunnel/tunnel_back` 12f@12fps, `tunnel_front_lip`)
- Canvas 260x130, pivot (0,70) = left end of the ground line.
- The ramp runs (20,70)→(170,118), which matches the `rover_tunnel` geometry.
- Pieces:
  - outcrop with layered strata
  - ribbed steel portal with shotcrete, rock bolts and mesh, and a hazard-striped ADIT-2 header
  - 5 work lights receding inside, plus rail, vent duct and cables
  - spoil piles, boulders and tracks
  - control shack with amber beacons, plus drifting dust haze
- The front lip still occludes the lower ramp. Preview: `tunnel_closeup.png`.

## Rover Bay v3 — single ORE BIN, right-wall entry, labelled trucks (supersedes v2 pits/labels)
- Floor `floors/floor_mine_rover_bay` (layered) + lowpower. ORE BIN on the LEFT x 14–98, top y 80; entry cutout moved to the RIGHT wall (x 292–360, same depth/jamb/header/AO/beacon, exterior matches world). Charger x 196–226. No wall pit labels.
- `floors/bin_fill_ore` 5 states (0–100 %), 84x18, attachToFloor (14,68); Pt-silver / He-3-blue strata.
- Trucks: `rover/truck_{pt,he3}_drive` (8f loop) and `rover/rover_bay_dump_{pt,he3}` (16f, 2.7–5.8 s, fps 5.16; rover sheets q86). `rover/rover_dump` (old outdoor hopper) is no longer in mine_starter. Bed labels PLATINUM / HELIUM-3 solid bold white on dark plate, cap height ≈ 11 px @3x; Pt load silver, He-3 load blue.
- `rover/rover_bay_route.json` (12 fps): reverseIn 0–2.2 (ease-out, x 372→binX 74) · settle 2.2–2.7 (low-g bounce) · tipUp 2.7–3.9 (0→38°) · pour 3.9–4.9 · tipDown 4.9–5.8 · settle2 5.8–6.1 · driveOut 6.1–7.9 (ease-in forward to x 372). Tint 0.45 at x>330 → 1.0 at x<220; redraw the right jamb strip over the truck while x+90>292.
- Tiers: L10 lane LEDs + BAY 3 charger (x140) · L20 floods + door strobes (x288) · L30 grizzly on bin mouth + vibrator · L40 FUSION CHARGER on charger · L50 gold.
- Crispness: tunnel base/layers/lip exported q95, haze moved to its own soft sprite `tunnel/tunnel_haze` (draw over lip); closeups are now 1:1 @3x from exported files with a 2x nearest zoom.
- Polish (00:50): pour stream now ends at the ORE BIN mouth (floor y 80) with a dust puff. Tunnel uses labelled trucks: `rover/rover_tunnel_{pt,he3}` (16f @8fps; descend 0–7, emerge 8–15; pivot (45,58); same ramp path). Old `rover_tunnel` removed. `rover/rover_drive` and `rover/rover_dump` are superseded by the truck sheets and excluded from mine_starter (files kept).
