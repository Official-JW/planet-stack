# Planet Stack — Moon Art Spec (v4, @3x/@2x)
All sizes are **logical points**. Pick set by DPR: `@3x/` if devicePixelRatio>2, else `@2x/` (see BLUR_FIX.md). WebP q92, alpha q100, no palette. Atlas pages ≤2048 px (full-screen bg images 1170×2532 are single images). `_masters/` = 6x lossless sources, never ship. Old top-level folders (floors/, ship/, astronaut/...) are legacy and are kept only until game.js switches over.

## Atlas JSON (sprite sheets)
`meta: {images:[pages], scale, fps, logicalFrame:{w,h}, pivot:{x,y}, loop}`; `frames: {name_i: {page, frame:{x,y,w,h} (px), duration}}`. Draw: `drawImage(page, fx,fy,fw,fh, x-pivot.x, y-pivot.y, logicalW, logicalH)`.

## Layered floors (360×120, pivot (0,120))
`floors/floor_X.webp` = static base. `floor_X.json`: `{base, layersImages, scale, logicalSize, pivot, fps:12, frames:16, loop:true, layers:[{x,y,w,h, frames:[{page,x,y,w,h}]}]}`. Each frame: draw base, then each layer's frame i at (x,y). 16-frame seamless eased loop @12 fps (steam curls, liquid sloshes, eased lights, motion-blur fans). Floors: oxygen, water, nuclear, living, markets, hospital, cafe; penthouse_control.

## Floor tiers (Oxygen Plant done; others to follow)
`floors/tiers/floor_oxygen_t{10,20,30,40,50}` (same layered format, transparent base), anchor floor origin (0,0), same 360×120. Draw order: base → t10 → t20 → … up to current tier (cumulative). L10 steel trim + 2nd electrolysis tank; L20 CO₂ scrubber wall; L30 industrial pipes with flowing bubbles; L40 glowing O₂ core; L50 gold trim, gold dome, mastery badge. Preview `oxygen_tiers.png`.
**Tier-up sequence (total 1.6 s):** 0 ms fx/fx_tierup_flash_rays (360×160, pivot (0,160), 16f @20fps) starts; 0–120 ms white flash (in sheet); 150 ms new tier layer drops from y−24 with alpha 0→1, 260 ms, easeOutBack(1.7) (bounce); 300 ms tier banner (fx/tier_banner_l{lv}, 220×44) scales 0.6→1.08→1 (250 ms) centred above floor, holds 900 ms, fades 200 ms; L50 only: fx/fx_gold_shimmer loops ×2 over the floor.

## Elevator (`elevator/`)
Shaft 40 wide on the tower's right: floors 360 + shaft 40 = 400; scale tower group ≈0.93. Footing: `world/tower_base_400` (412 wide, pivot centre-bottom (206,h)), replaces the 372 footing. Pieces: shaft_tile 40×120 (one per floor), shaft_top 40×30, shaft_pit 40×24, cable_tile 4×120 (centre x=20; maglev looks use maglev_glow 8f instead), call_panel 10×16 (2f, at shaft x=2,y=60 per floor), floor_indicator 12×6 (2f).
Car 34×56, pivot (17,56): draw car_{look}_back, riders, then car_{look}_doors frame (0 closed…7 open). Looks: cage L1, steel 10, glass 20, maglev 30, cargo 40, panorama 50, hauler 60, twin_deck 70, neon 80, platinum 90, gold_express 100. Riders (rider 9×16): 1–3 silhouettes standing on car floor y=52 (x=8,13,18 offsets); capacity >3 → show 2 riders + capacity_badge 16×10 at top-right with the number.
**Tween:** travel easeInOutCubic, 220 ms + 90 ms per floor; on arrival 2 pt settle bounce (overshoot down 2 pt, back over 160 ms, easeOutBack); doors open 150 ms after arrival (8 frames @24 fps = 333 ms); hold; close in reverse before departure. Tier-up: fx/fx_elevator_tierup (40×240, 16f) over the shaft. Preview `elevator_preview.png`.

## Astronaut (32×44, pivot (16,44))
walk/carry/push: 12 frames @14 fps with weight shift and low-g bounce; idle 8 @8 fps; wave 10 @12 fps (0–1 raise, 2–7 wave, 8–9 lower, not looped). Roles: worker (default), _engineer, _medic (walk/idle/carry/push).

## Collect pop-ups (economy)
Coins (fx/coin_spin + coin_sparkle) **only** for Markets, Hospital, Club, stipend, cargo. Life-support floors pop resources: fx/pickup_o2_spin (Oxygen), pickup_water_spin (Water), pickup_energy_spin (Nuclear), pickup_people_spin (population gain). All 20×20, pivot (10,10), 8 frames @12 fps loop, each with a matching pickup_*_sparkle (32×32, 6f, one-shot).
Tween (same for coin and resources): spawn at floor tap point, rise 28 pt over 600 ms easeOutCubic, scale 0.6→1.1→1 in the first 180 ms, fade out the last 150 ms; on tap or arrival at the HUD meter, play the sparkle and tick the meter.

## Low power
fx/floor_low_power (360×120, pivot (0,120), 16f @12 fps loop): dark overlay with irregular flicker plus a red top strip, drawn over floor and tiers; pause floor ambient layers. fx/icon_low_power_blink (24×24, 8f @8 fps, pivot (12,24)) at floor (340,22). UI icon ui/ui_icon_low_power.

## New resident arrives (first 30 s; high priority)
Assets: elevator car doors (or the airlock), fx/fx_door_hiss (48×32, 8f @16 fps, pivot (2,30) at door edge, flip X for the left side), astronaut_walk, astronaut_wave, fx/pickup_people_spin, fx/coin_spin, fx/fx_welcome_sparkle (64×64, 12f @20 fps, pivot centre).
| t (ms) | event |
|---|---|
| 0 | Car arrives (settle bounce) or airlock lights up |
| 150 | Doors open (8f, 333 ms) + fx_door_hiss at the door edge |
| 400 | Astronaut walks out 18 pt over 500 ms (walk @14 fps), easeOut |
| 900 | Switch to astronaut_wave (10f @12 fps = 830 ms), facing camera |
| 950 | fx_welcome_sparkle centred on the head (y−48) |
| 1000 | pickup_people_spin rises from y−50, 30 pt over 700 ms easeOutCubic, scale 0.6→1.1→1 |
| 1150 | coin_spin (stipend) rises 10 pt to the right, same tween |
| 1600 | Icons fade over 200 ms; HUD people and coin meters tick up (400 ms) with pickup sparkles |
| 1730 | Wave ends → idle, then walk to the assigned floor; doors close |

## FX
fx_collect_sparkle 48×48 12f @24; fx_upgrade_burst 160×160 16f; fx_floor_unlock 360×120 16f pivot (0,120), drawn over the new floor; fx_tierup_flash_rays; fx_gold_shimmer; fx_elevator_tierup; fx_door_hiss; fx_welcome_sparkle.

## Ship and world
ship/ (160×240, flame attached at (80,216), smoke, dust), launch_pad (ship pivot at pad (110,8)), launch_tower 120×250 pivot (101,250). bg/ globe, sky, stars, stars_twinkle, globe_surface_strip. cargo/.

UI: see UI_SPEC.md.
