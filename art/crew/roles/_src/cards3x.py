"""Planet Stack - pick-screen role cards, 3x for a 375 pt wide screen (see ../CARD_SPEC.md).
python3 cards3x.py HERO_DIR OUT_DIR [--roles a,b]   HERO_DIR/portrait_<role>.png (RGBA, transparent bg, from render_roles.py --mode portrait)
-> OUT_DIR/card_<role>.png  1125 x 480 px (= 375 x 160 pt @3x), palette PNG, target <= 60 KB.
Pure PIL: no 3D, safe to run any time."""
import sys, os, io, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import roles_table as RT
from badge2d import badge_icon, hex2rgb

FD = '/usr/share/fonts/truetype/sand-box/google/Rajdhani/'
def font(w, size): return ImageFont.truetype(FD + f'Rajdhani-{w}.ttf', size)
CW, CH = 1125, 480                       # 375 x 160 pt @3x
CH_ = 36                                 # corner chamfer (top-left + bottom-right)
PX0, PY0, PX1, PY1 = 24, 24, 444, 456    # portrait window (420 x 432)
TX = 486                                 # text column x
GROUP = {'start': 'STARTING CREW', 'flight': 'FLIGHT CREW', 'specialist': 'SPECIALIST'}
TOOL_LABEL = {'rock_pick': 'Rock pick', 'drive_controller': 'Drive controller + headset', 'big_wrench': 'Heavy wrench + tool belt',
              'cargo_tablet': 'Cargo tablet + radio', 'flight_yoke': 'Flight yoke + headset', 'nav_scope': 'Nav scope + headset',
              'power_driver': 'Power driver + tool belt', 'seed_case': 'Seedling pod', 'weld_torch': 'Weld torch', 'caliper': 'Caliper'}
TXT, TXT2, TXT3 = (244, 246, 249), (196, 205, 216), (138, 148, 160)

def chamfer(x0, y0, x1, y1, c): return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]

def wrap(d, text, f, w):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if d.textlength(t, font=f) <= w: cur = t
        else: lines.append(cur); cur = wd
    return lines + [cur]

def card(key, hero_path, idx):
    R = RT.ROLES[key]; acc = hex2rgb(R['accent'])
    bg = Image.new('RGBA', (CW, CH), (0, 0, 0, 255)); d = ImageDraw.Draw(bg)
    for y in range(CH):        # graphite gradient
        t = y / CH; d.line([(0, y), (CW, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip((26, 31, 39), (13, 16, 21))) + (255,))
    # portrait window: darker well + accent glow + faint grid
    well = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); wd = ImageDraw.Draw(well)
    wd.polygon(chamfer(PX0, PY0, PX1, PY1, 24), fill=(9, 11, 15, 255)); bg.alpha_composite(well)
    glow = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([PX0 + 40, PY0 + 60, PX1 - 40, PY1 + 120], fill=acc + (95,))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    m = Image.new('L', (CW, CH), 0); ImageDraw.Draw(m).polygon(chamfer(PX0, PY0, PX1, PY1, 24), fill=255)
    bg.paste(Image.alpha_composite(bg, glow), (0, 0), m)
    if hero_path and os.path.exists(hero_path):
        h = Image.open(hero_path).convert('RGBA')
        if h.size != (PX1 - PX0, PY1 - PY0): h = h.resize((PX1 - PX0, PY1 - PY0), Image.LANCZOS)
        lay = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); lay.alpha_composite(h, (PX0, PY0))
        bg.paste(Image.alpha_composite(bg, lay), (0, 0), m)
    d = ImageDraw.Draw(bg)
    d.line(chamfer(PX0, PY0, PX1, PY1, 24) + [chamfer(PX0, PY0, PX1, PY1, 24)[0]], fill=acc + (255,), width=3)
    # badge medallion on the portrait's lower-right corner
    b = badge_icon(R['badge'], R['accent'], 112)
    sh = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([PX1 - 92, PY1 - 92, PX1 + 28, PY1 + 28], fill=(0, 0, 0, 170))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4))); bg.alpha_composite(b, (PX1 - 88, PY1 - 88))
    # text column
    lab = f'{GROUP[R["group"]]}'; f0 = font('SemiBold', 30)
    num = f'{idx:02d}'; fn = font('Bold', 30)
    d.text((TX, 48), num, font=fn, fill=acc + (255,)); nx = TX + d.textlength(num, font=fn) + 14
    d.text((nx, 48), '/  ' + lab, font=f0, fill=TXT3 + (255,))
    name = R['name'].upper(); f1 = font('Bold', 100)
    while d.textlength(name, font=f1) > CW - TX - 60: f1 = font('Bold', f1.size - 2)
    d.text((TX - 4, 92), name, font=f1, fill=TXT + (255,))
    d.rectangle([TX, 214, TX + 120, 220], fill=acc + (255,))
    f2 = font('Medium', 46); lines = wrap(d, R['job'], f2, CW - TX - 56)[:2]
    for i, ln in enumerate(lines): d.text((TX, 240 + i * 54), ln, font=f2, fill=TXT2 + (255,))
    f3 = font('Bold', 28); f4 = font('SemiBold', 28)
    d.text((TX, 392), 'KIT', font=f3, fill=acc + (255,))
    d.text((TX + 58, 392), TOOL_LABEL.get(R['tool'], R['tool'].replace('_', ' ')).upper(), font=f4, fill=TXT3 + (255,))
    # mask to the card outline, accent frame, corner ticks
    out = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    mk = Image.new('L', (CW, CH), 0); ImageDraw.Draw(mk).polygon(chamfer(0, 0, CW - 1, CH - 1, CH_), fill=255)
    out.paste(bg, (0, 0), mk); d = ImageDraw.Draw(out)
    fr = chamfer(3, 3, CW - 4, CH - 4, CH_ - 2); d.line(fr + [fr[0]], fill=acc + (255,), width=6, joint='curve')
    for (x, y, sx, sy) in ((CW - 12, 12, -1, 1), (12, CH - 12, 1, -1)):
        d.line([(x, y), (x + sx * 70, y)], fill=acc + (255,), width=6); d.line([(x, y), (x, y + sy * 70)], fill=acc + (255,), width=6)
    return out

def save_small(im, path, budget=60_000):
    """RGB median-cut palette (Floyd-Steinberg) + one fully transparent index for the chamfered corners -> small 8-bit PNG."""
    a = im.getchannel('A'); rgb = Image.new('RGB', im.size, (13, 16, 21)); rgb.paste(im.convert('RGB'), (0, 0), a)
    for ncol in (255, 224, 192, 160, 128, 96):
        q = rgb.quantize(colors=ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        pal = q.getpalette()[:3 * ncol] + [0, 0, 0] * (256 - ncol); q.putpalette(pal)
        q.paste(255, (0, 0), a.point(lambda v: 255 if v < 128 else 0))
        buf = io.BytesIO(); q.save(buf, 'PNG', optimize=True, transparency=255)
        if buf.tell() <= budget: break
    open(path, 'wb').write(buf.getvalue()); return ncol, buf.tell()

if __name__ == '__main__':
    hd, od = sys.argv[1], sys.argv[2]; os.makedirs(od, exist_ok=True)
    roles = sys.argv[sys.argv.index('--roles') + 1].split(',') if '--roles' in sys.argv else RT.ORDER
    for k in roles:
        i = RT.ORDER.index(k) + 1
        im = card(k, os.path.join(hd, f'portrait_{k}.png'), i)
        ncol, sz = save_small(im, os.path.join(od, f'card_{k}.png'))
        print('CARD', k, im.size, ncol, 'colours', sz, 'B')
