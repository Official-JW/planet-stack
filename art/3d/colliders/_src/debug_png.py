"""Top-down debug plate: every collider (padded box / hull), walk gaps and cab-door pads over the road plan + the GLB walkable surfaces.
nice -n 19 python3 debug_png.py RASTER_DIR -> ../proofs/colliders_topdown.png (overview 2 px/m + station panels 12 px/m)"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); R = sys.argv[1]
D = json.load(open(os.path.join(H, '..', 'colliders.json'))); M = json.load(open(os.path.join(R, 'meta.json'))); C = M['cell']
RP = json.load(open(os.path.join(H, '..', '..', 'vehicles', 'ship_transporter', 'proofs', 'transport_road_plan.json')))
F = '/usr/share/fonts/truetype/dejavu/'
def font(s, b=False): return ImageFont.truetype(F + ('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'), s)
BG = (12, 15, 22); INK = (225, 230, 240); DIM = (135, 145, 165)
KC = dict(structure=(255, 120, 60), prop=(255, 196, 60), linear=(240, 90, 200), round=(80, 200, 255), pit=(150, 110, 255), placeholder=(170, 170, 170))
def obb(b):
    t = math.radians(b['yaw_deg']); u = (math.cos(t), -math.sin(t)); v = (-u[1], u[0])
    return [(b['cx'] + sx * b['hx'] * u[0] + sz * b['hz'] * v[0], b['cz'] + sx * b['hx'] * u[1] + sz * b['hz'] * v[1]) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
def gaprect(g): return obb(dict(cx=g['cx'], cz=g['cz'], hx=g['hx'], hz=g['hz'], yaw_deg=g['yaw_deg']))
# walkable surface cells (geometry exists, nothing in the band) per item, for context
SURF = []
for it in M['items']:
    G = np.fromfile(os.path.join(R, it['id'] + '.bin'), np.uint8).reshape(it['NZ'], it['NX'])
    Y = np.fromfile(os.path.join(R, it['id'] + '_y.bin'), np.float32); HI = Y[it['NX'] * it['NZ']:].reshape(it['NZ'], it['NX'])
    SURF.append((it, (G == 0) & (HI > -1e8) & (HI < M['band'][0]), (G == 0) & (HI >= M['band'][1])))
def draw(x0, x1, z0, z1, s, labels):
    W, Hh = int((x1 - x0) * s), int((z1 - z0) * s); im = Image.new('RGB', (W, Hh), (18, 22, 32)); d = ImageDraw.Draw(im, 'RGBA')
    T = lambda x, z: ((x - x0) * s, (z - z0) * s)
    step = 10 if s >= 6 else 50
    for gx in range(int(math.ceil(x0 / step) * step), int(x1) + 1, step): d.line([T(gx, z0), T(gx, z1)], fill=(255, 255, 255, 18))
    for gz in range(int(math.ceil(z0 / step) * step), int(z1) + 1, step): d.line([T(x0, gz), T(x1, gz)], fill=(255, 255, 255, 18))
    # road plan: transporter road + shoulders, HB-10, flatbed lanes, U-turn, Habitat/Engineering footprints
    cl = RP['centerline']; hw = RP['running_width'] / 2; gw = RP['graded_width'] / 2; rz = cl[0][1]
    d.rectangle([T(cl[1][0], rz - gw), T(cl[2][0], rz + gw)], fill=(92, 88, 82, 255)); d.rectangle([T(cl[1][0], rz - hw), T(cl[2][0], rz + hw)], fill=(120, 114, 104, 255))
    hb = RP['lv10_high_bay_HB10']; d.rectangle([T(hb['x'][0], hb['z'][0]), T(hb['x'][1], hb['z'][1])], outline=(200, 200, 120, 200), width=2)
    for z0l, z1l in ((10.2, 15.8), (19.2, 24.8)): d.rectangle([T(296, z0l), T(464, z1l)], fill=(80, 84, 92, 255))
    p = T(458, 17.5); r = 4.5 * s + 2.8 * s; d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], outline=(80, 84, 92, 255), width=max(1, int(5.6 * s)))
    # GLB ground surfaces (walkable, < band) and overhead-only cells
    for it, walk, over in SURF:
        if it['X0'] > x1 or it['X0'] + it['NX'] * C < x0: continue
        for mask, col in ((walk, (70, 110, 90, 110)), (over, (90, 120, 200, 70))):
            js, is_ = np.nonzero(mask)
            for j, i in zip(js, is_):
                X, Z = it['X0'] + i * C, it['Z0'] + j * C
                if x0 <= X <= x1 and z0 <= Z <= z1: d.rectangle([T(X, Z), T(X + C, Z + C)], fill=col)
    for e in D['colliders']:
        b = e['box']; col = KC[e['kind']]
        if b['cx'] + 60 < x0 or b['cx'] - 60 > x1: continue
        pts = [T(*q) for q in obb(b)]; d.polygon(pts, fill=col + (60 if 'hull' in e else 110,), outline=col + (255,))
        if 'hull' in e: d.polygon([T(*q) for q in e['hull']], fill=col + (90,), outline=(255, 255, 255, 230))
        if e.get('dynamic'): d.line(pts + [pts[0]], fill=(255, 255, 255, 200), width=1)
        if labels and s >= 6: d.text(T(b['cx'], b['cz']), e['id'].split('_')[-2], font=font(9), fill=(255, 255, 255, 200), anchor='mm')
    for g in D['walk_gaps']:
        if 'cx' not in g: continue
        col = (60, 255, 140) if g['kind'] != 'cab_door' else (40, 230, 255)
        d.polygon([T(*q) for q in gaprect(g)], fill=col + (120,), outline=col + (255,))
        if 'marker_xz' in g: m = T(*g['marker_xz']); d.ellipse([m[0] - 3, m[1] - 3, m[0] + 3, m[1] + 3], fill=(255, 255, 255))
    return im
TITLE = f'PLANET STACK · crew walk-blockers colliders.json · {D["count"]} colliders + {len(D["walk_gaps"])} walk gaps · world glTF m, +Z (camera side) drawn down · pad {D["pad_m"]} m · band y {D["band_m"][0]}-{D["band_m"][1]} m'
OV = draw(-20, 1130, -66, 52, 2.0, False)
PANELS = [('Life Support (0, 0) e8427ec4', -16, 14, -38, 15), ('Mine (160, 0) ef45f6f1', 144, 190, -14, 17), ('Refinery (320, 0) 93c44166 + bridge v5.3 5d862767 + RC-1 755815ec', 271, 341, -37, 27),
          ('Cargo Dock (360, -8) compact_v3 9fb1ddbe + SC-1 fad409cc', 342, 395, -64, 26), ('Launch Pad (457, 0) 82131aba (ship = dynamic, white edge)', 424, 490, -50, 27),
          ('Shipyard (960, 0) c0e9d54e', 905, 1025, -40, 49), ('Habitat (1068) + Engineering (1120) placeholders', 1058, 1130, -10, 10)]
S = 12.0; ims = [(t, draw(a, b, c, dd, S, True)) for t, a, b, c, dd in PANELS]
if os.environ.get("DUMP"):
    for k, (t, im) in enumerate(ims): im.save(os.path.join(os.environ["DUMP"], f"p{k}.png"))
Wd = max(OV.width, 2400) + 80
rows, row, wsum = [], [], 0
for t, im in ims:
    if row and wsum + im.width + 40 > Wd - 80: rows.append(row); row, wsum = [], 0
    row.append((t, im)); wsum += im.width + 40
rows.append(row)
Ht = 140 + OV.height + 60 + sum(max(im.height for _, im in r) + 70 for r in rows) + 140
img = Image.new('RGB', (Wd, Ht), BG); d = ImageDraw.Draw(img)
d.text((40, 24), TITLE, font=font(26, True), fill=INK)
d.text((40, 64), 'orange structure · yellow prop · magenta linear (pipe/fence/rail/berm segment) · cyan round (hull outlined white) · violet pit · grey placeholder · GREEN walk gap (door / ladder foot / crew spot) · CYAN truck cab-door step-out', font=font(17), fill=DIM)
d.text((40, 90), 'under: road plan 1df3e3d (ST-10 transporter road + shoulders, HB-10 outline), layout_v3 flatbed lanes + U-turn, GLB walkable surfaces (green tint) and overhead-only cells (blue tint). overview 2 px/m, panels 12 px/m', font=font(17), fill=DIM)
y = 140; d.text((40, y - 26), 'Overview x -20..1130', font=font(18, True), fill=INK); img.paste(OV, (40, y)); y += OV.height + 60
for r in rows:
    x = 40
    for t, im in r: d.text((x, y), t, font=font(17, True), fill=INK); img.paste(im, (x, y + 26)); x += im.width + 40
    y += max(im.height for _, im in r) + 70
txt = 'unresolved: ' + ' | '.join(D['unresolved'])
for k in range(0, len(txt), 230): d.text((40, y), txt[k:k + 230], font=font(15), fill=(255, 200, 120)); y += 22
os.makedirs(os.path.join(H, '..', 'proofs'), exist_ok=True); img.save(os.path.join(H, '..', 'proofs', 'colliders_topdown.png')); print(img.size)
