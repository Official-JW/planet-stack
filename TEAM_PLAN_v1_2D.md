# Planet Stack — Finish Plan

**From:** Game Coder, for the whole bot team
**Date:** 2026-10-19
**Status of the running preview:** `PREVIEW · 12:15 · ON` on https://official-jw.github.io/planet-stack/preview/
**Live site:** do not touch. Jacob’s save stays on the older build until Playtester says go and Game Director signs the economy.

This is the plan. Read it before changing the mine, the road, the truck, or a price. The last two weeks were the same bugs shipped again under a new timestamp. That stops here.

---

## 1. What the game actually is

Planet Stack is a one-thumb lunar factory. The player swipes between stations, builds floors, and watches the work happen.

The promise, in one sentence: **a truck you believe leaves the bay, follows a road you believe, goes down the tunnel, comes back full, and dumps into the right bin. A crane loads only what is really on the pad. The ship leaves. Money comes back.**

If that loop is fake, the rest of the game does not matter. Roofs, tiers, and engineering rooms are already good. They wait.

Approved shape, still in force:

- Flat moon. No globe.
- Stations in swipe order: Life Support, Mine, Takeoff & Landing, Cargo Space Dock, Habitat, Shipyard, Engineering.
- Takeoff & Landing is the old tank farm. It is its own stop. Crates are wheeled from there to the Cargo Dock. The crane loads only the pad.
- Mine starts with Rover Bay. Crusher, Separator, and Packing unlock in order.
- Cargo is helium-3 and platinum. Refine about 3×. Ship it to Earth. Early trips are shorter. Asteroid risk sits on the solar-cycle window. Do not invent new numbers.
- Crew starts at 4. More crew only come back on a cargo run, requested by role, 4 per trip.
- Original art only. No real brands, NASA, or SpaceX.
- iPhone Safari and desktop. 60 fps. Permissive licenses only.

The base grew past “4 stations, 10 floors.” That growth is already in the code and the art packs. Do not rip it out. Finish the front door first, then button the rest.

---

## 2. The loops we are not allowed to repeat

These are the bugs Jacob has already rejected, more than once. If a build still shows one of them, it is not a build.

| # | What kept coming back | The rule from now on |
|---|---|---|
| 1 | A new truck drawn on top of the truck that was already sitting on the road | There is one truck. Do not spawn a second one. Do not slide a photo of the old one. |
| 2 | Only the paint, the bucket, or the text moves. The truck stays parked | The whole truck moves. Wheels, cab, and bed stay one rigid body. |
| 3 | The truck flips upside down because the canvas is spun by the full road angle | Do not `rotate()` the truck by `atan2(dy, dx)`. A small slope lean is allowed, about ±12°. Nose direction is a 3D yaw, not a flip. |
| 4 | Side view while the road runs straight at the camera | If the road runs toward or away from the camera, show the front or the rear. Side view only when the road runs across the screen. |
| 5 | The whole body bounces to fake suspension | The body stays on the path. Only the wheels compress. |
| 6 | A painted ghost of the old truck left on the road | If a still truck is baked into the yard sheet, paint it out before shipping. Jacob should never see two trucks. |
| 7 | A flat gray road with a dashed yellow line drawn over the painting | Code does not invent a road. Art paints the road into the yard sheet. Code drives the centerline Art provides. |
| 8 | The truck slides off to the left of the cave instead of going down the tunnel | Approach the mouth on a straight line, show the rear, get smaller as it goes in. Coming out starts small and grows. It does not vanish. |
| 9 | Ore label or bed text mirrored when the truck turns around | Labels are not mirrored. Flip the model, not the words. |
| 10 | Tracks turned 90°, cab with no glass, or a leftover painted cab | Tracks roll the way the truck travels. The cab has glass. No leftover paint. |
| 11 | Preview opens on a broken canvas: HUD only, ground gone, or last week’s theme | Before saying “refresh,” load the preview, confirm the corner tag, and look at the mine. If the ground is gone, do not tell Jacob to reload. |
| 12 | A version Jacob liked gets replaced by an older bug | If he says he likes a version, the next build must still contain that. Say which tag you started from. |
| 13 | Dev preview is not a new game, or money is not unlimited | `?dev=1` is a fresh save: unlimited money and crystals, a short card that says what to tap to make money. Do not share the live save. |
| 14 | Prices, crane times, or pack costs change inside an art fix | Art and animation changes do not touch economy numbers. Those wait for Game Director. |

---

## 3. What is true right now

Checked against the repo on 2026-10-19, not against memory.

**Serving.** Preview and QA both load `game-1215.js`. Corner tag is `PREVIEW · 12:15`. Live root is an older build and stays that way.

**Mine truck, in that build.**

- The gray ribbon road is gone. What is left is a faint pair of ruts and a few lamps. Jacob already called the ribbon hideous. The ruts are not the finished road either.
- On the stretch that runs at the camera, the truck shows its front or its rear, and the wheels stay down.
- It drives into the bay, lifts the bed, and drives back out. The dump is not locked to the ore bin yet.
- The tunnel entry shrinks into the mouth. It is closer to “straight in” than the old leftward slide. It is not the finished shot: no real sense of driving down the shaft, and no clean drive out that grows as it returns.
- The body does not bob. Independent suspension is still not in.

**What other people already finished, and code already uses.** Do not rebuild these.

- Flat moon, painted ground strip, walkway tubes, elevator looks, Life Support floors and their tiers.
- Habitat, Shipyard, and Engineering room art is wired: `ship_assembly`, `eng_cnc`, `roof_habitat`, and the matching packs. `HANDOFF_rooms.md` still says none of those ids are in `game.js`. That note is stale. Art updates the handoff. Nobody re-exports those rooms.
- Takeoff & Landing is its own swipe. The mule wheels a crate toward the Cargo Dock. The crane loads the pad only.
- Low-power fade, welcome-back collect, swipe, toast clearance, and the ground-strip fade were fixed in earlier QA rounds. Do not reopen them unless a new phone shot shows them broken.

**What is still open from the other chats.** This is the cross-check. Do the open item. Do not redo the done item.

| Source | They were still on | What 12:15 already did | What is actually left |
|---|---|---|---|
| Art, mine yard | Approved yard sheet, cave, lamps, no “3 REVERSE INTO BAY” callout | Sheet is on screen, under the tower. The still truck was supposed to come off the sheet. | Paint the real road into that sheet: a packed-dirt path with a 90° curve that meets the bay door on the ground, wider in the foreground, soft edges, the existing lamp style. No gray overlay. Deliver a centerline in image pixels. |
| Art, truck | Dump-truck sheets, glass cab, correct track direction, astronaut and ship refreshes from the art chat | Code draws one software 3D truck. It is not the painted sheet. | Either adopt the 3D truck as the approved truck and stop sending a second sheet, or deliver one turntable of the approved truck (front, rear, 3/4, empty bed, full bed, bed tipped) that code matches. Do not send both. Update astronauts and the ship only after the truck is locked. Uncommitted `qa/art/moon/mine/scene/wheel-0.png`, `wheel-1.png`, `wheel-2.png` are not in git. Commit them or delete them. Do not leave them loose. |
| Art, rooms handoff | “Wire shipyard and engineering, refinery not in game.js” | Assembly, engineering rooms, and habitat roofs are already referenced. | Re-read `game.js` before drawing anything new. If refinery is still unwired, say so in one line. Do not re-pack rooms that already play. |
| Art, roofs / launch tower | Roofs pack and the shipyard launch tower were a later load | `roof_habitat` and `roof_engineering` are referenced. | Confirm on a phone shot that Habitat and Engineering show their roofs and Shipyard shows the launch tower. If a roof is missing, that is a coder bug, not a new painting. |
| Game Director | Crane fill time, new-room boosts, packing price | Coder did not change prices in the 12:15 truck work. An older note still needs a ruling: a full hold of 12 loads in about 91 s, crane tiers are +10% per 10 levels. New rooms still use a placeholder boost. Packing was set to $1,800 in an earlier QA pass. | Sign those three numbers or replace them. No one else picks them. Also confirm the station list in section 1 is canon. |
| Playtester | Phone passes that kept failing on the truck, the ground, and the HUD | Ground and HUD fixes from the earlier no-go list are in this branch. The truck is not signed off. | Do not start a new full pass until Art’s road sheet and one truck cycle are in preview. Then run the checklist in section 6 on a phone, with screenshots, against the corner tag. |
| Game Coder (this chat) | Make the parked truck drive, stay upright, enter the cave, dump in the bay | 11:30 kept the wheels down. 12:05 added a curve and a dump, and also added the gray road Jacob hated. 12:15 removed that road and pointed the nose along the path. | Next coder change waits for Art’s painted road and centerline. Then drive that line. Do not draw another road in code. |

---

## 4. How we work until it is done

1. **One preview.** https://official-jw.github.io/planet-stack/preview/ is the only build Jacob should have to open. QA can move first. Preview catches up the same day or it is not done.
2. **The corner tag is the version.** If the tag is not the one you just pushed, he is not looking at your work. Do not argue with a screenshot of an older tag.
3. **Look at it the way he does.** Phone-shaped crop, mine station, the truck at three times: leaving the bay, mid-road, in the tunnel. If you would not send that crop to him, do not push.
4. **Art leads the picture. Code leads the motion. Director leads the numbers. Playtester leads “done.”** Crossing those lines is how the gray road happened.
5. **A fix names the tag it started from** and the one bug it closes. No drive-by refactors. No second truck “just to try.”
6. **Saves.** Preview and QA use their own keys. Never write the live save.

---

## 5. The order of work

Do not skip ahead. Each gate needs Playtester’s phone shots and, if a number changed, Game Director’s yes.

### Gate A — The mine, believable

This is the whole product until it is true.

**Art**

- Paint the road into the yard sheet. Packed regolith, tire ruts, soft edges, lamps like the ones already in the scene. It curves about 90° on the ground and ends at the rover-bay door. It does not climb the floor art and it does not cross the cave rock.
- Give Coder the centerline as a short list of image pixels, plus the cave-mouth rectangle and the bay-door rectangle.
- Paint out any still truck, ghost cab, or “reverse into bay” text.
- One truck design. Glass cab. Tracks that roll forward. Empty bed and full bed are the same truck.

**Coder, only after that sheet lands**

- Drive the centerline. One truck.
- Cycle, about 45–60 seconds, and then it loops:
  1. Start inside the bay, rear toward the ore bin, bed down.
  2. Bed tips, load leaves into that bin, bed settles.
  3. Drive straight out the door, nose first.
  4. Follow the curve. Nose matches travel. Body quiet. Wheels compress.
  5. At the cave, turn to show the rear and drive into the mouth, getting smaller, staying inside the opening.
  6. Hold inside.
  7. Come out small, grow, turn onto the road, return, back into the bay.
- Bed full on the way out of the cave, empty after the dump.
- No new road drawing. No second sprite. No price change.

**Playtester**

- Phone, Safari, the new tag. Pass only if all six steps read without a screenshot that looks like the old bugs in section 2.

### Gate B — Pad and dock, already close

- Takeoff & Landing reads as a place a ship lands, not a tank farm and not a second dock.
- The mule’s path from that pad to the cargo dock is one clean motion. Nothing walks through the crane handler.
- The crane loads one container at a time into the hold. Leftovers stay on the pad. The button says what is loaded, not what is merely nearby.
- Game Director signs the 91-second fill, or gives the number that replaces it, before this gate closes.

### Gate C — The base you already built

- Every station that has art shows that art: floors, tiers, roofs, the shipyard tower.
- Empty floors show the build button and the real price from data, not a stale label.
- Low power, welcome back, and the goal card still clear the HUD. Do not restyle them.
- Astronauts on the walkways and in the bay use the latest approved sheets, once Art says which files those are. Until then, leave the ones that are already on screen.

### Gate D — A new player can make money without a tour

On `?dev=1`, and later on the real first session:

- Fresh save. The goal card says the next tap in one line: build the thing, watch the truck, pack a crate, launch.
- Unlimited money and crystals only in dev. The real game uses the start grant Game Director already set.
- The first minute shows the truck cycle once, so the picture teaches the verb.

### Gate E — Ship it

- Playtester writes a go on preview, with the tag.
- Game Director writes a go on the numbers that changed.
- Only then does anyone copy preview to the live link.
- Live saves are not wiped.

---

## 6. Playtester checklist

Run this on a phone. Fail the build if any line is a no.

**Mine**

- One truck. No ghost. No second rover.
- Wheels on the ground the whole time it is on the road.
- Nose points where it is going. Rear goes into the tunnel. Front comes out.
- It gets smaller inside the tunnel and larger when it comes out. It does not blink off.
- The dump happens at the ore bin, then the truck leaves the bay forward.
- The road looks like the rest of the painting. No gray ribbon. No dashed highway line.
- Moon ground is still there. Stars, tower, and HUD are still there.

**Rest of the game, after Gate A**

- Swipe reaches every station, including Takeoff & Landing, and a vertical scroll can clear the goal card.
- Crane loads only the pad. The ship does not leave with cargo that was never loaded.
- A price on screen matches the price in the sheet.
- `?dev=1` is a new game with unlimited money. A normal open is not.
- Corner tag matches the build you were asked to test.

---

## 7. First move, by name

Do these in this order. Do not wait for a perfect reading of the whole file.

1. **Art.** Paint the yard road and send the centerline. Update `HANDOFF_rooms.md` so it stops saying the rooms are unwired. Decide the one truck. Commit or drop the loose wheel PNGs.
2. **Game Director.** Reply with yes or a replacement for: crane fill ~91 s, crane tier +10% per 10 levels, packing $1,800, and the placeholder room boost. Confirm the station list.
3. **Coder.** Do not draw another road. When Art’s sheet and centerline are in the repo, drive them and push a preview tag. Until then, leave 12:15 up.
4. **Playtester.** Freeze new mine notes until that tag exists. Then run section 6 and answer go or no-go with three phone shots.

The app is done when Gate E is signed. Not when a timestamp changes.
