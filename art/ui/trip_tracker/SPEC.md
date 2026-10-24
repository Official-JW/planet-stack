# Ship trip tracker · SPEC for Game Coder (v2, Director fixes 10/24)

2D HUD overlay over the 3D game, in the same style as the HUD in `qa3d/index.html` (chamfered dark glass with a cyan hairline), with a flat cartoon Moon, Earth and ship. Units are **pt** (= CSS px). Re-run every image with `python3 art/ui/trip_tracker/_src/make_tracker.py` from the repo root. Numbers are in `_src/measure.json`.

## When it shows
- Only while a trip is live, from lift-off to touchdown: `liftoffTs <= now < liftoffTs + 616 s` at Lv1. **Never during boarding or before lift-off.** It is gone after touchdown.
- Launch Pad: the strip. Any other station: the chip.
- Reduced motion: no loops (pulse, flicker, bob), but the ship still moves.

## Layout: one thin strip at every size
- **Strip:** 16 pt tall. x = 8, width = **screenW − 72** (303 at 375, 321 at 393). Those are the HUD's columns, so it never reaches the Eve bubble.
- **Top:** `safe-top + 26 + 56 + 3`, i.e. 3 pt under the HUD (`#hud` top = safe-top + 26, height 56).
- **Chip:** 122 × 18 (widened from 112 for 11 pt text), same top-left as the strip.
- Measured with proof safe-top 20 at 375 × 667 and 59 at 393 × 852:

| Screen | HUD bottom | Strip y | Chip y | Framing band top | Strip clearance | Chip clearance |
|---|---|---|---|---|---|---|
| 375 × 667 | 102 | 105–121 | 105–123 | 144 | **23 pt** | **21 pt** |
| 393 × 852 | 141 | 144–160 | 144–162 | 165 | **5 pt** | **3 pt** |

**Hit area:** the strip is the tap target. Pad it to 44 pt with an invisible `::before` (−14 pt top and bottom). The padding is touch area only and draws nothing.

### Inside the strip (strip-local pt; W = strip width; RZ = 116)
- Phase dot r 2.5 at (9, 8). AT EARTH adds a 4.5 pt ring at 45 %.
- **All strip and chip text is 11 pt minimum** (Director). The strip stays 16 pt tall, with the same clearances.
- Phase label at x 15, baseline 11.8, **11 pt, tracking .08 em** (was 9.5 pt / .12), phase colour.
- Phase time left follows 3 pt after it: **11 pt, tracking .02 em** (was 10.5), #EAFCFF, tabular figures.
- Re-fit: the widest left text, "RETURNING 4:38", ends at x 89.4 (was 84.8). The Moon's left edge is at 98.5, so 9.1 pt stays clear without moving anything. "OUTBOUND 4:38" ends at 86.0 and "AT EARTH 1:02" at 79.8. A future level with a 10:00+ phase ends at 92.7 (5.8 pt clear).
- Nothing had to give: the Moon, Earth, path, divider and right zone are unchanged.
- Moon centre (104, 9), r 5.5.
- Earth centre (W − RZ − 10, 9), r 6: x 177 at 375, x 195 at 393.
- Flight path: quadratic Bézier P0 (111, 9), P1 (mid-x, 1), P2 (W − RZ − 17, 9). 15 dots, r 0.7.
- Ship: 10.5 pt, placed at path parameter `u` and rotated to the curve tangent. RETURNING adds 180° so it faces the Moon. AT EARTH: parked level at (Earth x − 11, 6) with no flame, inside a 5.5 pt pulse ring.
- Divider at x = W − RZ: 1 pt, #C9D3E6 at 25 %, inset 3 pt top and bottom.
- **Right zone**, right-aligned in a box from W − RZ + 1 to W − 6, which is **109 pt** at both sizes. **11 pt minimum** (Director), tracking .02 em.
  - Normal: "Back in " #C9D3E6 + "4:12" #EAFCFF (Lv1 max "Back in 10:16" = 53.5 pt).
  - **Tapped** text (the clock time #EAFCFF, the rest #C9D3E6). Pick the first form that applies:
    1. Under 1 h left: **"Back at 2:47 PM · in 4:12"**.
    2. 1 h or more: short form **"Back 12:47 PM · 1:04:12"**.
    3. If the short form is wider than 109 pt: drop the clock time and show **"Back in 1:04:12"**.
  - Measure with the real font at runtime (`measureText` or `scrollWidth`) and never go below 11 pt.
  - Measured at 11 pt, .02 em, with the Barlow Condensed Bold stand-in (`proofs/tapped_text_forms_3x.png`, `measure.json → right_zone`):

| Form | Worst-case text | Width | 375: x (strip-local) | 393: x (strip-local) | Spare in 109 |
|---|---|---|---|---|---|
| Under 1 h (Lv1 worst case, 616 s trip) | Back at 12:47 PM · in 10:16 | 107.3 pt | 189.7–297 | 207.7–315 | **+1.7 pt** |
| 1 h or more | Back 12:47 PM · 1:04:12 | 94.9 pt | 202.1–297 | 220.1–315 | +14.1 pt |
| Fallback | Back in 1:04:12 | 62.3 pt | 234.7–297 | 252.7–315 | +46.7 pt |

  - The under-1 h worst case fits with only 1.7 pt to spare. If the device's system-ui condensed font comes out wider, reduce tracking to 0 (saves 6 pt) before ever going below 11 pt.
  - The layout never changes size.

### Lit path dots: always the part behind the ship
- **OUTBOUND:** dots from the **Moon to the ship** (`t ≤ u`) are lit #7FF3FF. Dots ahead of the ship are #5F7189 at 80 %.
- **AT EARTH:** all dots lit (the trip out is complete).
- **RETURNING:** dots from **Earth to the ship** (`t ≥ u`) are lit. Dots between the ship and the Moon are unlit.

Here `t` is each dot's position along the path, 0 at the Moon and 1 at Earth. The lit section grows behind the ship as it flies and never runs ahead of it.

### Chip
**122 × 18**, chamfer 5. Ship 10 pt at (13, 9) with flame. "Ship back in " #C9D3E6 + "4:12" #EAFCFF, **11 pt, tracking .02 em**, at x 24, baseline 12.8. Chevron 1.5 pt #7FF3FF at x 111.
- Lv1 worst case "Ship back in 10:16" (73.6 pt) ends at x 97.6, 13.4 pt clear of the chevron.
- 1 h+ case "Ship back in 1:04:12" (82.5 pt) ends at x 106.5, 4.5 pt clear.
- At 112 wide with 11 pt text, the Lv1 text would have touched the chevron, which is why the chip grew. Tapping it runs the existing station slide to the Launch Pad.

### Money pop: real payout, routed around the ore panel
**Text and style:**
- "+$20,000" at Lv1; Coder feeds the real amount.
- Inter (or system-ui) 900, 15 pt, #FFD84D, with a 3 pt #3A2200 outline drawn as a stroke under the fill.
- **Ink box, including the outline:** baseline − 13.8 to baseline + 4.6, so 18.4 pt tall. The ink centre sits 4.6 pt above the baseline.
- **Ink widths:** "+$20,000" 80.4 pt (77.4 pt of glyphs). **Max is "+$999,999": 88.9 pt** (85.9 pt of glyphs).
- From $1,000,000 up, use the HUD's short form ("+$1.2M").

All positions below are the **ink centre** (cx, cy) in screen pt. Scale is around that centre.

**Route rule (runtime):**
- **Under:** let `under = stripBottom + 2 + 9.2`. If `under + 9.2 × 1.06 ≤ bandTop − 1`, the pop rides just under the strip.
- **In-strip:** otherwise it rides centred on the strip, in front of it (`cy = stripTop + 8`).

**Paths:**
- **375 × 667 (under):** pops just under the strip, centred on Earth, glides left below the HUD panels, then rises into the bottom of the Money counter.
- **393 × 852 (in-strip; the under route is impossible):** the strip bottom is y 160 and the band top is y 165, a 5 pt gap. The pop is 18.4 pt tall (9.7 pt even at 11 pt with no outline), so it cannot fit under the strip. The closest clean alternative is the in-strip route: the same path, but at the strip's height.
  - It covers the strip's own content (Earth, ship, phase label) for about 1 s.
  - It never touches the ore panel and stays above the band.

| Key | ms after +277.2 | 375: (cx, cy), scale, opacity | 393: (cx, cy), scale, opacity | Easing into this key |
|---|---|---|---|---|
| K0 start | 0 | (185, 132.2), .6, 0 | (203, 152), .6, 0 | n/a (cx = Earth screen x, clamped so the ink stays inside x 12 … screenW − 68) |
| overshoot | 110 | same, **1.06**, 1 | same, 1.06, 1 | easeOutCubic (scale and opacity) |
| settle | 170 | same, 1, 1 | same, 1, 1 | easeInOutSine |
| hold | 520 | same | same | n/a (hold 350 ms) |
| K1 glide end | 970 | (72.6, 132.2), 1, 1 | (76.5, 152), 1, 1 | **easeInOutCubic, 450 ms**: x only; cx = Money cell centre ((8 + moneyCellRight) / 2) |
| (fade starts) | 1150 | on the rise | on the rise | opacity 1 → 0 linear over 120 ms |
| K2 into Money | 1270 | (72.6, **102**), **.55**, 0 | (76.5, **141**), .55, 0 | **easeInCubic, 300 ms**: y and scale. cy = HUD bottom = Money cell bottom edge |

At 1270 ms: the Money counter adds the amount and plays `.bump` (300 ms). This replaces the old "rise 18 pt + flyChunks". After a reload or catch-up past +277.2, nothing plays.

**Measured clearances** for the widest ("+$999,999") ink across the whole path (sampled every 10 ms; `measure.json → pop_path`):

| | 375 × 667 (under) | 393 × 852 (in-strip) |
|---|---|---|
| Ink y at K0 (overshoot) | 123.0–141.4 (122.45–141.95) | 142.8–161.2 (142.25–161.75) |
| vs strip | 2 pt under the strip bottom (121); 1.45 pt at overshoot | on top of the strip (144–160) |
| vs band top | 144: **2.6 pt** clear (2.05 pt at overshoot) | 165: **3.8 pt** clear (3.25 pt at overshoot) |
| vs ore panel (x 143.1–311 / 151–329, bottom 102 / 141) | lowest ink top under it is 122.45: **20.45 pt** below. During the rise the ink is at x ≤ 117.0, **26 pt** left of the ore panel | **1.25 pt** below at overshoot (1.8 pt settled). During the rise the ink is at x ≤ 120.9, **30 pt** left |
| Ink x at K0 | 140.5–229.5 (81.5 pt inside the HUD column edge x 311) | 158.5–247.5 (81.5 pt inside x 329) |
| Never overlaps | the ore panel or the band | the ore panel or the band |

- **During the rise at 375** the pop crosses the strip's left end (the phase label and Moon) for about 0.2 s on its way into the Money cell. It is drawn above the strip.
- **393 is tight above** (1.25 pt from the ore panel at the 1.06 overshoot). If Coder's real ink box is taller than Inter's, drop the overshoot to 1.0 at 393 (1.8 pt clear).

## Colours
| Use | Hex |
|---|---|
| OUTBOUND | #7FF3FF |
| AT EARTH | #6FE08A |
| RETURNING | #FFC861 |
| Hairline | gradient 110°: #3AD0FF 85 % → #C9D3E6 60 % → #8794AD 35 % |
| Hairline, tapped | #7FF3FF → #3AD0FF |
| Fill | gradient 180°: #13213A → #0A1324 at 94 % |
| Moon | #F4F6F9 → #C3C9D1 → #8D96A2, craters #A3ABB6 |
| Earth | #7CC4FF → #2F86EA → #1A4FB0, land #5FD07A, glow #7FD4FF |
| Ship | stainless #FFFFFF → #C9D0D8 → #8E98A4, mid-blue band #2F6FD6, outline #16202E |
| Flame | #FFF6D6 → #FFC861 → #FF7A2F → transparent |

**Font:** `system-ui` 700–800 with `font-stretch: condensed`, as in the HUD. Barlow Condensed Bold stands in for it in the stills. Timers use `tabular-nums`.

## Timing from the saved trip timestamps (Game Coder's Lv1 numbers)
The trip runs **616 s** from lift-off to touchdown: 8 s climb + 600 s away + 8 s landing. Times are counted from lift-off:

| Phase | From | To | Lv1 length |
|---|---|---|---|
| OUTBOUND | +0 | +277.2 s | 4:37.2 |
| AT EARTH | +277.2 | +338.8 s | 1:01.6. **The sale and money pop fire once, at +277.2.** |
| RETURNING | +338.8 | +616.0 s | 4:37.2 |

"Back in" counts down to **+616** (touchdown). That is 45 / 10 / 45 % of the total, so scale it for other levels.
```
e = gameNow − liftoffTs                      // gameNow already includes ?speed=10
OUTBOUND : u = easeInOutSine(e / 277.2)
AT EARTH : u = 1 (ship parked)
RETURNING: u = 1 − easeInOutSine((e − 338.8) / 277.2)
easeInOutSine(x) = (1 − cos(πx)) / 2
phase left = phaseEnd − e;  Back in = 616 − e   (ceil to whole seconds; m:ss, h:mm:ss above 1 h)
```
- Recompute every frame from `gameNow`. Nothing tweens between frames, so after a reload, a phone lock or 6 h offline, the icon is exactly where the time says.
- Phases are timestamp comparisons, so they can't skip or repeat.
- One-shot effects keep a per-trip "played" flag and play only if `e − eventTime < duration`. After a reload past an effect, show its end state.

## Animations (real time, ms + easing)
| Effect | Trigger | Spec |
|---|---|---|
| Strip in | lift-off (+0) | slide from −8 pt + opacity 0 → 1, **260 ms easeOutCubic** |
| Engine glow | OUTBOUND, RETURNING | flame scaleX .85 ↔ 1.15, opacity .8 ↔ 1, **140 ms sine loop** (two offset sines). Off while AT EARTH. |
| Earth pop | +277.2 | Earth scale 1 → 1.18 → 1, **360 ms easeOutBack** (overshoot 1.7). White ring r 6 → 12 pt, opacity .8 → 0, **500 ms easeOutCubic**. |
| Money pop | +277.2, once per trip (lift-off pays nothing) | keyframes in **Money pop** above: pop in 170 ms, hold 350, glide left 450 easeInOutCubic, rise 300 easeInCubic into the Money cell bottom (fade over the last 120), then Money `.bump` 300 ms. 1.27 s in total. After a reload or offline catch-up past +277.2, no pop plays: the money is already paid and is counted in the away summary. |
| Pulse | whole of AT EARTH | ring round the parked ship, scale 1 → 1.6, opacity .6 → 0, **1200 ms easeOutSine loop**. Ship bobs ±0.5 pt, **1600 ms sine**. |
| Turn-around | +338.8 | icon rotates 180°, **320 ms easeInOutBack**. Draw it already turned if `e − 338.8 ≥ 0.32`. |
| Lit dots | every frame | lit set = `t ≤ u` (OUTBOUND), all (AT EARTH), `t ≥ u` (RETURNING). Each dot fades in over **120 ms linear** as the ship passes it. |
| Landing flash | +616 | flash disc on the Moon, r 6 → 14 pt, opacity .9 → 0, **420 ms easeOutQuad**. Moon scale 1 → 1.12 → 1, **280 ms easeOutBack**. Then, 600 ms later, the strip slides up −8 pt and fades, **240 ms easeInCubic**. |
| Tap | strip | right zone cross-fades to the tapped form (rule above), **150 ms easeOutQuad**. Hairline brightens. Reverts after **3000 ms** or on the next tap. Arrival time comes from the device clock (`Intl.DateTimeFormat`, hour + minute). |
| Chip | other stations | in: opacity + slide −6 pt, **200 ms easeOutCubic** |

`?speed=10` speeds up only `gameNow`. Effect durations stay at 1× (AT EARTH is about 6.2 s at speed 10, which still fits the pop and pulse).

## Parts (`parts/*@3x.png`, transparent, 47 KB total; or rebuild as inline SVG from `_src/make_tracker.py`)
| Part | pt | Notes |
|---|---|---|
| strip_bg_303x16, strip_bg_tapped_303x16 | 303 × 16 | 9-slice: chamfer 5, slice 8 pt each side |
| moon_11pt | 11 | |
| earth_12pt | 18 | 12 pt disc + 3 pt glow on each side |
| ship_icon_10_5pt | 12 × 7 | nose points +x, pivot at the body centre (6.3, 3.5) |
| ship_glow_flame | 9 × 6 | right edge on the nozzle |
| pulse_ring_11pt | 12 | |
| flash_landing_28pt | 28 | |
| path_dots_ref_303x16 | 303 × 16 | reference only; draw the dots in code |
| chip_bg_122x18, chip_full_example | 122 × 18 | |
| money_pop_example_20000 | 90 × 20 | reference only; render the pop as text |

## Stills (`proofs/`)
**Backgrounds:**
- Launch Pad: a real game-camera render with the ship and fuel hoses hidden, because the ship is away (`_src/render_empty_pad.py`; same camera as the 8f2191c proofs).
- Chip: the Shipyard proof.
- The HUD and Eve bubble are drawn copies, there only to show position. The settings gear is left out, because Coder is moving it out of the band.

**Files** (each has an `_overlay` version with the band, the HUD-bottom line and a 2× zoom with exact y values):
- `pad_outbound_{375x667,393x852}.png`
- `pad_at_earth_{375x667,393x852}.png`: "+$20,000" at K0 (under the strip at 375, in-strip at 393). The overlay also boxes "+$999,999" against the HUD column edge.
- `pad_returning_{375x667,393x852}.png`: lit dots run from Earth to the ship.
- `pad_returning_tapped_{375x667,393x852}.png`: "Back at 2:47 PM · in 4:12"
- `chip_shipyard_375x667.png`
- `strip_states_3x.png`: every state at 3×
- `pad_at_earth_pop_path_375x667.png`: mid-glide (745 ms). Its `_overlay` draws the centre path, K0/K1/K2, the widest ink box, the ore keep-out and the band. `pad_at_earth_pop_path_393x852.png` + `_overlay`: the in-strip alternative.
- `tapped_text_forms_3x.png`: the three tapped forms at 375 and 393 widths, each with a dashed 109 pt box and its measured width
