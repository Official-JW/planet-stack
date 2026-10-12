# Tier art handoff: Water, Nuclear, Refinery (L10-L50)
- Logical size: 360x120, pivot (0,120). Tiers anchor at floor origin (0,0).
- Use @3x when devicePixelRatio > 2, otherwise @2x.
- JSON: {base, layersImages[], scale, logicalSize, pivot, fps:12, frames:16, loop:true, layers:[{x,y,w,h, frames:[{page,x,y,w,h} x16]}]}
- Layer x/y/w/h are logical points. Frame rects are pixels in layersImages[page].
- Draw order (cumulative): base room, then t10, t20, t30, t40, t50, up to the current tier. Same as Oxygen.
- Base rooms: floors/floor_water.*, floors/floor_nuclear.* and the NEW floors/floor_refinery.* (flat file).
- Tiers: floors/tiers/floor_{water,nuclear,refinery}_t{10,20,30,40,50}.{json,webp,_layers.webp}
- Every JSON has exactly one layers page. Largest page is 2028 px.
- Total shipped: 2,700,987 bytes in 96 files (48 at @2x, 48 at @3x). Never ship _masters/.
- Previews: art/moon/{water,nuclear,refinery}_tiers.png
- Refinery is not wired into game.js yet. That's yours to wire.

## Update 2026-10-12: legibility pass
- Water L30 glass main moved up 2.4 pt and the L50 gold bands no longer cover the DIST-1 tag. Water tiers: @2x 256,813 / @3x 403,213 bytes.
- Base rooms floor_water and floor_nuclear re-exported with every label >= 3.5 pt (10.5 px @3x): ICE FEED (was REGOLITH ICE FEED), SE-1/SE-2 (were STIRLING), DOSIMETER, SCRAM RDY.
  - floor_water.*: @2x 203,498 / @3x 335,895 bytes (was 200,134 / 331,487)
  - floor_nuclear.*: @2x 225,394 / @3x 371,046 bytes (was 221,468 / 365,218)
  - These base files are not included in the tiers total above.
