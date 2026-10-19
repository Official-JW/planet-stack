# Truck lock — Gate A

**Adopted truck:** the software 3D truck already in `PREVIEW · 12:15` (`game-1215.js`).

- Glass cab
- Tracks roll with travel
- Empty bed and full bed use the same body (ore is a load state, not a second sheet)

**No second painted truck sheet.** Code draws the one truck. The yard sheet (`road-1125.png`) has the baked still truck / ghost cab / ore-on-platform painted out so Jacob never sees two trucks.

**Motion (Director locked cycle, 2026-10-19):**

1. Starts parked at `dump_stop_px` (340,370) with its rear to the ore bin, and tips.
2. Drives out the bay door nose-first onto `centerline_px`.
3. Follows the road nose-first to the cave, goes in rear-first, and comes back out nose-first.
4. Home: drives nose-first to point 0 (360,378), then backs the short leg through `bay_door_rect` to `dump_stop_px`.
5. That short bay leg is the **only** reversing. The cycle repeats from the tip.

**wheel-0.png / wheel-1.png / wheel-2.png:** confirmed absent on disk under `art/`, `qa/`, and `preview/`. Not invented. Do not add loose wheel PNGs.

Date: 2026-10-19 (Gate A).
