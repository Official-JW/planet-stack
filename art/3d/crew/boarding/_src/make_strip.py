# python3 make_strip.py IN_DIR OUT.png "label1|label2|..."  -> 6 x 393x852 frames side by side with 10 px gutters
import sys, os
from PIL import Image, ImageDraw
d, out, labs = sys.argv[1], sys.argv[2], sys.argv[3].split('|')
ims = [Image.open(f'{d}/f_{i:04d}.png').convert('RGB') for i in range(len(labs))]
w, h = ims[0].size
S = Image.new('RGB', (w * len(ims) + 10 * (len(ims) - 1), h), (40, 40, 40))
for i, im in enumerate(ims):
    dr = ImageDraw.Draw(im)
    if os.environ.get('BAND'):   # dashed guide lines for the HUD-free band (e.g. BAND=144,383 at 375x667)
        for yb in (int(v) for v in os.environ['BAND'].split(',')):
            for x in range(0, w, 8): dr.line([(x, yb), (x + 4, yb)], fill=(255, 200, 0))
    dr.rectangle([0, 0, w, 24], fill=(0, 0, 0)); dr.text((6, 6), labs[i], fill=(255, 255, 255)); S.paste(im, (i * (w + 10), 0))
S.save(out); print('strip', out, S.size)
