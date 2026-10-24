# strip of the GC-1 Store_A_Slot_19 frames at full res (750x1334 each) with labels
from PIL import Image, ImageDraw, ImageFont
import sys
R = '/workspace/dockl/v4/r/'; OUT = sys.argv[1]
T = [('2.8', 'approach done'), ('6.0', 'PICK event'), ('8.6', 'hoisted to carry'), ('11.1', 'travel'), ('17.2', 'SET event'), ('19.2', 'hook up')]
ims = [Image.open(R + f'clip_{t}.png').convert('RGB') for t, _ in T]; w, h = ims[0].size
S = Image.new('RGB', (w * len(ims), h + 60), (5, 6, 11)); d = ImageDraw.Draw(S)
try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
except Exception: F = ImageFont.load_default()
for i, (im, (t, lab)) in enumerate(zip(ims, T)):
    S.paste(im, (i * w, 60)); d.text((i * w + 20, 14), f'GC-1 Store_A_Slot_19  t {t} s  {lab}', font=F, fill=(230, 235, 245))
    if i: d.line([(i * w, 60), (i * w, h + 60)], fill=(60, 70, 90), width=2)
S.save(OUT); print(OUT, S.size)
