"""A vs B comparison sheet from the proofs (PIL).  python3 compose_sheet.py -> ../proofs/st10_A_vs_B_sheet.png"""
import json, os
SO = json.load(open('proofs/gamecam/shade_offline.json'))['shots']
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.normpath(os.path.join(H, '..', 'proofs'))
F = '/usr/share/fonts/truetype/dejavu/'
f = lambda s, b=False: ImageFont.truetype(F + ('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'), s)
GC = json.load(open(os.path.join(P, 'gamecam', 'gamecam_results.json')))
INFO = json.load(open(os.path.join(H, 'concept_info.json')))
W, COL = 2600, 1260; BG = (11, 14, 22); INK = (220, 228, 240); DIM = (140, 150, 170); CY = (58, 208, 255)
def fit(im, w): return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
cols = []
for c in ('a', 'b'):
    I = INFO[c]; tiles = []
    hl = fit(Image.open(os.path.join(P, f'st10{c}_loaded_hero.png')).convert('RGB'), COL)
    he = fit(Image.open(os.path.join(P, f'st10{c}_empty_hero.png')).convert('RGB'), COL // 2 - 6)
    g1 = Image.open(os.path.join(P, 'gamecam', f'st10{c}_loaded_gamecam_393x852.png')).convert('RGB')
    g2 = Image.open(os.path.join(P, 'gamecam', f'st10{c}_loaded_gamecam_375x667.png')).convert('RGB')
    gh = he.height; g1 = g1.resize((round(g1.width * gh / g1.height), gh), Image.LANCZOS); g2 = g2.resize((round(g2.width * gh * 667 / 852 / g2.height), round(gh * 667 / 852)), Image.LANCZOS)
    cols.append((I, hl, he, g1, g2, c))
hmax = max(110 + hl.height + 12 + he.height + 12 + 300 for (_, hl, he, *_r) in cols)
img = Image.new('RGB', (W, 120 + hmax), BG); d = ImageDraw.Draw(img)
d.text((40, 26), 'PLANET STACK  ·  Lv10 SHIP TRANSPORTER  ·  concept A vs B  (stills for approval)', font=f(36, True), fill=INK)
d.text((40, 76), 'Both carry the 40 m Lv1 pad ship upright on 0.45 m cradle jacks, straddling the 6 legs (r 9.26 m) · astronaut tender (1.8 m) on foot with tablet · Mine concept B house style', font=f(19), fill=DIM)
for k, (I, hl, he, g1, g2, c) in enumerate(cols):
    x = 40 + k * (COL + 40); y = 120
    d.text((x, y), I['title'], font=f(28, True), fill=CY); y += 40
    for ln in I['lines']: d.text((x, y), ln, font=f(18), fill=INK); y += 26
    y += 8; img.paste(hl, (x, y)); y += hl.height + 12
    img.paste(he, (x, y)); gx = x + he.width + 12; img.paste(g1, (gx, y)); img.paste(g2, (gx + g1.width + 12, y))
    d.text((x + 8, y + 6), 'EMPTY (clamps open)', font=f(16, True), fill=INK)
    y += he.height + 14
    r1, r2 = GC[f'{c}_loaded_393x852'], GC[f'{c}_loaded_375x667']
    rows = [('Footprint', I['footprint']), ('Running gear', I['gear']), ('Cradle', I['cradle']),
            ('Master tris (Blender, bevels)', f"{I['tris_master']:,}"), ('Game GLB estimate', I['game']),
            ('Game cam 393x852 / 375x667', f"spare {r1['spare_px']} / {r2['spare_px']} px (>=5)  ·  shaded est. p10-p25 {SO[c+'_loaded_393x852']['dark_p10']:.0f}-{SO[c+'_loaded_393x852']['dark_p25']:.0f} (offline; 60-75 target, unverified)"),
            ('Preview draws (merged by material)', '13 + 4 astronaut (merged by material, names normalised)')]
    for a, bb in rows: d.text((x, y), a, font=f(17, True), fill=DIM); d.text((x + 360, y), bb, font=f(17), fill=INK); y += 27
img.save(os.path.join(P, 'st10_A_vs_B_sheet.png')); print('sheet', img.size)
