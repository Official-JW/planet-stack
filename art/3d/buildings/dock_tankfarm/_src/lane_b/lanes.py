import json, math
R_T = (12**2 + 3.6**2) / (4 * 3.6)          # bay taper: two equal reverse arcs, 12 m long, 3.6 m offset
th = math.asin(6 / R_T); ARC = R_T * th; TAPER = 2 * ARC
OUT, BACK, BAY, PSPUR = 23.0, 32.0, 19.4, 19.75
RX_LOAD, RX_U, R_U = 318.0, 295.0, 4.5
pad_stop, pad_u, r_pu = 639.5, 641.0, (BACK - PSPUR) / 2
wp_out = [
 dict(n='Refinery Truck_Park (RC-1 load)', p=[318.0, OUT], hdg='+X', stop='load (RC-1)'),
 dict(n='Dock Bay_Taper_In', p=[464.0, OUT], seg_in='straight 146.0 m'),
 dict(n='Dock Road_Entry (bay straight start)', p=[476.0, BAY], seg_in=f'taper 2 arcs r {R_T:.2f} ({math.degrees(th):.1f} deg each), {TAPER:.2f} m'),
 dict(n='Dock Truck_Stop_Dock', p=[480.0, BAY], seg_in='straight 4.0 m', stop='dwell store 31.4 s / load 42.0 s'),
 dict(n='Dock Bay_Exit', p=[488.0, BAY], seg_in='straight 8.0 m'),
 dict(n='Dock Bay_Taper_Out', p=[500.0, OUT], seg_in=f'taper {TAPER:.2f} m'),
 dict(n='OUT-LANE END -> AA2 pad spur taper start (proposed)', p=[620.5, OUT], seg_in='straight 120.5 m', aa2=True),
 dict(n='(AA2) pad spur straight start, proposed', p=[632.5, PSPUR], seg_in=f'taper 12 m / 3.25 m offset', aa2=True),
 dict(n='(AA2) pad Truck_Stop, proposed', p=[pad_stop, PSPUR], seg_in='straight 7.0 m', stop='pad unload', aa2=True)]
R_PT = (12**2 + 3.25**2) / (4 * 3.25); PT = 2 * R_PT * math.asin(6 / R_PT)
wp_back = [
 dict(n='(AA2) pad Truck_Stop, proposed', p=[pad_stop, PSPUR], hdg='+X', aa2=True),
 dict(n='(AA2) U-turn start (Turn_Start), proposed', p=[pad_u, PSPUR], seg_in='straight 1.5 m', aa2=True),
 dict(n='BACK-LANE START <- AA2 U-turn end', p=[pad_u, BACK], seg_in=f'U-turn r {r_pu:.3f} about ({pad_u}, {(BACK + PSPUR) / 2}), {math.pi * r_pu:.2f} m (AA2)', hdg='-X', aa2=True),
 dict(n='Refinery U-turn start', p=[RX_U, BACK], seg_in=f'straight {pad_u - RX_U:.1f} m'),
 dict(n='Refinery U-turn end', p=[RX_U, OUT], seg_in=f'U-turn r {R_U} about ({RX_U}, {(OUT + BACK) / 2}), {math.pi * R_U:.2f} m', hdg='+X'),
 dict(n='Refinery Truck_Park', p=[RX_LOAD, OUT], seg_in=f'straight {RX_LOAD - RX_U:.1f} m', stop='load')]
L_ref_dock = 146 + TAPER + 4
L_dock_pad = 8 + TAPER + 120.5 + PT + 7
L_back = 1.5 + math.pi * r_pu + (pad_u - RX_U) + math.pi * R_U + (RX_LOAD - RX_U)
old_out = 636.5 - 318; old_back = 4.5 + math.pi * 4.5 + 346 + math.pi * 4.5 + 23
J = dict(units='world glTF m, +X east, +Z toward camera, y 0', lanes=dict(out=OUT, back=BACK, road_w=4.6, band=[OUT - 2.8, BACK + 2.8], clear=1.0),
  dock_bay=dict(z=BAY, x=[464, 500], taper_m=12, taper_r=round(R_T, 3), taper_len=round(TAPER, 3), road_strip_z=[BAY - 2.3, BAY + 2.3]),
  turn_limits='tapers r 10.9 and U-turns r 4.5 / 6.125 are < TURN_R_MAX 25 -> TURN_SPEED 4 m/s; no S-bends in the corridor (only the bay lane-change tapers)',
  out=wp_out, back=wp_back,
  lengths=dict(out_ref_to_dock_stop=round(L_ref_dock, 2), out_dock_stop_to_pad_stop=round(L_dock_pad, 2), out_total=round(L_ref_dock + L_dock_pad, 2),
               back_pad_stop_to_ref=round(L_back, 2), old_out=round(old_out, 2), old_back=round(old_back, 2)),
  road_tiles_hint='straight tiles z 23: x 296..464 and 500..620.5; z 32: x 295..641; bay tiles z 19.4 x 476..488 + 2 taper pieces (instanced: no new draws)')
json.dump(J, open('lanes_B.json', 'w'), indent=1); print(json.dumps(J['lengths']), round(R_T, 3), round(TAPER, 3), round(R_PT, 3), round(PT, 3))
