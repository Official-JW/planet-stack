"""Planet Stack - PIL passes after the renders (no 3D).
python3 compose.py lineup RAW_DIR OUT.png        RAW_DIR/lineup_raw.png + lineup_layout.json -> captioned lineup (badge + name plate per figure)
python3 compose.py game   RAW_DIR OUT_DIR        game_front/back_375x667.png -> OUT_DIR: game_front_375x667.png (as rendered), game_back_375x667.png,
                                                 game_figures_x8nn.png (1:1 pixels shown 8x, front | back, with role key)
python3 compose.py badges OUT_DIR                badge_<key>_256.png for every role + badges_sheet.png
python3 compose.py palette OUT.png               swatch sheet: normal / protan / deutan / tritan sims"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import roles_table as RT
from badge2d import badge_icon, hex2rgb
FD = '/usr/share/fonts/truetype/sand-box/google/Rajdhani/'
def font(w, size): return ImageFont.truetype(FD + f'Rajdhani-{w}.ttf', size)

def lineup(raw_dir, out):
    im = Image.open(os.path.join(raw_dir, 'lineup_raw.png')).convert('RGBA'); L = json.load(open(os.path.join(raw_dir, 'lineup_layout.json')))
    W, H = im.size; F = L['figures']; k_ = W / 3200
    f = font('Bold', int(34 * k_)); fs = font('SemiBold', int(22 * k_))
    for k, v in F.items():
        R = RT.ROLES[k]; acc = hex2rgb(R['accent']); t = R['name'].upper()
        d = ImageDraw.Draw(im); w = max(d.textlength(t, font=f), 120 * k_)
        x = v['x']; y = min(v['feet_y'] + 30 * k_, H - 150 * k_)
        pl = Image.new('RGBA', im.size, (0, 0, 0, 0)); p = ImageDraw.Draw(pl)
        pw = w / 2 + 20 * k_
        p.rounded_rectangle([x - pw, y + 46 * k_, x + pw, y + 102 * k_], radius=int(6 * k_), fill=(16, 19, 25, 225))
        p.rectangle([x - pw, y + 97 * k_, x + pw, y + 102 * k_], fill=acc + (255,))
        im.alpha_composite(pl)
        b = badge_icon(R['badge'], R['accent'], int(64 * k_)); im.alpha_composite(b, (int(x - b.width / 2), int(y - 22 * k_)))
        d = ImageDraw.Draw(im); d.text((x - d.textlength(t, font=f) / 2, y + 50 * k_), t, font=f, fill=(244, 246, 249, 255))
        n = f'{RT.ORDER.index(k) + 1:02d}'; d.text((x - d.textlength(n, font=fs) / 2, y + 108 * k_), n, font=fs, fill=acc + (255,))
    im.convert('RGB').save(out, optimize=True); print('LINEUP', out, im.size, os.path.getsize(out))

def game(raw_dir, od):
    os.makedirs(od, exist_ok=True); crops = []
    for v in ('front', 'back'):
        im = Image.open(os.path.join(raw_dir, f'game_{v}_375x667.png')).convert('RGB'); im.save(os.path.join(od, f'game_{v}_375x667.png'), optimize=True)
        L = json.load(open(os.path.join(raw_dir, f'game_{v}_layout.json')))['figures']
        xs = [q['x'] for q in L]; fy = max(q['feet_y'] for q in L); hp = max(abs(q['h_px']) for q in L)
        box = (max(0, int(min(xs) - 14)), int(fy - hp - 8), min(375, int(max(xs) + 14)), int(fy + 6))
        c = im.crop(box); crops.append((v, c.resize((c.width * 8, c.height * 8), Image.NEAREST), L, box, hp))
    W = max(c.width for _, c, *_ in crops) + 40; H = sum(c.height + 150 for _, c, *_ in crops) + 30
    sh = Image.new('RGB', (W, H), (20, 23, 28)); d = ImageDraw.Draw(sh); y = 20
    for v, c, L, box, hp in crops:
        d.text((20, y), f'{v.upper()} - game camera (38 deg vFOV, 18 deg down), figures {hp:.0f} px tall at 375 x 667, 1:1 pixels shown 8x', font=font('SemiBold', 30), fill=(220, 225, 232))
        sh.paste(c, (20, y + 44)); yy = y + 44 + c.height + 8
        for q in L:
            R = RT.ROLES[q['role']]; xx = 20 + (q['x'] - box[0]) * 8
            b = badge_icon(R['badge'], R['accent'], 44); sh.paste(b, (int(xx - 22), yy), b)
            t = f'{RT.ORDER.index(q["role"]) + 1:02d}'; d.text((xx - d.textlength(t, font=font('Bold', 26)) / 2, yy + 48), t, font=font('Bold', 26), fill=hex2rgb(R['accent']))
        y = yy + 100
    sh.save(os.path.join(od, 'game_figures_x8nn.png'), optimize=True); print('GAME', sh.size)

def badges(od):
    os.makedirs(od, exist_ok=True); sheet = Image.new('RGBA', (len(RT.ORDER) * 150 + 10, 210), (24, 28, 34, 255)); d = ImageDraw.Draw(sheet)
    for i, k in enumerate(RT.ORDER):
        R = RT.ROLES[k]; b = badge_icon(R['badge'], R['accent'], 256); b.save(os.path.join(od, f'badge_{R["badge"]}_256.png'), optimize=True)
        sheet.alpha_composite(badge_icon(R['badge'], R['accent'], 128), (i * 150 + 21, 12))
        for sz, ox in ((20, 0), (12, 30)):    # tiny sizes: how the medallion survives at phone scale
            t = badge_icon(R['badge'], R['accent'], sz); sheet.alpha_composite(t, (i * 150 + 50 + ox, 150 + (20 - sz) // 2))
        n = R['name']; d.text((i * 150 + 85 - d.textlength(n, font=font('SemiBold', 20)) / 2, 178), n, font=font('SemiBold', 20), fill=(210, 216, 224))
    sheet.save(os.path.join(od, 'badges_sheet.png'), optimize=True); print('BADGES', sheet.size)

def palette(out):
    from palette_check import sim, report
    kinds = ('normal', 'protan', 'deutan', 'tritan'); sw = 110
    im = Image.new('RGB', (180 + len(RT.ORDER) * sw, 60 + 4 * 90), (20, 23, 28)); d = ImageDraw.Draw(im)
    def l2s(c): return tuple(int(round(255 * (12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055))) for x in c)
    for i, k in enumerate(RT.ORDER):
        R = RT.ROLES[k]; d.text((180 + i * sw + 4, 14), R['name'], font=font('SemiBold', 16), fill=(220, 225, 232))
        for j, kd in enumerate(kinds):
            c = l2s(sim(R['accent'], kd)); x0, y0 = 180 + i * sw + 4, 50 + j * 90
            d.rectangle([x0, y0, x0 + sw - 8, y0 + 80], fill=c)
            b = badge_icon(R['badge'], '#%02x%02x%02x' % c, 40); im.paste(b, (x0 + 4, y0 + 36), b)
    r = report({k: RT.ROLES[k]['accent'] for k in RT.ORDER})
    for j, kd in enumerate(kinds):
        d.text((12, 60 + j * 90), kd, font=font('Bold', 28), fill=(230, 233, 238)); d.text((12, 94 + j * 90), f"min dE00 {r[kd]['min_pair']}", font=font('Medium', 20), fill=(160, 168, 178))
    im.save(out, optimize=True); print('PALETTE', im.size)

if __name__ == '__main__':
    m = sys.argv[1]
    if m == 'lineup': lineup(sys.argv[2], sys.argv[3])
    elif m == 'game': game(sys.argv[2], sys.argv[3])
    elif m == 'badges': badges(sys.argv[2])
    elif m == 'palette': palette(sys.argv[2])
