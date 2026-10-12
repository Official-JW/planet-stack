# Planet Stack — Moon Art Pack (v1)

All art is drawn in code (SVG → PNG/WebP) by `/workspace/artgen/*.py`. Rerun a script to regenerate.
**Every image is exported at 3x.** Divide pixel sizes by 3 to get logical (1x) points, or set the texture resolution to 3.
Every sprite sheet is a single horizontal strip with a matching `.json` atlas (TexturePacker-style "hash": `frames`, plus `meta.fps`, `meta.pivot` in logical px, `meta.logicalFrame`, `meta.loop`).
Pivots are given in logical px from the top-left corner of a frame.

## 1. Background (`bg/`), 390 × 844 logical, 1170 × 2532 px unless noted
Layer order, back to front, with parallax as a fraction of camera movement:

| # | File | Size | Parallax | Notes |
|---|------|------|----------|-------|
| 1 | `sky.webp` | full screen, opaque | 0.0 | Deep navy gradient with a faint nebula band. |
| 2 | `stars.webp` | full screen, alpha | 0.05 | About 420 small stars. |
| 3 | `stars_twinkle.webp` | full screen, alpha | 0.05 | 26 bright cross-glint stars. Loop the alpha 0.35 → 1 → 0.35 over 2.4 s (sine). For variety, run a second copy flipped horizontally and half a cycle out of phase. |
| 4 | `earth.webp` | 120 × 120 logical (360 px) | 0.1 | Earth with its glow. Mockup position: top-left corner at (40, 90). Optionally drift it by ±2 px over 20 s. |
| 5 | `globe.webp` | full screen, alpha | 0.3 | **The Moon globe.** v2 adds layered craters with central peaks, ejecta rays, scattered rocks with shadows, darker maria and a terminator shadow on the right. A circle of radius 760 centred at (195, 1320), so its top (the horizon) sits at y = 560, the bottom third of the screen. It includes the craters, shading, the bright rim line and a soft blue atmosphere glow. Use it on its own as the static version. |
| 5b | `globe_surface_strip.webp` | 1200 × 160 logical (3600 × 480 px), opaque | — | **Rotating surface.** It tiles seamlessly left to right, and its top edge is the horizon. To fake rotation, bend it along the arc (radius 760, centre (195, 1320)) with a mesh or rope, clip it to the globe circle and scroll its U offset at about 6 px/s. Then draw `globe_shade.webp` on top. |
| 5c | `globe_shade.webp` | full screen, alpha | same as 5 | Lighting overlay for 5b: edge darkening, rim line and glow. Use 5b + 5c **instead of** 5. |

## 2. World pieces (`world/`)
- `tower_base.png`: 372 × 39 logical (1116 × 117 px), pivot (186, 39). This is the footing where a tower meets the globe. Its top edge is flat, so the bottom floor sits on y = 0..4. Its bottom edge is an arc of radius 760, so it hugs the globe. Put the bottom-centre on the horizon point, then raise it about 25 px so the footing's middle meets the surface. Draw it **in front of** the globe and **behind** the lowest floor's slab.
- `site_marker.png`: a 4-frame sheet, 120 × 90 logical per frame, 6 fps, looping, pivot (60, 90). It shows a locked building site: a dashed outline, a "+", two traffic cones and a blinking orange beacon. Optionally pulse it at a scale of 1.0 → 1.03 every 1.6 s to invite a tap.

## 3. Floors (`floors/`) — v2 polish, 360×120 logical (1080×360 px), pivot (0,120) bottom-left
Per floor: `floor_<name>.png` (static), `floor_<name>_anim.png`+`.json` (**8 frames @ 8 fps, loop**, laid out in a 3-column grid — always read frame rects from the JSON), `floor_<name>_needs_stock.png` (dimmed + empty-crate icon; crossfade 0.25 s).
Every floor now has: textured/grimy back wall with panel seams and rivets, ceiling conduit with drooping cables and a room-code plate (O2-01, H2O-02, PWR-03, HAB-04, MKT-05, MED-06, CAF-07), ceiling light cones with bloom and a slight flicker, drifting dust motes, ambient occlusion on all edges, glass reflections, scan-lined screens, a cable tray (power, data and coolant colour codes), floor plates, and an exterior truss frame with a cool rim light on the left edge.
| name | moving parts |
|---|---|
| `oxygen` | Equipment: two PEM electrolysis stacks, colour-coded O₂ and H₂ lines, gas manifold A with pressure gauges and valves, a Sabatier reactor (CO₂+4H₂→CH₄+2H₂O), LOX and O₂ storage tanks with level bars, a status screen, a maintenance hatch and a breaker panel. Animation: Sabatier heater glow, manifold valves turning, gauge needle, tank levels, status LEDs, vent steam. |
| `water` | Equipment: a regolith-ice feed hopper with an auger, a 450 °C extraction oven, a 5 µm cartridge filter skid, distillation column DIST-1, clear potable and grey-water tanks with scale marks, flow meter FT-201, a water-loop screen and valves. Animation: the auger turning, oven glow, the column level, tank waves and bubbles, the flow reading, steam. |
| `nuclear` | Equipment: a Kilopower-style 10 kWe fission unit with a shield cone, a visible core and heat pipes to a 40 kWt radiator array, two Stirling converters, a CAUTION RADIATION AREA placard, a control-rod readout (k-eff, core temperature, kWe, SCRAM READY), breaker switches and battery strings B1–B3. Animation: core pulse, radiator heat tint, Stirling rotors, rod bars, battery charging, sparks. |
| `living_quarters` | Equipment: four chamfered sleep pods (P1–P4) with reading lights, occupancy LEDs and glass fronts, orange handholds, a galley (cabinets, food warmer with a timer, a 22 °C water dispenser, MRE packs), a porthole with Earth, an exercise band and lockers L1–L3. Animation: a rising "z", pod lights, warmer glow and countdown, warmer steam, the band flexing. |
| `markets` | Equipment: hydroponic racks HYDRO-A and HYDRO-B with grow LEDs (lettuce, tomatoes, herbs), drip lines, sealed-ration shelving, a checkout kiosk with tap-to-pay, a chilled 4 °C display case and a price board. The sign now reads "LUNAR MARKET". Animation: sign flicker, grow-light pulse, drips, the price total, pendant lamps. |
| `hospital` | heart-rate monitors, blinking cross |
| `moon_cafe` | espresso steam, steam from table cups, sign flicker, pendant lamps |
Walkable line: **y = 104** inside each floor. Stack floors at exactly 120 px pitch.

**Penthouse** `penthouse_control(.png/_anim)`: 360×180 logical (1080×540 px), pivot (0,180), **8 frames @ 8 fps**. Top 60 px is a glass dome with 7 framed ribs, two ring braces, rib lights, a beacon at the apex, a sweeping glass glint and a swinging dish antenna; bottom 120 px is the control room (radar sweep, scrolling bars, console lights).

## 4. Astronaut (`astronaut/`) — v3 EVA suit, **32×44 logical (96×132 px), pivot (16,44) at the bottom centre**, facing right (mirror for left)
The suit has a hard upper torso, a life-support backpack with vents and green/blue status lights, a gold-tinted visor with reflections, a helmet light pod, a chest control unit with a small display, joint rings at the knees and elbows, fabric fold shading, boots with treads, and role accent stripes on the shoulder, backpack, helmet and gloves.
| file | frames | fps | notes |
|---|---|---|---|
| `astronaut_walk` | 8 | 12 | walk speed ≈ 30 px/s |
| `astronaut_idle` | 8 | 6 | breathing; the chest display blinks |
| `astronaut_carry` | 8 | 12 | He-3 canister held in front |
| `astronaut_push` | 8 | 12 | **frame is 52×44**, pivot still (16,44); the dolly sticks out to the right |
Role variants have the same frames and differ only in accent colour:
- `astronaut_*`: worker, orange
- `astronaut_engineer_*`: blue
- `astronaut_medic_*`: green

The feet stand on the floor's walk line (y=104). The astronaut is now 44 px tall, about 37% of a floor's height.

## 5. Coin (`fx/`)
- `coin_spin`: 6 frames, 20×20 logical, 12 fps, loop, pivot (10,10).
- `coin_sparkle`: 6 frames, 32×32, 12 fps, once, pivot (16,16).
- Motion: rise 40 px over 0.6 s (ease-out cubic); scale 0.6→1.1 in 0.25 s (ease-out back) then 1.0 by 0.4 s; alpha fades to 0 over the last 0.2 s.

## 6. Cargo ship (`ship/`) — v3 realistic starter ship, about 2 floors tall
The ship is a tall, slim stainless-steel cylinder with an ogive nose. It has no logos or branding.
- `ship.png`: **160×240 logical (480×720 px)**, pivot (80,240) at the bottom centre, 2 frames at 2 fps (red and green nav lights blink).
  - The body is 38 px wide and made of brushed steel, with weld seam rings, faint dents and vertical reflections.
  - The left (windward) side carries charcoal hex heat-shield tiles.
  - It has two small forward flaps near the nose and two larger aft flaps at the base.
  - There's a row of 4 small windows and an outlined cargo door.
  - Lighting: a cool rim light on the left from Earthshine and a warm edge on the right.
  - Underneath: an aft skirt, five visible engine bells (part of a 3 centre + 3 outer layout) and short lunar landing legs.
- `ship_damaged.png`: same size, 4 frames at 6 fps. It shows scorched steel, clusters of missing tiles (bare steel showing through), a crack in the cargo door, smoke, sparks and a flickering red warning light.
- `ship_flame.png`: 80×150, 8 frames at 16 fps, looping, pivot (40,0). It's a blue-white methalox flame: translucent blue engine cores with Mach diamonds inside a pale plume. **Put its top-centre on ship point (80,216)** and draw it behind the ship.
- `smoke_plume.png`: 320×110, 10 frames at 12 fps, plays once, pivot (160,110). A grey regolith dust plume for engine start.
- `dust_puff.png`: 160×50, 6 frames at 12 fps, plays once, pivot (80,50). Plays on touchdown.
- `launch_pad.png`: 220×44, 4 frames at 2 fps (red edge beacons), pivot (110,44). A steel grated deck on lattice legs over a flame trench. **The ship's pivot goes at pad point (110,8).**
- `launch_tower.png`: 120×250, 2 frames at 2 fps (beacon and arm LED), pivot (101,250) at the tower's base. It's a steel lattice tower with a truss quick-disconnect (QD) arm and hoses reaching left. The arm's tip is at x=6, y≈96–108. Place the tower on the ground so the tip touches the hull: tower pivot x = ship centre + 19 + 95. In the mockup, the pad centre is at 510 and the tower pivot at 624, with both bottoms on the same ground line.
- **Launch:** retract the QD arm (rotate it away, or slide it right 30 px over 0.3 s). Then the ship squashes and shakes on the pad for 0.4 s (scale Y 1→0.97→1 and ±1 px jitter), with `smoke_plume` playing and the flame on. Then it rises off the top of the screen with ease-in (quad) over 1.5 s.
- **Landing:** it drops in with ease-out (cubic) over 1.8 s with the flame on, and the flame fades out over the last 0.3 s. On touchdown it squashes to scale Y 0.97 for 80 ms, bounces 3 px and plays `dust_puff`. Then the QD arm swings back in.
- **Offline return:** set the ship on the pad and play only `dust_puff`.
- (The old `launch_gantry.png` was replaced by `launch_tower.png`.)

## 7. Cargo (`cargo/`), bonus
- `he3_canister_raw` / `he3_canister_refined`: 4 frames, 20 × 28, 6 fps, looping, pivot (10, 28). The raw canister is frosty and dim. The refined one glows bright blue and pulses (one cycle about every 0.67 s; for a slower 1.5 s pulse, play at 2.7 fps).
- `pt_crate_raw`: 1 frame, 26 × 22, pivot (13, 22). Gray ore in a mesh cage.
- `pt_crate_refined`: 6 frames, 26 × 22, 10 fps, pivot (13, 22). An armoured crate with a silver shine sweep. Play it once every 2 s.
- **Lock-in:** the container slides into the hold, drops 2 px, shakes ±1 px for 0.12 s, and shows a white flash ring (draw it in code), with a clunk and a pop.

## Previews
- `contact_sheet.png`: every file in the pack.
- `mockup.png`: a full phone screen at 1170×2532. The world (tower and pad) is drawn at 0.56 zoom so the tower and ship fit side by side. It shows the curved globe, Earth, the tower (penthouse, Markets, Living Quarters and Oxygen on the tower base), the ship on its pad with the gantry, astronauts and a coin pop. At 1.0 zoom the camera would scroll.

## Palette
- Moon and steel: #2a3245 (outline), #3a4258, #5b667e, #8794ad, #c9d3e6
- Sky: #05070f → #2b3a5e
- Tappable or warm: #e8701a → #ffb04d
- Tech glow: #3ad0ff / #7ff3ff. OK: #6ee08a. Alert: #f25f5c


## Design language for floors (v3)
Equipment is based on real lunar-base engineering: PEM electrolysis, the Sabatier reaction, ISRU ice extraction, distillation, Kilopower and Stirling units, hydroponics. It uses chamfered panels and one consistent labelling system: a white tag with an orange bar for equipment IDs, blue for water and O₂, and yellow hazard tags. It also has cable trays, maintenance hatches and functional lighting. The hospital and Moon Café floors still use the v2 drawings and don't have the v3 engineering redesign yet.

## Colour pass (v4)
Each floor now has its own accent colour: an LED strip along the ceiling and the floor, pulsing status lights, warmer ceiling lights and +15% saturation.
| Floor | Accent | Wall tint |
|---|---|---|
| Oxygen | cyan/teal #2fe0d0 | teal-grey |
| Water | blue #3a9cff | blue |
| Nuclear | amber #ffb020 | neutral grey, with green and amber control-rod readouts |
| Living Quarters | soft orange #ff9a50 | warm, with a wood wainscot |
| Markets | green #7be05a | green-grey |
| Hospital | cyan #7ff3ff | (no wall tint change) |
| Moon Café | warm orange #ffb347 | (no wall tint change) |
