"""Draw a role badge (from roles_table.BADGES) as a flat 2D icon with PIL: graphite disc, accent ring, white symbol."""
from PIL import Image, ImageDraw
import roles_table as RT

def hex2rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def badge_icon(key, accent, size=256, ss=4, disc='#1d222a', sym='#f2f4f7', ring_w=0.11):
    S = size * ss; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2; R = S / 2 - 2 * ss
    d.ellipse([c - R, c - R, c + R, c + R], fill=hex2rgb(accent) + (255,))
    r2 = R * (1 - ring_w); d.ellipse([c - r2, c - r2, c + r2, c + r2], fill=hex2rgb(disc) + (255,))
    sc = r2 * 0.86
    P = lambda pts: [(c + u * sc, c - v * sc) for u, v in pts]
    for prim in RT.BADGES[key]():
        if prim[0] == 'fan': d.polygon(P(prim[1]), fill=hex2rgb(sym) + (255,))
        else:
            d.polygon(P(prim[1]), fill=hex2rgb(sym) + (255,)); d.polygon(P(prim[2]), fill=hex2rgb(disc) + (255,))
    return im.resize((size, size), Image.LANCZOS)

if __name__ == '__main__':
    import sys
    sheet = Image.new('RGBA', (8 * 140, 150), (40, 44, 50, 255))
    for i, k in enumerate(RT.ORDER):
        r = RT.ROLES[k]; sheet.alpha_composite(badge_icon(r['badge'], r['accent'], 128), (i * 140 + 6, 11))
    sheet.save(sys.argv[1] if len(sys.argv) > 1 else '/tmp/badges.png')
