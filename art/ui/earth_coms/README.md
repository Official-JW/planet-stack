# Earth Coms · UI kit (Eve)

2D HUD overlay for Eve's "Earth Coms" radio calls, laid over the 3D game. Style: Mine concept B, sleek high-tech: white and graphite panels, cyan accent and glow, soft gradients.
Units: **pt** (= CSS px on iPhone). Reference screen 393 × 852 pt (iPhone 15/16), safe-area top 59 pt, home bar 34 pt.

**Source:** Jacob's photo `art/eve/eve_source_jacob_1408.png` (1408²). The portraits are crops and resizes of that photo with a light cool grade (shadows lean cyan, slightly cooler white balance, +4 % contrast). Her face is not redrawn or regenerated. Re-run with `python3 art/ui/earth_coms/_src/make_portraits.py` and `_src/make_tiles.py` from the repo root.
- Avatar crop box (source px): (322, 96) – (1002, 776), circular alpha mask with 4× supersampled edge.
- Feed crop box (source px): (112, 40) – (1052, 742): head to chest, the "Earth–Moon Communications Link" screen behind her on the left.

## Files and sizes

| File | px | pt | Bytes |
|---|---|---|---|
| eve_avatar_1x.webp / .png | 64 × 64 | 64 | 1,740 / 3,424 |
| eve_avatar_2x.webp / .png | 128 × 128 | 64 | 4,088 / 7,663 |
| eve_avatar_3x.webp / .png | 192 × 192 | 64 | 6,930 / 13,940 |
| eve_feed_1x.webp / .png | 150 × 112 | 150 × 112 | 4,016 / 10,189 |
| eve_feed_2x.webp / .png | 300 × 224 | 150 × 112 | 10,022 / 29,255 |
| eve_feed_3x.webp / .png | 450 × 336 | 150 × 112 | 17,584 / 55,824 |
| fx_scanline_1x4.png | 1 × 4 | drawn at 1 × 2 | 77 |
| fx_static_64.png | 64 × 64 | drawn at 32 × 32 | 1,304 |
| earth_coms.css | | | 15,622 |

- WebP is q80 (method 6), and every file is well under 40 KB. PNG fallbacks are 256-colour palettes (Floyd–Steinberg dither) to keep the kit small. iOS Safari 14+ always takes the WebP.
- **Kit total (all images + CSS): 181,678 bytes (≈177 KiB), under the 200 KB target.** An iPhone at 3x actually loads only avatar_3x.webp, feed_3x.webp, the 2 tiles and the CSS: **41,517 bytes**.
- Not counted (not shipped): `prototype.html`, `MOTION.md`, `README.md`, `_src/`, `proofs/`. The font is the shared `art/fonts/rajdhani-700-latin.woff2` (OFL), already in the repo.

## Layout (393 pt screen)

All layers are CSS/inline SVG, with no 9-slice bitmaps. Copy the markup between the `Earth Coms kit markup` comments in `prototype.html`, plus `earth_coms.css`.
`.ec-root` sits over the canvas with `pointer-events: none`. Its top is `env(safe-area-inset-top) + 8 pt` (`--ec-top`; the prototype simulates 59 pt). Add `viewport-fit=cover` to the page's viewport meta.

**Incoming toast** `.ec-toast`: 300 × 60 pt pill, centred, top = `--ec-top` (y 67–127 on a 393 × 852 screen).
- Avatar 44 pt (uses the 64 pt assets via srcset), with a 2 pt cyan ring and glow and two pulse rings.
- "INCOMING · EARTH COMS": Rajdhani Bold 14/16, tracking .12 em, #3FE0FF.
- "Eve · Director of Earth Comms": system 12/15. The role is shortened in the toast only; the panel shows the full title.
- Answer button: 40 pt cyan disc with a phone glyph.

**Call panel** `.ec-panel`: 373 pt wide (10 pt side margins), radius 18, 1 pt cyan hairline at 40 %, backdrop blur 14.
- Header (30 pt): light strip #F4F7FA → #D5DEE6 with a cyan underline. It holds "◆ EARTH COMS" (Rajdhani 16, .14 em, #1E252D), the live dot (8 pt #FF4D5E) with "LIVE", a 4-bar signal meter (3 pt bars, 5/8/11/14 pt high; `data-level="0–4"`), and × to skip (44 pt hit area).
- Body padding 10/10/12:
  - Video feed: 150 × 112 pt, radius 10, cyan hairline. The scanline tile multiplies at 55 %, and the static tile drifts at 10 % with a cyan glass vignette, all in CSS.
  - Name plate (right column, 193 pt): "EVE" in Rajdhani 24, then "Director of Earth Communications" (system 12/15 #93A6B5, 2 lines). Screen readers get "EVE · Director of Earth Communications".
  - TX box: a 5-bar waveform (4 × 22 pt bars, 3 pt gap) and a label, "TRANSMITTING" (cyan) or "STANDING BY".
  - Dialogue box: full width (353 pt; text column 315 pt). System font 15/20 #E8F1F6, padding 9/26/9/12. **Auto height, 2–4 lines** (min 60, max 100 pt box), with the "tap to continue" chevron at bottom-right.

| Dialogue lines | Panel height | Panel bottom on 393 × 852 |
|---|---|---|
| 2 | 236 pt | y 303 |
| 3 | 256 pt | y 323 |
| 4 | 276 pt | y 343 |

The upgrade sheet (top ≈ y 616) is never touched. The panel overlaps the top of the station focus band (Mine view y 188–572) by up to 155 pt while a call is open. Approved by Director: while the panel is open, Coder eases the camera down by the panel's height (`--ec-panel-h-2/3/4`) with `camera.setViewOffset`, 300 ms each way on the panel's curve. See MOTION.md. The toast (to y 127) clears the focus band.

## Eve's script and text fit
The lines are the draft script from `TEAM_PLAN.md` § "Eve and Earth Coms", including the updated line 5. They are still awaiting Jacob's OK, so the box is flexible, not fixed. They're measured in the 315 pt text column at 15/20 (Inter as the SF Pro stand-in; Arial and Roboto give the same line counts):

| # | Trigger | Chars | Lines |
|---|---|---|---|
| 1 | During the landing | 145 | 4 |
| 2 | First ore | 101 | 3 |
| 3 | First upgrade affordable | 75 | 2 |
| 4 | First cargo ready | 65 | 2 |
| **5** | **At the first fuel check (updated)** | **157 (longest)** | **4** |
| 6 | First risk window | 116 | 3 |
| 7 | First delivery home | 99 | 3 |

**The longest line is #5, which wraps to 4 lines at 1x** with about 130 pt to spare on the last line (roughly 18 more characters). A line that runs past 4 lines should be split into two taps; the prototype supports multiple lines per beat (`lines[]`).

## Call rules (Director)
- Tutorial calls: add `data-tutorial` to `.ec-toast`. No timeout; pulses until opened. Try `prototype.html?tutorial=1`.
- Story calls: 8 s timeout, slide away, then `.ec-badge` on the Earth Coms button shows the missed count (`<span class="ec-badge" data-count="1">1</span>`).
- Heard = panel opened. The tutorial step advances on panel close.

## Colours

| Hex | Use |
|---|---|
| #3FE0FF | cyan accent, glow, kicker text, chevron, waveform |
| #12A9CF | cyan deep (gradients, meter bars on the light header) |
| #F4F7FA → #D5DEE6 | white/silver header strip |
| #0E1217 / #161C23 / #222A33 / #2F3944 | graphite 900 / 800 / 700 / 600 |
| #1E252D | ink on the light header |
| #E8F1F6 | dialogue text |
| #93A6B5 | secondary text (role, STANDING BY) |
| #FF4D5E | live dot |

## Fonts
- Headings and labels: Rajdhani Bold, shared OFL font.
- Dialogue: `-apple-system, "SF Pro Text", Inter, Roboto, "Helvetica Neue", Arial`. On iPhone that is SF Pro; the proofs were rendered with Inter.

## Motion
See `MOTION.md`, which lists every duration, easing curve and the reduced-motion fallback. `prototype.html` plays the whole sequence.
- Proof URLs: `?shot=1&state=toast|panel&line=1-7&freeze=800`, with `&talk=N` for a mid-typing frame and `&rm=1` for reduced motion.
- Use `?autoplay=1` to run all seven beats.

## Proofs (`proofs/`)
- `mockup_toast_393x852.png`, `mockup_toast_1179x2556.png`: toast over the gray station placeholder.
- `mockup_panel_393x852.png`, `mockup_panel_1179x2556.png`: open panel showing line 5 (longest, 4 lines).
- `mockup_panel_talking_393x852.png`: mid-typing line 3, with the waveform active.
- `contact_sheet.png`: every asset at 1:1, plus the overlay tiles, palette and components.
