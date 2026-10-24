# Builds the proof sheets in proofs/ from the raw captures.  python3 compose.py <raw_dir> <proofs_dir>
import sys, json, os, shutil
from PIL import Image, ImageDraw, ImageFont
RAW, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
F = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', s)
FB = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
M = json.load(open(f'{RAW}/metrics_stills_strips_metrics.json'))
SHAKE = "Rumble: camera never moves. Ship + flames only, horizontal +/-1.0 px at 375x667 and 393x852 (0 px vertical, pad 0 px)."
def caption(img, lines, size=13):
    h = 10 + len(lines) * (size + 6); o = Image.new('RGB', (img.width, img.height + h), (12, 14, 22)); o.paste(img, (0, 0)); d = ImageDraw.Draw(o)
    for i, l in enumerate(lines): d.text((8, img.height + 6 + i * (size + 6)), l, fill=(220, 226, 240), font=F(size))
    return o
# 1) clean stills with the requested names + labelled copies
for name, note in [('full_thrust', 'Full thrust, lift-off +3.8 s (alt 17 m): white-hot core + 4 Mach diamonds per engine'), ('ignition_dust', 'Ignition, lift-off -1.3 s: dust/grit ring + hard-edged radial sheets, warm pad glow')]:
    for wh in ['375x667', '393x852']:
        for sfx in ['', '@2x']:
            src = f'{RAW}/{name}_{wh}{sfx}.png'; shutil.copy(src, f'{OUT}/{name}_{wh}{sfx}.png')
        im = Image.open(f'{RAW}/{name}_{wh}@2x.png')
        caption(im, [note, SHAKE, 'Preview: official pad camera (Cam_Target, frame_w 78.25, 38 deg, 18 deg down), pad GLB 82131aba, DPR 2.'], 22).save(f'{OUT}/{name}_{wh}@2x_labeled.png')
# 2) nozzle close-ups
cl = Image.open(f'{RAW}/nozzle_closeup.png'); shutil.copy(f'{RAW}/nozzle_closeup.png', f'{OUT}/full_thrust_nozzle_closeup.png')
shutil.copy(f'{RAW}/nozzle_closeup_ignition.png', f'{OUT}/ignition_nozzle_closeup.png'); shutil.copy(f'{RAW}/nozzle_closeup_landing.png', f'{OUT}/landing_nozzle_closeup.png')
# 3) worst-case rumble frames with 5 px margins + bboxes
for wh in ['375x667', '393x852']:
    w, h = map(int, wh.split('x')); S = M[f'shake_{wh}']; tiles = []
    for side in ['L', 'R']:
        im = Image.open(f'{RAW}/shake_worst_{side}_{wh}.png').convert('RGB'); d = ImageDraw.Draw(im)
        d.rectangle([5, 5, w - 6, h - 6], outline=(255, 40, 40), width=1)
        for key, col in [('pad', (60, 255, 120)), ('ship', (80, 200, 255))]:
            b = S[side][key]; d.rectangle([b['x0'], b['y0'], b['x1'], b['y1']], outline=col, width=1)
        r, p, sr = S['rest']['ship'], S[side]['pad'], S[side]['ship']
        tiles.append(caption(im, [f'worst case {side}: ship x {sr["x0"]-r["x0"]:+.2f} px, y {sr["y0"]-r["y0"]:+.2f} px',
                                  f'pad bbox moved {p["x0"]-S["rest"]["pad"]["x0"]:+.2f} / {p["y0"]-S["rest"]["pad"]["y0"]:+.2f} px', 'red = 5 px margin  green = pad  blue = ship'], 11))
    o = Image.new('RGB', (tiles[0].width * 2 + 10, tiles[0].height), (12, 14, 22)); o.paste(tiles[0], (0, 0)); o.paste(tiles[1], (tiles[0].width + 10, 0))
    caption(o, [SHAKE[:60], SHAKE[60:]], 11).save(f'{OUT}/shake_worst_case_{wh}.png')
# 4) frame strips
def strip(prefix, ts, labels, out, crop):
    tiles = []
    for t, lab in zip(ts, labels):
        im = Image.open(f'{RAW}/{prefix}_{t}.png').convert('RGB').crop(crop); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width, 54], fill=(12, 14, 22)); d.text((8, 4), lab[0], fill=(255, 255, 255), font=FB(20)); d.text((8, 30), lab[1], fill=(190, 200, 220), font=F(16))
        tiles.append(im)
    o = Image.new('RGB', (sum(t.width for t in tiles) + 4 * (len(tiles) - 1), tiles[0].height), (12, 14, 22)); x = 0
    for t in tiles: o.paste(t, (x, 0)); x += t.width + 4
    o.save(out)
L = [-2100, -1960, -1800, -1300, -800, 0, 1000, 2500, 3800, 5000, 6500]
LL = [('HC+0.9 s', 'hatch closed, engines off'), ('IGN+40 ms', 'flicker-on flash'), ('IGN+200 ms', 'catches, dust ring'), ('IGN+0.7 s', 'growing, sheets out'),
      ('IGN+1.2 s', 'full length, diamonds'), ('LIFT-OFF', 't = 0'), ('+1.0 s', 'full thrust'), ('+2.5 s', 'climbing'), ('+3.8 s', 'diamonds start fading'),
      ('+5.0 s', 'plume widens, fades'), ('+6.5 s', 'diamonds gone, glow off')]
strip('strip_L', L, LL, f'{OUT}/liftoff_strip.png', (150, 0, 600, 1200))
strip('strip_L', L, LL, f'{OUT}/liftoff_strip_fullframe.png', (0, 0, 750, 1334))
D = [-6000, -4000, -2600, -1800, -1000, -300, 0, 120, 300, 700, 1500]
DL = [('TD-6.0 s', 'burn lit, 61 m up'), ('TD-4.0 s', 'plume narrowing'), ('TD-2.6 s', 'diamonds back'), ('TD-1.8 s', 'dust ring (smaller)'), ('TD-1.0 s', 'throttling down'),
      ('TD-0.3 s', '~50% thrust'), ('TOUCHDOWN', 't = 0, 45%'), ('TD+120 ms', 'cutting off'), ('TD+300 ms', 'cut-off, vapour puff'), ('TD+0.7 s', 'puff spreading'), ('TD+1.5 s', 'settled')]
strip('strip_D', D, DL, f'{OUT}/landing_strip.png', (150, 0, 600, 1200))
strip('strip_D', D, DL, f'{OUT}/landing_strip_fullframe.png', (0, 0, 750, 1334))
print('ok')
