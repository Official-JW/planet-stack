# Merge measured (three r186 skinned) checks into the timing json.
# python3 finalize_timing.py build_timing.json verify.json clearance.json deck_check.json camfit_375x667.json camfit_393x852.json landing_clear.json out.json
import json, sys
t, vb, cl, dc, c6, c8, lc, out = sys.argv[1:9]
d = json.load(open(t)); vb = json.load(open(vb)); cl = json.load(open(cl)); dc = json.load(open(dc)); c6 = json.load(open(c6)); c8 = json.load(open(c8)); lc = json.load(open(lc))
for c in d['crew']:
    mt = c['mantle']; meas = dc['per_crew']['Crew_%d' % c['crew']]['plants']
    for pl in mt['deck_foot_plants']:
        m = min((x for x in meas if x['foot'] == pl['foot']), key=lambda x: abs(x['land_s'] - pl['land_t']))
        pl['measured_sole_box'] = {'u': m['u'], 't': m['t'], 'z_min': m['z'], 'where': m['where'], 'detected_s': m['land_s']}
    mp = [p for p in mt['deck_foot_plants'] if p['phase'] == 'mantle']
    mt['through_hole_start'] = mt['mantle_start_climb_top']; mt['through_hole_end_both_boots_on_wing'] = max(p['land_t'] for p in mp)
    mt['step_off_side'] = mt['side']
mv = dc['per_part']
d['measured'] = {
    'glb': {'bytes': vb['bytes'], 'draws': vb['draws'], 'tris': vb['tris'], 'three': vb['three'], 'clips': [(x['name'], x['duration']) for x in vb['clips']]},
    'contacts_r186': vb['contacts'], 'planted_foot_slide_percentiles_m': vb['planted_foot_slide_percentiles_m'], 'worst_at': vb['worst_at'],
    'ik_target_reach': {'max_ratio': float(d['checks']['ik_max_stretch']), 'at': d['checks']['ik_stretch_at'], 'note': 'IK target distance / limb length; limbs are rigid (never stretched), >1 = the target is missed by that fraction for a frame'},
    'climber_clearance': cl,
    'climber_spacing_m': round(1.2 / d['rung_pair_s'] * d['climb_gap_s'], 2),
    'landing_vs_wip_pad': {'pad_md5': '9e44959341d7f57bf1b3bd21b826b940', 'min_m': dc['min_m'], 'hits': dc['hits'], 'per_part_min_m': {k: v['min_m'] for k, v in mv.items()},
                           'plants_in_well': sum(v['plants_in_well'] for v in dc['per_crew'].values()), 'plants_on_kerb': sum(v['plants_on_kerb'] for v in dc['per_crew'].values()),
                           'climb_min_frame_side_m': min(v['climb_min_frame_side_m'] for v in dc['per_crew'].values()), 'v1_c2d33fc_climb_frame_side_m': 0.048,
                           'cage_min_m': min(v['cage_min_m'] for v in dc['per_crew'].values()),
                           'hatch_jamb_note': '0.000 = gloves resting on the hatch jamb edge (|t| = 0.652) while stepping off: contact, no penetration'},
    'aa2_landing_clear_mjs': {'minClear': lc['minClear'], 'hits': lc['hits'], 'per_part': lc['per_part'], 'note': 'its climb/after-mantle split uses v1 STAND times (hardcoded), so only min/part/hits apply to v2'},
}
d['board_focus'] = {'position': c6['a_fit_whole']['focus'], 'mid_ladder_point': c6['mid_ladder_point'],
                    'camera': {'orientation': '38 deg vertical FOV, 18 deg look-down, game yaw; camera = focus + d*(0, sin18, cos18) (glTF)',
                               'distance_m (use 109.7)': c6['a_fit_whole']['distance_m'], 'ease': '1.2 s ease to Board_Focus, then hold',
                               '375x667 (a) whole ladder + 4 climbers': c6['a_fit_whole'], '375x667 requested 40 px crew': c6['req_40px'],
                               '375x667 (b) 40 px tracking': c6['b_40px_tracking'], '375x667 aimed at mid-ladder instead': c6['a_at_mid_ladder_focus'],
                               '375x667 (c) busy top only': {k: v for k, v in c6.items() if k.startswith('c_busy')},
                               '393x852 same camera (vFOV-locked, so the image scales by 852/667)': {'content_y_px': [round(149 * 852 / 667, 1), round(378 * 852 / 667, 1)], 'band_scaled_y_px': [round(144 * 852 / 667, 1), round(383 * 852 / 667, 1)], 'crew_px': round(16.1 * 852 / 667, 1)},
                               '393x852 own best fit (band 184-490, 6 px spare)': c8['a_fit_whole']}}
json.dump(d, open(out, 'w'), indent=1); print('wrote', out)
