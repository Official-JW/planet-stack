# Earth Coms · Motion spec

All values are implemented in `earth_coms.css` (CSS) and the `M` constants at the top of the script in `prototype.html` (JS timing).
Open `prototype.html` and press **▶ Play full sequence** to see all seven beats, or pick a beat and tap through by hand.
Only `transform`, `opacity` and `filter` animate, so everything stays on the compositor (60 fps in iPhone Safari).

## Easing tokens (`.ec-root` custom properties)

| Token | Curve | Used for |
|---|---|---|
| `--ec-ease-out-back` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | toast slide-in (small overshoot = "juicy" landing) |
| `--ec-ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | panel expand, content rise, waveform settle |
| `--ec-ease-in` | `cubic-bezier(0.5, 0, 0.75, 0)` | everything that leaves (tap-out, CRT-off, slide-out) |
| `--ec-ease-pulse` | `cubic-bezier(0.22, 0.61, 0.36, 1)` | avatar ring pulse |
| `--ec-ease-wave` | `cubic-bezier(0.45, 0, 0.55, 1)` | waveform bars, answer-button breathe, chevron bob, live dot |

## Sequence (t = 0 at the beat trigger)

| # | Step | Duration | Easing | What moves |
|---|---|---|---|---|
| 1 | **Toast slide-in** (`.ec-toast.is-in`) | 420 ms transform, 160 ms opacity | out-back / linear | `translateY(-(100% + top))` → 0; opacity 0 → 1 |
| 2 | **Ring pulse loop** (while toast waits) | 1600 ms, infinite; 2 rings, 2nd delayed 800 ms | pulse | ring `scale(1)` → `scale(1.45)`, opacity .75 → 0 |
| 2b | Answer-button breathe | 1600 ms, infinite | wave | cyan glow 8 → 18 px → 8 px |
| 2c | Untapped timeout | after 8000 ms | — | toast plays the slide-out (`.is-out`, step 7 timings); beat is **not** marked heard |
| 3 | **Tap → expand** | toast out 160 ms (in, `scale(.92)` + fade); panel 380 ms (out-expo) | | panel `translateY(-4px) scale(.80,.24)`, radius 30 → `none`, radius 18; opacity reaches 1 at 35 % |
| 3b | Content rise | 240 ms, out-expo; video row delay 90 ms, dialogue box delay 160 ms | | `translateY(8px)` + opacity 0 → rest |
| 4 | **Video connect flicker** | **250 ms**, linear, starts 160 ms after the tap | | keyframes: 0 % scaleY .04, brightness 2.2, desaturated → 20 % full height → 32 % opacity .25 → 46 % 1 + 2 px jitter, −12° hue → 60 % .55 → 74 % 1 → 100 % clean. Static overlay bursts .9 → .45 → .10 over the same 250 ms |
| 5 | **Typing** | starts 420 ms after the tap | — | **30 ms per character** (≈33 chars/s); +120 ms after a comma; +240 ms after `. ! ?` followed by a space. Blinking cyan caret, 900 ms `steps(1)` |
| 5b | **Waveform while talking** (`.is-talking`) | bars 1–5: 420 / 360 / 480 / 390 / 450 ms, `alternate infinite`, phase offsets 0 / −120 / −240 / −60 / −300 ms | wave | `scaleY(.22)` ↔ `scaleY(1)` (22 pt bars). Label reads TRANSMITTING (cyan). On line end the bars settle to `scaleY(.18)` in 200 ms (out-expo) and the label goes STANDING BY |
| 5c | Tap while typing | instant | — | the rest of the line appears at once, waveform settles |
| 5d | **Tap-to-continue chevron** (`.is-waiting`) | fade-in 160 ms linear; bob 900 ms alternate infinite | wave | `translateY(-1px)` ↔ `translateY(2px)` |
| 6 | Next line (tap) | — | — | text box clears, step 5 restarts; box height animates only by line count (auto height, 2–4 lines) |
| 7 | **Dismiss / slide-out** (tap after the last line, or ×) | 120 ms CRT-off on the feed, then 260 ms slide | in | feed `scaleY(.02)` + brightness 3 (120 ms); panel `translateY(-(100% + top + 16px))`, opacity → 0 (260 ms, starts at 120 ms). Total 380 ms |

Other loops: static noise drifts with `steps(4)` over 400 ms at 10 % opacity; the LIVE dot fades 1 → .35 over 1200 ms, alternate.

## Interaction rules
- The call never blocks gameplay: `.ec-root` is `pointer-events: none`; only the toast and the panel take taps.
- Tap the toast = answer. Tap the panel = finish the line → next line → hang up. × in the header = skip the call (44 pt hit area).
- **Heard = panel opened** (Director ruling). A tutorial step started by a call moves forward only when the panel **closes**.
- **Tutorial calls** (`data-tutorial` on `.ec-toast`): never time out. The toast keeps pulsing (`ec-tut-pulse`, 1200 ms, `--ec-ease-wave` ease-in-out, infinite: scale 1 → 1.03 plus cyan glow 10 → 22 px) until the player opens it. Covering the HUD while ringing is fine.
- **Story calls** (no flag): 8000 ms timeout, then the `.is-out` slide-away. The beat stays unheard and the Eve bubble (`.ec-bubble`) shows `.ec-badge` at its top-left (red dot, count in text and `data-count`) until the player plays it back. Hide it at 0.
- **Bubble while ringing** (`.ec-bubble.is-ringing`): a tutorial call uses `ec-tut-pulse-b`, 1200 ms, `--ec-ease-wave`, infinite (scale 1 → 1.08, glow 10 → 24 px). A story call gets a soft ring: `ec-ring`, 2000 ms, `--ec-ease-pulse`, infinite (scale 1 → 1.45, fading out). Ringing stops on answer or timeout. Toast or bubble tap = answer.
- **Tabs**: switching is instant, with no animation. The panel opens with the same expand (380 ms) on Task, or on the call view if a call is waiting. Close = ×, chevron, tap outside, or swipe up > 40 px, all using the same dismiss motion.
- **HUD fade:** the game's HUD container gets `.ec-hud` (a 150 ms linear opacity transition). Add `.ec-hud-dim` when the toast enters (opacity 0), and remove it once the toast's slide-away (260 ms) or tap-out (160 ms) ends, so the pills fade back in over 150 ms. `.ec-hud-dim` also turns off pointer events.
- **View shift uses the real height:** Coder reads `panel.getBoundingClientRect().height` after layout, on open and after every tab switch or line change, and re-eases `setViewOffset` (300 ms) whenever it changes. The `--ec-panel-h-*` values are reference numbers; the measured height wins.
- **View shift:** while the panel is open, Coder eases the camera down by the panel's height with `camera.setViewOffset`, 300 ms each way (`--ec-view-shift-ms`). In: `--ec-ease-out-expo`, starting with the panel expand. Out: `--ec-ease-in`, starting with the dismiss. Heights: `--ec-panel-h-2/3/4` = 272 / 292 / 312 px for 2 / 3 / 4 dialogue lines (including the 36 pt tab bar), and `--ec-panel-hmax-tabs` = 268 px as the MAXIMUM for Task / Updates / Calls (content-sized; `.ec-list` scrolls only past it); re-ease if the line count changes on the next tap.

## Reduced motion (`.ec-reduced` on `.ec-root`, set it when `matchMedia('(prefers-reduced-motion: reduce)')` matches)

| Step | Fallback |
|---|---|
| Toast in / out | opacity fade only, 150 ms linear, no slide or scale |
| Ring pulse | no animation; one static ring at `scale(1.18)`, opacity .6; button does not breathe |
| Expand | panel cross-fades in 150 ms linear; no scale, no content rise |
| Connect flicker | replaced by a 150 ms fade of the feed; static frozen at 8 % |
| Typing | whole line appears at once; no caret |
| Waveform | static bars at 40 / 70 / 100 / 70 / 40 % while the line is up |
| Chevron | shown, no bob |
| Dismiss | 150 ms fade-out, no CRT-off, no slide |
| Live dot | solid, no pulse |
| Bubble ring / pulse | no animation; static ring (3 px + 16 px glow) |
| Tutorial pulse | no pulse; static cyan ring (2 px + 14 px glow) |
| View shift | instant offset, no ease |
