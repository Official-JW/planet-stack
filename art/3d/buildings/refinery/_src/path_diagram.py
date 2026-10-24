"""Top-down truck path diagram for the Refinery: overlays markers, legs, yaw arrows, s_m and eased leg times on the ortho top render
(render_game_proofs.py --only top: ortho 30 m wide, centre (-5, -4.5) Blender = glTF (-5, z 4.5), 1600x1000).
usage: python3 path_diagram.py GAME.glb TOP.png OUT.png"""
import sys, json, struct, math
from PIL import Image, ImageDraw, ImageFont
G, TOP, OUT = sys.argv[1:4]
b = open(G, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + L])
im = Image.open(TOP).convert('RGB'); W, H = im.size; S = W / 30.0; CX, CZ = -5.0, 4.5
def px(x, z): return (W / 2 + (x - CX) * S, H / 2 + (z - CZ) * S)    # glTF z grows down-screen (camera on +Z looks -Z: top view +Y up = -z)
d = ImageDraw.Draw(im)
try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
except Exception: f = f2 = ImageFont.load_default()
N = {n['name']: n for n in g['nodes'] if 'name' in n}
seq = ['Truck_Path_%02d' % i for i in range(1, 8)] + ['Truck_Dump', 'Truck_Exit']
P = {n: N[n].get('translation', [0, 0, 0]) for n in seq}
def clamp(p): return (min(max(p[0], 30), W - 30), min(max(p[1], 30), H - 30))
for a, c in zip(seq, seq[1:]):
    nl = json.loads(N[a]['extras']['next_leg']); col = (255, 170, 40) if nl['dir'] == 'reverse' else ((80, 220, 255) if 'arc' in nl['type'] else (120, 255, 120))
    if a == 'Truck_Path_06':   # draw the arc properly
        pass
    p0, p1 = clamp(px(P[a][0], P[a][2])), clamp(px(P[c][0], P[c][2]))
    if 'arc' in nl['type']:
        cx, cz, r = -3.5, 4.5, 4.5
        a0 = math.atan2(P[a][2] - cz, P[a][0] - cx); a1 = math.atan2(P[c][2] - cz, P[c][0] - cx)
        if a1 > a0: a1 -= 2 * math.pi
        pts = [px(cx + r * math.cos(a0 + (a1 - a0) * k / 20), cz + r * math.sin(a0 + (a1 - a0) * k / 20)) for k in range(21)]
        d.line(pts, fill=col, width=5)
    else:
        d.line([p0, p1], fill=col, width=5)
    m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    off = {'Truck_Path_01': (-40, 10), 'Truck_Path_02': (0, 10), 'Truck_Path_07': (-30, 18), 'Truck_Dump': (0, 18)}.get(a, (14, -10))
    if 'arc' in nl['type']: m = px(-3.5 + 5.6 * math.cos(math.atan2((P[a][2] + P[c][2]) / 2 - 4.5, (P[a][0] + P[c][0]) / 2 + 3.5)), 4.5 + 5.6 * math.sin(math.atan2((P[a][2] + P[c][2]) / 2 - 4.5, (P[a][0] + P[c][0]) / 2 + 3.5))); off = (-20, -10)
    d.text((m[0] + off[0], m[1] + off[1]), '%.2f s%s' % (nl['t_s'], ' REV' if nl['dir'] == 'reverse' else ''), fill=col, font=f2)
for n in seq:
    x, _, z = P[n]; e = N[n]['extras']; q = px(x, z); inside = 0 <= q[0] <= W and 0 <= q[1] <= H; q = clamp(q)
    yw = math.radians(e.get('yaw_deg', 0.0)); dx, dz = math.cos(yw), -math.sin(yw)   # yaw about +Y: 0 = +X, 90 = -Z
    d.ellipse([q[0] - 9, q[1] - 9, q[0] + 9, q[1] + 9], fill=(230, 40, 30) if n != 'Truck_Dump' else (255, 210, 0), outline=(0, 0, 0), width=2)
    d.line([q, (q[0] + dx * 40, q[1] + dz * 40)], fill=(255, 255, 255), width=3)
    lab = '%s  s %.1f m%s' % (n.replace('Truck_', ''), e.get('s_m', 0), '' if inside else '  (x %.0f, off frame)' % x)
    lo = {'Truck_Path_03': (-10, -40), 'Truck_Path_07': (-200, 10), 'Truck_Exit': (12, 10), 'Truck_Path_01': (12, -36), 'Truck_Path_02': (-30, 16), 'Truck_Path_05': (14, -12), 'Truck_Path_06': (18, 4), 'Truck_Dump': (14, -34)}.get(n, (14, -30))
    d.text((q[0] + lo[0], q[1] + lo[1]), lab, fill=(255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
RT = N.get('Refinery', {}).get('extras', {}).get('truck_times'); RT = json.loads(RT) if RT else None
rx = sum(json.loads(N[n]['extras']['next_leg'])['t_s'] for n in seq[2:7])
txt = ['Refinery truck route (top, glTF x right, z down; 1 m = %.1f px). Green straight 8.33 m/s, cyan U-turn r 4.5 m at 4 m/s, orange reverse <= 3 m/s; eased (acc 3 / brake 4).' % S,
       'Arrive (U-turn start, Path_03) -> leave Truck_Dump: U-turn %.2f s + reverse %.2f s + tip %.2f s = %.2f s.  Inbound lane z +9, outbound z 0, both end at x -46.' % (
           (RT['uturn_03_to_07_s'], RT['reverse_s'], RT['tip_s'], RT['arrive_to_leave_s']) if RT else (sum(json.loads(N[n]['extras']['next_leg'])['t_s'] for n in seq[2:6]), json.loads(N['Truck_Path_07']['extras']['next_leg'])['t_s'], 3.0, rx + 3.0))]
d.rectangle([0, H - 64, W, H], fill=(0, 0, 0))
for i, t in enumerate(txt): d.text((12, H - 58 + i * 28), t, fill=(235, 235, 235), font=f2)
im.save(OUT); print('wrote', OUT)
