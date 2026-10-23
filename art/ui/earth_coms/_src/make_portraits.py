"""Earth Coms portrait crops from Jacob's photo (art/eve/eve_source_jacob_1408.png).
Crops + resizes + a light cool grade only. The face is not redrawn or regenerated.
Run from repo root: python3 art/ui/earth_coms/_src/make_portraits.py"""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
SRC = "art/eve/eve_source_jacob_1408.png"
OUT = "art/ui/earth_coms"
src = Image.open(SRC).convert("RGB")
assert src.size == (1408, 1408)

def grade(im):
    """Light cool grade: shadows lean cyan/teal, highlights stay neutral, skin kept natural."""
    a = np.asarray(im).astype(np.float32) / 255.0
    lum = (0.2126*a[..., 0] + 0.7152*a[..., 1] + 0.0722*a[..., 2])[..., None]
    shadow = np.clip(1.0 - lum*1.6, 0, 1)            # weight toward darks
    tint = np.array([-0.030, 0.006, 0.030])           # cyan-ish lift in shadows
    a = a + shadow*tint
    a[..., 0] *= 0.985                                # tiny overall red trim (cooler white balance)
    a[..., 2] *= 1.012
    a = (a - 0.5)*1.04 + 0.5                         # a touch of contrast for small sizes
    return Image.fromarray((np.clip(a, 0, 1)*255 + 0.5).astype(np.uint8))

def save(im, name, alpha=False):
    # PNG fallback: 256-colour palette (Floyd-Steinberg) to keep the kit small; WebP is the runtime file.
    im.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG).save(f"{OUT}/{name}.png", optimize=True)
    q = 80
    while True:
        im.save(f"{OUT}/{name}.webp", "WEBP", quality=q, method=6, alpha_quality=90)
        if os.path.getsize(f"{OUT}/{name}.webp") <= 40_000 or q <= 60: break
        q -= 4
    print(name, im.size, "png", os.path.getsize(f"{OUT}/{name}.png"), "webp", os.path.getsize(f"{OUT}/{name}.webp"), "q", q)

g = grade(src)

# Round avatar, head and shoulders. Source box (x0,y0,x1,y1), square.
AV = (322, 96, 1002, 776)
av_master = g.crop(AV)
for pt_px, sfx in ((64, "1x"), (128, "2x"), (192, "3x")):
    big = pt_px*4                                     # supersampled circular mask -> clean AA edge
    m = Image.new("L", (big, big), 0); ImageDraw.Draw(m).ellipse((0, 0, big-1, big-1), fill=255)
    m = m.resize((pt_px, pt_px), Image.LANCZOS)
    im = av_master.resize((pt_px, pt_px), Image.LANCZOS)
    if pt_px <= 64: im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=40, threshold=1))
    im = im.convert("RGBA"); im.putalpha(m)
    save(im, f"eve_avatar_{sfx}", alpha=True)

# Video feed, 150x112 pt (≈4:3), head to chest, comms screen at left behind her.
W, H = 150, 112
FW = 940; FH = round(FW*H/W)                          # 940 x 702
FX, FY = 112, 40
assert FX+FW <= 1408 and FY+FH <= 1408
feed = g.crop((FX, FY, FX+FW, FY+FH))
for s, sfx in ((1, "1x"), (2, "2x"), (3, "3x")):
    im = feed.resize((W*s, H*s), Image.LANCZOS)
    if s == 1: im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=40, threshold=1))
    save(im, f"eve_feed_{sfx}")
print("feed box", (FX, FY, FX+FW, FY+FH), "avatar box", AV)
