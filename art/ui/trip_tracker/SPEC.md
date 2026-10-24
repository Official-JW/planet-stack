# Ship trip tracker · SPEC for Game Coder (v2, Director fixes 10/24)

2D HUD overlay over the 3D game, in the same style as the HUD in `qa3d/index.html` (chamfered dark glass with a cyan hairline), with a flat cartoon Moon, Earth and ship. Units are **pt** (= CSS px). Re-run every image with `python3 art/ui/trip_tracker/_src/make_tracker.py` from the repo root. Numbers are in `_src/measure.json`.

## When it shows
- Only while a trip is live, from lift-off to touchdown: `liftoffTs <= now < liftoffTs + 616 s` at Lv1. **Never during boarding or before lift-off.** It is gone after touchdown.
- Launch Pad: the strip. Any other station: the chip.
- Reduced motion: no loops (pulse, flicker, bob), but the ship still moves.

## Layout: one thin strip at every size
- **Strip:** 16 pt tall. x = 8, width = **screenW − 72** (303 at 375, 321 at 393). Those are the HUD's columns, so it never reaches the Eve bubble.
- **Top:** `safe-top + 26 + 56 + 3`, i.e. 3 pt under the HUD (`#hud` top = safe-top + 26, height 56).
- **Chip:** 112 × 18, same top-left as the strip.
- Measured with proof safe-top 20 at 375 × 667 and 59 at 393 × 852:

| Screen | HUD bottom | Strip y | Chip y | Framing band top | Strip clearance | Chip clearance |
|---|---|---|---|---|---|---|
| 375 × 667 | 102 | 105–121 | 105–123 | 144 | **23 pt** | **21 pt** |
| 393 × 852 | 141 | 144–160 | 144–162 | 165 | **5 pt** | **3 pt** |

**Hit area:** the strip is the tap target. Pad it to 44 pt with an invisible `::before` (−14 pt top and bottom). The padding is touch area only and draws nothing.

### Inside the strip (strip-local pt; W = strip width; RZ = 116)
- Phase dot r 2.5 at (9, 8). AT EARTH adds a 4.5 pt ring at 45 %.
- Phase label at x 15, baseline 11.2, size 9.5, tracking .12 em, phase colour. Phase time left follows 3 pt after it: size 10.5, #EAFCFF, tabular figures.
- Moon centre (104, 9), r 5.5.
- Earth centre (W − RZ − 10, 9), r 6: x 177 at 375, x 195 at 393.
- Flight path: quadratic Bézier P0 (111, 9), P1 (mid-x, 1), P2 (W − RZ − 17, 9). 15 dots, r 0.7.
- Ship: 10.5 pt, placed at path parameter `u` and rotated to the curve tangent. RETURNING adds 180° so it faces the Moon. AT EARTH: parked level at (Earth x − 11, 6) with no flame, inside a 5.5 pt pulse ring.
- Divider at x = W − RZ: 1 pt, #C9D3E6 at 25 %, inset 3 pt top and bottom.
- **Right zone** (W − RZ … W − 6), right-aligned, size 10, tracking .05 em:
  - Normal: "Back in " #C9D3E6 + "4:12" #EAFCFF.
  - **Tapped:** "Back at " + "2:47 PM" #EAFCFF + "  ·  in 4:12". That is 104 pt, and the zone holds 109 pt. The worst case, "Back at 12:47 PM · in 1:04:12", is 119 pt, so drop to 9 pt when the text is wider than 109.
  - The layout never changes size.

### Lit path dots: always the part behind the ship
- **OUTBOUND:** dots from the **Moon to the ship** (`t ≤ u`) are lit #7FF3FF. Dots ahead of the ship are #5F7189 at 80 %.
- **AT EARTH:** all dots lit (the trip out is complete).
- **RETURNING:** dots from **Earth to the ship** (`t ≥ u`) are lit. Dots between the ship and the Moon are unlit.

Here `t` is each dot's position along the path, 0 at the Moon and 1 at Earth. The lit section grows behind the ship as it flies and never runs ahead of it.

### Chip
112 × 18, chamfer 5. Ship 10 pt at (13, 9) with flame. "Ship back in " #C9D3E6 + "4:12" #EAFCFF, size 10.5, at x 24. Chevron 1.5 pt #7FF3FF at x 101. Tapping it runs the existing station slide to the Launch Pad.

### Money pop: real payout
- **Text and style:** "+$20,000" at Lv1; Coder feeds the real amount. Inter (or system-ui) 900, 15 pt, #FFD84D, with a 3 pt #3A2200 outline drawn as a stroke under the fill.
- **Placement:** centred on Earth's x. Baseline 2 pt above the strip top (y 92–103 at 375, y 131–142 at 393). Clamp x so the text stays inside the HUD columns with 4 pt margin: left ≥ 12, right ≤ screenW − 68.
- **Widths:** "+$20,000" is 77.4 pt. **Max width: "+$999,999" = 86 pt**, at x 142–228 (375) and x 160–246 (393).
  - That leaves 134 / 152 pt on the left and **83 pt before the HUD column edge** (x 311 / 329) on the right.
  - It clears the strip top by 2 pt.
  - It overlays the bottom of the HUD's ore cell while it rises, because it is flying to the Money counter.
- Anything from $1,000,000 up should use the HUD's short form ("+$1.2M"), which is narrower.

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
| Money pop | +277.2, once per trip (lift-off pays nothing) | scale .6 → 1.1 → 1, **160 ms easeOutBack**. Rises 18 pt, **900 ms easeOutCubic**. Then the existing `flyChunks` to the HUD Money counter, and Money `.bump` (300 ms). After a reload or offline catch-up past +277.2, no pop plays: the money is already paid and is counted in the away summary. |
| Pulse | whole of AT EARTH | ring round the parked ship, scale 1 → 1.6, opacity .6 → 0, **1200 ms easeOutSine loop**. Ship bobs ±0.5 pt, **1600 ms sine**. |
| Turn-around | +338.8 | icon rotates 180°, **320 ms easeInOutBack**. Draw it already turned if `e − 338.8 ≥ 0.32`. |
| Lit dots | every frame | lit set = `t ≤ u` (OUTBOUND), all (AT EARTH), `t ≥ u` (RETURNING). Each dot fades in over **120 ms linear** as the ship passes it. |
| Landing flash | +616 | flash disc on the Moon, r 6 → 14 pt, opacity .9 → 0, **420 ms easeOutQuad**. Moon scale 1 → 1.12 → 1, **280 ms easeOutBack**. Then, 600 ms later, the strip slides up −8 pt and fades, **240 ms easeInCubic**. |
| Tap | strip | right zone cross-fades to the arrival time, **150 ms easeOutQuad**. Hairline brightens. Reverts after **3000 ms** or on the next tap. Arrival time comes from the device clock (`Intl.DateTimeFormat`, hour + minute). |
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
| chip_bg_112x18, chip_full_example | 112 × 18 | |
| money_pop_example_20000 | 90 × 20 | reference only; render the pop as text |

## Stills (`proofs/`)
**Backgrounds:**
- Launch Pad: a real game-camera render with the ship and fuel hoses hidden, because the ship is away (`_src/render_empty_pad.py`; same camera as the 8f2191c proofs).
- Chip: the Shipyard proof.
- The HUD and Eve bubble are drawn copies, there only to show position. The settings gear is left out, because Coder is moving it out of the band.

**Files** (each has an `_overlay` version with the band, the HUD-bottom line and a 2× zoom with exact y values):
- `pad_outbound_{375x667,393x852}.png`
- `pad_at_earth_{375x667,393x852}.png`: "+$20,000". The overlay also boxes "+$999,999" against the HUD column edge.
- `pad_returning_{375x667,393x852}.png`: lit dots run from Earth to the ship.
- `pad_returning_tapped_{375x667,393x852}.png`: "Back at 2:47 PM · in 4:12"
- `chip_shipyard_375x667.png`
- `strip_states_3x.png`: every state at 3×
