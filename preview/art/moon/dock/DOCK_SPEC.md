# Planet Stack: Cargo Space Dock (globe stop 3) art spec
The same conventions as ../ART_SPEC.md: logical points, @3x/@2x WebP q92 with full alpha, `_masters/` 6x lossless, atlas JSON `meta{images,scale,fps,logicalFrame,pivot,loop}`. Pack manifest: `../packs/dock.json` (2.24 MB @3x, 1.33 MB @2x). It loads when the player first rotates to the dock.

## Stop framing
Fit the 600-wide dock to the 390 screen at ×0.63, so the ship stands about 302 pt tall. Mockup: `../mine/mine_mockup_stop_dock.png`.

## Base dock (`pad/cargo_space_dock`, 600x70, pivot (300,70), deck surface y=20)
It has a flame trench at x 250–350, LOX and CH₄ fuel lines, a tank farm, and two LOADING zones (x 400–480, 500–580) whose labels are 10 pt heavy stencil letters with wide bridges on a dark backing plate. `cargo_space_dock_mini` (180x36) is the old small pad.
- **Neon sign:** `pad/dock_sign_neon_{base|pad_t10|pad_t20}` (200/240/280 x 30, pivot centre-bottom, 8f @8 flicker loop). Mount it centred on the dock front, bottom at deck y + 38. **Swap the width with the pad-size tier.**
- **Ship (4-floor, replaces the 2-floor 160x240 ship):** `ship/ship4_hull` 320x480, pivot (160,480), standing at dock (300,20). Pieces:
  - `ship4_flame` 160x300, 8f @16, pivot (80,0), at hull (160,432).
  - `ship4_engine_glow` 200x90, 4f, additive, at hull (160,440); shown only at ignition and landing.
  - **`ship4_navlights`** 104x24, 2f @2 fps, additive, top-left at hull (108,163); red and green alternate.
  - `dust_puff4`, `smoke_plume4`, `launch_tower4` (240x500, flipped, pivot (38,500), dock x 65).
  - The ship is never animated as a whole.
- **Cranes:**
  - `crane_gantry` 120x200, pivot (60,200), at dock x 430, with `crane_trolley` and `crane_hook_box`/`_empty` (40x40, pivot (20,0), 8f sway). The engine draws the cable.
  - `crane_jib_mast` 40x180, pivot (20,180), drawn ×1.45, at dock x 515, with `crane_jib_boom` 150x20, pivot (10,10), flipped, swinging ±8°.
  - Crane cycle: 6 s (see MINE_SPEC history: down 1.2 s, latch 0.3 s, up 1.2 s, traverse 1.5 s, release 0.5 s, return 1.3 s).
- **Floodlights:** `floodlight_mast` 30x150, pivot (15,150), at dock x 10 and 585, plus `floodlight_cone` 160x160 at 55% alpha, top at mast head.
- **Cargo mule:** `cargo_mule` 64x34, pivot (32,34), 4f, carrying one LOADED box. It hauls boxes from the Mine hopper to the LOADING zones at 30 pt/s.
- **Crew (1.3x):** `crew/crew13_{walk,carry,push,wave}` (walk/carry/wave 42x57, push 68x57; pivot (21,57); walk/carry/push 12f @14 loop, wave 10f @12 one-shot).
  - Six routes on the deck line: carry LOADING↔crane; push tanks↔trench; walk tower↔ship legs; walk crane↔jib; wave by the tower; carry zone 1↔zone 2.
  - Each turns with a 0.6 s pause.

## Upgrade tracks (4 tracks, L1–50, a new look every 10 levels)
Overlay layers are drawn over the base dock, the same idea as the floor tiers (cumulative within a track). Canvas: `tracks/dock_{track}_t{lv}` is 760x620, pivot (380,620), which is the same ground point as the dock pivot. The dock's left edge is at overlay x 80; the deck is at overlay y 570.
- **Draw order:** dock base → crew/refuel/pad overlays → ship → crane overlays → neon sign → sprites.
- **Crane speed:**
  - L10: second gantry G-2 (x 530–630) with work lights.
  - L20: heavy portal crane PC-1 (190 wide, 260 tall) with an operator cab and twin hoists.
  - Planned: L30 rail-mounted ship-to-shore crane; L40 automated twin-jib; L50 gold-trim mastery crane.
- **Crew size:**
  - L10: 4 more astronaut spots (green markers) plus a mule charger (a 2nd `cargo_mule` sprite).
  - L20: crew ready-room module plus a suit rack.
  - Planned: L30 crew rover; L40 forklift drones; L50 gold crew lounge.
- **Pad size:**
  - L10: deck wings +60 each side (720 wide).
  - L20: +80 wings (760) and a blast deck with a landing ring.
  - The neon sign swaps to the 240- and 280-wide versions.
  - Planned: L30/40 heavy-ship cradle and a deeper trench; L50 gold edge lights.
- **Refuel/repair speed:**
  - L10: LOX 2 and CH₄ 2 tanks plus a 2nd GSE fuel line (green).
  - L20: a repair gantry (service tower with 3 arms) and a LOX sphere.
  - Planned: L30 rapid-fill manifold; L40 robotic repair arms; L50 gold.
- **Done so far:** L10 and L20 for all 4 tracks. Preview: `dock_tiers.png`. Size: 0.41 MB @3x / 0.24 MB @2x.

## UI
- `ui/ui_icon_dock_wrench` 24x24 (UI-kit style).
- `ui/ui_btn_dock_wrench` 64x64 (56 icon frame centred).
- `ui/ui_btn_dock_wrench_firsttime` 64x64, 12f @12 loop: an amber ring pulse, a 6% scale breathe and a red "!" badge. Play it until the first tap, then swap to the static button.
