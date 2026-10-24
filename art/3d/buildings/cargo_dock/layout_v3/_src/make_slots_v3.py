"""Layout v3 slot plan: same 20 slots / numbering / fill order as v2, apron moved to the dock's right (former tank-farm front)."""
import json, sys
OUT = sys.argv[1]
DOCK = [360.0, 0.0, -8.0]; PAD_X = 457.0  # Launch Pad stays at x 457 (Director 10/24); only the Dock moved
COLS = [19.2, 21.9, 24.6, 27.3, 30.0]; ROWS = [14.5, 12.75]; TY = [0.12, 1.62]
CRANE_L = [24.6, 0.0, 16.5]; STOP_L = [26.5, 0.0, 21.0]
w = lambda l: [round(l[0] + DOCK[0], 4), round(l[1], 4), round(l[2] + DOCK[2], 4)]
slots = []; n = 0
for t, ty in enumerate(TY):
    for r in ROWS:
        for x in COLS:
            n += 1; l = [x, ty, r]; slots.append({'name': 'Slot_%02d' % n, 'tier': t + 1, 'local': l, 'world': w(l)})
J = {'what': 'Cargo Dock storage slots (layout v3), Lv1 cap 20. Slot_NN = CargoBox Base (bottom centre), yaw 0 (box long axis +X). Dock-local glTF metres of cargo_dock_compact_v3.glb; world = local + dock origin.',
     'dock_glb': 'cargo_dock_compact_v3.glb', 'dock_origin_world': DOCK, 'launch_pad_origin_world': [PAD_X, 0, 0],
     'box': [2.4, 1.5, 1.34], 'col_x': COLS, 'rows_z': ROWS, 'tier_y': TY, 'apron': [17.6, 31.6, 1.0, 15.6], 'apron_top_y': 0.12,
     'future_rows': [10.95, 9.2, 7.45, 5.7, 3.95], 'slots': slots,
     'storage_crane': {'glb': '../storage_crane/storage_crane.glb', 'place_world': w(CRANE_L), 'place_dock_local': CRANE_L, 'yaw_deg': 0},
     'truck_stop_dock': {'world': w(STOP_L), 'dock_local': STOP_L, 'heading': '+X (east, loaded lane z 13)',
                         'note': 'FB-05 origin; Bed_Slot_01 -> Pick_A (%.2f, 1.9, 13), Bed_Slot_02 -> Pick_B (%.2f, 1.9, 13)' % (w(STOP_L)[0] - 1.15, w(STOP_L)[0] - 3.65)}}
json.dump(J, open(OUT, 'w'), indent=1); print(OUT, len(slots), slots[0], slots[-1])
