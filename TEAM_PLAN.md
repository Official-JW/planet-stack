# Planet Stack, TEAM_PLAN v2 (Oct 22, 2026, full 3D)

## Standing rules (unchanged)
- Nothing to do with Feed Shield.
- All art, fonts and sound are original, with no real brands and only permissive open-source code.
- Nothing reaches preview without two passing runs from Playtester, then Jacob's "go."
- Every tag gets posted in the group before anyone runs it, and nobody pushes during a run.

## Builds
- /qa/ stays frozen at QA · 19:40 as the 2D fallback.
- 3D work goes to /qa3d/, tagged "QA3D · HH:MM."
- Preview stays at 12:15 until the first 3D build passes.

## Limits for every 3D build
- 60 fps on average, never under 55 over any 5 seconds, still above 55 after 10 minutes.
- First playable screen under 3 MB and under 3 seconds. Up to 8 MB in total, with the rest loading in the background.
- Each building no more than 2 MB, each prop no more than 300 KB, textures no bigger than 1024, and about 100 draw calls or fewer.

## Steps
- **Step 0 (Game Coder):** take the 2D Mine out behind a switch.
- **Step 1 (done):** mining brainstorm. Waiting on Jacob's pick of A, B or C.
- **Step 2 (Game Coder):** Three.js foundation with the flat ground, the fixed camera, sideways swipes, lighting, gray placeholder boxes and the `?dev=1` fps readout.
- **Step 2 (Art):** the 3D style guide plus the drill rig test model. Export rules: meters, Y up, facing +Z, origin at the base, named clips, Draco or meshopt, KTX2.
- **Step 3 (Art):** turntable montage of every model for Jacob's approval. Art does the hero models and Art Assistant does the props.
- **Step 4 (Game Coder):** the 3D Mine from Jacob's pick, then the other stations one at a time.

## Economy carryover into 3D
- 4 crew, 1 oxygen and 10 kW at the start. Buying a floor never lowers the crew.
- Time away pays 50%, capped at 4 hours. It runs on load and when the tab becomes visible again, with the "While you were away" card, and a clock set backward is ignored.
- The low-power banner reads "Build Nuclear (needs Oxygen Lv3 first)."
- Crystals show 0, or ∞ only in dev.

## Eve and Earth Coms
- The calls live in one beat list, where each beat names what triggers it. Calls are skippable, the game saves which ones you've heard, and they never block a tap.
- Her portrait slot stays a gray silhouette until Jacob gives the cue.
- Draft script for Jacob's OK:
  1. **Game start:** "Moonbase, this is Eve at Earth Coms. Good to hear you made it. First job: get that mine running. Tap where I'm pointing."
  2. **First ore:** "That's real ore. Earth's grid runs on Helium-3, so every load you send keeps the lights on down here."
  3. **First upgrade affordable:** "You've got the cash for an upgrade. Bigger mine, bigger loads. Tap Upgrade."
  4. **First cargo ready:** "Cargo's stacking up. Take it to the Space Dock and load the ship."
  5. **First fueling:** "Tanks fill on their own, it just takes time. When they're full, you're clear to launch."
  6. **First risk window:** "Heads up, there's an asteroid field on the route this week. Fly now for a bonus, or wait for clear skies. Your call."
  7. **First delivery home:** "Shipment received, Moonbase. Earth owes you one. Between us, the brass keep saying the word 'Mars.'"

## Next
- Jacob picks A, B or C.
- Jacob approves Eve's lines or edits them.
- Jacob gives the cue on Eve's portrait.
