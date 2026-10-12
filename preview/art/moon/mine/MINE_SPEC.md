# Planet Stack: Helium & Platinum Mine (building 2) art spec
Sizes are in logical points. Use `@3x/` when devicePixelRatio > 2, otherwise `@2x/`. Images are full-colour WebP (q92, alpha q100, no palette reduction). `_masters/` holds 6x lossless sources (never ship these). Atlas JSON uses the same format as ../ART_SPEC.md: `meta{images,scale,fps,logicalFrame,pivot,loop}`, `frames{name_i:{page,frame,duration}}`. Accent colour: amber #ff9a2a. He-3 is violet #c8a6ff, and LOADED/OK is green #39ff6a.

## Rover (`rover/`, 90x50, pivot (45,50) bottom centre, faces right; flip X for leftward)
| sheet | frames | fps | loop | notes |
|---|---|---|---|---|
| rover_drive | 14 | 12 | yes | wheels turn 120°/loop, suspension bob ±0.8, low-g dust behind the wheels, empty bed |
| rover_scoop | 16 | 12 | no | front arm lowers (f0–6), digs with a dust puff (f5–10), lifts; the bed fills 30%→100% |
| rover_dump | 16 | 12 | no | bed tips 0→36° (f0–6), pours out the rear (f4–11), dust cloud, lowers (f12–15) |
`rover_static` = drive frame 0. The headlight beam and red tail lamp are baked in.

## Rover path and dump timing (game logic)
The ground is the surface line at the Rover Bay door. The rover leaves `SURFACE LOCK A` (the left of the bay, floor x≈10–106) and drives outward with drive @12 fps at 24 pt/s for 3 s. It plays scoop (1.33 s) at the dig site, turns (flip X), and drives back. It reverses so its rear is over `pad/surface_hopper` (60x40, pivot (30,40)), with the rover pivot about 58 pt right of the hopper pivot. Then dump plays: 0 ms start tilt; **330 ms material pours** (spawn the ore tick or hopper fill); 920 ms pour ends; 1330 ms done. Then it drives back to its charging bay. Total loop ≈ 10 s at speed 1. Inside the bay floor, the parked rover is baked into the static art.

## Floors (`floors/`, 360x120, pivot (0,120), layered format exactly like ART_SPEC)
`floor_mine_{rover_bay,crusher,separator,packing}.webp` (static base) + `.json` / `_layers.webp` (16-frame seamless loop @12 fps) + `floor_mine_X_lowpower.webp` (dimmed/desaturated with a red top strip; pause the layers while low power, and the shared fx/floor_low_power can be drawn over it). Labels: MIN-B1, 02, 03, 04. Order from bottom: Rover Bay (garage door, intake hopper with ore, rotary feeder, conveyor, 2 charging bays), Crusher (jaw crusher + flywheel, cone crusher, conveyors, dust), Separator (glowing 700 °C kiln drum, gas line to 2 He-3 tanks, magnetic drum flinging platinum glints), Packing (overhead robot arm, conveyor of boxes whose LEDs turn green after sealing, outbound stack).

## LOADED box (`box/`, 28x24, pivot (14,24))
- `loaded_box` static; `loaded_box_pulse` 12f @12 fps loop = 1.0 s LED cycle (cosine ease).
- `loaded_box_sealed` 16f @12 fps one-shot: lid lowers (f0–4), latches swing shut (f4–8), the amber LED turns green with a flash (f8–10), then settles.
- `loaded_box_stack3` 58x46, pivot (29,46), 12f loop with the 3 LEDs out of phase.
- `loaded_box_hero_3x` (a 3x-larger render, 84x72 logical) + `_masters/box/loaded_box_hero_36x.png`.

## Mine-side launch pad (`pad/`)
`mine_pad` 180x36, pivot (90,36), 12f @12 fps loop (beacon lamps). Rough dusty plate with a scorch ring. **The ship (ship/ship 160x240, pivot (80,240)) stands at pad-local (62,10).** The box stack zone `CARGO STAGE` is pad-local x 118–172, deck y=10 (draw stack3 pivot at about (147,10)). `mine_pad_static` and `surface_hopper` are also provided.

## Previews
`mine_mockup.png` (390x844 @3x, with a zoomed inset of the surface), `loaded_box_hero.png`.
Scripts: /workspace/artgen/mine/ (rover.py, box.py, mfloors.py, pad.py, mockup.py; run them from that folder).
