"""Labelled callout proof: draws module callouts over the station-camera phone render.
usage: python3 make_callouts.py refinery_phone_1179x2556.png refinery_phone_1179x2556_callouts.json out.png
Anchors come from build_refinery.py --only phone (projected median of each module's visible vertices)."""
import json, sys
from PIL import Image, ImageDraw, ImageFont
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
src, js, out = sys.argv[1:4]
im = Image.open(src).convert('RGB'); W, H = im.size; k = W / 1179
J = json.load(open(js)); C = J['callouts']
ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
lv = Image.new('RGBA', im.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lv)  # leaders under the label boxes
COL = {'he3': (90, 228, 255, 255), 'fuel': (255, 160, 64, 255), 'intake': (240, 240, 240, 255)}
f = ImageFont.truetype(FB, int(27 * k)); ft = ImageFont.truetype(FB, int(44 * k)); fs = ImageFont.truetype(F, int(27 * k))
d.rectangle((0, 0, W, int(250 * k)), fill=(8, 10, 14, 200))
d.text((int(40 * k), int(30 * k)), 'REFINERY  -  station camera', font=ft, fill=(255, 255, 255, 255))
d.text((int(40 * k), int(100 * k)), 'Cyan: HELIUM-3 line (Tier_03 / 08 / 12)', font=fs, fill=COL['he3'])
d.text((int(40 * k), int(140 * k)), 'Orange: FUEL line, LOX + LCH4 (Tier_05 / 20) > buried PL-1 to pad', font=fs, fill=COL['fuel'])
d.text((int(40 * k), int(180 * k)), 'White: intake, shared HT-04 tipping at Truck_Dump', font=fs, fill=COL['intake'])
def column(items, x0, y0, dy, right):
    items = sorted(items, key=lambda c: c['y'] if not right else c['y'])
    for i, c in enumerate(items):
        ty = y0 + i * dy; col = COL[c['kind']]
        tw = d.textlength(c['text'], font=f)
        tx = x0 - tw if right else x0
        d.rectangle((tx - 8 * k, ty - 4 * k, tx + tw + 8 * k, ty + 34 * k), fill=(8, 10, 14, 215), outline=col, width=max(1, int(2 * k)))
        d.text((tx, ty), c['text'], font=f, fill=col)
        lx = tx + tw + 8 * k if not right else tx - 8 * k; ly = ty + 15 * k
        dl.line((lx, ly, c['x'], c['y']), fill=col, width=max(1, int(3 * k)))
        r = 7 * k; dl.ellipse((c['x'] - r, c['y'] - r, c['x'] + r, c['y'] + r), fill=col, outline=(0, 0, 0, 255))
top = [c for c in C if c['kind'] == 'he3']; bot = [c for c in C if c['kind'] != 'he3']
mx = sorted(c['x'] for c in C)[len(C) // 2]
tl = sorted([c for c in top if c['x'] < mx], key=lambda c: c['x']); tr = sorted([c for c in top if c['x'] >= mx], key=lambda c: c['x'])
bl = [c for c in bot if c['x'] < mx]; br = [c for c in bot if c['x'] >= mx]
# He-3 callouts above the plant, fuel + intake below. Each label column picks the row order (brute force over permutations)
# with the fewest leader crossings, then the shortest total leader length.
import itertools
def _x(p1, p2, p3, p4):
    def o(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0
def place(items, x0, y0, dy, right):
    best = None
    for perm in itertools.permutations(items):
        segs = []
        for i, c in enumerate(perm):
            tw = d.textlength(c['text'], font=f); lx = (x0 - tw - 8 * k) if right else (x0 + tw + 8 * k)
            segs.append(((lx, y0 + i * dy + 15 * k), (c['x'], c['y'])))
        n = sum(_x(*segs[i], *segs[j]) for i in range(len(segs)) for j in range(i + 1, len(segs)))
        ln = sum(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for a, b in segs)
        if best is None or (n, ln) < best[0]: best = ((n, ln), perm)
    for i, c in enumerate(best[1]): column([c], x0, y0 + i * dy, dy, right)
    return best[0][0]
ytop = min(c['y'] for c in C) - 90 * k; ybot = max(c['y'] for c in C) + 90 * k
nt = max(len(tl), len(tr)); x_ = []
x_.append(place(tl, 30 * k, max(270 * k, ytop - nt * 52 * k), 52 * k, False))
x_.append(place(tr, W - 30 * k, max(270 * k, ytop - nt * 52 * k), 52 * k, True))
x_.append(place(bl, 30 * k, ybot, 52 * k, False))
x_.append(place(br, W - 30 * k, ybot, 52 * k, True))
print('CROSSINGS per column', x_)
Image.alpha_composite(Image.alpha_composite(im.convert('RGBA'), lv), ov).convert('RGB').save(out)
print('CALLOUTS', len(C), out)
