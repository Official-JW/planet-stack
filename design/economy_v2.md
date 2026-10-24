# Planet Stack economy v2 (DRAFT for Game Director review)

Status: draft, 10/24/2026. Not posted and not built. When it's approved it gets built behind `?econ=v2` after the 4 PM build, and Playtester runs a separate balance pass on it.
Mapped onto: `origin/main` @ 563fbed, `qa3d/main.js` and `qa3d-next/main.js` (same `CFG`), plus the in-progress `gc-storage` (Cargo Dock, cap 20) and `ca-trip-tracker` (sale at 277.2 s) work.
All numbers come from one model, `design/econ_v2_model/` (`python3 tables.py`, `python3 sim3.py G=1.17 NEW2=1e7 NEW3=2e8`). Anything marked **(guess)** is a starting value to tune. Anything marked **(locked)** came from Jacob and doesn't change.

---

## 0. Locked facts this spec is built on
- **(locked)** Each delivery (the cargo drop-off at Earth) pays **$20,000 at Lv1**. Lift-off pays nothing. The sale fires once, at **277.2 s of the 616 s Lv1 trip** (45% of the trip).
- **(locked)** Flights cost fuel, not cash. The Refinery fuel line makes LOX and methane over time and stores it. Refueling at the pad takes **30 s per 1%, so 50 min for a full tank at Lv1**. Fuel-line and pump upgrades cut the wait.
- **(locked)** Buildings max out at **Lv50**, with new looks at **10/20/30/40/50**. Station order: Life Support, Mine, Refinery, Cargo Dock, Launch Pad, Shipyard, Habitat, Engineering.
- **(locked)** The Cargo Dock is storage, **20 boxes at Lv1**. Mining halts when the pallet, the flatbed and the dock are all full. Offline progress freezes when storage is full. **The ship doesn't fly while the player is away.**
- **(locked)** The Lv1 crane reaches the 20 Lv1 slots. Bigger caps get a **second crane, not a longer jib**.
- **(locked)** The Lv2 ship (a Shipyard upgrade) gets +1 seat and a hold of 10 → 12. **A Lv10 ship needs a Lv10 Launch Pad.**
- **(locked)** Crystals are bought with real money only and never earned. This spec has no crystal costs.
- **(locked)** The biggest goals are ship upgrades and building new ships. The Habitat lets crew stay, so more specialists come.

## What the code does today (what v2 replaces)
| Thing | Today (`CFG` in qa3d/main.js) | v2 |
|---|---|---|
| Start cash | `startMoney: 500` | **$3,000** (guess) |
| Ship sale | `boxValue: 36` per box (full hold $360), sells at the top of the climb (8 s) | **$2,000 per box at Lv1** (full 10-box hold = $20,000), sells at 45% of the trip (the tracker's 277.2 s) |
| Truck dump pay | `load0 12 + loadPerLvl 6` per dump, plus `richBonus 8` per deposit tap | **No cash** (guess, Director call). All money comes from Earth. The deposit tap keeps its +25% bed fill, so the next box comes sooner. |
| Drill upgrade | `drillCost0 15 × 1.65^n`, raises the load's $ | Merged into **Mine level** (see §2) |
| Chute Feed Rate | `fill0 120 s × 0.80^n`, 15 s floor, max Lv11, `$10 × 1.5^n` | Merged into **Mine level**: fill 60 s × 0.85^(L−1), 15 s floor at Lv10 |
| Extra trucks | `roverCost 60`, `TRUCK_SALE = false` | Come free with the Mine's looks (2 trucks at Lv20, 3 at 30, 4 at 40, 5 at 50) |
| Fuel | `fuelFillSec: 180`, a placeholder fill from touchdown | Pump and fuel-line model, 30 s per 1% at Lv1 (§4) |
| Trip | launch 8 + away 600 + land 8 = 616 s | Same at Lv1. Engineering shortens it (§1) |
| Ship hold | `holdCap: 10` | 10 + 2 per ship level (Lv2 = 12, Lv10 = 28) |
| Pallet / bay / flatbed | `palletCap 8`, `bayCap 12`, `perTrip 2` | Unchanged (flatbed throughput flagged in §7) |
| Dock | `STOR.dockCap: 20` (gc-storage, `?storage=on`) | Grows with Cargo Dock level (§3) |
| Offline | 50% of money after 5 min away, nothing past 4 h | Storage and fuel caps replace both (§5) |

Two mismatches the build has to settle (not economy numbers):
- The `STATIONS` array is `Life Support, Mine, Refinery, Takeoff & Landing, Cargo Space Dock, Habitat, Shipyard, Engineering`. Jacob's order is **Life Support, Mine, Refinery, Cargo Dock, Launch Pad, Shipyard, Habitat, Engineering**. v2 uses Jacob's order and names, and it's also the build/unlock order.
- TEAM_PLAN.md still says "Fuel is LOX + LH2 everywhere (no methane)" (Jacob, 10/23). Today's locked fact says **LOX and methane**. This spec uses LOX + methane, and TEAM_PLAN needs updating to match.

---

## 1. Income model

**Pay per delivery** = boxes in the hold × box value.

**Box value** = $2,000 × Refinery purity × Mine ore grade × Engineering × crew specialists
- Refinery purity: +3% per level above 1 (Lv50 = ×2.47) (guess)
- Mine ore grade: +2% per level above 1 (Lv50 = ×1.98) (guess)
- Engineering: +1% per level above 1 (Lv50 = ×1.49) (guess)
- Specialists: +1% per specialist (up to +98%) (guess). Crew = 4 + min(2 × Habitat level, 2 × (Life Support level − 1)). Specialists are the crew above the starting 4.

At Lv1 everything is ×1, so 10 boxes × $2,000 = **$20,000 (locked)**. A partial launch pays per box: 6 boxes pays $12,000.

**Trip length** = 616 s × (1 − 0.5% per Engineering level above 1). Lv50 = 465 s (−25%) (guess). The sale is always at **45% of the trip**: 277.2 s at Lv1, 209 s at Engineering 50. The 45/10/45 split stays the same.

**Cycle per ship** = refuel time + boarding (about 56 s, today's crew boarding) + trip. Refuel is in §4.

**Fleet limit:** every ship burns one full tank per trip, and all ships share one Refinery fuel line. So the fleet can't fly more than (fuel line %/min × 60 ÷ 100) trips per hour, and it can't deliver more boxes than the Mine makes.

### Income at milestones
This is a snapshot with every building at the same level and ships at min(level, 10). It's a reference point, not a real save.

| Everything at | Ships | Box value | Pay per full trip | Refuel | Trip | Cycle | Trips/h (fleet) | Boxes/h needed | Mine boxes/h | What limits it | $/h, game open | $ per 1 h check-in session |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lv1 | 1 × Lv1 (10 boxes) | $2,000 | **$20,000** | 50.0 min | 616 s | 61.2 min | 0.98 | 10 | 30 | ship fuel | **$19,600** | $20,000 (1 trip) |
| Lv2 | 1 × Lv2 (12) | $2,165 | $25,976 | 48.3 min | 613 s | 59.5 min | 1.01 | 12 | 32 | ship fuel | $26,200 | $26,000 (1 trip) |
| Lv5 | 1 × Lv5 (18) | $2,717 | $48,910 | 43.6 min | 604 s | 54.6 min | 1.10 | 20 | 39 | ship fuel | $53,800 | $48,900 (1 trip) |
| Lv10 | 1 × Lv10 (28) | $3,855 | $107,940 | 36.7 min | 588 s | 47.4 min | 1.27 | 35 | 48 | ship fuel | $137,000 | $216,000 (2 trips) |
| Lv20 | 2 × Lv10 (28) | $7,116 | $199,247 | 26.0 min | 557 s | 36.2 min | 2.77 | 78 | 96 | fuel line | $552,000 | $797,000 (4 trips) |
| Lv30 | 2 × Lv10 (28) | $12,044 | $337,236 | 18.4 min | 527 s | 28.1 min | 4.26 | 119 | 144 | ship fuel | $1.44M | $1.35M (4 trips) |
| Lv40 | 3 × Lv10 (28) | $19,114 | $535,183 | 13.1 min | 496 s | 22.3 min | 6.68 | 187 | 192 | fuel line | $3.57M | $4.82M (9 trips) |
| Lv50 | 3 × Lv10 (28) | $28,856 | $807,982 | 9.3 min | 465 s | 18.0 min | 10.0 (needs 281 boxes) | 281 | 240 | Mine | $6.93M | $9.70M (12 trips) |

Notes:
- The biggest single pop is about **$808k** (3 × Lv10 ship, everything Lv50). That fits Art's "+$999,999" pop width. `fmt()` switches to "$1.00M" past that anyway.
- What limits income moves around (fuel, then the fuel line, then the Mine). That's on purpose, so no single building is "the" upgrade.
- At Lv1 the Mine makes 3× what the ship carries. The extra fills storage, and storage is what the player comes back to.

---

## 2. Building cost curve (50 levels)

**Price to buy level L** (for L = 2..50) = Base × 1.17^(L−2) × T, rounded to 2 significant figures.
T = **1.5 on the look levels (10, 20, 30, 40, 50)**, otherwise 1. A look level is a rebuild, so it costs more than the level after it (for example Lv10 = ×5.27, Lv11 = ×4.11). That's on purpose: it feels like a big step.
Growth of 1.17 per level, the bases and the build prices are all **(guess)**. They were tuned so the pacing in §6 comes out right.

| Building | What a level gives | Base | Lv1 | Lv2 | Lv5 | Lv10 | Lv20 | Lv30 | Lv40 | Lv50 | Total to reach Lv50 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Life Support | Crew air: supports 2 more crew per level. No other building can be more than 10 levels above it | $2,000 | start | $2,000 | $3,200 | $11,000 | $51,000 | $240,000 | $1,200,000 | $5,600,000 | $28.1M |
| Mine | Faster chute (to Lv10), +2% ore grade per level, more trucks at 20/30/40/50 | $1,000 | start | $1,000 | $1,600 | $5,300 | $25,000 | $120,000 | $580,000 | $2,800,000 | $14.1M |
| Refinery | Fuel line rate, tank farm size, +3% He-3 purity per level | $1,500 | start | $1,500 | $2,400 | $7,900 | $38,000 | $180,000 | $880,000 | $4,200,000 | $21.2M |
| Cargo Dock | Storage cap and cranes (§3) | $1,500 | start | $1,500 | $2,400 | $7,900 | $38,000 | $180,000 | $880,000 | $4,200,000 | $21.2M |
| Launch Pad | Pump speed (§4). Ship level ≤ pad level. Second berth at Lv20, third at Lv40 | $3,000 | start | $3,000 | $4,800 | $16,000 | $76,000 | $370,000 | $1,800,000 | $8,400,000 | $42.3M |
| Shipyard | Unlocks ship levels (ship level ≤ Shipyard level). New ships at 20 and 40 | $5,000 | $10,000 to build | $5,000 | $8,000 | $26,000 | $130,000 | $610,000 | $2,900,000 | $14,000,000 | $70.4M |
| Habitat | +2 beds per level (crew who stay, which means specialists) | $4,000 | $40,000 to build | $4,000 | $6,400 | $21,000 | $100,000 | $490,000 | $2,300,000 | $11,000,000 | $55.9M |
| Engineering | −0.5% trip time and +1% pay per level. Gates new ships | $6,000 | $80,000 to build | $6,000 | $9,600 | $32,000 | $150,000 | $730,000 | $3,500,000 | $17,000,000 | $84.5M |

Build order follows the station order. Shipyard can be built after the first delivery, Habitat after the Shipyard, and Engineering after the Habitat. Life Support through Launch Pad start at Lv1.

Price multiplier per level bought (× Base):

| Lv | ×Base | Lv | ×Base | Lv | ×Base | Lv | ×Base | Lv | ×Base |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 1.00 | 12 | 4.81 | 22 | 23.11 | 32 | 111.06 | 42 | 533.87 |
| 3 | 1.17 | 13 | 5.62 | 23 | 27.03 | 33 | 129.95 | 43 | 624.63 |
| 4 | 1.37 | 14 | 6.58 | 24 | 31.63 | 34 | 152.04 | 44 | 730.81 |
| 5 | 1.60 | 15 | 7.70 | 25 | 37.01 | 35 | 177.88 | 45 | 855.05 |
| 6 | 1.87 | 16 | 9.01 | 26 | 43.30 | 36 | 208.12 | 46 | 1000.41 |
| 7 | 2.19 | 17 | 10.54 | 27 | 50.66 | 37 | 243.50 | 47 | 1170.48 |
| 8 | 2.57 | 18 | 12.33 | 28 | 59.27 | 38 | 284.90 | 48 | 1369.46 |
| 9 | 3.00 | 19 | 14.43 | 29 | 69.35 | 39 | 333.33 | 49 | 1602.27 |
| **10 (look)** | 5.27 | **20 (look)** | 25.32 | **30 (look)** | 121.70 | **40 (look)** | 585.00 | **50 (look)** | 2811.98 |
| 11 | 4.11 | 21 | 19.75 | 31 | 94.93 | 41 | 456.30 | | |

### Ships (the biggest goals)
Ship levels go from 1 to 10 for each ship and are bought at the Shipyard. **Ship level N needs Shipyard ≥ N and Launch Pad ≥ N** (this covers the locked "Lv10 ship needs Lv10 pad"). It also needs **Cargo Dock ≥ N** (guess, my proposal: without it the Dock never matters to a player who's online, see §7).

| Ship Lv | Hold | Seats | Price | Needs Shipyard / Pad / Dock at |
|---|---|---|---|---|
| 1 | 10 | 4 | starter | — |
| 2 | **12 (locked)** | **5 (locked +1)** | $8,000 | Lv2 |
| 3 | 14 | 5 | $14,000 | Lv3 |
| 4 | 16 | 6 | $23,000 | Lv4 |
| 5 | 18 | 6 | $39,000 | Lv5 |
| 6 | 20 | 7 | $67,000 | Lv6 |
| 7 | 22 | 7 | $110,000 | Lv7 |
| 8 | 24 | 8 | $190,000 | Lv8 |
| 9 | 26 | 8 | $330,000 | Lv9 |
| 10 | 28 | 9 | $560,000 | Lv10 (pad locked) |

Ship price = $8,000 × 1.7^(N−2), rounded (guess). Above Lv2, hold +2 per level and seats +1 every other level are guesses. In v2, seats don't change income. They set how many crew fly, which matters for boarding art and later specialist perks.

**New ships (guess):**
- Ship #2: **$10M**. Needs Shipyard 20 + Launch Pad 20 (second berth, part of the pad's Lv20 look) + Cargo Dock 20 + Engineering 10.
- Ship #3: **$200M**. Needs Shipyard 40 + Launch Pad 40 (third berth) + Cargo Dock 40 + Engineering 30.

Each new ship starts at Lv1 and is upgraded with the same table. Each berth has its own pump at the pad's rate. All ships share the Refinery fuel line and tank farm.

---

## 3. Storage (Cargo Dock)

Dock cap = 20 + 4 per level up to Lv10 (Lv10 = 56), then +1.6 per level, rounded down, to Lv50 (Lv50 = 120) (guess).
"Storage full" means what gc-storage's `stFull()` checks today: the Refinery pallet (8) full, FB-05 loaded and waiting, and the dock full. The pad bay (12) and a parked ship's hold also fill first, because the cranes keep moving boxes.

**Crane rule (my reading of Jacob's note, confirm with Art):** one crane covers the 20-slot Lv1 footprint. It can stack boxes 2 high by hoisting higher, which isn't a longer jib, so one crane reaches **40**. **The second crane (with its own 20-slot pad) appears at Dock Lv7, the first level over 40 (cap 44).** Two cranes stacking 2 high reach 80. From Lv26 (cap 81) both stack 3 high, which reaches 120, exactly the Lv50 cap. So there's never a third crane.
If Jacob means "one crane = 20 boxes, period", the second crane comes at **Dock Lv2** (cap 24) and the second crane is the only change until stacking. That's question 1 in §7.

| Dock Lv | Dock cap | Cranes | Stack | Whole buffer (dock + pallet 8 + flatbed 2 + bay 12) | Hours of Mine output that fills it (Mine at the same level) |
|---|---|---|---|---|---|
| 1 | **20 (locked)** | 1 | 1 high | 42 (+10 in a parked Lv1 hold = 52) | 1.4 h (1.7 h with the hold) |
| 2 | 24 | 1 | 2 high | 46 | 1.4 h |
| 5 | 36 | 1 | 2 high | 58 | 1.5 h |
| 6 | 40 | 1 | 2 high | 62 | 1.5 h |
| **7** | **44** | **2** | 2 high | 66 | 1.5 h |
| 10 | 56 | 2 | 2 high | 78 | 1.6 h |
| 20 | 72 | 2 | 2 high | 94 | 1.0 h |
| 25 | 80 | 2 | 2 high | 102 | 1.1 h |
| 26 | 81 | 2 | **3 high** | 103 | 1.1 h |
| 30 | 88 | 2 | 3 high | 110 | 0.8 h |
| 40 | 104 | 2 | 3 high | 126 | 0.7 h |
| 50 | 120 | 2 | 3 high | 142 (+84 in 3 parked Lv10 holds = 226) | 0.6 h (0.9 h) |

Hours to fill drop at high levels because the Mine outgrows the dock. That's deliberate pressure to buy Dock levels, but it's the first thing I'd retune (§7).

---

## 4. Fuel: Refinery fuel line + Launch Pad pump

Fuel is counted in % of one ship tank. Every ship needs **100% per trip** at every level, so a bigger ship doesn't need more fuel (guess).
- **Pump (Launch Pad):** q = 2.0 %/min × 1.035^(Pad−1). At Lv1 that's **30 s per 1%, 50 min for a full tank (locked)**.
- **Fuel line (Refinery):** p = 2.0 %/min × 1.045^(Refinery−1). LOX + methane, made all the time, including while the ship is away.
- **Tank farm (Refinery):** stores 100% + 10% per Refinery level above 1. It starts full.
- **Refuel at landing** = the longer of (100 ÷ q), the pump time, and ((100 − fuel stored) ÷ p), the time the line needs to make what's missing. The line keeps filling the tank farm while the ship is away, so at matching levels the pump is what you wait on, and the line limits you only when you skip Refinery levels or fly 2–3 ships.

| Level | Pump %/min | s per 1% | Full refuel by pump | Fuel line %/min | Line makes 1 tank in | Tank farm | Refuel at landing (pad and Refinery at this level) |
|---|---|---|---|---|---|---|---|
| 1 | 2.00 | **30.0** | **50.0 min** | 2.00 | 50.0 min | 100% | 50.0 min |
| 2 | 2.07 | 29.0 | 48.3 min | 2.09 | 47.8 min | 110% | 48.3 min |
| 5 | 2.30 | 26.1 | 43.6 min | 2.39 | 41.9 min | 140% | 43.6 min |
| 10 | 2.73 | 22.0 | 36.7 min | 2.97 | 33.6 min | 190% | 36.7 min |
| 20 | 3.85 | 15.6 | 26.0 min | 4.62 | 21.7 min | 290% | 26.0 min |
| 30 | 5.42 | 11.1 | 18.4 min | 7.17 | 14.0 min | 390% | 18.4 min |
| 40 | 7.65 | 7.8 | 13.1 min | 11.13 | 9.0 min | 490% | 13.1 min |
| 50 | 10.79 | 5.6 | 9.3 min | 17.29 | 5.8 min | 590% | 9.3 min |

Example of the two working together: Pad 10 with Refinery 1. The line made only 2 %/min × 11.2 min ≈ 22% while the ship was away, so refuel = (100 − 22) ÷ 2 = 39 min, not the pump's 36.7. The fuel gauge should show both, for example "Pump 22 s/1% · line low".

**Opening (guess, Director call):** the starter ship lands with **full tanks** (Earth fueled it for the round trip). Without that, the first launch can't happen before about 50 min, and the first delivery comes at about 55 min.

---

## 5. Offline (while the player is away)
1. **The ship never launches while you're away.** This is today's `sh.man` rule (Director 23:00). A ship that fills up while you're away waits for a Launch tap.
2. **A trip already in the air keeps going** on its saved lift-off time. Its sale fires at 45% and pays **100%** (guess). The player launched it, and the tracker already says "Back at 2:47 PM". Today `tripSell` applies `offlineRate` 0.5 after 5 min away, and that cut is dropped under `?econ=v2`. The ship lands and starts refueling.
3. **The Mine runs at full rate until storage is full, then it freezes** (`stFull`). It picks up again by itself as soon as a crane frees a slot (gc-storage already does this from timestamps).
4. **The fuel line keeps filling the tank farm**, and **the pump keeps filling a parked ship** from the tank farm, both until full. You come back to a fueled ship and a full dock.
5. **No cash is earned offline** except from a trip already in the air (there's no truck pay in v2).
6. The old **50% cut and 4 h cap are removed** under `?econ=v2`, because storage and tank size now set the limit. Keep a 24 h limit on catch-up length only to protect performance. Storage fills long before that.
7. The away card changes from "+$X" to "**+N boxes · Storage full since 2:47 PM · Fuel 100%**", plus "+$X from your trip" when rule 2 applied.
8. A clock set backward is still ignored (unchanged).

What that means: the effective offline cap is the storage hours in §3, about 1.7 h at Lv1 and about 0.9–1.6 h later. Coming back after that, everything is the same. A check-in player earns per session, not per hour away.

---

## 6. Target pacing
Two players were modeled with the same purchase rule (buy whatever adds the most $/h per $ spent, with ship upgrades bought together with the Shipyard/Pad/Dock levels they need):
- **Game open:** launches the moment the ship is ready. Measured in hours the game is open.
- **Check-in:** 4 sessions a day, 1 h in the game each, 3 h away between them. Counted in 16 h days (overnight adds nothing, because storage is full by then).

**First session, step by step (game open, guesses):**
| Time | What happens |
|---|---|
| 0:00–0:15 | Landing about 6 s, unload about 8 s, first tap under 15 s (§Opening, unchanged) |
| about 0:30 | **First upgrade:** Mine Lv2, $1,000 from the $3,000 start (Eve "Tap Upgrade" beat). Then Mine Lv3 for $1,200, leaving $800 |
| about 1:30 | First box (chute 60 s at Lv1, then about 43 s at Lv3, plus about 60 s haul) |
| about 19:00 | Hold full (10 boxes at about 1 per 1.7 min, plus about 2 min to the hold) |
| about 20:00 | Lift-off after boarding (about 56 s) |
| **about 24:30** | **First $20,000** (277.2 s after lift-off) |
| 24:30–30:00 | Spend it: Refinery 2–3, Mine 4–6, Launch Pad 2, Cargo Dock 2 (about $14k), and save toward the Shipyard |
| about 30:00 | Ship back, refuels about 46–48 min |
| **about 1:20** | Second delivery, then **Shipyard built + ship Lv2** (bundle about $27k: build $10k, Shipyard 2, Pad 2, Dock 2, ship $8k) |

**Milestones (from the model):**
| Milestone | Game open (hours) | Check-in (days) | Why this is the target |
|---|---|---|---|
| First upgrade | under 1 min | day 1 | Teaches the Upgrade sheet before the first box |
| First delivery ($20k) | about 0.4 h | day 1 | One full Lv1 trip, the moment the game is about |
| Ship Lv2 | about 1.3 h | day 1 | The first "ship upgrade" goal lands in session 1 or 2 |
| Ship Lv5 | about 5 h | day 1–2 | |
| **Launch Pad Lv10** | **about 6 h** | **about day 4** | The pump is worth less to a check-in player (refueling happens while they're away), so they get there later |
| Habitat built | about 12 h | about day 2 | The first specialists arrive |
| **Ship Lv10** | **about 24 h** | **about day 4** | About 4 days for a regular player: the first long-term goal you can see |
| **Ship #2** | about 51 h | about day 10–11 | "Build a new ship" as the second-week goal |
| Ship #3 | about 145 h | about day 39 | The late goal |
| Everything Lv50 | about 160 h | about day 47 | About 6–7 weeks for a regular player (guess at the right length) |

Why these numbers: Lv1→2 prices ($1k–$5k) are 5–25% of one delivery, so the first $20k buys 4–6 levels and feels big. Prices grow 1.17× per level, while income per milestone grows about 7× from Lv1 to Lv10 and about 50× to Lv20. So an early "round" of upgrades takes about one delivery, and late rounds take several hours of play. Ships are priced so each ship level costs about 1–4 deliveries at the level where you buy it.

Two flags from the model:
- **The Mine and Refinery max out early** (the check-in model has Mine Lv50 by about day 17). Their % bonuses are good value per dollar. If that feels wrong, raise their bases or growth.
- **Life Support's +10 gate** is what keeps it moving. Without the gate, nobody would buy Life Support before Habitat.

---

## 7. Open questions for Playtester to measure (and for Director/Jacob to decide)
1. **Crane reading** (Jacob/Art): one crane = 20 slots stacked 2 high (second crane at Dock Lv7), or one crane = 20 boxes (second crane at Dock Lv2)?
2. **Time to first $20k:** is about 24 min OK in the first session? Measure the real time from first tap to the sale, with and without `?speed=10`. Fallback: Eve offers a partial first launch at 5 boxes (pays $10k at about 16 min).
3. **Starter ship lands full of fuel?** If not, the first delivery is about 55 min. Jacob's call.
4. **Truck haul time:** the model uses about 60 s per round trip (the code's fallback). Read `__ps3d.route.trip` on the real route at 375 and 393. Box rate = 3600 ÷ (fill + haul).
5. **Flatbed and crane throughput:** FB-05 carries 2 boxes per run and each crane lift is 5–6 s. At Mine 20+ (96+ boxes/h) the flatbed may be the real limit. Measure boxes/h from pallet to hold. If it limits, the Dock looks should add flatbed bed size or a second flatbed.
6. **Is the Dock worth buying?** For a check-in player with 1 ship, storage (42+) is bigger than what they fly per session (10–28), so Dock levels pay nothing until about ship Lv10 or ship #2. That's why I put "ship Lv N needs Dock ≥ N" in. Check that it doesn't feel like a pointless gate.
7. **Hours until storage is full** at Dock 1/10/20 (expected 1.7 / 1.6 / 1.0 h). Is it long enough for a normal break? If not, raise the Dock cap or let the Mine slow down instead of the Dock filling up.
8. **Refuel feel:** is 50 min at Lv1 with the game open too long (people may close the game, which is fine for an idle game)? Watch whether the gauge plus the tracker make the wait clear.
9. **Partial launches:** they pay per box. Check nobody finds a trick: launching 1 box costs a full tank, so it's always worse. Confirm.
10. **Offline exactly-once:** lock the phone mid-trip, reload after the sale time, and check the sale pays 100% once, the dock freezes at full, the fuel and pump fill, and the ship waits for Launch.
11. **Economy pop range:** the biggest pop is about $808k. Check "+$807,982" at 375 and 393 at 11 pt+.
12. **Specialists:** is +1% each noticeable? Habitat 10 + Life Support 11 = 20 specialists = +20%. Maybe show it on the delivery pop ("+20% crew").
13. **Engineering is a weak buy** in the model until it gates ship #2. Consider making it +2% pay per level, or have it gate trip-tracker perks.
14. **Mine/Refinery max too early?** Watch for "nothing useful to buy" stretches around day 10–20.
15. **Migration:** `?econ=v2` should use its own save key, like qa3d-next does (`planetstack-qa3d-next`). Old drill/chute levels mean nothing in v2, so don't convert them, start fresh.

## Not in this spec (on purpose)
- Asteroid risk and reward (no numbers here yet).
- Build timers (upgrades stay instant, as today).
- Any crystal price or crystal skip.
