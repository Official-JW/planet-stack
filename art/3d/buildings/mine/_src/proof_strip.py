"""Compose the fill proof strip: FULL phone frames (10 / 33 / 66 / 100 %, chute_pour running at 10-66) each with a 3x inset of the truck.
  python3 proof_strip.py SRC_DIR RX OUT.png      (SRC_DIR from proof_fill.py --mode strip; RX 393 or 1179)"""
import sys
from PIL import Image, ImageDraw, ImageFont
src, rx, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
k = rx / 393.0
CROP = (255, 445, 375, 533)                    # truck on Path_Load + chute head on 393x852 (x0, y0, x1, y1)
PCTS = (10, 33, 66, 100)
def font(sz):
    try: return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', sz)
    except Exception: return ImageFont.load_default()
F = font(int(15 * k)); Fs = font(int(11 * k))
panels = []
for pct in PCTS:
    im = Image.open('%s/full_%d_%03d.png' % (src, rx, pct)).convert('RGB'); d = ImageDraw.Draw(im)
    c = tuple(int(v * k) for v in CROP)
    ins = im.crop(c).resize(((c[2] - c[0]) * 3, (c[3] - c[1]) * 3), Image.LANCZOS if rx > 393 else Image.NEAREST)
    ox, oy = int(16 * k), int(588 * k)
    d.rectangle((c[0] - 1, c[1] - 1, c[2], c[3]), outline=(47, 227, 255), width=max(1, int(k)))
    d.rectangle((ox - 2 * k, oy - 2 * k, ox + ins.width + 2 * k - 1, oy + ins.height + 2 * k - 1), fill=(47, 227, 255))
    im.paste(ins, (ox, oy))
    infl = 0.5 + 0.5 * (pct / 100) ** 0.8
    d.text((int(10 * k), int(150 * k)), 'fill %d %%' % pct, font=F, fill=(255, 255, 255))
    d.text((int(10 * k), int(170 * k)), 'influence %.3f%s' % (infl, '  + chute_pour' if pct < 100 else ''), font=Fs, fill=(200, 240, 255))
    d.text((ox, oy - int(15 * k)), '3x inset', font=Fs, fill=(200, 240, 255))
    panels.append(im)
gap = int(8 * k); W = sum(p.width for p in panels) + gap * (len(panels) - 1)
sheet = Image.new('RGB', (W, panels[0].height), (12, 12, 16)); x = 0
for p in panels: sheet.paste(p, (x, 0)); x += p.width + gap
sheet.save(out, optimize=True); print('WROTE', out, sheet.size)
