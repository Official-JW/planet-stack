import json
from PIL import Image, ImageDraw, ImageFont
F = json.load(open('/workspace/dockl/v3/frame_v3.json'))
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30); fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
except Exception: font = fs = ImageFont.load_default()
D = '/workspace/dockl/v3/r/'
# guides: band + subject box + spare numbers, both sizes
outs = []
for key, fn, s in (('375x667', 'full_375.png', 2), ('393x852', 'full_393.png', 3)):
    im = Image.open(D + fn).convert('RGB'); d = ImageDraw.Draw(im); z = F['sizes'][key]; t, b = z['band_y']; x0, y0, x1, y1 = z['subject_px']
    for y in (t, b): d.line([(0, y * s), (im.width, y * s)], fill=(255, 210, 0), width=s)
    d.rectangle([5 * s, (t + 5) * s, im.width - 5 * s, (b - 5) * s], outline=(255, 120, 0), width=1)
    d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], outline=(0, 255, 140), width=s)
    sp = z['spare_px']; txt = f"{key}  band y {t}-{b}  spare L {sp['left']} R {sp['right']} T {sp['top']} B {sp['bottom']} px"
    d.text((10 * s, (b + 10) * s), txt, fill=(255, 255, 255), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9 * s))
    d.text((10 * s, (b + 24) * s), f"ct {F['ct']}  frame_w {F['frame_w']}  (yellow = band, orange = 5 px limit, green = subject bounds)", fill=(255, 255, 255), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8 * s))
    outs.append(im.resize((im.width * 2 // s, im.height * 2 // s), Image.LANCZOS))
Wt = sum(o.width for o in outs) + 40; G = Image.new('RGB', (Wt, max(o.height for o in outs)), (30, 30, 34)); x = 0
for o in outs: G.paste(o, (x, 0)); x += o.width + 40
G.save(D + 'guides_v3.png')
# pick / swing / set strip at 375
fr = [('PICK  t 1.50 s', 'clip_1.5.png'), ('SWING  t 2.95 s', 'clip_2.95.png'), ('SET  t 4.30 s', 'clip_4.3.png')]
ims = [Image.open(D + f).convert('RGB') for _, f in fr]; w, h = ims[0].size
crop = (470, 520, 750, 740); cw, ch = (crop[2] - crop[0]) * 2, (crop[3] - crop[1]) * 2
S = Image.new('RGB', (3 * w + 4 * 20, 70 + h + 20 + ch + 60), (245, 246, 248)); d = ImageDraw.Draw(S)
d.text((20, 18), 'SC-1 storage crane  -  clip Store_A_Slot_20 (6.0 s, eased)  -  375x667 game cam @2x, layout v3, ct (369.5, 1.5, 8.6) frame_w 48', fill=(30, 30, 40), font=fs)
for i, ((lab, _), im) in enumerate(zip(fr, ims)):
    x = 20 + i * (w + 20); S.paste(im, (x, 70)); d.text((x + 10, 80), lab, fill=(255, 255, 255), font=font)
    dt = im.crop(crop).resize((cw, ch), Image.LANCZOS); S.paste(dt, (x + (w - cw) // 2, 70 + h + 20))
    ImageDraw.Draw(im)
    d.text((x + (w - cw) // 2, 70 + h + 20 + ch + 12), lab.split()[0] + '  detail x2 (crane + stack + FB-05 at Truck_Stop_Dock)', fill=(30, 30, 40), font=fs)
S.save(D + 'strip_v3.png'); print(S.size, G.size)
