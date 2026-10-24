# v3: merge measured (three r186 skinned) checks into the timing json.
# python3 finalize_timing.py build_timing.json verify.json clearance.json deck_check.json gate_v3.json aa2_v2.json camfit_v3.json focus_trigger.json board_focus_extras.json out.json
#   gate_v3.json  = nice -n 19 node /tmp/lp2/landing_clear_v3.mjs crew_boarding.glb <pad 7e02552> out.json   (AA2's v3 gate, 14 categories)
#   aa2_v2.json   = AA2's committed v2 landing_clear.mjs (7e02552), run unedited
import json, sys
t, vb, cl, dc, gt, lc, cf, tr, fx, out = sys.argv[1:11]
d = json.load(open(t)); vb = json.load(open(vb)); cl = json.load(open(cl)); dc = json.load(open(dc)); gt = json.load(open(gt)); lc = json.load(open(lc))
cf = json.load(open(cf)); tr = json.load(open(tr)); fx = json.load(open(fx))
PH = gt.get('phases', {})
for c in d['crew']:
    k = 'Crew_%d' % c['crew']; mt = c['mantle']; meas = dc['per_crew'][k]['plants']
    for pl in mt['deck_foot_plants']:
        m = min((x for x in meas if x['foot'] == pl['foot']), key=lambda x: abs(x['land_s'] - pl['land_t']))
        pl['measured_sole_box'] = {'u': m['u'], 't': m['t'], 'z_min': m['z'], 'where': m['where'], 'detected_s': m['land_s']}
    mt['walk_in_plants_measured'] = [x for x in meas if x['land_s'] > max(p['land_t'] for p in mt['deck_foot_plants']) + 0.2]
    mp = [p for p in mt['deck_foot_plants'] if p['phase'] == 'mantle']
    mt['through_hole_start'] = mt['mantle_start_climb_top']; mt['through_hole_end_both_boots_on_wing'] = max(p['land_t'] for p in mp)
    mt['step_off_side'] = mt['side']
    if k in PH: c['landing_script_phase'] = PH[k]
mv = dc['per_part']
d['landing_script_timings'] = {k: v for k, v in PH.items()}
d['measured'] = {
    'glb': {'bytes': vb['bytes'], 'draws': vb['draws'], 'tris': vb['tris'], 'three': vb['three'], 'clips': [(x['name'], x['duration']) for x in vb['clips']]},
    'contacts_r186': vb['contacts'], 'planted_foot_slide_percentiles_m': vb['planted_foot_slide_percentiles_m'], 'worst_at': vb['worst_at'],
    'ik_target_reach': {'max_ratio': float(d['checks']['ik_max_stretch']), 'at': d['checks']['ik_stretch_at'], 'note': 'IK target distance / limb length; limbs are rigid (never stretched), >1 = the target is missed by that fraction for a frame'},
    'climber_clearance': cl,
    'climber_clearance_note': 'v3 REGRESSION: the slow v3 mantle (rail press, slow boot set-downs) keeps each climber at the ladder top ~5 s while the next climber keeps climbing at the 3.4 s / 4.08 m stagger, so the upper climber\'s boots/shins overlap the next climber\'s head/forearms at z 20.4-21.9 (crew 1/2 ~43.0-45.3 s, 2/3 ~46.4-48.7 s, 3/4 ~49.8-52.1 s). Not one of the gate categories; see README.',
    'climber_spacing_m': round(1.2 / d['rung_pair_s'] * d['climb_gap_s'], 2),
    'landing_vs_pad_7e02552': {'pad_md5': '9e44959341d7f57bf1b3bd21b826b940', 'min_m': dc['min_m'], 'hits': dc['hits'], 'per_part_min_m': {k: v['min_m'] for k, v in mv.items()},
                               'plants_in_well': sum(v['plants_in_well'] for v in dc['per_crew'].values()), 'plants_on_kerb': sum(v['plants_on_kerb'] for v in dc['per_crew'].values()),
                               'climb_min_frame_side_m': min(v['climb_min_frame_side_m'] for v in dc['per_crew'].values()),
                               'cage_min_m': min(v['cage_min_m'] for v in dc['per_crew'].values()),
                               'hatch_edge_note': 'hatch_edge = the hatch opening edge (was hatch_jamb in v2); v3 keeps every crew vertex >= 3 cm from it'},
    'aa2_landing_clear_v3_gate': {'result': gt['summary']['result'], 'by_category': {k: v['status'] for k, v in gt['summary']['by_category'].items()}, 'exempt': gt['summary']['exempt'],
                                  'plants': gt['summary']['plants'], 'per_crew_min_m': {k: {'min_m': v['min_m'], 'part': v['part'], 'bone': v['bone'], 'at_s': v['at_s']} for k, v in gt['per_crew'].items()},
                                  'glb_vertices_left_in_well': gt['glb_vertices_left_in_well'], 'pad': '7e02552 launch_pad_game.glb'},
    'aa2_landing_clear_v2_unedited': {'minClear': lc['minClear'], 'hits': lc['hits'], 'per_part': lc['per_part'], 'plant_summary': lc.get('plant_summary')},
}
d['board_focus'] = {'nodes': fx, 'trigger': tr, 'fit': cf,
                    'camera': 'plain lookAt at the node (no setViewOffset), 38 deg vFOV, 18 deg look-down, game yaw; distance from frame_w as in qa3d-next fitSite(): d = (frame_w/2) / (tan(19 deg) * aspect)',
                    'switch': 'Board_Focus from crew_climb start; Board_Focus_Top once C1_Hips world y >= 14 m (fallback crew_climb clip-local %.3f s, absolute %.3f s)' % (tr['bones']['C1_Hips']['clip_local_s'], tr['bones']['C1_Hips']['absolute_s'])}
json.dump(d, open(out, 'w'), indent=1); print('wrote', out)
