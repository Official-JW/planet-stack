# Why the floors look blurry, and how to fix it (for Game Coder)

These findings come from a read-only review of `game.js` and `index.html` (commit da584f4). The renderer is a Canvas 2D context (`#cv`). It does not use PixiJS or Phaser, so there are no mipmaps or `autoDensity`; everything goes through `drawImage` with bilinear smoothing.

## The causes, most important first

1. **DPR is capped at 2 (`game.js:111`):** `maxDPR=Math.min(2,window.devicePixelRatio||1)`. iPhones are DPR 3, so the backing canvas has only 2/3 of the screen's pixels and the browser upscales it 1.5× with CSS. That alone makes everything soft.
2. **Adaptive resolution steps DPR down to 1.5 or 1 (`game.js:322-323`):** if the frame rate drops below 50 fps for 2 s, `maxDPR` drops 0.5 at a time and never comes back up. On an iPhone this probably fires during the first heavy seconds (image decode and the globe band rebuild), leaving the game at DPR 1 to 1.5. That's a 2–3× upscale and very blurry.
3. **Non-integer world scale (`SC=W/390`, `game.js:113`):** an iPhone 15 is 393 pt wide, so SC = 1.0077, and every sprite is resampled by a non-integer factor. On top of that, `ctx.translate(tf.x,tf.y); ctx.rotate(tf.a)` (`render()`, buildings) places the towers at fractional, often rotated positions. Rotated and sub-pixel `drawImage` calls are always filtered, which softens 1 px lines.
4. **Squash and stretch on every floor:** `ctx.scale(sx,sy)` for the build, upgrade and tap effects is fine while it plays, but make sure it returns to exactly 1 (it does), and snap the translate to device pixels when idle (see fix C).
5. **Art was palette-reduced to 256 colours (Pillow quantize, my doing):** this causes banding in the gradients and dither noise. At high DPR the dither reads as softness or grain. **This is fixed in the new art pack**: every file is now full-colour RGBA WebP.
6. **3x art drawn at 2x or lower DPR:** with DPR at 2 or less, a 1080 px floor gets downscaled. Canvas 2D has no mipmaps, so a big downscale with `imageSmoothingQuality` set only on the main context can alias, and the band context `bctx` never sets it at all.
7. **Globe band and sky caches are rebuilt at the current DPR:** they inherit whatever reduced DPR item 2 picked.

## Concrete code changes

**A. Honour the full device DPR and stop the permanent downgrade.**
```js
let maxDPR = Math.min(3, window.devicePixelRatio || 1);   // was min(2, …)
// adaptive: only lower to 2 (never below), and only after 5 s of < 40 fps; re-check upward every 10 s
if (perfN/perfT < 40 && maxDPR > 2) { maxDPR = 2; resize(); }
```
If performance is the worry, keep the canvas at full DPR and cut overdraw instead (see E).

**B. Pick the art set by DPR (new folders in this pack).**
```js
const ART_SCALE = (window.devicePixelRatio || 1) > 2 ? 3 : 2;          // @3x top tier, @2x otherwise
const A = `art/moon/@${ART_SCALE}x/`;
// every atlas JSON has meta.scale; spr() already divides by logical size, so nothing else changes
```
On a 3x phone the @3x set maps 1:1 to device pixels (a 360 pt floor is 1080 px). Everything is WebP q92 atlases (pages ≤2048 px; the full-screen backgrounds are single 1170×2532 images). `_masters/` (6x lossless) is source only and must never be shipped or loaded.

**C. Snap to device pixels and use integer-friendly scaling.**
- Use `SC = 1` and centre a 390 pt world column (letterbox the extra 3 pt with the sky), *or* round so that `DPR*SC` hits a clean ratio: `SC = Math.round(W/390*DPR*4)/(4*DPR)`.
- When `|tf.a| < 0.001` (the tower at rest, centred), skip `ctx.rotate` and round the translate: `ctx.translate(Math.round(tf.x*DPR*SC)/(DPR*SC), Math.round(tf.y*DPR*SC)/(DPR*SC))`. Rotate only while the camera is moving.
- Snap the floor x position (`-180`) and the astronaut x to whole device pixels the same way.

**D. Smoothing settings on every context.**
```js
for (const c of [ctx, bctx, skyC?.getContext('2d')]) if (c) { c.imageSmoothingEnabled = true; c.imageSmoothingQuality = 'high'; }
```
Set this again after every `cv.width=` (resizing a canvas resets its state).

**E. Performance headroom so the DPR can stay high.**
- Cache each tower (static floors) into an offscreen canvas at the current DPR. Rebuild it only on build or upgrade, then draw the small animated layers (see `ART_SPEC.md`, "Layered floor animation") on top. That swaps seven 2160 px `drawImage` calls per frame for one blit plus about 10 small ones.
- The globe band redraws 170 slices every frame. Cache it per integer pixel of `u0`, or draw it at DPR 2 in its own canvas (it's soft texture, so the blur won't show there).
- Use `createImageBitmap(img)` for every sprite after loading. It decodes off the main thread and stops the first-seconds stall that trips the adaptive DPR.

**F. Don't preload the old top-level 3x PNGs once the @3x/@2x sets are used** (`index.html:5`). Preload the chosen set's static floor WebPs instead.

## Quick test
Add `?dbg=1` to log `devicePixelRatio`, `maxDPR`, `cv.width/innerWidth`, and `SC`. On iPhone you want DPR = 3, `cv.width/innerWidth` = 3 and SC = 1 (or a rounded value). Then compare a crop of the Oxygen floor's "PEM-1" tag: it should have crisp 1 px text edges.
