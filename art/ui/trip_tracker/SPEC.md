# Ship trip tracker · SPEC for Game Coder (stills for Director approval, no code yet)

2D HUD overlay over the 3D game, same family as the HUD in `qa3d/index.html` (chamfered dark glass, cyan hairline) with flat cartoon Moon / Earth / ship. Units are **pt** (= CSS px). Re-run every image with `python3 art/ui/trip_tracker/_src/make_tracker.py` from the repo root.

## When it shows
- Only while a trip is live: `liftoffTs <= now < landTs`. **Never during boarding or before lift-off**, and it is gone after landing.
- Launch Pad: the strip. Any other station: the chip.
- Reduced motion: no loops (pulse, flicker, bob). Position still moves.

## Position (fits under the money / ore HUD, above the framing band)
HUD (`#hud`): top = safe-top + 26, height 56, x 8 .. screenW − 64. The tracker uses the **same columns**: x 8, width = **screenW − 72** (303 at 375, 321 at 393), so it never touches the Eve bubble or the gear.
`trackerTop = safe-top + 26 + 56 + 3` (3 pt under the HUD).

| Variant | Height | Use when |
|---|---|---|
| **Standard**: strip 22 + 2 gap + caption line 10 ("Back in 4:12" under the strip, right-aligned) | 34 | `bandTop − trackerTop ≥ 39` (34 + 5 spare) |
| **Thin**: strip 16, "Back in 4:12" moves inside the strip at the right end | 16 | otherwise (needs ≥ 21) |
| **Chip** (other stations) | 18 | always |

Measured (proof safe-top: 20 at 375 × 667, 59 at 393 × 852):

| Screen | HUD bottom | Band top | Standard block | Thin strip | Chip |
|---|---|---|---|---|---|
| 375 × 667 | 102 | 144 | strip y 105–127, caption y 129–139 → **5 pt clear** ✅ | y 105–121 → 23 pt clear | y 105–123 → **21 pt clear** |
| 393 × 852 | 141 | 165 | y 144–178 → **13 pt inside the band ❌** | y 144–160 → **5 pt clear** ✅ | y 144–162 → **3 pt clear** |

So: standard at 375 × 667, thin at 393 × 852. In Safari tabs, where safe-top is 0, both sizes have room for the standard strip (it would be y 85–119 at either size). Pick the variant at runtime from the real numbers.
Hit area: the strip is the tap target, padded to 44 pt tall with an invisible `::before` (−11 pt top and bottom). The padding is touch area only and draws nothing.

## Parts (`parts/*@3x.png`, transparent; or rebuild them as inline SVG from `_src/make_tracker.py`, which is cleaner)
| Part | pt | Notes |
|---|---|---|
| strip_bg_std_303x22, strip_bg_thin_303x16 | 303 × 22 / 303 × 16 | 9-slice: chamfer 6 (5 thin), slice 8 pt each side. Hairline 1 pt gradient 110° #3AD0FF 85 % → #C9D3E6 60 % → #8794AD 35 %. Fill 180° #13213A → #0A1324 at 94 %. |
| moon_15pt | 15 | Radial #F4F6F9 → #C3C9D1 → #8D96A2, craters #A3ABB6, 0.7 pt outline #16202E |
| earth_16pt | 24 (16 pt disc + 4 pt glow) | Radial #7CC4FF → #2F86EA → #1A4FB0, land #5FD07A, glow #7FD4FF 45 % → 0 |
| ship_icon_13pt | 15 × 9 (body 13 × 4.5) | Nose points +x. Stainless gradient #FFFFFF → #C9D0D8 → #8E98A4, mid-blue band #2F6FD6, fins #8E98A4, outline #16202E 0.6 pt. Pivot at the body centre (canvas 7.8, 4.5 pt). |
| ship_glow_flame | 11 × 7 | Sits behind the tail: anchor the right edge at the nozzle (ship-local −7, 0). Colours #FFF6D6 → #FFC861 → #FF7A2F → 0. |
| pulse_ring_16pt | 16 | 1.2 pt ring, #6FE08A |
| flash_landing_36pt | 36 | Radial white 95 % → #BFF8FF 60 % → #7FF3FF 0 |
| path_dots_std | 303 × 22 | Reference only. Draw the dots in code so the travelled part can turn cyan. |
| chip_bg_112x18, chip_full_example | 112 × 18 | Chamfer 5, same hairline and fill as the strip |

Total parts: 53 KB.

## Layout inside the strip (strip-local pt, W = strip width)
**Standard (22 tall)**
- Phase dot r 3 at (11, 11). Phase label at x 19, baseline 14.6, size 10.5, tracking .14 em, phase colour. Phase time left goes after it (+5 pt gap) at size 11.5, #EAFCFF, tabular figures.
- Moon centre (128, 13), r 7.5. Earth centre (W − 13, 13), r 8.
- Flight path: quadratic Bézier P0 (137, 13), P1 ((115 + W)/2, 0), P2 (W − 23, 13). 27 dots, r 0.85. Travelled dots #7FF3FF, untravelled #5F7189 at 80 %.
- Ship: 13 pt, on the path at `u`, rotated to the curve tangent. RETURNING adds 180°.
- AT EARTH: ship parked at (W − 28, 7), level, no flame, with the pulse ring r 7.5 around it.
- Caption, 2 pt under the strip, right-aligned to W − 2: "Back in " #C9D3E6 + "4:12" #EAFCFF, size 10.5, tracking .06 em.

**Thin (16 tall)**: dot r 2.5 at (9, 8). Label size 9.5 at x 15. Moon (98, 9) r 5.5. Earth (W − 86, 9) r 6. Path P0 (105, 9), P1 (mid, 1), P2 (W − 93, 9), 21 dots r 0.7. Ship 10.5 pt. A divider at x W − 74 (1 pt, #C9D3E6 25 %), then "Back in 4:12" right-aligned to W − 6 at size 10.

**Chip (112 × 18)**: ship 10 pt at (13, 9) with flame. "Ship back in " #C9D3E6 + "4:12" #EAFCFF, size 10.5 at x 24. Chevron "›" 1.5 pt #7FF3FF at x 101. Same top-left as the strip.

**Font**: `system-ui` 700–800 with `font-stretch: condensed`, the same as the HUD labels. The stills use Barlow Condensed Bold as a stand-in. Use `font-variant-numeric: tabular-nums` on every timer so the digits don't jiggle.
**Phase colours**: OUTBOUND #7FF3FF, AT EARTH #6FE08A, RETURNING #FFC861. Money pop #FFD84D with a #3A2200 outline.

## Timing: everything comes from the saved trip timestamps
`T = landTs − liftoffTs` (Lv1 = 600 s). Phases (Director ruling):
- **OUTBOUND** 0–45 % (4:30 at Lv1)
- **AT EARTH** 45–55 % (1:00)
- **RETURNING** 55–100 % (4:30)

```
p        = clamp((gameNow − liftoffTs) / T, 0, 1)        // gameNow already includes ?speed=10
OUTBOUND : u = easeInOutSine(p / .45)                    // slow lift-off, cruise, slow arrival
AT EARTH : u = 1 (ship parked)
RETURNING: u = 1 − easeInOutSine((p − .55) / .45)
easeInOutSine(x) = (1 − cos(πx)) / 2
phase time left = phaseEnd − gameNow;   "Back in" = landTs − gameNow   (ceil to the second, m:ss; h:mm:ss above 1 h)
```
Recompute every frame from `gameNow`. Nothing is tweened between frames, so after a reload, a phone lock or 6 h offline the icon is exactly where the time says. Phase changes come from comparing timestamps, so they can't skip or repeat. Each one-shot effect has a saved "played" flag per trip and plays only if `gameNow − eventTs < its duration`. After a reload past it, show the end state with no replay.

## Animations (real time, ms + easing)
| Effect | Trigger | Spec |
|---|---|---|
| Strip in | lift-off (`liftoffTs`) | slide from −8 pt + opacity 0 → 1, **260 ms easeOutCubic** |
| Engine glow | OUTBOUND, RETURNING | flame scaleX .85 ↔ 1.15 and opacity .8 ↔ 1, **140 ms sine loop** (two offset sines so it doesn't look mechanical). Off while AT EARTH. |
| Earth pop | start of AT EARTH | Earth scale 1 → 1.18 → 1 over **360 ms easeOutBack** (overshoot 1.7). A white ring r 8 → 16 pt, opacity .8 → 0, **500 ms easeOutCubic**. |
| **Cargo sale + money pop** | **start of AT EARTH** (sale fires here; lift-off pays nothing) | "+$X" pops by Earth: scale .6 → 1.1 → 1 over **160 ms easeOutBack**, then rises 18 pt in **900 ms easeOutCubic**, then flies to the HUD Money counter with the existing `flyChunks` (gold dots), and Money plays its `.bump` (300 ms). Plays once per trip. On a reload or offline catch-up after AT EARTH started, no pop plays and the money is already paid (counted in the away summary). The value shown in the still, $240, is a placeholder. |
| Pulse | whole of AT EARTH | ring around the parked ship, scale 1 → 1.6 and opacity .6 → 0, **1200 ms easeOutSine loop**. Ship bobs ±0.75 pt, **1600 ms sine**. |
| Turn-around | start of RETURNING | icon rotates 180° over **320 ms easeInOutBack**. If `gameNow − returnStart ≥ 320 ms`, draw it already turned. |
| Landing flash | `landTs` | flash disc on the Moon, r 8 → 18 pt, opacity .9 → 0, **420 ms easeOutQuad**. Moon scale 1 → 1.12 → 1, **280 ms easeOutBack**. After **600 ms** the strip slides up −8 pt and fades out, **240 ms easeInCubic**. |
| Tap → arrival time | tap the strip | the caption cross-fades (**150 ms easeOutQuad**) to "Back at 2:47 PM · in 4:12". Use the device clock (`Intl.DateTimeFormat`, hour + minute). The hairline brightens to #7FF3FF → #3AD0FF. Reverts after **3000 ms** or on the next tap. In the thin strip the right-end text swaps to "Back 2:47 PM". The layout never grows, so nothing enters the band. |
| Chip | other stations, trip live | in: opacity + slide −6 pt, **200 ms easeOutCubic**. Tap: the existing station slide to the Launch Pad, then the chip fades out and the strip fades in. |

`?speed=10`: only `gameNow` speeds up. Effect durations stay at 1×, so AT EARTH (6 s at speed 10) still fits the pop and the pulse.

## Stills (`proofs/`)
The Launch Pad backgrounds are a real game-camera render with the **ship and fuel hoses hidden**, because the ship is away during a trip (`_src/render_empty_pad.py` on `launch_pad_master.blend`, the same camera as the 8f2191c proofs: target (0, 0.7, 4), pitch 18°, vertical FOV 38°, frame_w 78.25). The Shipyard chip still uses `shipyard_portrait_375x667.png`. The HUD, Eve bubble and gear are drawn mocks of `qa3d/index.html`, there only for position.
- `pad_outbound_375x667.png`, `pad_at_earth_375x667.png` (with the money pop), `pad_returning_375x667.png`
- `pad_outbound_375x667_overlay.png`: band and HUD lines plus a 2× zoom with the exact y values
- `pad_tapped_375x667.png`: arrival-time state
- `pad_outbound_thin_375x667(.png|_overlay.png)`, `pad_outbound_thin_393x852(.png|_overlay.png)`
- `pad_outbound_393x852.png` + `_std_overlay.png`: the standard strip at 393, which does **not** fit (kept to show why the thin one exists)
- `chip_shipyard_375x667.png` + `_overlay.png` (2× zoom with the y values)
- `strip_states_3x.png`: every state at 3×

Known, not ours: the settings gear (`#setBtn`, safe-top + 90..126) already reaches into the band at both sizes (y 110–146 at 375, 149–185 at 393). The tracker stays left of it.
