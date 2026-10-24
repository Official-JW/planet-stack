import io, os, cairosvg
from PIL import Image, ImageDraw, ImageFont
from make_icons import ICONS, OUT
FONTDIR = "/workspace/planet-stack/art/fonts"
def font(sz):
    for f in sorted(os.listdir(FONTDIR)) if os.path.isdir(FONTDIR) else []:
        if f.lower().endswith((".ttf", ".otf")):
            try: return ImageFont.truetype(os.path.join(FONTDIR, f), sz)
            except Exception: pass
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", sz)
def icon(svg, s):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=s, output_height=s))).convert("RGBA")
S = 3  # proof drawn at 3x (iPhone @3x) so the 24 pt bar is shown at real device pixels
W, H = 1200, 900
im = Image.new("RGBA", (W, H), (11, 14, 19, 255)); d = ImageDraw.Draw(im)
d.text((30, 22), "Planet Stack - crystal currency icon options (no diamond / no gem facets)", fill="#E6EEF5", font=font(28))
names = {"A_energy_cell": "A  Energy Cell", "B_shard_cluster": "B  Raw Shard Cluster", "C_core_token": "C  Helio Core Token"}
col = W // 3
for i, (k, svg) in enumerate(ICONS.items()):
    x0 = i * col
    d.text((x0 + 30, 80), names[k], fill="#7FF0FF", font=font(26))
    # large
    im.alpha_composite(icon(svg, 256), (x0 + (col - 256)//2, 125))
    # top bar mock at 24 pt (= 72 px @3x), and 1x 24 px actual
    by = 420
    d.rounded_rectangle((x0 + 30, by, x0 + col - 30, by + 44*S//2*1), radius=33, fill=(20, 25, 32, 255), outline=(52, 62, 74, 255), width=2)
    im.alpha_composite(icon(svg, 24*S//1 if False else 48), (x0 + 50, by + 9))
    d.text((x0 + 108, by + 12), "120", fill="#FFFFFF", font=font(40))
    d.text((x0 + 30, by + 75), "top bar @2x (24 pt = 48 px)", fill="#8794A2", font=font(18))
    # true 1x 24 px and 20 px
    by2 = 560
    d.rounded_rectangle((x0 + 30, by2, x0 + 160, by2 + 34), radius=17, fill=(20, 25, 32, 255), outline=(52, 62, 74, 255))
    im.alpha_composite(icon(svg, 24), (x0 + 40, by2 + 5))
    d.text((x0 + 70, by2 + 7), "120", fill="#FFFFFF", font=font(19))
    d.rounded_rectangle((x0 + 175, by2 + 2, x0 + 290, by2 + 32), radius=15, fill=(20, 25, 32, 255), outline=(52, 62, 74, 255))
    im.alpha_composite(icon(svg, 20), (x0 + 184, by2 + 7))
    d.text((x0 + 210, by2 + 8), "120", fill="#FFFFFF", font=font(16))
    d.text((x0 + 30, by2 + 42), "actual 24 px          actual 20 px", fill="#8794A2", font=font(16))
    # 24px zoomed 4x nearest to judge pixels
    z = icon(svg, 24).resize((96, 96), Image.NEAREST)
    bg = Image.new("RGBA", (96, 96), (20, 25, 32, 255)); bg.alpha_composite(z)
    im.alpha_composite(bg, (x0 + 30, 650)); d.text((x0 + 140, 690), "24 px, zoom x4", fill="#8794A2", font=font(16))
    # on light bg
    lb = Image.new("RGBA", (96, 96), (236, 240, 244, 255)); lb.alpha_composite(icon(svg, 64), (16, 16))
    im.alpha_composite(lb, (x0 + 30, 770)); d.text((x0 + 140, 810), "64 px on light", fill="#8794A2", font=font(16))
im.convert("RGB").save(os.path.join(OUT, "crystal_options_proof.png"), optimize=True)
print("ok")
