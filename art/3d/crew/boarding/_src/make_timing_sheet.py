# python3 make_timing_sheet.py crew_boarding_timing.json CREW_BOARDING_TIMING.md
import json, sys
d = json.load(open(sys.argv[1])); o = []
f = lambda t: f'{t:6.2f}'
o.append('# Crew boarding — timing sheet\n')
o.append(f"Generated from `crew_boarding_timing.json` (build_boarding.py). Global time in seconds from the start of `crew_call`; key rate in the GLB is 15 Hz, source sampled at {d['fps']} fps.\n")
o.append('## Clips (play back to back, each clip starts at its own local 0)\n\n| clip | global start | global end | duration |\n|---|---|---|---|')
for k, (a, b) in d['clips'].items(): o.append(f'| `{k}` | {a:.2f} | {b:.3f} | {b - a:.3f} |')
o.append(f"\nTotal: **{d['total_s']:.2f} s**. Rung pair cycle **{d['rung_pair_s']} s** (2 rungs = 1.2 m per cycle, 0.75 m/s). Climber stagger (mount to mount) **{d['climb_gap_s']} s**.")
o.append("After `inside_hatch` the crew member's Root is scaled to 1e-4 (hidden) and holds that pose to the end of `crew_climb`.\n")
o.append('Ladder (measured from launch_pad_game.glb, ship-leg ladder on the +X/+Z side): rungs at y = 0.65 + 0.6·i, i = 0..34 (top rung 21.05 m), deck/rail top 21.85 m, hatch frame grips at 22.55 / 23.2 m.\n')
o.append('## Phases per crew member\n\n| crew | role | call | walk start | at ladder / queue spot | mount (first reach) | climb start | climb top | on deck (mantle done) | inside hatch (hidden) | ladder time |\n|---|---|---|---|---|---|---|---|---|---|---|')
for c in d['crew']:
    o.append(f"| {c['crew']} | {c['role']} | {c['call'][0]:.2f}–{c['call'][1]:.2f} | {c['walk_start']:.2f} | {c['arrive_ladder_or_queue']:.2f} | {c['mount']:.2f} | {c['climb_start']:.2f} | {c['climb_top']:.2f} | {c['on_deck']:.2f} | {c['inside_hatch']:.2f} | {c['on_deck'] - c['mount']:.2f} |")
o.append('\nPhase notes: *call* = Cargo Manager (crew 1) hand to helmet radio 0.2–2.95 s and points to the pad 1.35–3.1 s; crew 2–4 raise a hand to acknowledge. *walk* = planted-foot gait along the shared route around the ship-leg pad; crew 2–4 wait at queue spots by the ladder and step to the ladder foot 3.0 s before their mount. *climb* = diagonal pairs (right hand + left foot on even rungs, left hand + right foot on odd rungs), hands swing in 0.42 of the cycle, feet 0.45. *mantle* (≈3.25 s) = grips on the hatch frame, step onto the deck, then walk ≈1.4 s into the hatch.\n')
o.append('## Ladder occupancy (who is on the ladder when)\n')
o.append('| crew | on ladder | overlaps with |\n|---|---|---|')
cr = d['crew']
for c in cr:
    ov = [f"crew {e['crew']} ({max(c['mount'], e['mount']):.1f}–{min(c['on_deck'], e['on_deck']):.1f})" for e in cr if e is not c and e['mount'] < c['on_deck'] and c['mount'] < e['on_deck']]
    o.append(f"| {c['crew']} | {c['mount']:.2f}–{c['on_deck']:.2f} | {', '.join(ov) or '—'} |")
o.append(f"\nSeveral crew are on the ladder at once (it is 21.6 m tall), spaced about 4.1 m (≈7 rungs) apart body to body: min clearance upper boots → lower gloves {d['checks']['min_gap_upper_boots_to_lower_gloves_m']} m (at {d['checks']['min_gap_at'][0]} s, crew {d['checks']['min_gap_at'][1]} above crew {d['checks']['min_gap_at'][2]}). Each limb moves in its own window, so climbers never move in lockstep.\n")
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
