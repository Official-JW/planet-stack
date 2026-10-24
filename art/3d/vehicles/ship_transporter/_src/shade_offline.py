# Offline shaded-side check for the game-cam proofs (no render). The in-page p25() readback in gamecam.html is
# INVALID (beauty readPixels returns ~36 everywhere while the frame is ~60-190), so this measures the saved 1x _clean
# frames: luminance of non-ground, non-road pixels inside the transporter bbox (transporter + carried ship).
# The 'dark_p25' (p25 of all object pixels) bounds the shaded side from above; 'dark_p10' approximates its floor.
# It also repaints overlay line 3 in the committed 1x frames so they don't show the invalid number.
import json, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
G = sys.argv[1] if len(sys.argv) > 1 else 'proofs/gamecam'
d = json.load(open(f'{G}/gamecam_results.json')); out = {}
try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
except Exception: F = ImageFont.load_default()
for k, v in d.items():
    if not isinstance(v, dict) or 'bb' not in v or '@2x' in k: continue
    f = f"{G}/{v['file'].split('/')[-1]}"; im = np.asarray(Image.open(f.replace('.png', '_clean.png')).convert('RGB')).astype(float)
    b = v['bb']; x0, x1, y0, y1 = [int(round(b[q])) for q in ('x0', 'x1', 'y0', 'y1')]
    c = im[max(y0, 0):y1, max(x0, 0):x1]; Y = 0.2126*c[..., 0] + 0.7152*c[..., 1] + 0.0722*c[..., 2]
    m = ((np.abs(c[..., 0]-c[..., 2]) < 10) | (c[..., 2]-c[..., 0] > 6)) & (np.abs(Y-51) > 8) & (Y > 15)
    p10, p25, p50 = [round(float(x), 1) for x in np.percentile(Y[m], [10, 25, 50])]
    out[k] = {'object_px': int(m.sum()), 'dark_p10': p10, 'dark_p25': p25, 'p50': p50, 'spare_px': v['spare_px']}
    o = Image.open(f).convert('RGB'); dr = ImageDraw.Draw(o); dr.rectangle((0, 33, o.size[0], 47), fill=(5, 6, 11))
    dr.text((8, 34), f"spare {v['spare_px']} px {'PASS' if v['spare_px'] >= 5 else 'FAIL'} · shaded est. p10-p25 {p10:.0f}-{p25:.0f} (offline, target 60-75)", fill=(201, 211, 230), font=F); o.save(f)
json.dump({'method': __doc__ if __doc__ else open(__file__).read().split('\nimport')[0], 'note': 'in-page shaded_p25 in gamecam_results.json is INVALID (readback bug); use these', 'shots': out}, open(f'{G}/shade_offline.json', 'w'), indent=1)
for k, v in out.items(): print(k, v)
