// write cargo_dock_slots_lv1_v4.json (20 slots under the GC-1 runway, stop, picks, rig, clips, timeline). usage: node make_slots_v4.mjs DOCK_V4.glb OUT.json [verify.json]
import fs from 'fs'; import crypto from 'crypto';
import { RIG, RUNWAY, COLS, STOP, PICKS, SLOTS, CLIPS, KT, SEGMENTS, EVENTS, DOCK_WORLD, TIER03, ROWS, BLOCK_X, TIER_Y } from './v4_layout.mjs';
const [,, GLB, OUT, VER] = process.argv; const md5 = crypto.createHash('md5').update(fs.readFileSync(GLB)).digest('hex');
const W = p => [+(p[0] + DOCK_WORLD[0]).toFixed(3), +(p[1] + DOCK_WORLD[1]).toFixed(3), +(p[2] + DOCK_WORLD[2]).toFixed(3)];
const V = VER ? JSON.parse(fs.readFileSync(VER)) : null;
const seg = SEGMENTS.map(([n, t0, t1]) => ({ segment: n, t0, t1, moves: { approach: 'bridge z + trolley x from rest to over the pick; hook 7.0 -> carry 6.0', lower: 'hook carry -> pick', pick_hold: 'hold; pick event 1.95 (parent box to Hook_Attach)', hoist: 'hook pick -> carry 6.0',
  travel: 'bridge z + trolley x to over the slot, hook at carry 6.0 (box base 4.5)', set_lower: 'hook carry -> slot', set_hold: 'hold; set event 5.75 (unparent box at the slot)', up: 'hook slot -> carry', return: 'bridge/trolley/hook back to rest (z 9.0, x 0, hook 7.0)' }[n] }));
const out = {
  version: 'layout_v4', dock_glb: 'cargo_dock_overhead_v4.glb', dock_glb_md5: md5, dock_origin_world: DOCK_WORLD, units: 'm, y up; local = world - dock_origin_world',
  camera: { ct_world: [369.5, 1.5, 8.6], frame_w: 48, rule: '38 deg vFOV, 18 deg pitch, d=(fw/2)/(tan19*aspect), ct = screen centre (unchanged from v3)' },
  launch_pad_x: 457,
  truck_stop_dock: { local: STOP.local, world: STOP.world, heading: '+X', lane: 'loaded lane world z 13', moved_from_world: [386.5, 0, 13], why: 'GC-1 cannot reach x 386.5; the stop slides 24.1 m west along the same lane so both bed slots are under the GC-1 runway' },
  picks: Object.fromEntries(Object.entries(PICKS).map(([k, p]) => [k, { node: 'Pick_' + k, bed_slot: p.bed_slot, box_base_local: p.box_base, box_base_world: W(p.box_base), hook_attach_local: p.hook }])),
  crane: { name: 'GC-1', cap_t: 40, type: 'overhead bridge crane on an elevated runway (was a rail gantry in v3)', node: 'GC_Rig', joints: { GC_Bridge: 'translation z (local), rest 9.0, range [3.8, 21.0]', GC_Trolley: 'translation x, y 11.5, rest 0, range [-5.2, 5.2]', GC_Hook: 'translation y relative to trolley; Hook_Attach world y = 11.5 + t.y; rest 7.0, carry 6.0' },
    hook_attach: 'Hook_Attach (child of GC_Hook); parent the CargoBox at (0,-1.5,0) so its Hook_Point (0,1.5,0) sits on Hook_Attach; yaw 0', draw_calls: 1, mesh: 'GC_Mesh (skinned, SHM_Paint, 3 joints)',
    runway: { beams_x: [-RUNWAY.x, RUNWAY.x], beam_y: [RUNWAY.y0, RUNWAY.y1], rail_top_y: RUNWAY.rail, z_local: [RUNWAY.z0, RUNWAY.z1], z_world: [RUNWAY.z0 - 8, RUNWAY.z1 - 8], columns_z_local: COLS, cantilever_m: +(RUNWAY.z1 - COLS[COLS.length - 1]).toFixed(2), lowest_overhead_over_road_m: V ? V.road.static_surface_min_y_at_z_gt_17_2 : null } },
  lv5: { node: 'GC_Bridge2_Stub', tier: 5, cap_t: 40, note: 'second bridge + trolley on the same runway, parks at the hall end (z 3.8). Stub only; it cannot pass GC-1, so GC-1 keeps all truck moves.' },
  slots: SLOTS.map(s => ({ name: s.name, block: s.block, row: s.row, tier: s.tier, local: s.box_base, world: W(s.box_base), hook_attach_local: s.hook, yaw_deg: 0 })),
  slot_grid: { blocks_x_local: BLOCK_X, rows_z_local: ROWS, tiers_base_y: TIER_Y, row_pitch_m: 1.8, box_bbox_m: [2.4, 1.5, 1.34], fill_order: 'Slot_01..05 left low (hall -> front), 06..10 right low, 11..15 left top, 16..20 right top; load out LIFO 20 -> 01' },
  clips: { count: CLIPS.length, names: 'Store_{A|B}_Slot_NN (bed -> slot), Load_{A|B}_Slot_NN (slot -> bed). A = Bed_Slot_01, B = Bed_Slot_02', duration_s: 8.0, fps_hint: 30,
    easing: 'smoothstep (3s^2 - 2s^3) per segment; baked as CUBICSPLINE with zero tangents (exact smoothstep)', key_times: KT, events: EVENTS, segments: seg,
    heights: { rest_hook_y: RIG.hook_rest, carry_hook_y: RIG.carry, carry_box_base_y: RIG.carry - 1.5, pick_hook_y: PICKS.A.hook[1], slot_hook_y: TIER_Y.map(y => y + 1.5) },
    box_rule: 't < 1.95: box on the bed (Store) or in the slot (Load); 1.95..5.75: child of Hook_Attach at (0,-1.5,0); >= 5.75: in the slot (Store) or on the bed (Load)' },
  timeline: { unload_truck: [{ clip: 'Store_A_Slot_NN', t: [0, 8] }, { clip: 'Store_B_Slot_NN+1', t: [8, 16] }], load_truck: [{ clip: 'Load_A_Slot_NN', t: [0, 8] }, { clip: 'Load_B_Slot_NN-1', t: [8, 16] }], per_box_s: 8, per_truck_s: 16 },
  road: { band_world_z: [10.2, 24.8], clear_strip_world_z_max: 9.2, ground_geometry_in_band: false, overhead: 'runway beams + knee braces cantilever over the loaded lane at >= ' + (V ? V.road.static_surface_min_y_at_z_gt_17_2 : '?') + ' m (accepted precedent: SC-1 jib >= 6.3 m, refinery bridge)' },
  tier03: { note: 'Lv3 extra containers moved to the ground in the freed right area (v3 they topped the removed Lv1 stacks)', centres_local_xz: TIER03 },
  retired: { SC1_storage_crane: 'not needed (GC-1 does all moves); storage_crane.glb kept in repo for reference', side_apron: 'removed', generic_container_stacks_lv1: 'removed', crane_gantry_move: 'removed (GC-1 legs/ground rails gone)' },
  verify: V ? { pass: V.pass, draws_lv1: V.draws_lv1, checks: V.checks, camera: V.camera, road: V.road } : null };
fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); console.log('wrote', OUT, md5);
