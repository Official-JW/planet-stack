# Planet Stack, TEAM_PLAN v2 (Oct 22, 2026, full 3D)

## Standing rules (unchanged)
- Nothing to do with Feed Shield.
- All art, fonts and sound are original, with no real brands and only permissive open-source code.
- Nothing reaches preview without two passing runs from Playtester, then Jacob's "go."
- Every tag gets posted in the group before anyone runs it, and nobody pushes during a run.

## §Opening (Jacob, 2026-10-22)
Approved by Game Director. This is the target the Mine A loop is built toward.
1. **Landing:** the starter ship touches down on the pad with a crew of 4.
2. **Unload:** the crew unload the Mine and Refinery kits from the ship and set them up, with Eve's Earth Coms walking the player through it. Playtester's requirement: the landing and unload are short or skippable, and the first tappable thing comes within 15 s. Eve's first call can play during the landing.
3. **Mine and refine:** the drill (Mine option A) pulls ore. The Refinery is its own unit beside the Mine. It turns ore into Helium-3 and other materials, and it makes the ship's fuel.
4. **Fill up:** fuel and cargo take a while to collect. When both are full, the player launches for Earth.
5. **While away:** the Mine keeps running on its own and stockpiles ore and fuel materials. It uses the saved-timestamp away-earnings system, which must keep working through reloads and phone locks.
6. **Return:** the player can build a Launch Pad, which raises the ship's cargo capacity and cuts refueling time. It unlocks after the first trip home.
- The crew sleep on the ship, so there are no sleeping quarters. Habitat is paused.
- **Art order update:** Art & Animation does Life Support, then the Dock and Tank Farm, then Engineering. Art Assistant finishes Mine concept C, then the Launch Pad, then the Shipyard. The starter ship's interior should read as believable crew quarters.

**Director's locked numbers:**
- **Landing:** about 6 s, and a tap skips it. Eve's first call starts while the ship comes down.
- **Unload:** about 8 s. The 4 crew walk down the ramp carrying two kits (Mine and Refinery), and the rig unfolds in place. The first deposit glows by about 12 s, so the first tap comes in under 15 s.
- **First trip:** the ship launches once fuel and cargo are both full, which takes about 3 minutes with level-1 kit. Fuel uses the existing Tank Farm timings. The trip takes about 10 minutes.
- **While the ship is away:** the Mine runs on its own at full rate until its stockpile is full. It fills a separate stockpile, not the OreFill bin. The stockpile cap is 10 minutes of output at the current drill rate, so it grows with drill upgrades. It shows as an ore pile beside the rig that visibly grows while the ship is away, and the crew load it onto the ship on return. If the game is closed, the stockpile fills at 50% and still stops at the 10-minute cap; the 4 h cap only limits ordinary away money. The trip timer runs from the saved time, so the ship can be back and waiting when the player opens the game.
- **Return:** Eve's call unlocks the Launch Pad for $250 and a 60 s build. It gives +50% ship cargo and 30% faster refueling, and upgrades raise both.
- **Art order:** Mine concept C comes first, and Life Support continues. Art & Animation then does the starter ship's crew-quarters interior (a lit crew deck and a ramp) and the Refinery unit. Art Assistant does the Launch Pad, then the Shipyard. The opening crates and the unload animation come next. Habitat is paused.
- **Build order:** Game Coder builds §Opening on placeholders after the bar/UI restyle build.
- **Habitat (Jacob, 2026-10-22, via Director):** sleeping quarters return later as a purchase that grows the team. The 4 starting crew sleep on the ship. Habitat unlocks after the Launch Pad, and each crew-quarters module bought adds +2 crew capacity (the only way past 4). Life Support must keep up with the larger crew, like the old "+N miners" link. Director sets the prices when it's built. Art: buried, regolith-covered crew modules added one at a time, with a new module shown on each purchase; paused until Art Assistant gets to it.
- **Refinery and fuel (Jacob, 2026-10-23, via Director):** the Refinery is part of the Mine station, beside the rig in the same view, not a seventh stop. The truck goes Mine conveyor → refinery intake bin → back, and the deposit bonus pays as the bed starts tipping at the bin, followed by the full 3 s truck_dump. Two lines: He-3 (sieve, ~700 °C kiln, cold traps, He-3/He-4 column, blue canisters) and fuel (crusher, ilmenite separator, H2 reduction, electrolyzer, LOX and LH2 tanks to the Tank Farm). The whole Mine station must fit in 1.2 MB, 50k triangles and 25 draws, with Cam_Target and frame_w covering both the rig and the bin. Fuel is LOX + LH2 everywhere (no methane). Shipyard REF-01 becomes FAB-01, a metals foundry.

## Size budget (Director, inside the 8 MB total)
- Engine, UI and first screen: 1.0 MB
- Mine: 1.2 MB
- Each of the 5 buildings: 0.9 MB, with the Tank Farm inside the Dock's share
- Ship, crew and props: 1.0 MB
  - Director ruling (10/24/2026): while the ship lives inside the Launch Pad GLB, the whole pad file (ship included) counts as a building under the 0.9 MB building share, and crew plus props stay in this 1.0 MB group. Once the ship moves into its own file, the ship counts toward this 1.0 MB group again.
- Reserve: 0.3 MB
- Shared textures go in `art/3d/buildings/_shared/`. The first screen stays under 3 MB, and the other buildings are lazy-loaded.

## Builds
- /qa/ stays frozen at QA · 19:40 as the 2D fallback.
- 3D work goes to /qa3d/, tagged "QA3D · HH:MM."
- Preview stays at 12:15 until the first 3D build passes.

## Limits for every 3D build
- 60 fps on average, never under 55 over any 5 seconds, still above 55 after 10 minutes.
- First playable screen under 3 MB and under 3 seconds. Up to 8 MB in total, with the rest loading in the background.
- Each building no more than 0.9 MB (Mine 1.2 MB; see Size budget), each prop no more than 300 KB, textures no bigger than 1024, and about 100 draw calls or fewer.

## Steps
- **Step 0 (Game Coder):** take the 2D Mine out behind a switch.
- **Step 1 (done):** mining brainstorm. Waiting on Jacob's pick of A, B or C.
- **Step 2 (Game Coder):** Three.js foundation with the flat ground, the fixed camera, sideways swipes, lighting, gray placeholder boxes and the `?dev=1` fps readout.
- **Step 2 (Art):** the 3D style guide plus the drill rig test model. Export rules: meters, Y up, facing +Z, origin at the base, named clips, Draco or meshopt, KTX2.
- **Step 3 (Art):** turntable montage of every model for Jacob's approval. Art does the hero models and Art Assistant does the props.
- **Step 4 (Game Coder):** the 3D Mine from Jacob's pick, then the other stations one at a time. The Mine A loop is built toward §Opening above (landing and unload first, Launch Pad after the first trip home).

## Economy carryover into 3D
- 4 crew, 1 oxygen and 10 kW at the start. Buying a floor never lowers the crew.
- Time away pays 50%, capped at 4 hours. It runs on load and when the tab becomes visible again, with the "While you were away" card, and a clock set backward is ignored.
- The low-power banner reads "Build Nuclear (needs Oxygen Lv3 first)."
- Crystals show 0, or ∞ only in dev.

## Eve and Earth Coms
- The calls live in one beat list, where each beat names what triggers it. Calls are skippable, the game saves which ones you've heard, and they never block a tap.
- Her portrait slot stays a gray silhouette until Jacob gives the cue.
- Draft script for Jacob's OK:
  1. **During the landing (placeholder until Jacob approves Eve's script):** "Earth Coms to lander. Telemetry looks clean, Commander. Set her down easy, unload the mining and refinery kits, and get that drill turning. Over."
  2. **First ore:** "That's real ore. Earth's grid runs on Helium-3, so every load you send keeps the lights on down here."
  3. **First upgrade affordable:** "You've got the cash for an upgrade. Bigger mine, bigger loads. Tap Upgrade."
  4. **First cargo ready:** "Cargo's stacking up. Take it to the Space Dock and load the ship."
  5. **At the first fuel check (placeholder until Jacob approves Eve's script):** "Your tanks are filling, but she won't lift until the oxygen and hydrogen are topped off and the hold is full. Load her up and bring that Helium-3 home. Over."
  6. **First risk window:** "Heads up, there's an asteroid field on the route this week. Fly now for a bonus, or wait for clear skies. Your call."
  7. **First delivery home:** "Shipment received, Moonbase. Earth owes you one. Between us, the brass keep saying the word 'Mars.'"

## Next
- Jacob picks A, B or C.
- Target for the Mine A loop: §Opening (Jacob, 2026-10-22).
- Jacob approves Eve's lines or edits them.
- Jacob gives the cue on Eve's portrait.

## Crew check gates
- Swing time: a swing runs from the last frame a foot is within 2 cm of its surface (lowest sole point) before it lifts, to the first frame it is back within 2 cm or on a rung. It must be under 0.6 s. Art aims for 0.55 s (Director, 2026-10-24).
- Ladder start: each climber's ladder start must be no more than 0.100 s from baseline, with a 1 ms float tolerance (Director, 2026-10-24 4:49 PM). Inside times, lift-off and BOARD_SEC must stay unchanged.

## Known issues

- Pad queue, 4 flyers (Director, 10/24/2026): a Tier_12 block on the ship (hidden at Lv1, not in the colliders) sits 0.23 m from queue slot 3 (z about -0.63). Once Tier_12 shows, slot 3 is about 0.62 m short of the 0.55 m collider clearance. Art & Animation checks this clearance when Tier_12 is built.
