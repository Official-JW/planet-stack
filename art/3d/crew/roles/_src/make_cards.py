"""Planet Stack - crew role cards + lineup captions (PIL compositing, no 3D).
python3 make_cards.py cards  HERO_DIR OUT_DIR        -> OUT_DIR/card_<role>_750x1050.png   (hero_<role>.png 750x780 RGBA from render_roles.py --mode card)
python3 make_cards.py lineup RAW.png LAYOUT.json OUT -> lineup with a plain caption under each figure
python3 make_cards.py badges OUT_DIR                 -> badge_<key>_256.png icons for every role in roles_table
Card: 750 x 1050 px portrait (5:7; = 250 x 350 pt @3x on an iPhone pick screen). Font: Rajdhani (SIL OFL, same family as art/fonts)."""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import roles_table as RT
from badge2d import badge_icon, hex2rgb

FD = '/usr/share/fonts/truetype/sand-box/google/Rajdhani/'
def font(w, size): return ImageFont.truetype(FD + f'Rajdhani-{w}.ttf', size)
CW, CH = 750, 1050
TOOL_LABEL = {'rock_pick': 'Rock pick', 'drive_yoke': 'Drive yoke + headset', 'big_wrench': 'Heavy wrench', 'cargo_tablet': 'Cargo tablet + radio'}

def chamfer(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]

def card(key, hero_path, out_path, idx):
    R = RT.ROLES[key]; acc = hex2rgb(R['accent'])
    im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    # background: graphite vertical gradient inside the chamfered card shape
    bg = Image.new('RGBA', (CW, CH))
    for y in range(CH):
        t = y / CH; c0, c1 = (24, 29, 37), (12, 15, 20)
        ImageDraw.Draw(bg).line([(0, y), (CW, y)], fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)) + (255,))
    grid = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); g = ImageDraw.Draw(grid)
    for x in range(15, CW, 30): g.line([(x, 0), (x, 800)], fill=(255, 255, 255, 9))          # faint blueprint grid behind the hero
    for y in range(15, 800, 30): g.line([(0, y), (CW, y)], fill=(255, 255, 255, 9))
    bg.alpha_composite(grid)
    glow = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([CW / 2 - 300, 170, CW / 2 + 300, 770], fill=acc + (70,)); glow = glow.filter(ImageFilter.GaussianBlur(90))
    bg.alpha_composite(glow)
    fl = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); ImageDraw.Draw(fl).ellipse([CW / 2 - 230, 742, CW / 2 + 230, 800], fill=(0, 0, 0, 120))
    bg.alpha_composite(fl.filter(ImageFilter.GaussianBlur(14)))
    hero = Image.open(hero_path).convert('RGBA')
    bg.alpha_composite(hero, (0, 30))
    # info panel
    pnl = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); ImageDraw.Draw(pnl).rectangle([0, 812, CW, CH], fill=(14, 17, 22, 238))
    bg.alpha_composite(pnl); pd = ImageDraw.Draw(bg)
    pd.line([(36, 812), (CW - 36, 812)], fill=acc + (255,), width=3)
    pd.polygon([(36, 806), (190, 806), (202, 818), (36, 818)], fill=acc + (255,))
    name = R['name'].upper(); f1 = font('Bold', 74)
    while pd.textlength(name, font=f1) > CW - 80: f1 = font('Bold', f1.size - 2)
    pd.text((38, 834), name, font=f1, fill=(244, 246, 249, 255))
    pd.text((40, 922), R['job'], font=font('Medium', 38), fill=(196, 205, 216, 255))
    tl = TOOL_LABEL.get(R['tool'], R['tool'].replace('_', ' ').capitalize())
    pd.text((40, 984), 'KIT', font=font('Bold', 26), fill=acc + (255,))
    pd.text((90, 984), tl.upper(), font=font('SemiBold', 26), fill=(150, 160, 172, 255))
    # top bar: badge + role number
    b = badge_icon(R['badge'], R['accent'], 132)
    hexbg = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); ImageDraw.Draw(hexbg).ellipse([28, 28, 172, 172], fill=(10, 12, 16, 200))
    bg.alpha_composite(hexbg.filter(ImageFilter.GaussianBlur(3))); bg.alpha_composite(b, (34, 34))
    f2 = font('SemiBold', 26)
    lab = 'CREW ROLE'; pd.text((CW - 40 - pd.textlength(lab, font=f2), 44), lab, font=f2, fill=(150, 160, 172, 255))
    num = f'{idx:02d}'; f3 = font('Bold', 64); pd.text((CW - 40 - pd.textlength(num, font=f3), 66), num, font=f3, fill=acc + (255,))
    # mask to the chamfered shape + accent trim
    m = Image.new('L', (CW, CH), 0); ImageDraw.Draw(m).polygon(chamfer(0, 0, CW - 1, CH - 1, 46), fill=255)
    im.paste(bg, (0, 0), m)
    d = ImageDraw.Draw(im)
    d.line(chamfer(3, 3, CW - 4, CH - 4, 44) + [chamfer(3, 3, CW - 4, CH - 4, 44)[0]], fill=acc + (255,), width=6, joint='curve')
    d.line(chamfer(14, 14, CW - 15, CH - 15, 38) + [chamfer(14, 14, CW - 15, CH - 15, 38)[0]], fill=(255, 255, 255, 34), width=2)
    # corner ticks
    for (x, y, sx, sy) in ((CW - 14, 14, -1, 1), (14, CH - 14, 1, -1)):
        d.line([(x, y), (x + sx * 60, y)], fill=acc + (255,), width=6); d.line([(x, y), (x, y + sy * 60)], fill=acc + (255,), width=6)
    im.save(out_path, optimize=True); print('CARD', out_path, im.size)

def lineup(raw, layout, out):
    im = Image.open(raw).convert('RGBA'); L = json.load(open(layout)); d = ImageDraw.Draw(im)
    f = font('Bold', 40)
    for k, v in L.items():
        R = RT.ROLES[k]; acc = hex2rgb(R['accent']); t = R['name'].upper(); w = d.textlength(t, font=f)
        x = v['x']; y = min(v['feet_y'] + 34, 1080 - 70)
        pl = Image.new('RGBA', im.size, (0, 0, 0, 0)); pdr = ImageDraw.Draw(pl)
        pdr.rounded_rectangle([x - w / 2 - 22, y, x + w / 2 + 22, y + 54], radius=6, fill=(18, 22, 28, 215))
        pdr.rectangle([x - w / 2 - 22, y + 48, x + w / 2 + 22, y + 54], fill=acc + (255,))
        im.alpha_composite(pl); d = ImageDraw.Draw(im)
        d.text((x - w / 2, y + 2), t, font=f, fill=(244, 246, 249, 255))
    im.convert('RGB').save(out, optimize=True); print('LINEUP', out, im.size)

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'cards':
        hd, od = sys.argv[2], sys.argv[3]; os.makedirs(od, exist_ok=True)
        for i, k in enumerate([k for k in RT.ORDER if RT.ROLES[k]['tier'] == 1]):
            hp = os.path.join(hd, f'hero_{k}.png')
            if os.path.exists(hp): card(k, hp, os.path.join(od, f'card_{k}_750x1050.png'), i + 1)
    elif mode == 'lineup': lineup(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == 'badges':
        od = sys.argv[2]; os.makedirs(od, exist_ok=True)
        for k in RT.ORDER:
            R = RT.ROLES[k]; badge_icon(R['badge'], R['accent'], 256).save(os.path.join(od, f'badge_{R["badge"]}_256.png'), optimize=True)
