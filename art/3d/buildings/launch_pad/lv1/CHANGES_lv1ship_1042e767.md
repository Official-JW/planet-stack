# launch_pad_game_lv1ship.glb (md5 1042e76793da1f97a9837a4a823873f0)

Committed 10/25/2026 for Coder, to ship with AA3's gear update. 349,160 B, 15 draws, meshopt plus quantization.

## Changes from the live pad (live/models/launch_pad_db78a6f7.glb)
- New cockpit window band CW-1: 4 panes below the nose on the camera side, part of the Ship_Placeholder mesh (+0 draws). It's about 6 px tall at 375.
- New `Cockpit_Window` empty (child of Ship_Placeholder). Its extras hold on_hex `#ffb46a`, off_hex `#141b22` and default "on". Coder switches the glow through the pane vertex colours; see `SPEC_cockpit_window.md`.
- New `Engine_Ring_Mount` empty at ship-local (0, 2.9, 0), the mount for the later aft skirt. Nothing is attached to it yet.
- It also carries the Lv1 pad changes from lv1door 2c287db2: the closed cargo door, the fuel line trimmed to 12 m, the plate, the west-facing pipe end and the 641/592 notes. Compared with db78a6f7, that's 35 node transform or extras differences and 49 changed accessors.
- Proof: `proofs/lv1ship_1042e767_cockpit_glow_on_375.png` (md5 15b627a72337dad5ca351e28e9361ab0), 375×667, Eevee, glow on.

## Not in this file
- The crane move (c0639c1 / f6af441) is parked. The crane here is the a257d930-era one.
- The aft skirt fit and the cargo door crawler move haven't been done.
- I haven't re-checked this file against the live db78a6f7 ladder cage or the clearance gate (a0584fb). Playtester should run its normal checks before it goes live.
