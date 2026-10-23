"""Turntable contact sheet: 8 x 45-degree views (labelled) + close-up + crew-port detail.  python3 make_sheet.py [dir]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
T = os.path.join(D, 'turntable')
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
W, cell, head = 4400, 1100, 180
cl = Image.open(os.path.join(T, 'closeup.png')).convert('RGB'); po = Image.open(os.path.join(T, 'ports.png')).convert('RGB')
rh = 1500
clw = int(cl.width * rh / cl.height); pow_ = W - clw
H = head + 2 * cell + 80 + rh + 70
img = Image.new('RGB', (W, H), (14, 16, 20)); d = ImageDraw.Draw(img)
d.text((60, 36), 'Planet Stack · Starter Ship master — 8-angle turntable', font=ImageFont.truetype(FB, 66), fill=(240, 242, 245))
d.text((60, 118), 'true scale: 40.0 m tall, 8.0 m hull diameter · 1.8 m astronauts for scale · Cycles · sintered pad + low blast berm · original design, no logos',
       font=ImageFont.truetype(F, 34), fill=(160, 168, 178))
lf = ImageFont.truetype(FB, 40)
for k in range(8):
    im = Image.open(os.path.join(T, f'turn_{k*45:03d}.png')).convert('RGB').resize((cell, cell), Image.LANCZOS)
    x, y = (k % 4) * cell, head + (k // 4) * cell
    img.paste(im, (x, y)); d.rectangle((x + 20, y + 20, x + 210, y + 84), fill=(0, 0, 0))
    d.text((x + 36, y + 28), f'{k*45:>3}°', font=lf, fill=(255, 255, 255))
y = head + 2 * cell + 10
d.text((60, y + 10), 'CLOSE-UP — caged crew ladder + airlock dust-off, cargo door + hoist lowering REFINERY, MINE on pad', font=ImageFont.truetype(FB, 40), fill=(240, 242, 245))
d.text((clw + 40, y + 10), 'CREW DECK — 4 sleep pods behind small shuttered ports', font=ImageFont.truetype(FB, 40), fill=(240, 242, 245))
img.paste(cl.resize((clw, rh), Image.LANCZOS), (0, y + 70))
pw = po.resize((pow_, int(po.height * pow_ / po.width)), Image.LANCZOS)
img.paste(pw.crop((0, max(0, (pw.height - rh) // 2), pow_, max(0, (pw.height - rh) // 2) + rh)), (clw, y + 70))
img.save(os.path.join(D, 'starter_ship_turntable_sheet.png'), optimize=True); print(img.size)
