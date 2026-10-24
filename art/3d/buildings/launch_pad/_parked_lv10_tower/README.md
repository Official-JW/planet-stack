# PARKED: launch tower LT-1 + crew lift + access arm + queue walkway (for the Lv10 Launch Pad redesign)

Director's final ruling, 10/24/2026 11:29 PT: the launch tower and the elevator move to the **Lv10 Launch Pad**. Pads Lv1 to Lv9 have no
tower, and the crew keep climbing the ladder. This code is parked here so it isn't lost. It is **not** built or rendered by anything:
build_launch_pad.py never imports it.

- `lp_lv1_tower_parked.py` is the 10/24 Lv1 tower draft. Its `build(G)` ran from build_launch_pad.py before the +SHIFT move. It removes the
  ladder, cage and well lid, then adds the tower, lift car, door portals, access arm, queue walkway, 1.8 m queue figures and Lift_* markers.
  It also contains an early copy of the TF-1 tank farm. The live TF-1 is now in `../lv1/_src/lp_lv1.py`.
- The draft geometry was checked only, never rendered as a deliverable. Its numbers: tower 3.6 m square at u 14.4–18.0 on the 330° axis, top about z 28.9. Lift
  rise 21.54 m (z 0.31 → 21.85). Arm 8.9 m long, 1.80 m clear between rails. Raw tris: tower 3.0k, arm 1.1k, car 0.2k, walkway 0.2k.

## Requirements for the Lv10 design
- **The tower must reach the hatch of every ship from Lv10 up.** From Lv10, ships have no ladder and board from the tower only. Ships also
  get taller (Lv2 already adds a 3–4 m cargo ring at the same 8.0 m diameter). So the shaft and stops must grow with them: use one
  landing stop per hatch height, each with its own arm or a height-adjustable arm. Keep the stop heights as parameters.
- **Elevator (Director-locked spec):**
  - 2-crew car with a clear cab floor of 1.4 × 1.2 m, kept clear for crew animation.
  - Doors face the access arm. They are bi-parting and need room to slide.
  - DoorsOpen 1.5 s and DoorsClose 1.5 s. ElevatorUp 10 s and ElevatorDown 8 s. Every move is eased.
  - Name the clips and markers clearly (ElevatorUp, DoorsOpen, ...).
- **Queue walkway:**
  - 7 m of clear, flat walkway straight to the car doors.
  - Crew wait in line 1.5 m apart, facing the car.
  - No obstacles. Keep it clear of the fuel farm, lines and truck road.
  - It must be fully on screen at 375×667 with at least 5 px of clearance.
- **Access arm and landing:** wide enough for 2 crew to walk side by side, with at least 3 cm from the rails for each. The ship doorway itself is 1.3 m wide.
- **Crane PC-1:** the free-360 jib (15 m) passed 0.7 m from the draft tower corner at bearing ~41°. Add a slew keep-out or move the tower.
- **Look:** the approved Lv0 look (glossy white, graphite and cyan strips, weathered). Original design only. Game budget: reuse existing materials (≤15 draws, ≤30k tris).
