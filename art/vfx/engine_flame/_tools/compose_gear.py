# Landing-gear proof sheets.  python3 compose_gear.py <raw_dir> <proofs_dir>   (raw from capture_all.mjs ONLY=...gear...)
import sys, json, os, glob
from PIL import Image, ImageDraw, ImageFont
RAW, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
F = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', s)
FB = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
M = json.load(open([f for f in glob.glob(f'{RAW}/metrics_*.json') if 'gear' in f][0]))['gear']
def label(im, a, b, sz=1.0):
    d = ImageDraw.Draw(im); h = int(54 * sz); d.rectangle([0, 0, im.width, h], fill=(12, 14, 22))
    d.text((8, 4), a, fill=(255, 255, 255), font=FB(int(20 * sz))); d.text((8, int(30 * sz)), b, fill=(190, 200, 220), font=F(int(15 * sz))); return im
def row(tiles, foot):
    o = Image.new('RGB', (sum(t.width for t in tiles) + 4 * (len(tiles) - 1), tiles[0].height + 12 + 20 * len(foot)), (12, 14, 22)); x = 0
    for t in tiles: o.paste(t, (x, 0)); x += t.width + 4
    d = ImageDraw.Draw(o)
    for i, l in enumerate(foot): d.text((8, tiles[0].height + 6 + i * 20), l, fill=(220, 226, 240), font=F(14))
    return o
cl = M['clearance']; c6, c11 = cl['n=6'], cl['lv=10']
mn = lambda c, src: min(c[f'launch_{src}']['c'], c[f'land_{src}']['c'])
CLR = (f"Measured flame-to-gear clearance, every frame at 30 fps (launch -2.0..+8.0 s, landing -8.0..+0.22 s): 6 engines plume {mn(c6, 'plume'):.2f} m, "
       f"splash {mn(c6, 'splash'):.2f} m; 11 engines plume {mn(c11, 'plume'):.2f} m, splash {mn(c11, 'splash'):.2f} m. Never touches a leg or door.")
calls = M['calls'][0]; ro = M['calls_ring_only'][0]
BUD = f"Draw calls with gear {calls['off']} -> {calls['on']} (flame +{calls['added']}); bare ring {ro['off']} -> {ro['on']}: gear adds {calls['off'] - ro['off']} (legs, doors, ring and band are one skinned mesh)."
for ph, ts, labs, name, hdr in [
    ('launch', [500, 1600, 2700, 4400], [('LO+0.5 s', 'legs down, locked'), ('LO+1.6 s', 'doors open'), ('LO+2.7 s', 'mid-fold (knee, then swing)'), ('LO+4.4 s', 'doors shut, flush')], 'gear_retract', 'Gear_Retract: doors open LO+1.0-1.6, fold LO+1.6-3.6 (knee first, then swing in, easeInOutCubic), doors close LO+3.6-4.2. LO = tap + 55.99 s.'),
    ('land', [-7500, -6400, -5000, -3000, 0], [('TD-7.5 s', 'stowed, doors shut'), ('TD-6.4 s', 'doors open'), ('TD-5.0 s', 'swinging out'), ('TD-3.0 s', 'locked, doors shut'), ('TOUCHDOWN', 'feet compress 5 cm')], 'gear_deploy', 'Gear_Deploy: doors open TD-7.0-6.4, swing out + lock TD-6.4-4.0 (settle bounce at lock), doors close TD-4.0-3.4, 5 cm compression at TD. TD = tap + 671.99 s.')]:
    tiles = []
    for t, (a, b) in zip(ts, labs):
        im = Image.open(f'{RAW}/gear_pad_{ph}_{t}.png').convert('RGB'); bb = M['frames'][f'pad_{ph}_{t}']['ship']
        cx, y1 = (bb['x0'] + bb['x1']) / 2, bb['y1']; box = [int(2 * (cx - 80)), int(2 * (y1 - 125)), int(2 * (cx + 80)), int(2 * (y1 + 25))]
        tiles.append(label(im.crop(box), a, b, 0.8))
    row(tiles, [hdr, '375x667 pad camera (DPR 2), crop round the ship base. ' + BUD, CLR]).save(f'{OUT}/{name}_strip_375.png')
    tiles = [label(Image.open(f'{RAW}/gear_close_{ph}_{t}.png').convert('RGB').resize((600, 600), Image.LANCZOS), a, b) for t, (a, b) in zip(ts, labs)]
    row(tiles, [hdr, 'Gear close-up (proof camera only; pad props hidden). 4 legs at build 60/150/240/330 deg, 15 deg off the nearest bell, clear of ladder and hoist.', CLR]).save(f'{OUT}/{name}_closeup.png')
json.dump(M, open(f'{OUT}/gear_metrics.json', 'w'), indent=1); print('ok')
