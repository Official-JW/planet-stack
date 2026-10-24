import sys
from PIL import Image, ImageDraw, ImageFont
src, W, H, out_clean, out_ov = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
BANDS = {(393, 852): (12, 381, 165, 534), (375, 667): (12, 363, 144, 383)}
im = Image.open(src).convert('RGB').resize((W, H), Image.LANCZOS); im.save(out_clean)
x0, x1, y0, y1 = BANDS[(W, H)]
ov = im.copy(); d = ImageDraw.Draw(ov, 'RGBA')
d.rectangle([0, 0, W, y0], fill=(0, 0, 0, 110)); d.rectangle([0, y1, W, H], fill=(0, 0, 0, 110))
d.rectangle([x0, y0, x1, y1], outline=(255, 214, 0, 255), width=1)
try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
except Exception: f = None
d.text((x0 + 3, y0 - 14), 'safe band x %d-%d  y %d-%d  (frame_w 78.25, >=5 px spare)' % (x0, x1, y0, y1), fill=(255, 214, 0, 255), font=f)
d.text((4, 4), 'Launch Pad Lv0 + all tiers - %dx%d game camera' % (W, H), fill=(255, 255, 255, 255), font=f)
ov.save(out_ov)
