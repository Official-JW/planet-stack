# strip of the GC-1 Store_A_Slot_19 frames at full res (750x1334 each) with labels
from PIL import Image, ImageDraw, ImageFont
import sys
R = '/workspace/dockl/v4/r/'; OUT = sys.argv[1]
T = [('1.40', 'approach done'), ('1.95', 'PICK event'), ('2.55', 'hoisted to carry'), ('3.85', 'travel'), ('5.75', 'SET event'), ('6.35', 'hook up')]
ims = [Image.open(R + f'clip_{t}.png').convert('RGB') for t, _ in T]; w, h = ims[0].size
S = Image.new('RGB', (w * len(ims), h + 60), (5, 6, 11)); d = ImageDraw.Draw(S)
try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
except Exception: F = ImageFont.load_default()
for i, (im, (t, lab)) in enumerate(zip(ims, T)):
    S.paste(im, (i * w, 60)); d.text((i * w + 20, 14), f'GC-1 Store_A_Slot_19  t {t} s  {lab}', font=F, fill=(230, 235, 245))
    if i: d.line([(i * w, 60), (i * w, h + 60)], fill=(60, 70, 90), width=2)
S.save(OUT); print(OUT, S.size)
