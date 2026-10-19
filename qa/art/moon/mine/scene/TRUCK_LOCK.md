# Truck lock — Gate A

**Adopted truck:** the software 3D truck already in `PREVIEW · 12:15` (`game-1215.js`).

- Glass cab
- Tracks roll with travel
- Empty bed and full bed use the same body (ore is a load state, not a second sheet)

**No second painted truck sheet.** Code draws the one truck. The yard sheet (`road-1125.png`) has the baked still truck / ghost cab / ore-on-platform painted out so Jacob never sees two trucks.

**Motion (Director 2026-10-19):** Road travel is forward nose-first on `centerline_px`. At the bay only: reverse in along the short leg from point 0 through `bay_door_rect` to `dump_stop_px` (340,370), tip with rear at the hopper, then drive out forward. No reverse on the road itself.

**wheel-0.png / wheel-1.png / wheel-2.png:** confirmed absent on disk under `art/`, `qa/`, and `preview/`. Not invented. Do not add loose wheel PNGs.

Date: 2026-10-19 (Gate A).
