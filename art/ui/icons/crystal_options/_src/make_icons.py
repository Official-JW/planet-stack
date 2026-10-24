"""Planet Stack crystal (premium currency) icon options. No diamond / faceted gem shapes.
Renders SVG -> PNG 64/128/192, quantizes (Pillow libimagequant/octree) + oxipng."""
import io, os, cairosvg, oxipng
from PIL import Image
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GLOW = '''<radialGradient id="halo" cx="32" cy="32" r="30" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#3EE8FF" stop-opacity=".55"/><stop offset=".55" stop-color="#22CFFF" stop-opacity=".18"/>
 <stop offset="1" stop-color="#22CFFF" stop-opacity="0"/></radialGradient>'''

A = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64"><defs>{GLOW}
<linearGradient id="shell" x1="0" x2="1"><stop offset="0" stop-color="#C9D2DA"/><stop offset=".35" stop-color="#FFFFFF"/><stop offset="1" stop-color="#9AA6B1"/></linearGradient>
<linearGradient id="cap" x1="0" x2="1"><stop offset="0" stop-color="#2A3038"/><stop offset=".4" stop-color="#4A535E"/><stop offset="1" stop-color="#1B2026"/></linearGradient>
<linearGradient id="core" x1="0" x2="1"><stop offset="0" stop-color="#0FA9D8"/><stop offset=".5" stop-color="#C8FAFF"/><stop offset="1" stop-color="#0FA9D8"/></linearGradient></defs>
<circle cx="32" cy="33" r="30" fill="url(#halo)"/>
<g transform="translate(32 32) scale(1.1) rotate(15) translate(-32 -32)">
<rect x="27" y="4" width="10" height="6" rx="2" fill="url(#cap)"/>
<rect x="19" y="8" width="26" height="50" rx="9" fill="url(#cap)"/>
<rect x="21" y="15" width="22" height="36" rx="4" fill="url(#shell)"/>
<rect x="25" y="18.5" width="14" height="29" rx="4" fill="#0A3A4C"/>
<rect x="26.5" y="20" width="11" height="26" rx="3.2" fill="url(#core)"/>
<rect x="30" y="21.5" width="4" height="23" rx="2" fill="#FFFFFF" opacity=".9"/>
<path d="M25 27h14M25 33h14M25 39h14" stroke="#0A3A4C" stroke-width="1.4" opacity=".55"/>
<rect x="22.5" y="10.5" width="3" height="45" rx="1.5" fill="#FFFFFF" opacity=".18"/>
</g></svg>'''

B = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64"><defs>{GLOW}
<linearGradient id="sh" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#0E9CCB"/><stop offset=".6" stop-color="#5BEBFF"/><stop offset="1" stop-color="#E6FDFF"/></linearGradient>
<linearGradient id="sh2" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#0A7FAA"/><stop offset="1" stop-color="#7FF0FF"/></linearGradient>
<linearGradient id="rock" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5A636E"/><stop offset="1" stop-color="#1E242B"/></linearGradient></defs>
<circle cx="32" cy="30" r="30" fill="url(#halo)"/>
<g transform="translate(32 32) scale(1.08) translate(-32 -33)">
<path d="M14 49 L9.5 33 L12 31.5 L13.5 24 L16.5 27 L22 44 Z" fill="url(#sh2)"/>
<path d="M41 47 L46 30 L50.5 19.5 L53 22 L55 29.5 L50 47 Z" fill="url(#sh2)"/>
<path d="M20.5 50 L23 30 L26.5 18 L29.5 6 L32.5 9.5 L36 20 L38.5 31 L42 50 Z" fill="url(#sh)"/>
<path d="M28.6 12 L27.2 27 L28.8 44 L30.4 27 Z" fill="#FFFFFF" opacity=".75"/>
<path d="M49.6 25 L48 34 L48.6 40 L50.8 31 Z" fill="#FFFFFF" opacity=".5"/>
<path d="M13.6 30 L12.6 36 L15 42 L14.8 34 Z" fill="#FFFFFF" opacity=".45"/>
<path d="M6 52 Q9 46 16 46.5 L24 45 Q32 43.5 40 45.5 L49 45 Q57 45.5 58 52 Q56 57.5 46 58 L18 58 Q7 57.5 6 52 Z" fill="url(#rock)"/>
<path d="M12 49 Q20 47 30 48 Q42 47 52 49" stroke="#B9C3CC" stroke-width="1.4" fill="none" opacity=".55" stroke-linecap="round"/>
</g></svg>'''

C = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64"><defs>{GLOW}
<linearGradient id="rim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".5" stop-color="#D5DCE3"/><stop offset="1" stop-color="#8C98A4"/></linearGradient>
<radialGradient id="face" cx="32" cy="28" r="22" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#3B444F"/><stop offset="1" stop-color="#161B21"/></radialGradient>
<radialGradient id="orb" cx="29.5" cy="29.5" r="10" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".35" stop-color="#9FF6FF"/><stop offset="1" stop-color="#10A8D8"/></radialGradient></defs>
<circle cx="32" cy="32" r="31" fill="url(#halo)"/>
<circle cx="32" cy="32" r="28" fill="url(#rim)"/>
<circle cx="32" cy="32" r="22" fill="url(#face)"/>
<g stroke="#2A3038" stroke-width="2.4" stroke-linecap="round">
<path d="M32 7v4M32 53v4M7 32h4M53 32h4"/></g>
<circle cx="32" cy="32" r="16.5" fill="none" stroke="#2BD8FF" stroke-width="1.6" opacity=".7"/>
<ellipse cx="32" cy="32" rx="17" ry="6.5" fill="none" stroke="#7FF0FF" stroke-width="2" transform="rotate(-28 32 32)"/>
<circle cx="32" cy="32" r="13" fill="#22CFFF" opacity=".22"/>
<circle cx="32" cy="32" r="9" fill="url(#orb)"/>
<circle cx="45.6" cy="24.3" r="2.2" fill="#E6FDFF"/>
</svg>'''

ICONS = {"A_energy_cell": A, "B_shard_cluster": B, "C_core_token": C}

def png(svg, size, colors=96):
    raw = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    q = im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    b = io.BytesIO(); q.save(b, "PNG", optimize=True)
    return oxipng.optimize_from_memory(b.getvalue(), level=6, strip=oxipng.StripChunks.safe())

if __name__ == "__main__":
    for name, svg in ICONS.items():
        open(f"{OUT}/crystal_{name}.svg", "w").write(svg)
        for size, suf in ((64, ""), (128, "@2x"), (192, "@3x")):
            d = png(svg, size, {64: 96, 128: 64, 192: 48}[size])
            p = f"{OUT}/crystal_{name}{suf}.png"; open(p, "wb").write(d)
            print(os.path.basename(p), len(d))
