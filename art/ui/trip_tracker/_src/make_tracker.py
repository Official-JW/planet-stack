#!/usr/bin/env python3
"""Planet Stack - ship trip tracker stills + 3x parts. Run from repo root:
   python3 art/ui/trip_tracker/_src/make_tracker.py
Backgrounds are read from git (commit 8f2191c launch pad proofs, shipyard portrait)."""
import io, math, subprocess, json
import cairosvg
from PIL import Image

OUT = 'art/ui/trip_tracker'
BG = {
 'pad375': ('8f2191c', 'art/3d/buildings/launch_pad/proofs/launch_pad_phone_375x667.png'),
 'pad393': ('8f2191c', 'art/3d/buildings/launch_pad/proofs/launch_pad_phone_393x852.png'),
 'yard375': ('HEAD', 'art/3d/buildings/shipyard/shipyard_portrait_375x667.png'),
 # ship away: same game camera, ship + fuel hoses hidden (render_empty_pad.py, launch_pad_master.blend)
 'empty375': (None, f'{OUT}/_src/bg_pad_ship_away_375x667.png'),
 'empty393': (None, f'{OUT}/_src/bg_pad_ship_away_393x852.png'),
}
def bg(key):
    rev, p = BG[key]
    if rev is None: return Image.open(p).convert('RGBA')
    data = subprocess.check_output(['git', 'show', f'{rev}:{p}'])
    return Image.open(io.BytesIO(data)).convert('RGBA')

# ---------------- palette ----------------
C = dict(panelA='#13213a', panelB='#0a1324', hair1='#3ad0ff', hair2='#c9d3e6',
         text='#eafcff', sub='#c9d3e6', cyan='#7ff3ff', dotOff='#5f7189',
         out='#7ff3ff', earth='#6fe08a', ret='#ffc861', gold='#ffd84d',
         steel1='#ffffff', steel2='#c9d0d8', steel3='#8e98a4', stripe='#2f6fd6',
         ink='#16202e')
PH = {'OUTBOUND': C['out'], 'AT EARTH': C['earth'], 'RETURNING': C['ret']}
FONT = "Barlow Condensed"   # stand-in for system-ui 800 condensed (SF Pro Condensed) used by the HUD

# ---------------- geometry (pt) ----------------
SAFE = {375: 20, 393: 59}          # status bar 20 (iPhone SE/8), notch/island 59 (iPhone 15/16)
BAND = {375: (144, 383), 393: (165, 534)}
HUD_T, HUD_H, GAP = 26, 56, 3       # qa3d/index.html: #hud top = safe-top + 26, height 56
X0, W = 8, 0                        # strip x = 8 .. (screenW - 64): same columns as the HUD
STD = dict(h=22, cap=10, capgap=2)  # standard: strip 22 + 2 gap + caption 10 = 34 pt block
THIN = dict(h=16)                   # thin: caption moves inside the strip
CHIP_H = 18

def hud_bottom(w): return SAFE[w] + HUD_T + HUD_H
def block_top(w): return hud_bottom(w) + GAP

def defs():
    return f'''<defs>
 <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{C['panelA']}" stop-opacity=".94"/><stop offset="1" stop-color="{C['panelB']}" stop-opacity=".94"/></linearGradient>
 <linearGradient id="hair" x1="0" y1="0" x2="1" y2=".25"><stop offset="0" stop-color="{C['hair1']}" stop-opacity=".85"/><stop offset=".45" stop-color="{C['hair2']}" stop-opacity=".6"/><stop offset="1" stop-color="#8794ad" stop-opacity=".35"/></linearGradient>
 <linearGradient id="hairOn" x1="0" y1="0" x2="1" y2=".25"><stop offset="0" stop-color="#7ff3ff"/><stop offset="1" stop-color="#3ad0ff" stop-opacity=".8"/></linearGradient>
 <linearGradient id="steel" x1="0" y1="-1" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="{C['steel1']}"/><stop offset=".55" stop-color="{C['steel2']}"/><stop offset="1" stop-color="{C['steel3']}"/></linearGradient>
 <radialGradient id="flame" cx=".85" cy=".5" r=".85"><stop offset="0" stop-color="#fff6d6"/><stop offset=".35" stop-color="#ffc861"/><stop offset=".7" stop-color="#ff7a2f" stop-opacity=".7"/><stop offset="1" stop-color="#ff5a1f" stop-opacity="0"/></radialGradient>
 <radialGradient id="moon" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#f4f6f9"/><stop offset=".6" stop-color="#c3c9d1"/><stop offset="1" stop-color="#8d96a2"/></radialGradient>
 <radialGradient id="earth" cx=".35" cy=".3" r=".85"><stop offset="0" stop-color="#7cc4ff"/><stop offset=".55" stop-color="#2f86ea"/><stop offset="1" stop-color="#1a4fb0"/></radialGradient>
 <radialGradient id="atmo" cx=".5" cy=".5" r=".5"><stop offset=".7" stop-color="#7fd4ff" stop-opacity=".45"/><stop offset="1" stop-color="#7fd4ff" stop-opacity="0"/></radialGradient>
 <radialGradient id="flash" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffffff" stop-opacity=".95"/><stop offset=".45" stop-color="#bff8ff" stop-opacity=".6"/><stop offset="1" stop-color="#7ff3ff" stop-opacity="0"/></radialGradient>
 <radialGradient id="eglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffd27a" stop-opacity=".9"/><stop offset="1" stop-color="#ff8a3d" stop-opacity="0"/></radialGradient>
</defs>'''

def chamfer(x, y, w, h, c):
    return f'M{x+c},{y} H{x+w} V{y+h-c} L{x+w-c},{y+h} H{x} V{y+c} Z'

def panel(x, y, w, h, c=6, on=False):
    hair = 'url(#hairOn)' if on else 'url(#hair)'
    return (f'<path d="{chamfer(x,y,w,h,c)}" fill="{hair}"/>'
            f'<path d="{chamfer(x+1,y+1,w-2,h-2,c-0.6)}" fill="url(#panel)"/>')

def moon(cx, cy, r):
    k = r / 8
    return (f'<g transform="translate({cx},{cy}) scale({k})">'
            f'<circle r="8" fill="url(#moon)" stroke="{C["ink"]}" stroke-width=".7"/>'
            '<circle cx="-2.6" cy="-1.8" r="1.9" fill="#a3abb6"/><circle cx="2.8" cy="2.2" r="1.4" fill="#a3abb6"/>'
            '<circle cx="2.2" cy="-3.6" r=".9" fill="#a3abb6"/><circle cx="-1.6" cy="3.9" r=".8" fill="#a3abb6"/></g>')

def earth(cx, cy, r):
    k = r / 9
    return (f'<g transform="translate({cx},{cy}) scale({k})">'
            '<circle r="12" fill="url(#atmo)"/>'
            f'<circle r="9" fill="url(#earth)" stroke="{C["ink"]}" stroke-width=".7"/>'
            '<path d="M-6.5,-3.5 C-4.5,-6.5 -1,-6 0,-4 C1,-2.2 -1.8,-1 -2.8,0.6 C-3.8,2.4 -6.4,1.4 -7,-0.6 Z" fill="#5fd07a"/>'
            '<path d="M2.2,1 C4.4,-0.4 6.8,0.8 6.6,3 C6.4,5.2 3.6,6.6 2,5.4 C0.8,4.4 0.8,2 2.2,1 Z" fill="#5fd07a"/>'
            '<path d="M2.4,-6.6 C4,-6.4 5.4,-5 5,-3.8 C4.2,-3.6 2.8,-4.6 2.4,-6.6 Z" fill="#5fd07a"/>'
            '<path d="M-5,-6 C-1,-8.6 4,-8.4 6.4,-5.6" fill="none" stroke="#ffffff" stroke-opacity=".55" stroke-width="1" stroke-linecap="round"/></g>')

def ship(cx, cy, ang, L=14, glow=True, flame=1.0):
    """starter-ship icon, nose along +x before rotation; L = body length in pt"""
    k = L / 14
    g = ''
    if glow:
        g = (f'<ellipse cx="{-7-3.6*flame}" cy="0" rx="{4.4*flame}" ry="2.2" fill="url(#flame)"/>'
             f'<circle cx="-7" cy="0" r="3.4" fill="url(#eglow)" opacity=".8"/>')
    body = ('<path d="M-3.6,-2.3 L-6.4,-4.1 L-6.6,-2.1 Z M-3.6,2.3 L-6.4,4.1 L-6.6,2.1 Z" fill="#8e98a4" stroke="#16202e" stroke-width=".55" stroke-linejoin="round"/>'
            '<rect x="-7.4" y="-1.5" width="1.2" height="3" rx=".3" fill="#4d5764"/>'
            '<path id="sb" d="M-6.4,-2.4 L2.6,-2.4 Q6.6,-1.4 7.4,0 Q6.6,1.4 2.6,2.4 L-6.4,2.4 Z" fill="url(#steel)"/>'
            '<clipPath id="sbc"><path d="M-6.4,-2.4 L2.6,-2.4 Q6.6,-1.4 7.4,0 Q6.6,1.4 2.6,2.4 L-6.4,2.4 Z"/></clipPath>'
            '<rect x="1.0" y="-3" width="1.5" height="6" fill="#2f6fd6" clip-path="url(#sbc)"/>'
            '<rect x="-6.4" y="-2.4" width="13.8" height="1.1" fill="#ffffff" opacity=".45" clip-path="url(#sbc)"/>'
            '<path d="M-6.4,-2.4 L2.6,-2.4 Q6.6,-1.4 7.4,0 Q6.6,1.4 2.6,2.4 L-6.4,2.4 Z" fill="none" stroke="#16202e" stroke-width=".6" stroke-linejoin="round"/>')
    return f'<g transform="translate({cx},{cy}) rotate({ang}) scale({k})">{g}{body}</g>'

def qbez(p0, p1, p2, t):
    a = (1-t)**2; b = 2*(1-t)*t; c = t*t
    x = a*p0[0] + b*p1[0] + c*p2[0]; y = a*p0[1] + b*p1[1] + c*p2[1]
    dx = 2*(1-t)*(p1[0]-p0[0]) + 2*t*(p2[0]-p1[0]); dy = 2*(1-t)*(p1[1]-p0[1]) + 2*t*(p2[1]-p1[1])
    return x, y, math.degrees(math.atan2(dy, dx))

def dots(p0, p1, p2, u, n, r, split=True, lit='moon'):
    """lit = the part of the path BEHIND the ship: 'moon' (OUTBOUND: Moon..ship), 'earth' (RETURNING: Earth..ship), 'all' (AT EARTH)"""
    s = ''
    for i in range(n + 1):
        t = i / n
        x, y, _ = qbez(p0, p1, p2, t)
        on = split and (lit == 'all' or (lit == 'moon' and t <= u + 1e-9) or (lit == 'earth' and t >= u - 1e-9))
        col = C['cyan'] if on else C['dotOff']
        op = '1' if on else '.8'
        s += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{col}" opacity="{op}"/>'
    return s

def ease_io_sine(x): return (1 - math.cos(math.pi * x)) / 2

# Lv1 (Game Coder): lift-off -> touchdown 616 s (8 s climb + 600 s away + 8 s landing); 45 / 10 / 45 %
TOTAL, T_EARTH, T_RET = 616.0, 277.2, 338.8
def phase_at(t):
    if t < T_EARTH: return 'OUTBOUND', T_EARTH - t, ease_io_sine(t / T_EARTH)
    if t < T_RET: return 'AT EARTH', T_RET - t, 1.0
    return 'RETURNING', TOTAL - t, 1 - ease_io_sine((t - T_RET) / (TOTAL - T_RET))

def mmss(s):
    s = int(math.ceil(s)); return f'{s//60}:{s%60:02d}'

from PIL import ImageFont
_BF = '/usr/share/fonts/truetype/sand-box/google/Barlow Condensed/BarlowCondensed-Bold.ttf'
def tw(s, size, ls):
    f = ImageFont.truetype(_BF, 100)
    return (f.getlength(s) / 100) * size + ls * size * len(s)
def rich(x, y, parts, size, anchor='start', ls=.06):
    """parts = [(text, colour), ...]; laid out manually"""
    total = sum(tw(t, size, ls) for t, _ in parts)
    cx = x - total if anchor == 'end' else x
    out = ''
    for t, col in parts:
        out += txt(cx, y, t.replace(' ', '&#160;'), size, col, ls=ls)
        cx += tw(t, size, ls)
    return out
def txt(x, y, s, size, col, anchor='start', ls=.12, weight=700):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-weight="{weight}" font-size="{size}" '
            f'letter-spacing="{ls*size:.2f}" fill="{col}" text-anchor="{anchor}">{s}</text>')

# Strip-local layouts. Origin = strip top-left. Width 303 pt at both sizes (x 8 .. 311 at 375; 8 .. 329 would be 321 at 393 - kept 303 + right-aligned chip column logic: width = screenW - 72).
RZ = 116   # right zone (divider at W - RZ); text box = W-RZ+1 .. W-6 = 109 pt
RZ_AVAIL = RZ - 7
RZ_SIZE, RZ_LS = 11, .02   # Director: 11 pt minimum everywhere
LBL_SIZE, LBL_LS = 11, .08
CHIP_W = 122
def hms(s):
    s = int(math.ceil(s)); return f'{s//3600}:{s%3600//60:02d}:{s%60:02d}' if s >= 3600 else mmss(s)
def tapped_parts(secs, clock):
    """Director's rule: <1 h normal form; >=1 h short form; if short form > 109 pt drop the clock."""
    if secs < 3600:
        return 'normal', [('Back at ', C['sub']), (clock, C['text']), (f' · in {hms(secs)}', C['sub'])]
    pr = [('Back ', C['sub']), (clock, C['text']), (f' · {hms(secs)}', C['sub'])]
    if sum(tw(t, RZ_SIZE, RZ_LS) for t, _ in pr) <= RZ_AVAIL:
        return 'short', pr
    return 'fallback', [('Back in ', C['sub']), (hms(secs), C['text'])]
def parts_w(pr): return sum(tw(t, RZ_SIZE, RZ_LS) for t, _ in pr)
def strip_thin(w, t, tapped=False, rz_parts=None):
    W = w - 72; h = THIN['h']
    name, left, u = phase_at(t); col = PH[name]
    s = panel(0, 0, W, h, 5, on=tapped)
    s += f'<circle cx="9" cy="{h/2}" r="2.5" fill="{col}"/>'
    if name == 'AT EARTH':
        s += f'<circle cx="9" cy="{h/2}" r="4.5" fill="none" stroke="{col}" stroke-opacity=".45" stroke-width="1"/>'
    s += txt(15, h/2 + 3.8, name, LBL_SIZE, col, ls=LBL_LS)
    lw = tw(name, LBL_SIZE, LBL_LS)
    s += txt(15 + lw + 3, h/2 + 3.8, mmss(left), LBL_SIZE, C['text'], ls=.02)
    mx, ex, cy = 104, W - RZ - 10, h/2 + 1
    p0, p1, p2 = (mx + 7, cy), ((mx + ex)/2, cy - 8), (ex - 7, cy)
    lit = {'OUTBOUND': 'moon', 'AT EARTH': 'all', 'RETURNING': 'earth'}[name]
    s += dots(p0, p1, p2, u, 14, .7, lit=lit)
    s += moon(mx, cy, 5.5) + earth(ex, cy, 6)
    if name == 'AT EARTH':
        s += f'<circle cx="{ex-11}" cy="{cy-3}" r="5.5" fill="none" stroke="{C["earth"]}" stroke-opacity=".55" stroke-width="1"/>'
        s += ship(ex - 11, cy - 3, 0, 10, glow=False)
    else:
        x, y, a = qbez(p0, p1, p2, u)
        s += ship(x, y, a + (180 if name == 'RETURNING' else 0), 10.5)
    s += f'<rect x="{W-RZ}" y="3" width="1" height="{h-6}" fill="#c9d3e6" opacity=".25"/>'
    if rz_parts is None:
        rz_parts = tapped_parts(TOTAL - t, '2:47 PM')[1] if tapped else [('Back in ', C['sub']), (hms(TOTAL - t), C['text'])]
    s += rich(W - 6, h/2 + 3.8, rz_parts, RZ_SIZE, anchor='end', ls=RZ_LS)
    return s, W, h, dict(path=[p0, p1, p2], moon=(mx, cy, 5.5), earth=(ex, cy, 6), u=u, lit=lit), name

def chip(t):
    h = CHIP_H; w = CHIP_W
    s = panel(0, 0, w, h, 5)
    s += ship(13, h/2, -90 + 90, 10)  # pointing right = travelling
    s += rich(24, h/2 + 3.8, [('Ship back in ', C['sub']), (hms(TOTAL - t), C['text'])], 11, ls=.02)
    s += f'<path d="M{w-11},{h/2-3.5} l3.5,3.5 l-3.5,3.5" fill="none" stroke="{C["cyan"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    return s, w, h

# ---------------- mock HUD & status bar ----------------
def status(w):
    st = SAFE[w]
    s = f'<rect x="0" y="0" width="{w}" height="{st}" fill="#000" opacity=".55"/>'
    s += f'<text x="{24 if w==375 else 36}" y="{14 if w==375 else 33}" font-family="Inter" font-weight="600" font-size="{12 if w==375 else 16}" fill="#fff">9:41</text>'
    if w == 393:
        s += '<rect x="134" y="11" width="125" height="37" rx="18.5" fill="#000"/>'
    bx = w - (34 if w == 375 else 46); by = 5 if w == 375 else 24
    s += f'<rect x="{bx}" y="{by}" width="22" height="11" rx="3" fill="none" stroke="#fff" stroke-opacity=".6"/><rect x="{bx+2}" y="{by+2}" width="16" height="7" rx="1.5" fill="#fff"/>'
    return s

def hud(w, money='$1,860'):
    st = SAFE[w]; y = st + HUD_T; r = w - 64; cw = (r - 8 - 6)
    c1 = cw / 2.3; c2 = cw - c1
    s = panel(8, y, c1, HUD_H, 10) + panel(8 + c1 + 6, y, c2, HUD_H, 10)
    s += f'<circle cx="26" cy="{y+16}" r="7" fill="none" stroke="#7ff3ff" stroke-width="1.6"/><text x="26" y="{y+19.5}" font-family="Inter" font-weight="800" font-size="9" fill="#7ff3ff" text-anchor="middle">$</text>'
    s += txt(38, y + 19.5, 'MONEY', 9, C['sub'], ls=.18)
    s += f'<text x="18" y="{y+44}" font-family="Inter" font-weight="800" font-size="17" fill="#eafcff">{money}</text>'
    x2 = 8 + c1 + 6 + 10
    s += f'<path d="M{x2+2},{y+22} l5,-9 l6,4 l5,-6" fill="none" stroke="#7ff3ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
    s += f'<text x="{x2+26}" y="{y+23}" font-family="Inter" font-weight="800" font-size="20" fill="#7ff3ff">11</text>'
    s += txt(x2 + 52, y + 21, 'ORE/MIN', 9, C['sub'], ls=.06)
    s += f'<rect x="{x2}" y="{y+36}" width="{c2-20}" height="4" fill="#ffffff" fill-opacity=".07"/><rect x="{x2}" y="{y+36}" width="{(c2-20)*.62}" height="4" fill="#3ad0ff"/>'
    # Eve bubble placeholder (gear omitted: Coder is moving it out of the band)
    s += f'<circle cx="{w-8-24}" cy="{st+30+24}" r="24" fill="#1b2a40" stroke="#3ad0ff" stroke-width="2"/>'
    s += f'<image href="file://{EVE}" x="{w-8-46}" y="{st+32}" width="44" height="44" clip-path="circle(22px)"/>' if EVE else ''
    return s
import os
EVE = os.path.abspath('art/ui/earth_coms/eve_avatar_2x.png')

def svg_doc(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{defs()}{body}</svg>'

def render(svg, scale=1):
    png = cairosvg.svg2png(bytestring=svg.encode(), scale=scale, unsafe=True)
    return Image.open(io.BytesIO(png)).convert('RGBA')

def compose(bgkey, w, h, body, path):
    base = bg(bgkey)
    ov = render(svg_doc(w, h, body))
    base.alpha_composite(ov)
    base.convert('RGB').quantize(256, dither=Image.Dither.FLOYDSTEINBERG).save(path, optimize=True)
    return path

def measure_line(w, y, label, col, x1=None, x2=None, side='left'):
    x1 = 0 if x1 is None else x1; x2 = w if x2 is None else x2
    return (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{col}" stroke-width="1" stroke-dasharray="4 2"/>' +
            (f'<text x="{(x2-3) if side=="right" else (x1+3)}" y="{y-2.5}" font-family="DejaVu Sans" font-size="8" fill="{col}" text-anchor="{"end" if side=="right" else "start"}">{label}</text>' if label else ''))

def band_overlay(w):
    t, b = BAND[w]
    return (f'<rect x="12" y="{t}" width="{w-24}" height="{b-t}" fill="none" stroke="#ffd84d" stroke-width="1"/>' +
            measure_line(w, t, '', '#ff5a6a') +
            f'<text x="15" y="{t+9}" font-family="DejaVu Sans" font-size="8" fill="#ff5a6a">framing band top y {t}</text>')

results = {}
from PIL import ImageDraw
def inset(path, y0, y1, marks, at, x0=0, x1=125, k=2):
    """2x magnified crop of the strip area with exact y lines, pasted into the empty ground area"""
    im = Image.open(path).convert('RGB')
    crop = im.crop((x0, y0, x1, y1)).resize(((x1-x0)*k, (y1-y0)*k), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 8)
    ly = []
    for y, lab, col in marks:
        yy = (y - y0) * k
        d.line([(0, yy), (crop.width, yy)], fill=col, width=1)
    im2 = Image.new('RGB', (im.width, crop.height + 34), (8, 10, 16))
    im2.paste(crop, (4, 22))
    d2 = ImageDraw.Draw(im2)
    d2.text((6, 4), f'2x zoom, screen y {y0}-{y1}, x {x0}-{x1}', fill=(200, 210, 225), font=f)
    last = -99
    for y, lab, col in sorted(marks):
        yy = 22 + (y - y0) * k
        ty = max(yy - 5, last + 10); last = ty
        d2.line([(4 + crop.width, yy), (crop.width + 12, ty + 5)], fill=col)
        d2.text((crop.width + 14, ty), lab, fill=col, font=f)
    d2.rectangle([0, 0, im2.width - 1, im2.height - 1], outline=(90, 100, 120))
    im.paste(im2, (0, at))
    im.quantize(256, dither=Image.Dither.FLOYDSTEINBERG).save(path, optimize=True)
FILES = []
def save(name): FILES.append(name); return f'{OUT}/proofs/{name}'

# ---------------- money pop (real payout, Inter 900 15 pt, gold with dark outline) ----------------
_IF = ImageFont.truetype('/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf', 100)
_IF.set_variation_by_axes([14, 900])
def pop_w(s, size=15):
    b = _IF.getbbox(s); return (b[2] - b[0]) / 100 * size
POP_SIZE, POP_CAP = 15, 15 * 0.727     # Inter cap height .727 em
def pop_place(w, ex, strip_top, s):
    """centred on Earth x, clamped inside the HUD columns (x 8 .. screenW-64) with 4 pt margin; baseline 2 pt above the strip"""
    pw = pop_w(s); lo, hi = 8 + 4, w - 64 - 4
    cx = min(max(ex, lo + pw / 2), hi - pw / 2)
    base = strip_top - 2
    return cx, base, (cx - pw / 2, base - POP_CAP, cx + pw / 2, base)
POP_UP, POP_DN = 13.8, 4.6          # ink incl. 1.5 pt outline: baseline-13.8 .. baseline+4.6 (18.4 pt tall)
POP_C = (POP_UP - POP_DN) / 2        # ink centre sits 4.6 pt above the baseline
POP_HALF = (POP_UP + POP_DN) / 2     # 9.2
POP_OVER = 1.06
def money_cell(w):
    r = w - 64; cw = r - 8 - 6; c1 = cw / 2.3
    return (8, 8 + c1), (8 + c1 + 6, r)          # money x, ore x
def pop_route(w, ex):
    """keyframes (ms, cx, cy, scale, opacity); cy = ink centre"""
    st = block_top(w); sb = st + THIN['h']; band = BAND[w][0]; hb = hud_bottom(w)
    (m0, m1), _ = money_cell(w)
    under = sb + 2 + POP_HALF
    if under + POP_HALF * POP_OVER <= band - 1:
        route, cy = 'under', under
    else:
        route, cy = 'in-strip', st + THIN['h'] / 2
    mx = (m0 + m1) / 2
    K = dict(route=route, k0=(ex, cy), k_glide_end=(mx, cy), k_end=(mx, hb),
             ink_k0=(cy - POP_HALF, cy + POP_HALF), ink_k0_over=(cy - POP_HALF * POP_OVER, cy + POP_HALF * POP_OVER))
    return route, K
def ease_ioc(x): return 4*x**3 if x < .5 else 1 - (-2*x + 2)**3 / 2
def pop_state(K, ms):
    """centre, scale, opacity at time ms after +277.2"""
    (x0, y0), (x1, _), (_, y2) = K['k0'], K['k_glide_end'], K['k_end']
    if ms < 110:  f = 1 - (1 - ms/110)**3; return x0, y0, .6 + (POP_OVER - .6)*f, f
    if ms < 170:  f = (1 - math.cos(math.pi*(ms-110)/60))/2; return x0, y0, POP_OVER + (1 - POP_OVER)*f, 1
    if ms < 520:  return x0, y0, 1, 1
    if ms < 970:  f = ease_ioc((ms-520)/450); return x0 + (x1-x0)*f, y0, 1, 1
    f = min(1, (ms-970)/300)**3
    op = 1 if ms < 1150 else max(0, 1 - (ms-1150)/120)
    return x1, y0 + (y2-y0)*f, 1 - .45*f, op
def pop_c(cx, cy, s, sc=1, op=1):
    return f'<g opacity="{op}" transform="translate({cx},{cy}) scale({sc}) translate({-cx},{-cy})">{pop_svg(cx, cy + POP_C, s)}</g>'
def pop_svg(cx, base, s):
    return (f'<text x="{cx}" y="{base}" font-family="Inter" font-weight="900" font-size="{POP_SIZE}" fill="#3a2200" stroke="#3a2200" stroke-width="3" stroke-linejoin="round" text-anchor="middle">{s}</text>'
            f'<text x="{cx}" y="{base}" font-family="Inter" font-weight="900" font-size="{POP_SIZE}" fill="{C["gold"]}" text-anchor="middle">{s}</text>')

# ---------------- stills (thin strip = the only layout) ----------------
STILLS = [('outbound', 162.0), ('at_earth', 279.0), ('returning', 468.0), ('returning_tapped', 364.0)]
SIZES = {375: ('empty375', 667), 393: ('empty393', 852)}
for w, (key, H) in SIZES.items():
    bt = block_top(w); bandT = BAND[w][0]
    for nm, t in STILLS:
        tapped = nm.endswith('tapped')
        s, W, h, meta, name = strip_thin(w, t, tapped=tapped)
        body = status(w) + hud(w, '$41,860' if nm == 'outbound' else '$61,860') + f'<g transform="translate({X0},{bt})">{s}</g>'
        rec = dict(strip=(bt, bt + h), band_top=bandT, clearance=bandT - bt - h, hud_bottom=hud_bottom(w), phase=name,
                   t=t, back_in=mmss(TOTAL - t), u=round(meta['u'], 4), lit=meta['lit'])
        ex = X0 + meta['earth'][0]
        if nm == 'at_earth':
            route, K = pop_route(w, ex)
            cx, cy = K['k0']
            body += pop_c(cx, cy, '+$20,000')
            w2 = pop_w('+$20,000') + 3; w9 = pop_w('+$999,999') + 3      # ink incl. outline
            bb9 = (cx - w9/2, cy - POP_HALF, cx + w9/2, cy + POP_HALF)
            (_, _), (o0, o1) = money_cell(w)
            rec['pop_k0'] = dict(route=route, centre=(round(cx, 1), round(cy, 1)), ink_y=(round(cy - POP_HALF, 1), round(cy + POP_HALF, 1)),
                                 x_20000=(round(cx - w2/2, 1), round(cx + w2/2, 1)), x_999999=(round(bb9[0], 1), round(bb9[2], 1)),
                                 clear_ore_bottom=round(cy - POP_HALF - hud_bottom(w), 1), clear_band=round(bandT - cy - POP_HALF, 1),
                                 clear_right_of_hud_column=round((w - 64) - bb9[2], 1))
        if tapped:
            body += f'<circle cx="{X0+60}" cy="{bt+h/2}" r="12" fill="#ffffff" fill-opacity=".18" stroke="#ffffff" stroke-opacity=".6"/>'
        compose(key, w, H, body, save(f'pad_{nm}_{w}x{H}.png'))
        ov = body + band_overlay(w) + measure_line(w, hud_bottom(w), f'HUD bottom y {hud_bottom(w)}', '#9fb3c8', side='right')
        ov += f'<rect x="{X0-0.5}" y="{bt}" width="{W+1}" height="{h}" fill="none" stroke="#3aff9c"/>'
        ov += f'<text x="15" y="{bandT+19}" font-family="DejaVu Sans" font-size="8" fill="#3aff9c">strip y {bt}-{bt+h} · clears band by {bandT-bt-h} pt</text>'
        marks = [(hud_bottom(w), f'HUD bottom {hud_bottom(w)}', '#9fb3c8'), (bt, f'strip top {bt}', '#3aff9c'),
                 (bt + h, f'strip bottom {bt+h}', '#3aff9c'), (bandT, f'band top {bandT} (clear {bandT-bt-h} pt)', '#ff5a6a')]
        if nm == 'at_earth':
            ov += f'<rect x="{bb9[0]:.1f}" y="{bb9[1]:.1f}" width="{bb9[2]-bb9[0]:.1f}" height="{bb9[3]-bb9[1]:.1f}" fill="none" stroke="#ff9a4a" stroke-dasharray="2 1"/>'
            ov += f'<line x1="{w-64}" y1="{SAFE[w]+HUD_T}" x2="{w-64}" y2="{bandT}" stroke="#ff9a4a" stroke-dasharray="2 2"/>'
            ov += (f'<text x="15" y="{bandT+30}" font-family="DejaVu Sans" font-size="8" fill="#ff9a4a">dashed = widest pop "+$999,999" ink {bb9[2]-bb9[0]:.1f} pt, x {bb9[0]:.0f}-{bb9[2]:.0f}; HUD column edge x {w-64}</text>')
            ov += (f'<text x="15" y="{bandT+41}" font-family="DejaVu Sans" font-size="8" fill="#ff9a4a">pop start ({route}) ink y {bb9[1]:.1f}-{bb9[3]:.1f} · ore bottom {hud_bottom(w)} · band {bandT}</text>')
            marks.append((bb9[1], f'pop top {bb9[1]:.1f}', '#ff9a4a')); marks.append((bb9[3], f'pop bottom {bb9[3]:.1f}', '#ff9a4a'))
        compose(key, w, H, ov, save(f'pad_{nm}_{w}x{H}_overlay.png'))
        y0 = hud_bottom(w) - 18; y1 = bandT + 6
        inset(f'{OUT}/proofs/pad_{nm}_{w}x{H}_overlay.png', y0, y1, marks, 430 if w == 375 else 600, x0=95, x1=220)
        results[f'{nm}_{w}'] = rec

# ---------------- money pop path (375: under the strip; 393: in-strip fallback) ----------------
pop_path = {}
for w, (key, H) in SIZES.items():
    bt = block_top(w); bandT = BAND[w][0]; hb = hud_bottom(w)
    s, W, h, meta, name = strip_thin(w, 277.9)
    ex = X0 + meta['earth'][0]
    route, K = pop_route(w, ex)
    MID = 745                                         # mid-glide
    cx, cy, sc, op = pop_state(K, MID)
    body = status(w) + hud(w, '$41,860') + f'<g transform="translate({X0},{bt})">{s}</g>' + pop_c(cx, cy, '+$20,000', sc, op)
    tag = f'pad_at_earth_pop_path_{w}x{H}'
    compose(key, w, H, body, save(tag + '.png'))
    (m0, m1), (o0, o1) = money_cell(w)
    ov = body + band_overlay(w)
    ov += f'<rect x="{o0}" y="{SAFE[w]+HUD_T}" width="{o1-o0}" height="{HUD_H}" fill="#ff5a6a" fill-opacity=".12" stroke="#ff5a6a" stroke-dasharray="3 2"/>'
    ov += f'<text x="{o0+4}" y="{SAFE[w]+HUD_T-3}" font-family="DejaVu Sans" font-size="7" fill="#ff5a6a">ore panel x {o0:.1f}-{o1}, bottom y {hb} (keep out)</text>'
    # sweep of the widest pop's ink along the path
    pts = []; boxes = ''
    for ms in range(0, 1271, 10):
        x, y, sc_, o_ = pop_state(K, ms); pts.append((x, y))
        hw = (pop_w('+$999,999') + 3) / 2 * sc_; hh = POP_HALF * sc_
        pop_path.setdefault(w, dict(max_ink_bottom=0, min_clear_ore=1e9, route=route))
        pp = pop_path[w]
        pp['max_ink_bottom'] = max(pp['max_ink_bottom'], y + hh)
        if x + hw > o0 and x - hw < o1: pp['min_clear_ore'] = min(pp['min_clear_ore'], y - hh - hb)
        pp['max_right'] = max(pp.get('max_right', 0), x + hw)
    ov += '<polyline points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts) + '" fill="none" stroke="#ffd84d" stroke-width="1.2" stroke-dasharray="3 2"/>'
    labs = [('K0 0-520 ms pop at Earth', K['k0']), ('K1 970 ms glide end', K['k_glide_end']), ('K2 1270 ms into Money', K['k_end'])]
    for i, (lab, (x, y)) in enumerate(labs):
        ov += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="#ffd84d" stroke="#000" stroke-width=".6"/>'
    hw = (pop_w('+$999,999') + 3) / 2
    for (x, y) in (K['k0'], K['k_glide_end']):
        ov += f'<rect x="{x-hw:.1f}" y="{y-POP_HALF:.1f}" width="{2*hw:.1f}" height="{2*POP_HALF:.1f}" fill="none" stroke="#ff9a4a" stroke-width=".7" stroke-dasharray="2 1"/>'
    ov += f'<line x1="{m0}" y1="{hb}" x2="{m1:.1f}" y2="{hb}" stroke="#3aff9c" stroke-width="1.5"/>'
    pp = pop_path[w]
    lines = [f'money pop path ({route}); yellow dashes = centre path, orange = widest "+$999,999" ink at K0 / K1',
             f'K0 ({K["k0"][0]:.1f}, {K["k0"][1]:.1f}) -> K1 ({K["k_glide_end"][0]:.1f}, {K["k_glide_end"][1]:.1f}) -> K2 ({K["k_end"][0]:.1f}, {K["k_end"][1]:.1f}) = Money cell bottom',
             f'ink max bottom y {pp["max_ink_bottom"]:.1f} vs band {bandT} (clear {bandT-pp["max_ink_bottom"]:.1f})',
             (f'under ore x-range: ink top >= {hb + pp["min_clear_ore"]:.1f} (ore bottom {hb}, clear {pp["min_clear_ore"]:.1f})' if pp['min_clear_ore'] < 1e8 else 'never inside ore x-range'),
             f'still = {MID} ms (mid-glide): centre ({cx:.1f}, {cy:.1f})']
    for i, l in enumerate(lines):
        ov += f'<text x="10" y="{bandT+28+10*i}" font-family="DejaVu Sans" font-size="6.8" fill="#ffd84d">{l}</text>'
    compose(key, w, H, ov, save(tag + '_overlay.png'))
    marks = [(hb, f'HUD/ore bottom {hb}', '#ff5a6a'), (bt, f'strip top {bt}', '#3aff9c'), (bt + h, f'strip bottom {bt+h}', '#3aff9c'),
             (bandT, f'band top {bandT}', '#ff5a6a'), (K['k0'][1] - POP_HALF, f'pop ink top {K["k0"][1]-POP_HALF:.1f}', '#ff9a4a'),
             (K['k0'][1] + POP_HALF, f'pop ink bottom {K["k0"][1]+POP_HALF:.1f}', '#ff9a4a')]
    inset(f'{OUT}/proofs/{tag}_overlay.png', hb - 16, bandT + 6, marks, 430 if w == 375 else 600, x0=0, x1=118 if w == 375 else 160)
    pop_path[w].update(k0=K['k0'], k1=K['k_glide_end'], k2=K['k_end'], still_ms=MID, still_centre=(round(cx, 1), round(cy, 1)),
                       ink_k0=K['ink_k0'], ink_k0_overshoot=K['ink_k0_over'], band_top=bandT, ore_x=(round(o0, 1), o1), money_x=(m0, round(m1, 1)), ore_bottom=hb)

# chip on the Shipyard (375) + overlay
w = 375; bt = block_top(w)
cs, cw, ch = chip(364.0)
body = status(w) + hud(w, '$61,860') + f'<g transform="translate({X0},{bt})">{cs}</g>'
compose('yard375', w, 667, body, save('chip_shipyard_375x667.png'))
ov = body + band_overlay(w) + measure_line(w, hud_bottom(w), f'HUD bottom y {hud_bottom(w)}', '#9fb3c8', side='right')
ov += f'<rect x="{X0-0.5}" y="{bt}" width="{cw+1}" height="{ch}" fill="none" stroke="#3aff9c"/>'
ov += f'<text x="{X0+cw+6}" y="{bt+12}" font-family="DejaVu Sans" font-size="8" fill="#3aff9c">chip y {bt}-{bt+ch} · clears band by {BAND[w][0]-bt-ch} pt</text>'
compose('yard375', w, 667, ov, save('chip_shipyard_375x667_overlay.png'))
inset(f'{OUT}/proofs/chip_shipyard_375x667_overlay.png', 84, 150, [(hud_bottom(w), 'HUD bottom 102', '#9fb3c8'), (bt, f'chip top {bt}', '#3aff9c'), (bt+ch, f'chip bottom {bt+ch}', '#3aff9c'), (144, f'band top 144 (clear {144-bt-ch} pt)', '#ff5a6a')], 440)
results['chip_375'] = dict(chip=(bt, bt + ch), band_top=144, clearance=144 - bt - ch)
results['chip_393'] = dict(chip=(block_top(393), block_top(393) + ch), band_top=165, clearance=165 - block_top(393) - ch)

# ---------------- 3x zoom sheet ----------------
rows = []
for nm, t in STILLS:
    s, W, h, meta, name = strip_thin(375, t, tapped=nm.endswith('tapped'))
    extra = ''
    if nm == 'at_earth':
        extra = pop_c(meta['earth'][0], 16 + 2 + POP_HALF, '+$20,000')
    rows.append((s + extra, W, 18 + (22 if nm == 'at_earth' else 0), nm, 0))
cs, cw, ch = chip(364.0); rows.append((cs, cw, 20, 'chip', 0))
y = 10; body = f'<rect width="330" height="{sum(r[2]+22 for r in rows)+10}" fill="#05070c"/>'
for s, Wd, hh, nm, off in rows:
    body += f'<text x="10" y="{y+7}" font-family="DejaVu Sans" font-size="7" fill="#7f8ea3">{nm}</text>'
    body += f'<g transform="translate(12,{y+12+off})">{s}</g>'; y += hh + 22
render(svg_doc(330, y + 10, body), 3).convert('RGB').quantize(256).save(save('strip_states_3x.png'), optimize=True)

# ---------------- tapped text forms, measured at 375 and 393 ----------------
FORMS = [('under 1 h (Lv1 worst case)', 616.0, '12:47 PM', 'forced', None),
         ('1 h or more', 3852.0, '12:47 PM', 'forced', None),
         ('fallback if short form too wide', 3852.0, '12:47 PM', 'fallback', None)]
text_forms = {}
rows = []
for w in SIZES:
    for label, secs, clock, mode, _ in FORMS:
        if label.startswith('under'):
            pr = tapped_parts(secs, clock)[1]; form = 'normal'
        elif mode == 'fallback':
            pr = [('Back in ', C['sub']), (hms(secs), C['text'])]; form = 'fallback'
        else:
            pr = [('Back ', C['sub']), (clock, C['text']), (f' · {hms(secs)}', C['sub'])]; form = 'short'
        s, W, h, meta, _ = strip_thin(w, 400.0, tapped=True, rz_parts=pr)
        tw_ = parts_w(pr)
        x0 = W - RZ + 1
        s += (f'<rect x="{x0}" y="-1.5" width="{RZ_AVAIL}" height="{h+3}" fill="none" stroke="#ff9f43" stroke-width=".4" stroke-dasharray="1.5 1"/>')
        txt_ = ''.join(t for t, _ in pr)
        text_forms[f'{form}_{w}'] = dict(text=txt_, size_pt=RZ_SIZE, tracking_em=RZ_LS, width_pt=round(tw_, 1), avail_pt=RZ_AVAIL,
                                         spare_pt=round(RZ_AVAIL - tw_, 1), fits=tw_ <= RZ_AVAIL, x=(round(W - 6 - tw_, 1), W - 6), strip_w=W)
        rows.append((s, W, f'{w} · {label}: "{txt_}" = {tw_:.1f} pt of {RZ_AVAIL} ({RZ_AVAIL - tw_:+.1f})'))
y = 10; SW = 345; body = ''
for s, Wd, lab in rows:
    body += f'<text x="10" y="{y+7}" font-family="DejaVu Sans" font-size="6.5" fill="#7f8ea3">{lab}</text>'
    body += f'<g transform="translate(12,{y+12})">{s}</g>'; y += 16 + 22
body = f'<rect width="{SW}" height="{y+10}" fill="#05070c"/>' + body
render(svg_doc(SW, y + 10, body), 3).convert('RGB').quantize(256).save(save('tapped_text_forms_3x.png'), optimize=True)

# ---------------- 3x parts ----------------
import glob
for f in glob.glob(f'{OUT}/parts/*.png'): os.remove(f)
def part(name, w, h, body):
    im = render(svg_doc(w, h, body), 3)
    im.save(f'{OUT}/parts/{name}@3x.png', optimize=True)
    return name, im.size, os.path.getsize(f'{OUT}/parts/{name}@3x.png')
P = []
P.append(part('moon_11pt', 11, 11, moon(5.5, 5.5, 5.5)))
P.append(part('earth_12pt', 18, 18, earth(9, 9, 6)))       # 12 pt disc + 3 pt glow each side
P.append(part('ship_icon_10_5pt', 12, 7, ship(6.3, 3.5, 0, 10.5, glow=False)))
P.append(part('ship_glow_flame', 9, 6, f'<g transform="translate(8.5,3) scale({10.5/14})"><ellipse cx="-3.6" cy="0" rx="4.4" ry="2.2" fill="url(#flame)"/><circle cx="0" cy="0" r="3.4" fill="url(#eglow)" opacity=".8"/></g>'))
P.append(part('pulse_ring_11pt', 12, 12, f'<circle cx="6" cy="6" r="5.5" fill="none" stroke="{C["earth"]}" stroke-width="1"/>'))
P.append(part('flash_landing_28pt', 28, 28, '<circle cx="14" cy="14" r="14" fill="url(#flash)"/>'))
s, W, h, meta, _ = strip_thin(375, 0)
p0, p1, p2 = meta['path']
P.append(part('path_dots_ref_303x16', W, h, dots(p0, p1, p2, 0, 14, .7, split=False)))
P.append(part('strip_bg_303x16', 303, 16, panel(0, 0, 303, 16, 5)))
P.append(part('strip_bg_tapped_303x16', 303, 16, panel(0, 0, 303, 16, 5, on=True)))
cs, cw, ch = chip(364.0)
P.append(part('chip_bg_122x18', 122, 18, panel(0, 0, 122, 18, 5)))
P.append(part('chip_full_example', 122, 18, cs))
P.append(part('money_pop_example_20000', 90, 20, pop_svg(45, 15, '+$20,000')))
geo = {}
for w in SIZES:
    _, W, h, m, _ = strip_thin(w, 0)
    geo[w] = dict(strip_w=W, path=m['path'], moon=m['moon'], earth=m['earth'], divider_x=W - RZ)
json.dump(dict(timing=dict(total_s=TOTAL, outbound=(0, T_EARTH), at_earth=(T_EARTH, T_RET), returning=(T_RET, TOTAL), sale_and_pop_at=T_EARTH),
               layout='thin strip only (16 pt)', strip_local=geo, pop=dict(font='Inter 900 15 pt', max_text='+$999,999', max_w_pt=round(pop_w('+$999,999'), 1),
               w_20000_pt=round(pop_w('+$20,000'), 1)), results=results, pop_path={str(k): {kk: (tuple(round(x, 2) for x in vv) if isinstance(vv, tuple) else (round(vv, 2) if isinstance(vv, float) else vv)) for kk, vv in v.items()} for k, v in pop_path.items()}, left_label=dict(size_pt=LBL_SIZE, tracking_em=LBL_LS), chip_w=CHIP_W, right_zone=dict(size_pt=RZ_SIZE, tracking_em=RZ_LS, avail_pt=RZ_AVAIL, forms=text_forms), parts=P), open(f'{OUT}/_src/measure.json', 'w'), indent=1)
print(json.dumps(results, indent=1)); print(P)
