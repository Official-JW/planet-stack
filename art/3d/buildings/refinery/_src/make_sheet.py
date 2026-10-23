import sys
from PIL import Image, ImageDraw, ImageFont
src, out, title, sub = sys.argv[1:5]
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
W = 4000; cell = 1000; head = 170
hero = Image.open(sys.argv[5] if len(sys.argv) > 5 else f'{src}/hero.png').convert('RGB')
hh = int(hero.height * W / hero.width)
H = head + 2 * cell + 70 + hh + 60
img = Image.new('RGB', (W, H), (14, 16, 20)); d = ImageDraw.Draw(img)
d.text((60, 40), title, font=ImageFont.truetype(FB, 64), fill=(240, 242, 245))
d.text((60, 115), sub, font=ImageFont.truetype(F, 32), fill=(160, 168, 178))
lf = ImageFont.truetype(FB, 34)
for k in range(8):
    im = Image.open(f'{src}/turn_{k*45:03d}.png').convert('RGB').resize((cell, cell), Image.LANCZOS)
    x, y = (k % 4) * cell, head + (k // 4) * cell
    img.paste(im, (x, y))
    d.rectangle((x + 20, y + 20, x + 190, y + 76), fill=(0, 0, 0))
    d.text((x + 34, y + 26), f'{k*45:>3}°', font=lf, fill=(255, 255, 255))
y = head + 2 * cell + 10
d.text((60, y + 8), 'HERO  —  cinematic 3840×2160 (scaled)', font=ImageFont.truetype(FB, 40), fill=(240, 242, 245))
img.paste(hero.resize((W, hh), Image.LANCZOS), (0, y + 60))
d.text((60, H - 48), 'Planet Stack · Refinery (Mine station) concept master · Cycles · astronaut = 1.8 m for scale · HT-04 shown for scale · original art', font=ImageFont.truetype(F, 28), fill=(140, 148, 158))
img.save(out, optimize=True); print(out, img.size)
