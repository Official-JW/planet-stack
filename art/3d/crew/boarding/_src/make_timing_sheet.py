# python3 make_timing_sheet.py crew_boarding_timing.json CREW_BOARDING_TIMING.md
import json, sys
d = json.load(open(sys.argv[1])); o = []
f = lambda t: f'{t:6.2f}'
o.append('# Crew boarding — timing sheet\n')
o.append(f"Generated from `crew_boarding_timing.json` (build_boarding.py). Global time in seconds from the start of `crew_call`; key rate in the GLB is 15 Hz, source sampled at {d['fps']} fps.\n")
o.append('## Clips (play back to back, each clip starts at its own local 0)\n\n| clip | global start | global end | duration |\n|---|---|---|---|')
for k, (a, b) in d['clips'].items(): o.append(f'| `{k}` | {a:.2f} | {b:.3f} | {b - a:.3f} |')
o.append(f"\nTotal: **{d['total_s']:.2f} s**. Rung pair cycle **{d['rung_pair_s']} s** (2 rungs = 1.2 m per cycle, {1.2 / d['rung_pair_s']:.2f} m/s). Climber stagger (mount to mount) **{d['climb_gap_s']} s**.")
o.append("After `inside_hatch` the crew member's Root is scaled to 1e-4 (hidden) and holds that pose to the end of `crew_climb`.\n")
o.append('Ladder (measured from launch_pad_game.glb, ship-leg ladder on the +X/+Z side): rungs at y = 0.65 + 0.6·i, i = 0..34 (top rung 21.05 m), stile tops / deck top 21.85 m.\n')
o.append('Pad-local frame used for the landing (same as Art Assistant 2): u along the 330° ladder axis from Ship_Center (glTF (0, ·, −13)), t sideways (t = (p − C)·(0.5, 0, −0.866)), z = glTF y. The crew root sits at the pad origin.\n')
if 'board_focus' in d:
    bf = d['board_focus']; o.append('## Board_Focus / Board_Focus_Top (empty nodes in the GLB, children of CrewBoarding)\n')
    o.append(f"- camera: {bf['camera']}")
    o.append(f"- switch: {bf['switch']}")
    for n, v in bf['nodes'].items():
        o.append(f"- **{n}**: translation {v.get('translation')}, extras frame_w {v.get('extras', {}).get('frame_w')}; trigger `{json.dumps(v.get('extras', {}).get('trigger'))}`")
    o.append('\n| node | viewport / band | distance m | crew px | spare top px | spare bottom px |\n|---|---|---|---|---|---|')
    for n, v in bf['fit']['nodes'].items():
        for vw, f_ in v['views'].items(): o.append(f"| {n} | {vw} | {f_['distance_m']} | {f_['crew_px']} | {f_['spare_top_px']} | {f_['spare_bottom_px']} |")
    o.append('')
if 'landing_script_timings' in d:
    o.append('Per-crew timings in the format landing_clear_v3.mjs takes: `' + json.dumps(d['landing_script_timings']) + '`\n')
o.append('## Phases per crew member\n\n| crew | role | call | walk start | at ladder / queue spot | mount (first reach) | climb start | climb top | on deck (mantle done) | inside hatch (hidden) | ladder time |\n|---|---|---|---|---|---|---|---|---|---|---|')
for c in d['crew']:
    o.append(f"| {c['crew']} | {c['role']} | {c['call'][0]:.2f}–{c['call'][1]:.2f} | {c['walk_start']:.2f} | {c['arrive_ladder_or_queue']:.2f} | {c['mount']:.2f} | {c['climb_start']:.2f} | {c['climb_top']:.2f} | {c['on_deck']:.2f} | {c['inside_hatch']:.2f} | {c['on_deck'] - c['mount']:.2f} |")
o.append('\nPhase notes: *call* = Cargo Manager (crew 1) hand to helmet radio 0.2–2.95 s and points to the pad 1.35–3.1 s; crew 2–4 raise a hand to acknowledge. *walk* = planted-foot gait along the shared route around the ship-leg pad; crew 2–4 wait at queue spots by the ladder and step to the ladder foot before their mount (mounts are chained: each is at least one stagger after the previous). *climb* (v3) = the arms do the climbing (hand-over-hand on the rungs, curled grip); the boots trail under the body, toes down, >= 3 cm behind the rungs (AA2 v3 gate: a boot near a rung must be still). *mantle* = see the hatch landing section.\n')
if any('mantle' in c for c in d['crew']):
    o.append('## Hatch landing: mantle + walk-in per climber (Art Assistant 2 option 1 landing)\n')
    o.append('Open well u 4.05–5.15, |t| < 0.62 (no deck in front of the hatch); kerb |t| 0.62–0.68 (top z 21.88); wing stand area u 4.3–4.7, |t| 0.75–1.25, deck top z 21.85. v3: the climb ends low with the gloves on rungs 33/34; the hands move up onto the stiles and the climber presses up; the lead boot goes out through the cage side opening, over the kerb, and is SET DOWN slowly on the wing (still-sole rule), the trail boot follows; walk-in: each wing boot is lifted slowly, crosses the kerb >= 3 cm high and lands in the doorway (0 plants in the well, 0 on the kerb).\n')
    o.append('| crew | step-off side | through-hole start (climb top) | through-hole end (both boots on the wing) | hands off | walk-in end (inside hatch, hidden) |\n|---|---|---|---|---|---|')
    for c in d['crew']:
        mt = c['mantle']; o.append(f"| {c['crew']} | {mt['side']} (lead {mt['lead_foot']}) | {mt['mantle_start_climb_top']:.2f} | {mt.get('through_hole_end_both_boots_on_wing', 0):.2f} | {mt['hands_released']:.2f} | {mt['walk_in_end_inside_hatch']:.2f} |")
    o.append('\nFoot plants at deck height (sole centre u, t, z; land time = contact). `mantle` = step-off onto the wing, `walk_in` = steps to the hatch (the last plants are inside the hatch, u < 3.9).\n')
    for c in d['crew']:
        o.append(f"<details><summary>Crew {c['crew']} plants</summary>\n\n| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |\n|---|---|---|---|---|---|---|---|---|")
        for pl in c['mantle']['deck_foot_plants']:
            mb = pl.get('measured_sole_box', {}); f2 = lambda r: f"{r[0]:.3f}–{r[1]:.3f}" if r else ''
            o.append(f"| {pl['land_t']:.2f} | {pl['foot']} | {pl['sole_center_utz'][0]:.3f} | {pl['sole_center_utz'][1]:.3f} | {pl['sole_center_utz'][2]:.3f} | {pl['phase']} | {f2(mb.get('u'))} | {f2(mb.get('t'))} | {mb.get('where', '')} |")
        o.append('\n</details>\n')
if 'measured' in d:
    o.append('## Measured checks (three r186 skinned playback of the shipped GLB)\n')
    for k, v in d['measured'].items(): o.append(f'- **{k}**: `{json.dumps(v)}`')
    o.append('')
o.append('## Ladder occupancy (who is on the ladder when)\n')
o.append('| crew | on ladder | overlaps with |\n|---|---|---|')
cr = d['crew']
for c in cr:
    ov = [f"crew {e['crew']} ({max(c['mount'], e['mount']):.1f}–{min(c['on_deck'], e['on_deck']):.1f})" for e in cr if e is not c and e['mount'] < c['on_deck'] and c['mount'] < e['on_deck']]
    o.append(f"| {c['crew']} | {c['mount']:.2f}–{c['on_deck']:.2f} | {', '.join(ov) or '—'} |")
o.append(f"\nAll four are on the ladder at once, spaced {1.2 / d['rung_pair_s'] * d['climb_gap_s']:.2f} m apart in steady climb ({d['climb_gap_s']} s stagger). Measured clearance: see *Measured checks*. Each limb moves in its own window, so climbers never move in lockstep.\n")
o.append('## Rung timing per crew member\n\nEach row = one limb move: lift-off → contact, target rung index (height of rung). `rail_top` = deck rail grip, `hatch_frame` = hatch frame grips during the mantle, `deck` = foot onto the deck.\n')
for c in cr:
    mv = []
    for limb, L in c['rung_moves'].items():
        for m in L: mv.append((m[0], m[1], limb, m[2]))
    mv.sort()
    o.append(f"<details><summary>Crew {c['crew']} — {c['role']} ({len(mv)} limb moves, {c['mount']:.2f}–{c['on_deck']:.2f} s)</summary>\n\n| lift-off | contact | limb | target | height m |\n|---|---|---|---|---|")
    for a, b, limb, r in mv:
        if isinstance(r, (int, float)):
            r = int(r); h = '21.87 (rail top)' if r == 35 else f'{0.65 + 0.6 * r:.2f}'; tg = 'rail_top' if r == 35 else f'rung {r}'
        else: tg, h = str(r), ''
        o.append(f'| {a:.2f} | {b:.2f} | {limb} | {tg} | {h} |')
    o.append('\n</details>\n')
o.append('## Build checks\n')
for k, v in d['checks'].items(): o.append(f'- `{k}`: {v}')
open(sys.argv[2], 'w').write('\n'.join(o) + '\n'); print('wrote', sys.argv[2])
