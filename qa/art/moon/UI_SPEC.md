# Planet Stack — UI Spec (Upgrade sheet, HUD, hints)
Assets: `@3x/ui/` and `@2x/ui/` (WebP q92). Nine-slice insets in `ui/ui_kit.json` (logical pt). Mockup: `upgrade_menu_mockup.png`.

## Type
- Labels/body: **Inter** 500/600, 14 pt (rows), 11–11.5 pt (captions, tracking .6).
- Numbers/buttons: **Rajdhani** 700, 16 pt values, 19 pt "UPGRADE" (tracking 1). Rajdhani has no ₂: render subscripts as smaller text offset +1.5 pt.

## Colour
bg #0d1424 · edge #5fd4ff · cyan #3ad0ff · amber #ffb347 · orange #ff8a2a · green #5be08a (gains) · text #eaf2ff · dim #8fa3c4 · red #ff6a5a (can't afford) · rows #0b1426 stroke #2c3d62.
Resource colours: O₂ #2fe0d0/#7fe0ff · water #3a9cff · energy #ffd23a · people #eaf2ff · coin #ffc83a.

## Layout (390 pt wide screen)
Sheet top y=384, top corner radius 24, grabber 40×5. Outer padding 20. Stat rows 350×44, radius 12, gap 8. Hire row 56 high, radius 14. Toggle 132×56 radius 16; Upgrade button 206×54 radius 16. Progress track 350×14 radius 7, pips every 10 levels (diamond 14).

## Stat rows by floor type (economy)
Life-support floors produce resources, not money:
- Oxygen Plant: `Supports 12 people → 15` (ui_icon_people), `O₂ output 2.4 → 2.6 kg/h`, `Crew 3/4`.
- Water: Supports N people; Water output. Nuclear: Energy output (ui_icon_energy); Supports N floors.
- Money (ui_icon_coin / income rows) only for Markets, Hospital, Club, stipend, cargo.

## Icons (24 pt)
ui_icon_ coin, oxygen, water, energy (bright meter bolt), power, food, people, worker, income, lock, low_power (warning triangle).
HUD resource meters use: oxygen, water, energy, people, coin.

## Animations
- Sheet open: translateY 100%→0, 280 ms, cubic-bezier(.2,.9,.3,1); scrim 0→.35 alpha 200 ms. Close: 200 ms ease-in.
- Button press: scale .96 on down (80 ms ease-out), back to 1 on up (140 ms, cubic-bezier(.3,1.6,.5,1)). Disabled: no scale, ui_btn_primary_disabled.
- Affordable glow: ui_btn_glow alpha .35↔.8, 1.6 s ease-in-out loop.
- Number tick-up: 400 ms ease-out, integer steps, value scale 1→1.12→1 and colour flash green.
- Level-up flash: white overlay on the sheet header .6→0 over 250 ms, level badge scale 1→1.3→1 (300 ms), fx_upgrade_burst centred on the floor.
- Toggle x1/x10/Max: knob slides 160 ms cubic-bezier(.2,.9,.3,1).
- Progress fill: width tween 300 ms ease-out; reaching a pip swaps ui_pip_milestone → _done with scale 1→1.4→1.

## Swipe-to-rotate hint (one-time)
Assets: ui_swipe_arc (240×60, follows globe arc radius 760, centre it on screen x, 110 pt above the globe horizon), ui_swipe_hand (32×32, pivot fingertip (10,4)).
Tween per loop (1.6 s), ×3, then fade out and never show again (set a flag):
- 0–200 ms: arc + hand fade 0→1.
- 200–1200 ms: hand travels along the arc from 20%→80% of its length (ease-in-out), arc glow alpha .4→1 behind the hand; hand rotates to the arc tangent.
- 1200–1600 ms: hand fades 1→0 (arc stays at .6).
Cancel instantly on the first real swipe.

## Low power state (HUD)
When energy < demand: affected floors draw fx/floor_low_power over everything (12 fps), floor ambient layers pause, and fx/icon_low_power_blink sits at floor (340,22). HUD energy meter turns #ff6a5a and pulses.
