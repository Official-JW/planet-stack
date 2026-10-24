"""Edge check (mask_*: white = structure standing > 0.45 m; ground/road/ruts/deposits drop out) + comparison sheets. python3 sheets.py DIR  (stills in DIR, masks in DIR/_check)"""
import sys, os, json
from PIL import Image, ImageDraw, ImageFont
D = sys.argv[1]; FONT = '/usr/share/fonts/truetype/sand-box/google/Chakra Petch/ChakraPetch-Bold.ttf'
VS = ('current', 'A', 'B'); lab = {'current': 'CURRENT (ef45f6f1)', 'A': 'Lv10 A  TYCHO DEEPWORKS', 'B': 'Lv10 B  ARGENT SEAM'}
res = {}
for sz in ('393x852', '375x667'):
    for v in VS:
        m = Image.open(os.path.join(D, '_check', 'mask_%s_%s.png' % (v, sz))).convert('L').point(lambda p: 255 if p > 127 else 0); bb = m.getbbox(); W, H = m.size
        mg = dict(L=bb[0], R=W - bb[2], T=bb[1], B=H - bb[3]); res['%s_%s' % (v, sz)] = dict(bbox=bb, margins_px=mg, pass_5px=min(mg.values()) >= 5)
json.dump(res, open(os.path.join(D, '_check', 'edge_check.json'), 'w'), indent=1); print(json.dumps(res, indent=1))
f = ImageFont.truetype(FONT, 20)
for sz in ('393x852', '375x667'):
    g = [Image.open(os.path.join(D, 'mine_lv10_%s_%s.png' % (v, sz))).convert('RGB') for v in VS]; w, h = g[0].size
    S = Image.new('RGB', (w * 3 + 40, h + 44), (12, 13, 16)); d = ImageDraw.Draw(S)
    for i, (v, im) in enumerate(zip(VS, g)): S.paste(im, (10 + i * (w + 10), 40)); d.text((10 + i * (w + 10), 10), lab[v], font=f, fill=(170, 235, 255))
    S.save(os.path.join(D, 'mine_lv10_compare_game_%s.png' % sz))
if all(os.path.exists(os.path.join(D, 'mine_lv10_%s_hero_1920x1080.png' % v)) for v in VS):
    h = [Image.open(os.path.join(D, 'mine_lv10_%s_hero_1920x1080.png' % v)).convert('RGB') for v in VS]; f2 = ImageFont.truetype(FONT, 34)
    S = Image.new('RGB', (1920, 1100), (12, 13, 16)); d = ImageDraw.Draw(S)
    for (x, y), v, im in zip(((0, 0), (960, 0), (480, 560)), VS, h): S.paste(im.resize((960, 540)), (x, y)); d.text((x + 18, y + 14), lab[v], font=f2, fill=(170, 235, 255))
    S.save(os.path.join(D, 'mine_lv10_compare_hero_1920x1100.png'))
