# Next preview changes (locked in group, 10/11 23:50)
- Money ONLY from mining + refining. Remove per-resident stipend, Market/Hospital/Club income. Keep $500 grant. Mine pays small raw-ore trickle before first ship returns.
- Residents = miners; life support/habitat raise miner count. Life support upgrade shows "+N miners".
- First goal points at the Mine.
- Platinum crate ~1 min, Helium-3 canister ~3 min, He-3 worth ~4x per container.
- Refinery: refined cargo x3 value; upgrades speed it; coin pop-ups on Refinery floor.
- Coin pop-ups only at Cargo Space Dock delivery, ore trickle, Refinery. Market/Hospital/Club use resident/happiness icon.
- Market floor renamed Supply Depot (stores Earth supplies, no coins).
- Habitat and Mine start with first floor unlocked.
- Mine pad renamed Cargo Space Dock (art files cargo_space_dock*).
- Nuclear cost $150.
- Fixes: Upgrade button pinned to bottom of sheet; "supports N people" in nameplate strip; debug box off sheet.
- Pending art: ore-chunk pop-up, new Mine spec (4-floor ship, rover tunnel, busy dock).
- Add LICENSES file (no 3rd-party code; art fonts Rajdhani/Inter OFL, DejaVu).
- Incoming art (Mine spec drop): He-3 pressurized canister (violet trim, LED, LOADED) distinct from platinum LOADED box; pop-ups ore chunk, "+miner" helmet, refined-cargo coin; Supply Depot floor art.
- He-3 canister: glowing blue core is main color, violet trim only.
- Dev mode: ?dev=1 on preview = unlimited money + "Max out" button (unlock all floors/levels). Own save key planetstack-dev. Live stays normal.
- Floors with no tier art fall back to base art (never blank). ?dev=1 must be ignored on live root.
- New MINE_SPEC: ship4_hull 320x480 anchor (160,480) at dock (300,20), separate flame/glow; pad/cargo_space_dock 600x70 anchor (300,70) w/ cranes + astronaut routes; rover front layer 1.25x scale, 1.15x parallax, 24f tunnel behind lip; he3_canister* blue; fx/ ore,+miner,refined pop-ups; Supply Depot = mine/floor_market.
- Mine split into starter pack (Rover Bay, rover+tunnel, dock, ship, containers) and later pack (Crusher/Separator/Packing/penthouse on unlock). First-screen budget issue: Life Support+UI alone was 2.79 MB @3x.
- Globe: 6 stops at 60 deg: Life Support, Mine, Cargo Space Dock, Habitat, Shipyard, Engineering. Dock stop scaled ~0.65 to fit 600w, uses @3x; 1.3x crew set for dock. Tunnel front layer drawn at tower/dock seam so rover drives between.
- Load: first screen <3 MB; Mine starter pack streams in background; 150 KB Mine still image covers gap. Later Mine pack on unlock.
- Cargo Space Dock is its own station (6 stations). No floors: upgrade tracks crane speed, crew size, pad size (bigger ships), refuel/repair speed; each to L50, new look every 10 levels.
- Dock art in art/moon/dock/ (own spec + pack). Upgrade looks are layers over base dock. Tap pad opens dock upgrade menu + wrench button that pulses first time. All 4 upgrades must fit in menu with Upgrade button visible.
- Mining cave stays on the Mine's ground in front of the tower (rover in/out there); LOADED boxes hauled over to the Dock (replaces tunnel-at-seam idea).
- Rover Bay garage: rovers drive inside and dump into labeled bins (silver "PLATINUM", blue "HELIUM-3", icons); "ROVER BAY" sign over door. Rover route: cave -> garage -> dump by ore type. Cargo vehicle hauls LOADED boxes Mine -> Dock.
- Walkway tubes between neighboring stations: one reusable tube piece stretched per gap, drawn at horizon edge as globe turns, astronauts walking through. (Art pending.)
- TODO: nudge Mine tunnel (currently tower x+115) so it's fully on screen (Game Director approved).
- Refinery real art (base + L10-50) coming from Art Assistant: swap placeholder.
- Rover Bay bins: DO NOT wire yet; A&A rebuilding (rovers enter via side-wall cutout). Rebuilt cave brings own x offset.
- DONE (10/12/2026 - planet-stack - 00:31, preview only): Water, Nuclear, Refinery L10-L50 tier overlays wired (cumulative, lazy-loaded per level; not in first screen). Refinery placeholder replaced by floors/floor_refinery base room. First screen 2.79 MB @3x.
- DONE (00:31): Mine tunnel moved from tower x+115 to x-150 (hopper 10 -> 60) so it's fully on screen at 390x844. Temporary until rebuilt cave brings its own offset. Rover Bay bins NOT wired (on hold).
- DONE (preview): Moon radius 760 -> 1900 (flatter horizon), rotPerSlot 0.5 -> 0.2 so swipe distance/duration unchanged; all angle thresholds scaled 0.4x.
- DONE (preview): Rover Bay v3 wired: floor + 5-step ORE BIN fill (+1 per pour), truck_{pt,he3}_drive (wheels reversed when backing), rover_bay_dump_{pt,he3} 2.7-5.8 s, route from rover_bay_route.json, depth tint, right-jamb redraw. Old rover_* sheets and outdoor hopper retired.
- DONE (preview): Outdoor truck uses rover_tunnel_{pt,he3} on the cave v3 ramp, clipped so it never draws over the portal, fades into the mouth; tunnel_haze over lip; soft-edged cave; dust + contact shadows; eased moves + settle bounce. Cave at x-67 (scale 1) fully on screen.
- DONE (preview): dock sign at real 48pt with v2 glow (alpha curve, additive) + bloom; t20 sign wired. Dock uses @2x on 3x phones (drawn at 0.65). Dock tracks drawn from dock_tracks.json (all pieces, on demand).
- TODO: walkway tubes (shared/walkway) not wired yet.
- DONE (preview): dock sideways pan (±60pt, starts centred; a drag pans to the edge; only a NEW swipe from the edge changes station); sign always level. Stop dots tappable (big hit area); station name no longer clips. Nameplates: badge pinned right, name/meter truncated with … (big numbers now Qa/Qi/…). Mine top floor headroom. Max out completes goals.
- DONE (preview): pacing: crates/canisters pay 30% when packed, 70% on delivery; Crusher $250.
- DONE (preview): outside truck follows the Moon curve; walkway tubes between neighbouring stations (station spacing 0.25 rad, no artificial sink).
- TODO: Hospital/Cafe art not placed (Game Director to decide); tiers must be a later pack.
- DONE (preview): flick (v>0.3 px/ms or 20% width) advances; dots 44pt-tall nearest-dot hit zone; Shipyard–Engineering tube; tube footings seated per WALKWAY spec (fixed 40pt trusses, tube lowered to reach ground), 1 astronaut on short tubes. Dock-side gap ~97pt needs mid at 0.77 (clamped 0.85) -> A&A shorter mid.
- TODO: when shared/walkway/walkway_mid_s (36px) lands, use caps + one mid_s for short gaps (~97pt -> ~1.03x).
- DONE (preview): Habitat (Living, Hospital, Café, Supply Depot), Shipyard (Refinery, Assembly 2-slot 360x240, Parts, Fuel), Engineering (CNC, CAD, CAM, Print, Chem, Prop) room art wired; tiers cumulative; rooms load per building (groups habitat_rooms/shipyard_rooms/engineering_rooms) on build/visit, never first screen. New rooms use placeholder balance: role boost ×(1+0.03·out) mining each — Game Director to set. Roofs/Launch Tower/Penthouse not in batch.
- DONE (preview): walkway_mid_s for short gaps (G-60<41): cap + one mid_s ×(G-60)/36 + cap, one truss under centre.
- DONE (preview): room boosts (+3% L1, +1%/lvl, +52% L50, no tier doubling) summed additively over 12 support rooms (incl. Supply Depot), applied once to mining. Max out: ×7.24.
- DONE (preview): income chain fix: Mine/Refinery curve 312.5^((lv-1)/49)×2^tiers = 10,000× at L50 (no elite/mastered/elevator compounding); Crusher/Separator/Packing +50%→+300% summed; rooms ×(1+sum) once; refined 3× once. Max out cargo $84.5M/min (+$1.75M/min refined bonus).
- DONE (preview): compact money (3 sig digits, ≤6 chars: $840, $1.75K, $86.2M…); hybrid Mine/Refinery curve 1.25^(L-1) to L10 then g≈1.0979, ×2 per tier: L10 14.9×, L50 10,000×.
- TODO (after Playtester's 01:22 timing): money pop-up starts above nameplate, >=4pt gap, eased rise not clipping floor above; on top floor start lower so it doesn't hit the roof.
- TODO (after Playtester's 01:22 timing, with pop-up fix): wire roofs per ART_SPEC ROOFS, pack art/moon/packs/roofs.json (later load). Habitat/Engineering roofs 360x180 pivot (0,180), still base + 16f motion @12fps. Shipyard gets Launch Tower 360x360 pivot (0,360) instead of roof; draw ship, tower, crew arm, fuel arm; arms play once @12fps. Preview art/moon/roofs_sheet.png. @3x arm frames may be repacked (same names).
- Roofs: preload + decode all arm frames when the Shipyard pack loads (before first swing) to avoid hitching.
- Roofs update: arm frames repacked to 1 page per arm; frames trimmed with {x,y} offset in atlas JSON, add offset when drawing. roofs.json 0.89MB @3x / 0.58MB @2x.

## Playtester NO-GO fixes (10/12)
- [x] Life Support (Oxygen/Water/Nuclear) + Living Quarters run without crew; save migration frees their crew to idle (also fixed: fresh save no longer puts a worker on Oxygen)
- [x] Unassign: tap crew icon (44×44 hit) sends one resident to idle (reuses existing worker icon)
- [x] Trips 2 min → 5 min → 10 min, trip count saved (S.trips); ore income unchanged
- [x] Max-out total includes refining income
- [x] Compact numbers everywhere (rates, capacities, pop/cap, supports); nameplates ≤18 chars
- [x] Goal card fades + stops catching taps when scrolled high (top nameplates readable)
- [x] Living Quarters: +1 bed per level; site dots use fixed-width slots (tap = that dot, pill centred)
- [x] Supply Depot tiers t10–t50 via packs/supply_depot_later_tiers.json (json files DO exist; 0 × 404 in test)
- [x] Money pop-up starts above nameplate (≥4pt gap), eased rise, lower start on top floor
- [x] Roofs: Habitat + Engineering (360×180, 16f@12fps); Shipyard Launch Tower w/ ship, crew + fuel arms (trimmed frames w/ offsets, play once on launch)
- [x] Re-exported Engineering/Parts/Fuel L50 badges, Engineering tiers, Living Quarters tiers
- [x] Fresh-save soft-lock check: Nuclear + Water + Crusher with 3 crew → Crusher staffed, money keeps flowing

## Done in 10/12 02:31 preview push (01:55 re-check fixes)
- [x] Goals: Supply Depot goal removed; chain is Crusher → Rover Bay Lv 10 → Separator ($800, was $1.6K) → Refinery. Fresh-save bot run at ?speed=10: Separator built at ~6:49 game time, longest gap between purchases 76 s (no 3-min dead stretch).
- [x] Crew sheet: person icon only unassigns, separate "+" only assigns (both 44 pt tall); unassigned floors are no longer auto-restaffed; no crew controls or "now staffs" toast on Oxygen/Water/Nuclear/Living Quarters; duplicate Crew stat row removed, row text no longer spills.
- [x] Payouts: value frozen at launch; button, trip card, toast and payout all use it. Dock labels now "Ship hold X/Y · waiting on pad N Pt + M He-3".
- [x] Tapping a station dot closes any open sheet first; the tap never reaches the sheet.
- [x] Dock "Next look" moved to its own wrapping line; "placeholder art" text removed; floor packs load the moment a floor is built (Crusher/Hospital show real art).
- [x] Tunnel trucks in mine_later_tunnel_trucks (loads after mine_starter); every mine_later_* pack waits for the first screen; the truck waits in the bay until the pack is ready.
- [x] Walkway: measured per frame between the two on-screen tower walls, caps pinned to the walls, fades under ~40 pt, drawn behind every tower.

## Done in follow-up preview push
- [x] fx_upgrade_burst (722 KB @3x) moved off the first screen into fx_burst, loaded right after it; upgrades before it loads play a quick scale-pop on the floor. First screen ~2.07 MB @3x.
- [x] Crew hint wraps to two lines (no ellipsis); nothing spills out of the crew row.
- [x] Upgrade burst v2: fx_later_upgrade_burst pack (two pages: sharp + half-res glow at drawScale 2, 16 frames @ 42 ms); loader draws glow then sharp per frame with offsets x drawScale. Still loads after the first screen; scale-pop fallback kept.

## Done in 10/12/2026 - planet-stack - 03:15 preview push (r6 no-go)
- [x] Pacing: mining no longer stops when the pad is full (surplus sells at the pack share), so money keeps ticking while the ship is away. Bot run: Refinery affordable 10:28 (was never within 15 min), longest wait 91 s.
- [x] Walkway hidden while the globe turns (120 ms out, 200 ms back in at rest).
- [x] Toasts sit over the goal card (never over a button); Dock money pop-up on delivery.
- [x] Taps no longer freeze a running turn; the globe always settles on a station.
- [x] ?dev=1&fresh clean dev save (preview only); build stamp next to PREVIEW.
- [x] 10/12/2026 - planet-stack - 03:22: Refinery $2,500 (bot: bought 9:49, longest gap 91 s; saver-only wait after Separator 3:02). Bigger Dock delivery pop-up (Rajdhani Bold 22/26 pt, self-hosted art/fonts/rajdhani-700-latin.woff2 with fallback).
- [x] 10/12/2026 - planet-stack - 03:34: Rajdhani OFL.txt (unmodified) at art/fonts/OFL.txt; LICENSES updated.

## 10/12/2026 - planet-stack - 03:40 (committed locally, waiting to push; amended 03:44)
- [x] Walkway rest stubs from both walls of the main tower (cap_R on its left wall, cap on its right wall, mids to the screen edge, 24 pt fade, walker every 8-12 s, behind the towers, hidden while turning). NOTE: at phone size the towers fill the full width (walls ~4-15 pt from the edges) so the stubs are not visible yet; needs a design call.
- [x] Mine loading: old mine_preview overlay removed; the real Mine layout draws with placeholder floors while mine_starter loads (no snap).
- [x] Dev: ?dev=1&truckdelay=N holds the tunnel-truck pack N s.
- [x] Station dots: no tap highlight/focus ring after a turn.
- [x] Walkway at rest (Game Director): airlock caps drawn OVER the main tower's outer wall column (~10 pt in), on both sides; Mine right cap lifted above the truck opening; Dock caps sit on the pad deck clear of the cranes. Tube/mids stay behind the towers; all fade out during turns.
- [x] Mine raised right cap: two ~6 pt steel legs (rib style) with foot plates and contact shadows down to the regolith, right of the wall line, clear of the truck opening and path.

## r8 fixes (10/12/2026)
- Refinery starts unbuilt (root cause: cost-0 assembly_up was auto-built on fresh saves, so the Shipyard counted 1 floor and drew the unbuilt Refinery). Old saves migrated; dashed empty-floor frame with centred $2,500 button; goal completes on build.
- Ship pays exactly the value locked at launch; cargo/min HUD now = 30% pack share on all containers + 70% (and refined bonus) capped by ship throughput.
- Image loads retry 3x (400/800/1200 ms).
- One amber HUD pill "Low power: build Nuclear ($150)" → taps to Nuclear; per-floor warning icons removed.
- Stray "Build Assembly · $0" gone (same root cause).
- Pad dip (GD call a): loaded containers stay counted on the pad until launch, then leave for real; 400 ms low-g slide into the hold (top first), "Pad N/60" ticks down, "−N loaded"; refill uses normal mining drop-in.
- Toast sits just below the low-power pill when it shows (GD call b).
- Pad slide tweak: each container starts 40 ms after the one above (top first), 400 ms ease-in-out move; hold target follows the ship; count ticks after the last one lands.
- Lift timing (GD): ship stays on the pad until the last container lands and the pad tick-down ends, then lifts after a 150 ms beat (no hatch: ship art has no hatch frames). Containers no longer follow the hold. Visual only; trip timer + payout stay locked to the launch tap.
- Cargo hatch (dock_later_hatch, after first screen): open on the pad, shuts 0→5 over 120 ms in the 150 ms pre-lift beat, held shut in flight; plain pause until it loads.
- floor_empty art (floors_later_empty, after first screen) for every unbuilt floor incl. the Refinery site, button centred; dashed frame until it loads.
- Low power pill also shows when energy limits the crew (pop >= energy cap); "A miner left: not enough energy" toast kept and taps to Nuclear.

## r9 (Playtester 04:20 no-go)
- Low-power pill names the next real step (upgrade Oxygen to Lv3 → build Water ($120) → build Nuclear ($150) → upgrade Nuclear); tap opens that step (sheet if built, else its station); miner-left toast uses the same target.
- Floor labels stick just below the Goal card when a floor's top is under it (every station, any scroll).
- Toast sits 18 px below the pill (8 pt gap even during its 10 px slide-in).
- Hold scales with trip: 1x / 2.5x / 6x (12/30/72); crane scales the same (full hold loads in ~2 min); pad cap = max(60, hold).
- ?dev params (truckdelay, speed…) survive the ?fresh URL cleanup.
- Art checks: pad stack stays capped at its full 60-height (counter shows real N/72; slide still animates max 12); sticky floor label = same plate + 1 pt drop shadow, fades in over 120 ms.
- Big launches: loaded containers stay drawn until they leave; past the 12 animated, the rest fade out over 200 ms after the slide so the stack matches the remaining pad (unloaded ones stay). No pop-back; lift beat unchanged.

## r12 (08:07 PT) — flat world rework
- Moon globe + rotation removed; flat procedural regolith (strata, craters, boulders, hard shadows); straight horizontal pan, 1:1 swipe, snaps to 6 stations.
- Buildings upright on foundation pads with contact shadows; dock on a solid plinth.
- Glass walkway tubes always visible on support legs (old fade removed).
- Mine layout + loader are PLACEHOLDERS (Art's v3–v5 mine files are unapproved mockups; v6 coming) — nothing baked in.
- Upgrade sheet: 36x5 grab handle, drag-to-dismiss (1:1, backdrop fades, >30% or flick closes in 250 ms ease-out, else spring back); iOS touch handled on the touch target.
- Separator $500; Rover Bay upgrade base 20→12 for pacing; toast placed after econ() so it sits 18 px under the pill.
- Pad cap constant PAD_VIS (4 tiers × 3 = 12/stack, 24 total); He-3 stack in front of the orange tower; Pt crate clears crossbar.
- Rover stopX 92, truck x ≥ stopX; during truckdelay truck waits visible at the bin (x=92).

## r13 (08:14 PT) — Art ground strip (local commit, not pushed)
- ground_later_strip pack (art/moon/ground/@Nx/ground_strip.webp + json) loads after the first screen with the shared retry; code ground stays as the first-screen fallback, 200 ms crossfade to the strip.
- Strip groundLineY (44) sits on HOR, so pads and walkway legs stand on Art's ground line; tiles every 1170 pt, device-pixel snapped with a 1 px overlap.

## r13b (08:20 PT) — pack lists (local commit, not pushed)
- mine_later_dump: rover_bay_dump_pt/he3; until loaded the Rover Bay shows rover_bay_dump_still_pt/he3 (mine_starter, 90x58, pivot 0,58).
- floors_later_offscreen: Rover Bay floor (base, layers, low-power, t10–t50) + bin_fill_ore; placeholders until loaded. bin_fill_ore was previously never defined (its def sat inside a comment) — fixed.
- Both packs are requested after the first screen; neither is in the first-screen wait.

## r13c (08:21 PT) — upgrade burst later (local commit, not pushed)
- fx_later_upgrade_burst (fx_upgrade_burst + _glow) now requested after the first screen, not in the first-screen wait. Until it loads, floor upgrades show the scale-pop and dock upgrades the toast only.

## r13c (09:51 PT) — Playtester no-go fixes (deployed to /qa/ only)
- Low power: one steady state with hysteresis (short <0.99 or <0.999 for 0.6 s; restore after ≥0.999 for 1.2 s). Normal lights drawn once, floor _lowpower layer crossfaded over it 400 ms each way (Life Support has no _lowpower art: steady 60% dim). The 12 fps floor_low_power flicker overlay and the per-frame E.power re-pick (tower cache key, roof, truck clock) are gone; truck clock accumulates so speed changes never jump it.
- Pad: one visible tier = one row of 3 single crates (the stack3 sprite was 2 rows tall → ~8 rows). 4 rows per stack, 24 max; stageCap 60→72 so the label reads N/72.
- Swipes: touch events drive gestures on touch devices (pointer only for mouse); ghost/stale touches can't block drags; touchcancel snaps; dock pan carries on into the station swipe.
- Vertical scroll on every station; range lets the topmost item clear the HUD goal card (safe-area aware), min 60 pt.
- /qa/ path with 'QA · HH:MM' tag; separate save key.

## r14 (11:01 PT) — Playtester run-1 fixes (/qa/ only)
- Welcome back: display:none unless shown, own top layer (z 200, last body child), COLLECT on pointerup/touchend/click, dismiss removes pointer events at once and the element after the fade.
- Low-power dim + ground crossfade animate per rAF from the frame timestamp, eased (400 ms / 200 ms); power re-read every frame; restore buffer 0.6 s. Ground: code ground stays fully under the strip; strip fades 0→1 after img.decode() + warm-up draw; code ground removed after the fade.
- Trip tiers: /qa/?dev=1 shared the preview dev save (trips already ≥1 → 5:00 first trip). Dev save key is now per build, and ?fresh clears this build's own save.

## r14b (11:15 PT) — code ground brightened (/qa/)
- Code-drawn ground gradient x1.21 (Art), same stops/shape, tinted to the strip's average surface hue (R 1.023 / G 1.000 / B 0.968). Strip unchanged.

## r14c (11:17 PT) — code ground scale 1.21 → 1.13 (GD), hue tint kept

## r15 (QA 12:15)
- Toast is placed every frame at least 8pt below the stats bar and 18pt below the low-power pill. It no longer animates `top`.
- Low-power dim/crossfade (mine floors and Life Support) uses the same eased 400ms fade each way from the rAF clock. Ambient layers and trucks no longer freeze; the truck slows smoothly with the fade.
- The ground strip fade is advanced per frame. In dev it logs `[ground strip] alpha` to the console and an on-screen readout.
- COLLECT and welcome-back payouts are held until tapped, then banked with a money pop.
- Touch input is enabled only after the loader is gone. The loader is pointer-events:none while it fades.
- mine_starter re-export: tunnel_back and tunnel_front_lip have feathered edges (@3x pack 1,169,428 B).

## r16 (QA · 13:23) — fixes only (no new Mine)
- Packing $6,400 → $1,800 (GD).
- Price staleness audit: canvas Build pills + lock labels already read F[].cost live; upgrade sheet re-rendered only per $50 money bucket and dock sheet per $20, elevator sheet never → all three now re-render on every $1 / any cost change.
- Toast clears stats bar, low-power pill and Goal card by ≥8 pt each, including the 10 px slide-in.
- Welcome back only after ≥60 s real (wall-clock) away in every mode incl. ?dev=1/?speed; shorter gaps bank silently.
- Dev: [mine dim] alpha logged every frame + on-screen readout.
- ADIT-2 halo fix: Art's tunnel_back / tunnel_front_lip (@3x/@2x) 13:05 re-export; mine_starter bytes +17,200 @3x / +9,442 @2x. No truck_wheel.

## r17 (QA · 22:10) — mine yard + crane rulings
- Mine yard (no v7g file in the repo): cave shifted right and drawn closer (×1.18), with a road strip, a moving conveyor up to the tower, an attendant platform, and a warm work light. The cutaway floor tower is unchanged. Side-by-side with Art's v7g still needs that file.
- Crane phase 2, from the written rulings (the patch file was not in the repo): 7.6 s hammerhead cycle, sway under 0.5° before the hook enters the bay, 0.4 s roller, hatch closes on launch. One container moves into the hold at the roller. Launch takes only that hold ("X of Y loaded"). Leftovers stay on the pad. No slide-in.

## r18 (23:54 PT) — preview link caught up
- GitHub /preview/ was still the 08:07 page (gray code-drawn ground). This push copies the QA build there: painted ground on the first screen, flat moon, crane cycle, mine yard. Corner tag PREVIEW · 23:54.
- Live root is not touched. Preview saves stay on planetstack-preview.

## r19 (00:05 PT) — stop the fake mine yard
- Removed the stand-in road, conveyor, stick attendant, and orange blob. They were covering the real cave and are not the approved sheets.
- Still missing from the repo, so not drawn: scene sheets, attendant_marshal, road_light, lamp_post. The live mine is the older ADIT-2 cave plus Rover Bay until those files land.

## r20 (00:12 PT) — mine yard uses the approved sheet
- The foreground is the flat cave, road, platinum truck, and lamp posts from the approved yard sheet. The old rocky ADIT-2 cave is not drawn when that sheet is loaded.
- The "3 REVERSE INTO BAY" callout is painted out. Fresh saves still only have Rover Bay built; Crusher, Separator, and Packing show when built.

## r21 (00:16 PT) — yard sits under the floor
- The cave, road, truck, and lamps draw behind the tower. Rover Bay stays visible.

## r22 (00:30 PT) — dock: Takeoff & Landing, then wheeled to the cargo dock
- The ship side of the pad is labeled TAKEOFF & LANDING. That is the old tank farm. It is not a new station and it does not change save data or prices.
- A mule wheels a crate from that platform across to the CARGO DOCK. The crane still loads only what is on the pad.

## r23 (10:40 PT) — mining truck drives the cave
- The still truck is off the yard sheet. The 3D truck leaves the Rover Bay, drives down into the cave, disappears, comes back out, and drives into the bay. About an 8 second loop. No price changes.

## r24 (10:45 PT) — Takeoff & Landing is its own stop
- Swipe order is now Life Support, Mine, Takeoff & Landing, Cargo Space Dock, Habitat, Shipyard, Engineering.
- The ship, fuel tanks, and launch button sit on Takeoff & Landing. A mule wheels a crate off that pad toward the Cargo Dock. The crane stays on the dock. No price changes. Saves are unchanged.

## r25 (11:05 PT) — the road dump truck, not the old rover
- The 3D rover is gone from the mine road and from inside the Rover Bay.
- The still truck is gone from the road. The moving piece is the whole truck, paint and body together, not a highlight sliding off. It is not mirrored. No price changes.











- Dock reads "In hold X" and "On pad Y". Stockpile draws at most 12 containers plus a "+N" badge. The handler stands on a clear mark; other walkers and the mule stay behind it.
- Needs Game Director sign-off: a full hold of 12 now loads in about 91 s (was about 120 s). Each crane tier (every 10 levels) is +10% speed, not the old +4% per level. Longer trips still speed the crane so a bigger hold fills in that same ~91 s.
