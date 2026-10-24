# python3 make_strip.py IN_DIR OUT.png "label1|label2|..."  -> 6 x 393x852 frames side by side with 10 px gutters
import sys
from PIL import Image, ImageDraw
d, out, labs = sys.argv[1], sys.argv[2], sys.argv[3].split('|')
ims = [Image.open(f'{d}/f_{i:04d}.png').convert('RGB') for i in range(len(labs))]
w, h = ims[0].size
S = Image.new('RGB', (w * len(ims) + 10 * (len(ims) - 1), h), (40, 40, 40))
for i, im in enumerate(ims):
    dr = ImageDraw.Draw(im); dr.rectangle([0, 0, w, 24], fill=(0, 0, 0)); dr.text((6, 6), labs[i], fill=(255, 255, 255)); S.paste(im, (i * (w + 10), 0))
S.save(out); print('strip', out, S.size)
