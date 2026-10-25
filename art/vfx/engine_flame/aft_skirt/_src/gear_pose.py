# Gear layout + pose maths shared by build_aft_skirt.py (geometry, joints, baked clips). gear.js runs the same maths at runtime
# from the numbers exported in the GLB extras (scene.extras.gear), so the two can't drift.
import math
import numpy as np
LEG_DEG = [60.0, 150.0, 240.0, 330.0]      # build angles: 15 deg off the 6-ring bells (45 + 60k), clear of the ladder (270) and the hoist drop (215)
BAND_R = 4.45                               # aft-skirt band outer skin (doors sit flush in it)
LINER_R = 4.04                              # bay back wall
BAY_HW = 0.42 / BAND_R                      # bay half width (rad): 0.84 m wide bays
BAY_Y0, BAY_Y1 = 2.50, 6.35                 # bay sill / header (sill 2.45 -> 2.50, A&A3 10/24: door bottom edge 5 cm further from the exit plane = plume >= 1.67 m at every level)
NOTCH_Y0, NOTCH_Y1, NOTCH_HW = 4.95, 5.85, 0.14 / 4.45   # door notch round the locked upper strut (crosses the skin at y ~5.0-5.7)
R_HIP, Y_HIP = 4.19, 6.05                   # hip pivot (bay top, mid depth)
R_FOOT = 6.4                                # foot pad centre radius when down
FOOT_Y = -0.242                             # pad bottom = Lv1 contact plane: 1.142 m below the nozzle exit plane (exit at y 0.9 in this frame)
R_UP, R_LO, PAD_R = 0.085, 0.07, 0.19       # slim: 17 cm upper strut, 14 cm shock body, 38 cm pads
LO_OFF = 0.17                               # lower strut sits 17 cm to the side of the upper, so it folds alongside it
DOOR_OPEN_DEG = 100.0
STROKE = 0.05                               # shock stroke: feet compress 5 cm at touchdown
# timeline (ms). Launch: rel lift-off (LO = tap + 55.99 s). Landing: rel touchdown (TD = LO + 616 s).
T = dict(R_DOOR_OPEN=(1000, 1600), R_KNEE=(1600, 3400), R_SWING=(2200, 3400), R_SETTLE=(3400, 3600), R_DOOR_CLOSE=(3600, 4200),
         D_DOOR_OPEN=(-7000, -6400), D_KNEE=(-6400, -4400), D_SWING=(-6300, -5200), D_BOUNCE=(-4400, -4000), D_DOOR_CLOSE=(-4000, -3400))
# knee and swing finish together (retract) / start together (deploy): the pad rim only clears the bay liner when the knee is not fully
# folded until the swing is >= 0.9 stowed (A&A3 60 Hz scan, 10/24/2026); fully folded with the leg still out it dipped 4 cm into the liner.
BOUNCE_RAD = 0.07          # knee lock settle, peak (rad): hyperextends past lock, rebounds 43 %, C1 (zero speed in and out)
STOW_SETTLE_RAD = 0.025    # hip settle as the leg seats in the bay, peak (rad): out toward the door plane first, never into the liner
def settle(u): return math.sin(math.pi * u) ** 2 * math.sin(2 * math.pi * u) * math.exp(-2.5 * u) / 0.2940373 if 0 <= u <= 1 else 0.0   # damped, peak 1
CLIP_NOTES = {'Gear_Retract': 'clip t = 0 at LO + 1.0 s (tap 56.99 s); 3.2 s long; doors open 0-0.6, knee 0.6-2.4, swing 1.2-2.4, stow settle 2.4-2.6, doors close 2.6-3.2',
              'Gear_Deploy': 'clip t = 0 at TD - 7.0 s (tap 664.99 s); 3.6 s long; doors open 0-0.6, knee 0.6-2.6, swing 0.7-1.8, lock bounce 2.6-3.0, doors close 3.0-3.6'}
def ease(x): x = min(1.0, max(0.0, x)); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def win(t, ab): a, b = ab; return ease((t - a) / (b - a))
def rot(axis, ang):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
def quat(axis, ang): axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis); s = math.sin(ang / 2); return [float(axis[0] * s), float(axis[1] * s), float(axis[2] * s), float(math.cos(ang / 2))]
def legs():
    out = []
    for k, dg in enumerate(LEG_DEG):
        a = math.radians(dg); n = np.array([math.cos(a), 0, -math.sin(a)]); t = np.array([math.sin(a), 0, math.cos(a)]); up = np.array([0, 1.0, 0])
        H = n * R_HIP + up * Y_HIP; F = n * R_FOOT + up * FOOT_Y; d = (F + up * 0.12 - H); d /= np.linalg.norm(d); K = H + d * 0.5 * np.linalg.norm(F + up * 0.12 - H)
        theta = math.acos(float(np.dot(d, -up)))
        hip_sign = min((1, -1), key=lambda s: np.linalg.norm(rot(t, s * theta) @ d - (-up)))
        Lk = np.linalg.norm(F - K)   # knee folds outward (foot swings out and up, never into the hull)
        knee_sign = max((1, -1), key=lambda s: np.dot((rot(t, s * math.pi / 2) @ (F - K)), n))
        off = t * LO_OFF
        doors = []
        for side, sg in (('a', -1), ('b', 1)):
            ha = a + sg * BAY_HW; hinge = np.array([math.cos(ha), 0, -math.sin(ha)]) * BAND_R + up * 0.5 * (BAY_Y0 + BAY_Y1); mid = a + sg * BAY_HW * 0.5
            pm = np.array([math.cos(mid), 0, -math.sin(mid)]) * BAND_R + up * hinge[1]
            dsign = max((1, -1), key=lambda s: np.dot(rot(up, s * 0.3) @ (pm - hinge), n))
            doors.append(dict(side=side, hinge=hinge.tolist(), sign=dsign))
        out.append(dict(k=k, a=a, deg=dg, n=n.tolist(), t=t.tolist(), H=H.tolist(), K=K.tolist(), F=F.tolist(), off=off.tolist(), d=d.tolist(), theta=theta,
                        hip_sign=hip_sign, knee_sign=knee_sign, doors=doors, j_leg=1 + k * 5, j_knee=2 + k * 5, j_foot=3 + k * 5, j_door_a=4 + k * 5, j_door_b=5 + k * 5))
    return out
def joint_list(L):
    J = [('Aft_Skirt_Root', -1, [0, 0, 0])]
    for lg in L:
        k = lg['k']; J.append((f'Gear_Leg_{k}', 0, lg['H'])); J.append((f'Gear_Knee_{k}', len(J) - 1, lg['K']))
        J.append((f'Gear_Foot_{k}', len(J) - 1, (np.array(lg['F']) + np.array(lg['off'])).tolist()))
        J.append((f'Gear_Door_{k}a', 0, lg['doors'][0]['hinge'])); J.append((f'Gear_Door_{k}b', 0, lg['doors'][1]['hinge']))
    return J
def state(phase, t, alt=0.0):
    """phase 'launch' (t rel LO) or 'land' (t rel TD) -> door (0 shut..1 open), knee (0 locked..1 folded), swing (0 down..1 stowed), ext (0..1 of the 5 cm stroke)"""
    if phase == 'launch':
        door = win(t, T['R_DOOR_OPEN']) - win(t, T['R_DOOR_CLOSE']); knee = win(t, T['R_KNEE']); swing = win(t, T['R_SWING']); bounce = 0.0
        a, b = T['R_SETTLE']; hip = STOW_SETTLE_RAD * settle((t - a) / (b - a))
    else:
        door = win(t, T['D_DOOR_OPEN']) - win(t, T['D_DOOR_CLOSE']); swing = 1 - win(t, T['D_SWING']); knee = 1 - win(t, T['D_KNEE'])
        a, b = T['D_BOUNCE']; bounce = -BOUNCE_RAD * settle((t - a) / (b - a)); hip = 0.0
    ext = 1 - min(1.0, max(0.0, (STROKE - alt) / STROKE))
    return dict(door=door, knee=knee, swing=swing, bounce=bounce, settle=hip, ext=ext)
def joint_values(lg, st):
    t = lg['t']; up = [0, 1, 0]
    v = {f"Gear_Leg_{lg['k']}": ('rotation', quat(t, lg['hip_sign'] * (lg['theta'] * st['swing'] - st.get('settle', 0.0)))),
         f"Gear_Knee_{lg['k']}": ('rotation', quat(t, lg['knee_sign'] * (math.pi * st['knee'] + st['bounce']))),
         f"Gear_Foot_{lg['k']}": ('translation', (np.array(lg['F']) + np.array(lg['off']) - np.array(lg['K']) + np.array(lg['d']) * STROKE * st['ext']).tolist())}
    for dr in lg['doors']: v[f"Gear_Door_{lg['k']}{dr['side']}"] = ('rotation', quat(up, dr['sign'] * math.radians(DOOR_OPEN_DEG) * st['door']))
    return v
def bake_clips(L):
    out = {}
    for name, phase, t0, dur in (('Gear_Retract', 'launch', 1000, 3200), ('Gear_Deploy', 'land', -7000, 3600)):
        times = [i / 30 for i in range(int(dur / 1000 * 30) + 1)]; chans = {}
        for tt in times:
            st = state(phase, t0 + tt * 1000, alt=1.0)   # in the air: shocks fully extended
            for lg in L:
                for jn, (path, val) in joint_values(lg, st).items(): chans.setdefault((jn, path), []).append(val)
        out[name] = (times, [(jn, path, vals) for (jn, path), vals in chans.items()])
    return out
def export_meta(L):
    return dict(legs=[{k: v for k, v in lg.items()} for lg in L], timeline_ms=T, door_open_deg=DOOR_OPEN_DEG, stroke_m=STROKE, bounce_rad=BOUNCE_RAD, stow_settle_rad=STOW_SETTLE_RAD,
                band_r=BAND_R, contact_y=FOOT_Y, bay=dict(half_width_rad=BAY_HW, y0=BAY_Y0, y1=BAY_Y1, liner_r=LINER_R), clip_notes=CLIP_NOTES)
