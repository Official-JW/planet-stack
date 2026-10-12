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
