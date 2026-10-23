"""python3 phone_downscale.py DIR : mine_phone_1179x2556.png -> mine_phone_393x852.png (Lanczos)"""
import sys, os
from PIL import Image
d = sys.argv[1]; im = Image.open(os.path.join(d, 'mine_phone_1179x2556.png')).convert('RGB')
im.resize((393, 852), Image.LANCZOS).save(os.path.join(d, 'mine_phone_393x852.png'), optimize=True)
print('ok', im.size)
