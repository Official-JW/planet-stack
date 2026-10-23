"""Process diagram: overhead plate (build_refinery.py --only diagram -> diagram_plate.png + diagram_points.json) + numbered
badges, flow arrows and a legend.  python3 make_diagram.py <dir> <out.png>"""
import sys, json, math
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
P = json.load(open(f'{src}/diagram_points.json')); pts = P['pts']
plate = Image.open(f'{src}/diagram_plate.png').convert('RGB'); PW, PH = plate.size
LW = 1500; W, H = PW + LW, max(PH + 230, 2440)
img = Image.new('RGB', (W, H), (14, 16, 20)); img.paste(plate, (0, 170)); d = ImageDraw.Draw(img, 'RGBA')
WHITE, CYAN, ORANGE, GREY = (235, 238, 242), (70, 215, 255), (255, 150, 70), (170, 178, 188)
d.text((60, 36), 'REFINERY  —  PROCESS DIAGRAM', font=ImageFont.truetype(FB, 64), fill=WHITE)
d.text((60, 112), 'Mine station, compact layout (top view, north up).  Truck HT-04 dumps into RB-1; ore splits into a He-3 line and a fuel line (LOX / LH2, no methane).', font=ImageFont.truetype(F, 30), fill=GREY)
STEPS = [  # key, badge, colour, title, detail
    ('truck', 'T', WHITE, 'HT-04 haul truck', 'hauls ore from the Mine, reverses to Path_Dump and tips'),
    ('bin', '1', WHITE, 'RB-1 intake bin', 'grizzly bars scalp boulders (Intake_Grate shakes)'),
    ('feeder', '2', WHITE, 'BF-1 belt feeder', 'meters ore out of the bin bottom'),
    ('splitter', '3', WHITE, 'SP-1 splitter', 'flop gate: He-3 branch | fuel branch'),
    ('elevator', 'H1', CYAN, 'BE-1 elevator + covered gallery', 'lifts the He-3 feed over the fuel row'),
    ('sieve', 'H2', CYAN, 'SV-1 sieve', 'keeps fines < 100 µm (He-3 sits on fine grains)'),
    ('kiln', 'H3', CYAN, 'KN-1 sealed rotary kiln', '~700 °C: releases the solar-wind volatiles'),
    ('hood', 'H4', CYAN, 'gas hood + CP-1 compressor', 'collects and compresses the evolved gas'),
    ('traps', 'H5', CYAN, 'CT-1..4 cold traps', 'strip H2O > CO2 > N2 > H2  (H2 goes to the fuel line)'),
    ('column', 'H6', CYAN, 'DC-1 cryo distillation column', 'splits He-3 from He-4'),
    ('fill', 'H7', CYAN, 'FS-1 filling station', 'He-3 canisters (glowing blue) on the rack  > He3_Output'),
    ('tailings', 'H8', CYAN, 'tailings', 'spent regolith out of the kiln'),
    ('crusher', 'F1', ORANGE, 'CR-1 crusher', 'breaks ore to liberate ilmenite'),
    ('magsep', 'F2', ORANGE, 'MS-1 magnetic separator', 'concentrates ilmenite (FeTiO3)'),
    ('reactor', 'F3', ORANGE, 'RX-1 H2 reduction reactor', '900-1000 °C:  FeTiO3 + H2 > Fe + TiO2 + H2O'),
    ('slag', 'F3b', ORANGE, 'slag + iron bin', 'Fe / TiO2 residue'),
    ('condenser', 'F4', ORANGE, 'WC-1 condenser', 'knocks the water out of the H2 stream'),
    ('electrolyzer', 'F5', ORANGE, 'EL-1 electrolyzer', '2 H2O > 2 H2 + O2;  H2 recycled to RX-1 (overhead loop)'),
    ('liquefier', 'F6', ORANGE, 'LQ-1 liquefier + RAD-1 radiators', 'liquefies O2 (90 K) and H2 (20 K)'),
    ('lox', 'F7', ORANGE, 'LOX-1 / LH2-1 tanks', 'cryo storage  > Fuel_Output'),
    ('tankfarm', 'F8', ORANGE, 'TO TANK FARM', 'LOX + LH2 header  > Pipe_TankFarm'),
    ('h2x', 'X', CYAN, 'H2 crossover rack + catwalk', 'cold-trap H2 > liquefier'),
    ('control', 'C', WHITE, 'CM-1 control module', 'airlock A-1 + dust shower, power masts, switchgear'),
]
def xy(k): x, y = pts[k]; return (x, y + 170)
def arrow(a, b, col, w=7):
    (x0, y0), (x1, y1) = a, b; L = math.hypot(x1 - x0, y1 - y0)
    if L < 60: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L; x0, y0 = x0 + ux * 34, y0 + uy * 34; x1, y1 = x1 - ux * 38, y1 - uy * 38
    d.line((x0, y0, x1, y1), fill=col + (230,), width=w)
    px, py = -uy, ux; d.polygon([(x1 + ux * 18, y1 + uy * 18), (x1 + px * 13, y1 + py * 13), (x1 - px * 13, y1 - py * 13)], fill=col + (240,))
for chain, col in ((['truck', 'bin', 'feeder', 'splitter'], WHITE),
                   (['splitter', 'elevator', 'sieve', 'kiln', 'hood', 'traps', 'column', 'fill'], CYAN), (['kiln', 'tailings'], CYAN),
                   (['splitter', 'crusher', 'magsep', 'reactor', 'condenser', 'electrolyzer', 'liquefier', 'lox', 'tankfarm'], ORANGE),
                   (['reactor', 'slag'], ORANGE), (['traps', 'h2x', 'liquefier'], CYAN)):
    for a, b in zip(chain, chain[1:]): arrow(xy(a), xy(b), col)
bf = ImageFont.truetype(FB, 26)
for k, badge, col, t, _ in STEPS:
    x, y = xy(k); r = 30 if len(badge) < 3 else 36
    d.ellipse((x - r, y - r, x + r, y + r), fill=(10, 12, 16, 235), outline=col, width=5)
    tw = d.textlength(badge, font=bf); d.text((x - tw / 2, y - 16), badge, font=bf, fill=col)
# legend
x0 = PW + 50; y = 200; tf, df = ImageFont.truetype(FB, 32), ImageFont.truetype(F, 26)
for hdr, col, keys in (('INTAKE', WHITE, 'T123'), ('He-3 LINE', CYAN, 'H'), ('FUEL LINE  (LOX / LH2 only)', ORANGE, 'F'), ('SUPPORT', WHITE, 'XC')):
    d.text((x0, y), hdr, font=ImageFont.truetype(FB, 38), fill=col); y += 58
    for k, badge, c_, t, det in STEPS:
        if (keys == 'H' and badge.startswith('H')) or (keys == 'F' and badge.startswith('F')) or (keys not in ('H', 'F') and badge in keys):
            d.ellipse((x0, y, x0 + 54, y + 54), outline=c_, width=4); tw = d.textlength(badge, font=bf); d.text((x0 + 27 - tw / 2, y + 12), badge, font=bf, fill=c_)
            d.text((x0 + 72, y - 2), t, font=tf, fill=WHITE); d.text((x0 + 72, y + 36), det, font=df, fill=GREY); y += 82
    y += 24
d.text((60, H - 50), 'Planet Stack · Refinery (Mine station) · stencil labels are invented, no real logos · original art', font=ImageFont.truetype(F, 26), fill=(130, 138, 148))
img.save(out, optimize=True); print(out, img.size)
