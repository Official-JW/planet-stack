# Planet Stack autocheck (Playwright, Chromium only)

A fresh-load smoke check of one build URL on two iPhone viewports. It uses real touch
swipes and taps, and prints a PASS / FAIL / WARN / n/a table. The exit code is 0 when
nothing failed, 1 on any FAIL, and 2 if the script itself crashed.

## Setup (once, about 300 MB, all inside this folder and gitignored)
    cd qa/autocheck
    npm install
    PLAYWRIGHT_BROWSERS_PATH=./browsers npx playwright install --only-shell chromium
The script sets `PLAYWRIGHT_BROWSERS_PATH=./browsers` itself when that folder exists.
Set `CHROME_PATH=/path/to/chrome` to use a different Chromium.

## Run
    PS_TESTER_CODE=NNNNN node autocheck.js                       # default target: https://official-jw.github.io/planet-stack/dev/
    node autocheck.js https://official-jw.github.io/planet-stack/live/
    node autocheck.js <url> --expect md5s.json --code NNNNN --name "QA Autocheck"
Flags:
- `--viewports 393x852,375x812`: the default viewports.
- `--dpr 3`
- `--out ./out`
- `--keep-shots`: keep the failure screenshots.
- `--load-timeout 90`: seconds.
- `--quiet`: no progress log on stderr.
- `--ts N`: QA fast-forward. Adds `qa=1&ts=N` to the URL (the game clamps N to 1–60; decimals are fine) and checks that
  `window.PS_QA.scale` is N and the `QA xN` corner badge shows (no badge at 1). Only the dev/ build has it, and only after a
  valid tester code has passed the gate; anywhere else the row is n/a.
- `--qa`: shorthand for QA fast-forward at 10×: adds `qa=1&ts=10` (`--ts N` overrides the 10). `--ts N` on its own also
  adds `qa=1`.
- `--qa-ignored`: for live/ (or any build that must not have fast-forward). Loads the URL with `qa=1&ts=10` (or `--ts N`),
  then checks there is no `window.PS_QA`, no `QA xN` badge, `__ps3d.SPD` is 1 and the game clock runs at 1.00× the wall
  clock over 3 s. Light mode: it skips Eve and the station walk (console / network rows still run). E.g.
  `node autocheck.js https://official-jw.github.io/planet-stack/live/ --qa-ignored --viewports 393x852`
- `--skip`: after the station walk, calls `window.PS_QA.skipToTouchdown()` once. PASS if the ship trip in flight reached
  touchdown (prints where it started, the money it paid and the game seconds skipped), n/a if there is no `PS_QA` or the ship
  is on the pad with no trip in flight, FAIL otherwise. On its own (no `--ts`) it adds just `qa=1`.
- The URL is used exactly as given (plus `qa`/`ts` from `--ts`/`--skip`), so other query flags pass straight through. dev/ ignores every QA flag except `qa` and `ts`.

`--expect` is a JSON object that maps path to md5, either at the top level or under `"files"`. QA Manager supplies it for each build:

    { "files": { "dev/main.js": "9f1c…", "dev/index.html": "ab12…" } }

A key matches a served path exactly or as a suffix. Short md5 prefixes are allowed. The
script fetches any listed file the page didn't load itself. No hashes are hard-coded.
Without `--expect`, it prints every md5 it saw and saves them to `out/md5-seen.json`.

## Dev code gate: where QA gets the code
dev/ opens with a 5-digit tester-code gate (`#gate`). The page checks the code against the
dev Worker (`https://planet-stack-dev.official-jw.workers.dev`, `GET /codes`, then `POST /lock`).
- The codes live in that Worker's KV namespace **`PS_DEV`, key `codes`** (see
  `QA/dev_build_checklist.md`).
- **Ask EM or the Director for a dedicated QA code.** Do not borrow a tester's code: each
  code locks to one device at a time (90 s lease), so a run would lock that tester out
  (`in_use`) or fail against them.
- Pass the code with `PS_TESTER_CODE=NNNNN` or `--code NNNNN`. It is never hard-coded,
  printed or saved.
- The script uses one random device id per run, so both viewports count as the same device.
  It closes pages with pagehide so the lock is released.
- With no code, the gate reports n/a and the build checks don't run.
- `?mock=1` (in-page codes 00000–00010) works only on localhost, e.g. a local `http.server`
  copy of dev/.

## What each check does (per viewport)
| Check | How |
|---|---|
| LOAD | A new Chromium context: no cache (CDP), empty storage, service workers blocked, isMobile, hasTouch, DSF 3, iPhone UA. Steps through the code and name gates, then waits for `__ps3d.coverGone`. Reports the cover time and which upgrade UI it found. |
| CONSOLE errors / NETWORK failures | Every console error, pageerror, requestfailed and HTTP ≥ 400 is a FAIL and is listed in full. |
| E2 Eve line N | Waits for Eve's first call, taps the toast, then samples about every 40 ms: text typed, talking or waiting, voice playing (WebAudio buffers and `<audio>` /eve/ plays, plus `PS_DEV.voice`), and a Next/Done cue. It FAILs if the cue shows before the text finishes or while the voice is playing, or if it says the wrong word (Next, or Done on the last line). If the build has no cue, it prints n/a with the timings. |
| NAV i Station | A real touch swipe to each of the 8 stations. Checks `__ps3d.S.site` and the `#name` label. If a swipe doesn't land, it is a FAIL and the script recovers with `goSite`. |
| SETTLE i | After every station switch the script waits until `S.site` is the new station, `camX` is within 0.5 m of its resting x (`i × PX/PADI`, i.e. i × 160 m) and `__ps3d.frames` has gone up since then. After 4 s it gives up with a WARN that shows site, camX, frames and the box's 1-minute load (WARN never changes the exit code). Builds without `frames`/`PX` fall back to "camX stopped moving". |
| E1 / TAP (new panel) | For each `__ps3d.upRects()` target on screen that belongs to this station (`UPT[].site`; site −1 = the roaming truck, always kept), it finds a point where the canvas is on top and `pickUp` returns that target, then taps it for real. Other stations' targets get one `skipped` info row. The hit test is `elementFromPoint`, which skips pointer-events:none layers like `#hud`; points below `#hud`'s real bottom edge are tried first, and a tap that only fit under the HUD is an info row. A "no clear tap point" WARN lists what the 25 grid points hit instead. The card must be that object (`upCur`, `#upName == UP[p].name`, and `#upKick` starts with the station name). Then it closes the card with a tap on X. |
| CARD Station: object | The card-title check (EM 10/31), from the same real taps (settle runs before every tap): `drill` (Mine) must open "Drill" at every viewport (393 and 375 by default); `padFuel` (Launch Pad fuel hoses) and `fuelPlant` (Refinery) must open a title starting "Fuel". **Pad tanks:** when padFuel has a tank box (gc-ui2: `UPT padFuel.add`) or the pad model has a `/tank/i` mesh, one extra real tap on the tanks must also open "Fuel"; otherwise an info row says "no pad tank meshes". **Coming soon:** gc-ui2 gives the 5 empty stations (Life Support, Cargo Space Dock, Shipyard, Habitat, Engineering) their own targets (`lifeSupport`, `dock`, `shipyard`, `habitat`, `engineering`); the title or kicker must contain "Coming soon". On older builds a station with no target of its own gets one real tap on its model (mid-screen if none is loaded). Title = `[data-card-title]` (its value, else its text) when the build has it, else `#upName` text; the row says `attr` or `fallback #upName`. gc-ui2 should show `attr` everywhere. Result: PASS, FAIL (wrong title) or NO CARD. NO CARD is a **FAIL when the build has `[data-card-title]`** and info on older builds. No glow or ring is checked (Director's spec is a soft glow on the object's own materials plus a centred card). Works with `--qa --ts 10`. |
| E1 swipe i→i+1 card open | Opens a card (using the hook for setup only), then really swipes on the scrim. The card must close and the station must advance. |
| E1 sheet (old sheet) | Real tap on the Upgrade handle `#grab`. The visible rows must match that station. It WARNs where the global sheet shows Mine rows at a station with no upgrade object of its own. |
| E1 swipe … sheet open | Swipes above the open sheet. The sheet must close or show rows for the new station. |
| MD5 | Compares against `--expect`. It FAILs if one path was served with different contents between viewports. The page's own document (served as `.../dev/`) counts as `dev/index.html`. A listed file the page didn't load is fetched from the target folder (`.../dev/` + `dev/main.js` → `.../dev/main.js`). If that fetch fails (e.g. 404) the row is a script ERROR, not a FAIL: exit code 2 when there is no real FAIL. |

**Old sheet vs new panel.** The script chooses by what is in the DOM after load:
- `#grab` + `#sheet`: the old drag sheet (live, qa3d-next before UI-1).
- `#upPanel` + `__ps3d.upRects`: the new tap-to-open panel (gc-ui1).
- `#upPanel` without the hook: `new-nohook`, so E1 is n/a.
- Neither: n/a.

## Moving targets, pad tanks and x order (EM 17:08)
- **Truck / ship:** before each tap the script waits up to 4 s for the target's screen rect to hold still (centre moves < 1.5 px over 300 ms).
  If the finger still lands on another object and that object's card opens, the row is **info** ("the card under the finger opened instead"), not FAIL.
  Missed taps are info when `--ts` is above 1 or the target never held still; otherwise WARN as before.
- **Pad tanks:** after closing the previous card the script waits (up to 4 s) for `__ps3d.uc.w === 0` (gc-ui2 card camera eased back) before it
  measures the tanks and taps. If it never gets there, the CARD row says so.
- **Station x / order:** when the build has `__ps3d.SX` and `__ps3d.ORD` (Life Support move: LS at x 910 between Shipyard and Habitat), settle uses
  `SX[site]` for the resting camera x and the NAV walk follows ORD (an info row lists it). Builds without them keep index order and `site × gap`.

## Load gate
Before it starts the browser the script reads `/proc/loadavg`. It starts only when the 1-minute load is under `--max-load` (default 10;
`--max-load 0` turns the gate off). While waiting it prints the current load every 20 s. After `--load-wait` minutes (default 20) it
gives up, prints why and exits 3 without starting a browser.

## Output and cleanup
- Progress goes to stderr. The table goes to stdout.
- `out/report.json` and `out/md5-seen.json` are written there; `out/` is gitignored.
- Failure screenshots are small JPEGs. They are deleted once the report is written unless
  you pass `--keep-shots`.
- No videos and no traces.
- The script launches one headless browser and closes it in `finally`.

## Hooks relied on
- `window.__ps3d`: `S`, `STATIONS`, `coverGone`, `camX`, `frames`, `PX`, `PADI`, `sheetOpen`, `ec`, `goSite`, `gateMsg`.
- New panel: `UP`, `UPT`, `upRects`, `pickUp`, `openUp`, `closeUp`, `upCur`, `upClosed`.
- Dev voice: `PS_DEV.voice`.
- QA fast-forward (dev/ with `?qa=1`, after a valid tester code only): `PS_QA.scale`, `PS_QA.skipToTouchdown()`, `#qaBadge`.
Hooks are used only to find targets and read state. All input is real touch.

## Limitations
- Chromium only, no WebKit, so it is not a Safari test.
- Audio is muted, but play timing is still measured.
- E2 is n/a in every current build: none has a Next/Done cue yet. When one ships, give it
  `#ecNext`/`#ecDone`, `[data-eve-cue]`, a Next/Done button in `#ecPanel`, or a
  `__ps3d.eveCue` hook.
- Moving targets such as trucks can drift off the tap point. That gives a WARN, not a FAIL
  (info for the truck and the ship when `--ts` is above 1, since they then move N× faster).
  It is a FAIL only if the target was still under the finger and no card opened.
- On a heavily loaded box a run takes 1.5–3.5 minutes. Under load the first tap on the old
  sheet handle sometimes needs a retry; that shows as a WARN.
