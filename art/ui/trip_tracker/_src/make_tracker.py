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

def dots(p0, p1, p2, u, n, r, split=True):
    s = ''
    for i in range(n + 1):
        t = i / n
        x, y, _ = qbez(p0, p1, p2, t)
        col = C['cyan'] if (split and t <= u) else C['dotOff']
        op = '1' if (split and t <= u) else '.8'
        s += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{col}" opacity="{op}"/>'
    return s

def ease_io_sine(x): return (1 - math.cos(math.pi * x)) / 2

TOTAL = 600  # Lv1: 270 / 60 / 270 s  (45 / 10 / 45 %)
def phase_at(t):
    if t < 270: return 'OUTBOUND', 270 - t, ease_io_sine(t / 270)
    if t < 330: return 'AT EARTH', 330 - t, 1.0
    return 'RETURNING', 600 - t, 1 - ease_io_sine((t - 330) / 270)

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
def strip_std(w, t, tapped=False, money=None):
    W = w - 72; h = STD['h']
    name, left, u = phase_at(t)
    col = PH[name]
    s = panel(0, 0, W, h, 6, on=tapped)
    # label zone
    s += f'<circle cx="11" cy="{h/2}" r="3" fill="{col}"/>'
    if name == 'AT EARTH':
        s += f'<circle cx="11" cy="{h/2}" r="5.2" fill="none" stroke="{col}" stroke-opacity=".45" stroke-width="1"/>'
    s += txt(19, h/2 + 3.6, name, 10.5, col, ls=.14)
    lw = {'OUTBOUND': 50, 'AT EARTH': 48, 'RETURNING': 55}[name]
    s += txt(19 + lw + 5, h/2 + 3.8, mmss(left), 11.5, C['text'], ls=.02, weight=700)
    # track zone
    mx, ex, cy = 128, W - 13, h/2 + 2
    p0, p1, p2 = (mx + 9, cy), ((mx + ex)/2, cy - 13), (ex - 10, cy)
    s += dots(p0, p1, p2, u if name == 'OUTBOUND' else (1 if name == 'AT EARTH' else u), 26, .85, split=True)
    s += moon(mx, cy, 7.5)
    s += earth(ex, cy, 8)
    if name == 'AT EARTH':
        sx, sy = ex - 15, cy - 6
        s += f'<circle cx="{sx}" cy="{sy}" r="7.5" fill="none" stroke="{C["earth"]}" stroke-opacity=".55" stroke-width="1.2"/>'
        s += f'<circle cx="{ex}" cy="{cy}" r="11.5" fill="none" stroke="#ffffff" stroke-opacity=".35" stroke-width="1"/>'
        s += ship(sx, sy, 0, 12, glow=False)
    else:
        x, y, a = qbez(p0, p1, p2, u)
        if name == 'RETURNING': a += 180
        s += ship(x, y, a, 13, glow=True)
    meta = dict(path=[p0, p1, p2], moon=(mx, cy, 7.5), earth=(ex, cy, 8))
    return s, W, h, meta, name, left

def caption_std(W, t, tapped=False):
    back = TOTAL - t
    if tapped:
        return rich(W - 2, 9, [('Back at ', C['sub']), ('2:47 PM', C['text']), (f'  ·  in {mmss(back)}', C['sub'])], 10.5, anchor='end')
    return rich(W - 2, 9, [('Back in ', C['sub']), (mmss(back), C['text'])], 10.5, anchor='end')

def strip_thin(w, t):
    W = w - 72; h = THIN['h']
    name, left, u = phase_at(t); col = PH[name]
    s = panel(0, 0, W, h, 5)
    s += f'<circle cx="9" cy="{h/2}" r="2.5" fill="{col}"/>'
    s += txt(15, h/2 + 3.2, name, 9.5, col, ls=.12)
    lw = {'OUTBOUND': 44, 'AT EARTH': 42, 'RETURNING': 48}[name]
    s += txt(15 + lw + 4, h/2 + 3.4, mmss(left), 10.5, C['text'], ls=.02)
    mx, ex, cy = 98, W - 86, h/2 + 1
    p0, p1, p2 = (mx + 7, cy), ((mx + ex)/2, cy - 8), (ex - 7, cy)
    s += dots(p0, p1, p2, u, 20, .7)
    s += moon(mx, cy, 5.5) + earth(ex, cy, 6)
    if name == 'AT EARTH':
        s += ship(ex - 11, cy - 3, 0, 10, glow=False)
    else:
        x, y, a = qbez(p0, p1, p2, u)
        s += ship(x, y, a + (180 if name == 'RETURNING' else 0), 10.5)
    s += f'<rect x="{W-74}" y="3" width="1" height="{h-6}" fill="#c9d3e6" opacity=".25"/>'
    s += rich(W - 6, h/2 + 3.4, [('Back in ', C['sub']), (mmss(TOTAL - t), C['text'])], 10, anchor='end', ls=.05)
    return s, W, h, dict(path=[p0, p1, p2], moon=(mx, cy, 5.5), earth=(ex, cy, 6)), name

def chip(t):
    h = CHIP_H; w = 112
    s = panel(0, 0, w, h, 5)
    s += ship(13, h/2, -90 + 90, 10)  # pointing right = travelling
    s += rich(24, h/2 + 3.5, [('Ship back in ', C['sub']), (mmss(TOTAL - t), C['text'])], 10.5, ls=.05)
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
    # Eve bubble placeholder + gear
    s += f'<circle cx="{w-8-24}" cy="{st+30+24}" r="24" fill="#1b2a40" stroke="#3ad0ff" stroke-width="2"/>'
    s += f'<image href="file://{EVE}" x="{w-8-46}" y="{st+32}" width="44" height="44" clip-path="circle(22px)"/>' if EVE else ''
    gx = w - 14 - 36; gy = st + 90
    s += f'<path d="{chamfer(gx,gy,36,36,8)}" fill="#0f1a2e" fill-opacity=".9" stroke="#3ad0ff" stroke-opacity=".4"/><circle cx="{gx+18}" cy="{gy+18}" r="6.5" fill="none" stroke="#c9d3e6" stroke-width="3" stroke-dasharray="2.2 1.6"/><circle cx="{gx+18}" cy="{gy+18}" r="2.5" fill="none" stroke="#c9d3e6" stroke-width="1.5"/>'
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

# ---------------- stills ----------------
STILLS = [('outbound', 162), ('at_earth', 272), ('returning', 468)]
for w in (375,):
    bt = block_top(w)
    for nm, t in STILLS:
        s, W, h, meta, name, left = strip_std(w, t)
        body = status(w) + hud(w, '$1,860' if nm != 'returning' else '$2,100')
        body += f'<g transform="translate({X0},{bt})">{s}</g>'
        body += f'<g transform="translate({X0},{bt+h+STD["capgap"]})">{caption_std(W, t)}</g>'
        if nm == 'at_earth':
            ex = X0 + meta['earth'][0]; ey = bt + meta['earth'][1]
            # money pop: rises from Earth toward the HUD Money counter (stays above the band)
            body += f'<path d="M{ex-14},{ey-12} Q{ex-80},{ey-40} 120,{SAFE[w]+HUD_T+40}" fill="none" stroke="{C["gold"]}" stroke-opacity=".55" stroke-width="1.2" stroke-dasharray="1 3" stroke-linecap="round"/>'
            for i, (dx, dy) in enumerate([(-30, -20), (-52, -26), (-70, -30)]):
                body += f'<circle cx="{ex+dx}" cy="{ey+dy}" r="{2.2-i*.4}" fill="{C["gold"]}"/>'
            px, py = ex - 78, bt + 1
            body += (f'<text x="{px}" y="{py}" font-family="Inter" font-weight="900" font-size="15" fill="#3a2200" stroke="#3a2200" stroke-width="3" stroke-linejoin="round" text-anchor="middle">+$240</text>')
            body += f'<text x="{px}" y="{py}" font-family="Inter" font-weight="900" font-size="15" fill="{C["gold"]}" text-anchor="middle">+$240</text>'
        compose('empty375', w, 667, body, save(f'pad_{nm}_375x667.png'))
        stripY = (bt, bt + h); capY = (bt + h + STD['capgap'], bt + h + STD['capgap'] + STD['cap'])
        results[f'{nm}_375_std'] = dict(strip=stripY, caption=capY, block_bottom=capY[1], band_top=BAND[w][0], clearance=BAND[w][0]-capY[1])
        if nm == 'outbound':
            ov = body + band_overlay(w)
            ov += measure_line(w, SAFE[w]+HUD_T+HUD_H, f'HUD bottom y {SAFE[w]+HUD_T+HUD_H}', '#9fb3c8', side='right')
            ov += f'<rect x="{X0-0.5}" y="{stripY[0]}" width="{W+1}" height="{capY[1]-stripY[0]}" fill="none" stroke="#3aff9c" stroke-width="1"/>'
            ov += (f'<text x="15" y="{BAND[w][0]+19}" font-family="DejaVu Sans" font-size="8" fill="#3aff9c">strip y {stripY[0]}-{stripY[1]} · caption y {capY[0]}-{capY[1]} · clears band by {BAND[w][0]-capY[1]} pt</text>')
            compose('empty375', w, 667, ov, save(f'pad_{nm}_375x667_overlay.png'))
            inset(f'{OUT}/proofs/pad_{nm}_375x667_overlay.png', 92, 150, [(hud_bottom(w),'HUD bottom 102','#9fb3c8'),(stripY[0],f'strip top {stripY[0]}','#3aff9c'),(stripY[1],f'strip bottom {stripY[1]}','#3aff9c'),(capY[0],f'caption top {capY[0]}','#7ff3ff'),(capY[1],f'caption bottom {capY[1]}','#7ff3ff'),(144,'band top 144 (clear 5 pt)','#ff5a6a')], 430, x0=190, x1=315)

# tapped state (RETURNING, back in 4:12)
w = 375; bt = block_top(w); t = 600 - 252
s, W, h, meta, name, left = strip_std(w, t, tapped=True)
body = status(w) + hud(w, '$2,100') + f'<g transform="translate({X0},{bt})">{s}</g>'
body += f'<g transform="translate({X0},{bt+h+STD["capgap"]})">{caption_std(W, t, tapped=True)}</g>'
body += f'<circle cx="160" cy="{bt+h/2}" r="13" fill="#ffffff" fill-opacity=".18" stroke="#ffffff" stroke-opacity=".6"/>'
compose('empty375', w, 667, body, save('pad_tapped_375x667.png'))

# thin strip, 375 and 393
for w, key in ((375, 'empty375'), (393, 'empty393')):
    bt = block_top(w); H = 667 if w == 375 else 852
    s, W, h, meta, name = strip_thin(w, 162)
    body = status(w) + hud(w) + f'<g transform="translate({X0},{bt})">{s}</g>'
    compose(key, w, H, body, save(f'pad_outbound_thin_{w}x{H}.png'))
    ov = body + band_overlay(w) + measure_line(w, hud_bottom(w), f'HUD bottom y {hud_bottom(w)}', '#9fb3c8', side='right')
    ov += f'<rect x="{X0-0.5}" y="{bt}" width="{W+1}" height="{h}" fill="none" stroke="#3aff9c"/>'
    ov += f'<text x="15" y="{BAND[w][0]+19}" font-family="DejaVu Sans" font-size="8" fill="#3aff9c">thin strip y {bt}-{bt+h} · clears band by {BAND[w][0]-bt-h} pt</text>'
    compose(key, w, H, ov, save(f'pad_outbound_thin_{w}x{H}_overlay.png'))
    results[f'outbound_{w}_thin'] = dict(strip=(bt, bt+h), band_top=BAND[w][0], clearance=BAND[w][0]-bt-h)

# 393 standard (expected NOT to fit with safe-top 59) - overlay shows the overlap
w = 393; bt = block_top(w)
s, W, h, meta, name, left = strip_std(w, 162)
body = status(w) + hud(w) + f'<g transform="translate({X0},{bt})">{s}</g>' + f'<g transform="translate({X0},{bt+h+2})">{caption_std(W, 162)}</g>'
compose('empty393', 393, 852, body, save('pad_outbound_393x852.png'))
cb = bt + h + 2 + STD['cap']
ov = body + band_overlay(w) + measure_line(w, hud_bottom(w), f'HUD bottom y {hud_bottom(w)}', '#9fb3c8', side='right')
ov += f'<rect x="{X0-0.5}" y="{bt}" width="{W+1}" height="{cb-bt}" fill="none" stroke="#ff5a6a"/>'
ov += f'<text x="15" y="{BAND[w][0]+30}" font-family="DejaVu Sans" font-size="8" fill="#ff5a6a">standard block y {bt}-{cb}: {cb-BAND[w][0]} pt INSIDE band - use thin strip here</text>'
compose('empty393', 393, 852, ov, save('pad_outbound_393x852_std_overlay.png'))
results['outbound_393_std'] = dict(strip=(bt, bt+h), caption=(bt+h+2, cb), band_top=165, clearance=165-cb)

# chip on the Shipyard (375) + overlay
w = 375; bt = block_top(w)
cs, cw, ch = chip(348)
body = status(w) + hud(w, '$2,100') + f'<g transform="translate({X0},{bt})">{cs}</g>'
compose('yard375', w, 667, body, save('chip_shipyard_375x667.png'))
ov = body + band_overlay(w) + measure_line(w, hud_bottom(w), f'HUD bottom y {hud_bottom(w)}', '#9fb3c8', side='right')
ov += f'<rect x="{X0-0.5}" y="{bt}" width="{cw+1}" height="{ch}" fill="none" stroke="#3aff9c"/>'
ov += f'<text x="{X0+cw+6}" y="{bt+12}" font-family="DejaVu Sans" font-size="8" fill="#3aff9c">chip y {bt}-{bt+ch} · clears band by {BAND[w][0]-bt-ch} pt</text>'
compose('yard375', w, 667, ov, save('chip_shipyard_375x667_overlay.png'))
inset(f'{OUT}/proofs/chip_shipyard_375x667_overlay.png', 92, 150, [(hud_bottom(w),'HUD bottom 102','#9fb3c8'),(bt,f'chip top {bt}','#3aff9c'),(bt+ch,f'chip bottom {bt+ch}','#3aff9c'),(144,f'band top 144  (clearance {144-bt-ch} pt)','#ff5a6a')], 440)
results['chip_375'] = dict(chip=(bt, bt+ch), band_top=144, clearance=144-bt-ch)
results['chip_393'] = dict(chip=(block_top(393), block_top(393)+ch), band_top=165, clearance=165-block_top(393)-ch)

# ---------------- 3x zoom sheet of every state ----------------
rows = []
for nm, t in STILLS + [('tapped', 348)]:
    s, W, h, meta, name, left = strip_std(375, t, tapped=(nm == 'tapped'))
    extra = ''
    if nm == 'at_earth':
        ex, ey = meta['earth'][0], meta['earth'][1]
        extra = (f'<text x="{ex-40}" y="{ey-4}" font-family="Inter" font-weight="900" font-size="12" fill="#3a2200" stroke="#3a2200" stroke-width="2.5" stroke-linejoin="round" text-anchor="middle">+$240</text>'
                 f'<text x="{ex-40}" y="{ey-4}" font-family="Inter" font-weight="900" font-size="12" fill="{C["gold"]}" text-anchor="middle">+$240</text>')
    rows.append((s + f'<g transform="translate(0,{h+2})">{caption_std(W, t, nm=="tapped")}</g>' + extra, W, 36, nm))
ts, W2, h2, _, _ = strip_thin(375, 162); rows.append((ts, W2, 18, 'thin'))
cs, cw, ch = chip(348); rows.append((cs, cw, 20, 'chip'))
y = 10; body = f'<rect width="330" height="{sum(r[2]+22 for r in rows)+10}" fill="#05070c"/>'
for s, Wd, hh, nm in rows:
    body += f'<text x="10" y="{y+7}" font-family="DejaVu Sans" font-size="7" fill="#7f8ea3">{nm}</text>'
    body += f'<g transform="translate(12,{y+12})">{s}</g>'; y += hh + 22
sheet = render(svg_doc(330, y + 10, body), 3)
sheet.convert('RGB').quantize(256).save(save('strip_states_3x.png'), optimize=True)

# ---------------- 3x parts ----------------
def part(name, w, h, body):
    im = render(svg_doc(w, h, body), 3)
    im.save(f'{OUT}/parts/{name}@3x.png', optimize=True)
    return name, im.size
P = []
P.append(part('moon_15pt', 15, 15, moon(7.5, 7.5, 7.5)))
P.append(part('earth_16pt', 24, 24, earth(12, 12, 8)))      # 16 pt disc + 4 pt atmosphere each side
P.append(part('ship_icon_13pt', 15, 9, ship(7.8, 4.5, 0, 13, glow=False)))
P.append(part('ship_glow_flame', 11, 7, f'<g transform="translate(10.5,3.5) scale({13/14})"><ellipse cx="-3.6" cy="0" rx="4.4" ry="2.2" fill="url(#flame)"/><circle cx="0" cy="0" r="3.4" fill="url(#eglow)" opacity=".8"/></g>'))
P.append(part('pulse_ring_16pt', 16, 16, f'<circle cx="8" cy="8" r="7.4" fill="none" stroke="{C["earth"]}" stroke-width="1.2"/>'))
P.append(part('flash_landing_36pt', 36, 36, '<circle cx="18" cy="18" r="18" fill="url(#flash)"/>'))
s, W, h, meta, *_ = strip_std(375, 0)
p0, p1, p2 = meta['path']
P.append(part('path_dots_std', W, h, dots(p0, p1, p2, 0, 26, .85, split=False)))
P.append(part('strip_bg_std_303x22', 303, 22, panel(0, 0, 303, 22, 6)))
P.append(part('strip_bg_thin_303x16', 303, 16, panel(0, 0, 303, 16, 5)))
cs, cw, ch = chip(348)
P.append(part('chip_bg_112x18', 112, 18, panel(0, 0, 112, 18, 5)))
P.append(part('chip_full_example', 112, 18, cs))
json.dump(dict(results=results, path_std=meta['path'], moon=meta['moon'], earth=meta['earth'],
               path_thin=strip_thin(375, 0)[3]['path'], parts=P), open(f'{OUT}/_src/measure.json', 'w'), indent=1)
print(json.dumps(results, indent=1)); print(P)
