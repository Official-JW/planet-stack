"""Planet Stack - crew role system: the ONE table every script reads (Blender kit builder, card compositor, GLB packer, ROLES.md).
Adding a role = adding one entry here (+ a tool builder in role_kit.py if it needs a new tool; badges are pure 2D data below).
Pure Python (no bpy) so the PIL card script can import it too.

Fields
  name      display name on the pick screen
  job       one-line plain-English job description
  accent    hex accent paint (stripes, pauldron lame, badge ring, card trim). Must stay clear of the suit's cyan glow (#3ad0ff)
            and the gold-orange visor (#ffae2e) at phone size.
  tool      tool builder key in role_kit.TOOLS (held in the RIGHT hand with a closed power grip)
  extras    extra kit parts in role_kit.EXTRAS (headset, shoulder radio, forearm tablet, accent gloves ...)
  badge     badge key in BADGES (simple original geometric symbol, white on a graphite disc with an accent ring)
  arm_r     right-arm pose (pitch fwd, abduct, elbow bend) for the tool hold; left arm stays relaxed
  roll      optional wrist roll (rad) that leans the held tool out of the body silhouette
  tier      1 = starting four, 2 = later roles (flight crew + specialists)
  group     start | flight | specialist (pick-screen section)
"""
ROLES = {
    # ---- starting four
    'miner':         dict(name='Miner',         job='Mines ore at the Mine.',              accent='#d68f00', tool='rock_pick',    extras=[],
                          badge='ore', arm_r=(0.26, 0.22, 0.95), roll=0.38, card_az=-14, tier=1, group='start'),
    'mine_driver':   dict(name='Mine Driver',   job='Drives the mine truck.',              accent='#2cffba', tool='drive_controller',   extras=['headset', 'accent_gloves'],
                          badge='wheel',   arm_r=(0.16, 0.30, 0.85), tier=1, group='start'),
    'mechanic':      dict(name='Mechanic',      job='Upgrades and builds.',                accent='#b81c00', tool='big_wrench',   extras=['tool_belt'],
                          badge='gear',    arm_r=(0.2, 0.36, 1.3), roll=0.28, card_az=-15, tier=1, group='start'),
    'cargo_manager': dict(name='Cargo Manager', job='Runs cargo and radios the crew.',     accent='#8b1fc5', tool='cargo_tablet', extras=['shoulder_radio'],
                          badge='crate',   arm_r=(0.42, 0.06, 1.12), tier=1, group='start'),
    # ---- flight crew: the only two who fly once the Habitat is built
    'captain':       dict(name='Captain',       job='Flies the ship once the Habitat is up.', accent='#647fff', tool='flight_yoke', extras=['headset'],
                          badge='chevron3', arm_r=(0.18, 0.28, 0.9), tier=2, group='flight'),
    'co_captain':    dict(name='Co-Captain',    job='Navigates and flies second seat.',    accent='#12afc3', tool='nav_scope',    extras=['headset'],
                          badge='chevron2', arm_r=(0.3, 0.16, 1.1), roll=0.2, tier=2, group='flight'),
    # ---- specialists
    'engineer':      dict(name='Engineer',      job='Builds new ships at the Shipyard.',   accent='#b87249', tool='power_driver', extras=['tool_belt'],
                          badge='rocket',  arm_r=(0.3, 0.2, 1.15), tier=2, group='specialist'),
    'botanist':      dict(name='Botanist',      job='Grows food in the greenhouse.',       accent='#d0ff66', tool='seed_case',    extras=[],
                          badge='leaf',    arm_r=(0.12, 0.26, 0.55), tier=2, group='specialist'),
    'welder':        dict(name='Welder',        job='Welds and repairs hull plates.',      accent='#ff4993', tool='weld_torch',   extras=['accent_gloves'],
                          badge='spark',   arm_r=(0.3, 0.2, 1.15), roll=0.3, tier=2, group='specialist'),
    'machinist':     dict(name='Machinist',     job='Machines parts in the workshop.',     accent='#b82756', tool='caliper',      extras=[],
                          badge='nut',     arm_r=(0.36, 0.12, 1.2), tier=2, group='specialist'),
}
ORDER = ['miner', 'mine_driver', 'mechanic', 'cargo_manager', 'captain', 'co_captain', 'engineer', 'botanist', 'welder', 'machinist']

# ---------------------------------------------------------------- badges: 2D primitives in a unit disc (radius 1, +v = up)
#   ('fan',  [(u, v), ...])                 star-shaped polygon, filled from its centroid
#   ('ring', [(u, v), ...], [(u, v), ...])  band between an outer and an inner loop (same point count) = shape with a hole
import math
def _circle(r, n=32, a0=0.0, cx=0.0, cy=0.0): return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]
def _quad(p0, p1, w):
    (x0, y0), (x1, y1) = p0, p1; dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); nx, ny = -dy / L * w / 2, dx / L * w / 2
    return [(x0 + nx, y0 + ny), (x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny)]

def _ore():        # rough ore chunk: irregular lumpy rock split into three chipped facets by thin gaps (the gaps read as a vein line) + a small chip
    A, B, C, D, E = (-0.16, 0.6), (0.2, 0.64), (0.5, 0.42), (0.68, 0.06), (0.6, -0.36)
    F, G, H, I, J = (0.22, -0.6), (-0.28, -0.6), (-0.6, -0.34), (-0.7, 0.06), (-0.5, 0.42)
    P, Q = (0.0, 0.16), (0.3, -0.1)
    lump = lambda a, b, k: ((a[0] + b[0]) / 2 + k * (b[1] - a[1]), (a[1] + b[1]) / 2 - k * (b[0] - a[0]))   # bulge an edge outward
    def piece(pts, sc=0.92):
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        return [(cx + (x - cx) * sc, cy + (y - cy) * sc) for x, y in pts]
    top = [A, lump(A, B, 0.12), B, C, P, J, lump(J, A, 0.1)]
    right = [C, lump(C, D, 0.1), D, E, Q, P]
    low = [P, Q, E, lump(E, F, 0.12), F, G, lump(G, H, 0.08), H, I, J]
    chip = [(0.52, 0.62), (0.66, 0.56), (0.62, 0.44)]
    return [('fan', piece(top)), ('fan', piece(right)), ('fan', piece(low, 0.95)), ('fan', chip)]

def _wheel():      # tyre ring + hub + 3 spokes
    out = [('ring', _circle(0.74, 40), _circle(0.52, 40)), ('fan', _circle(0.17, 20))]
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        out.append(('fan', _quad((0.12 * math.cos(a), 0.12 * math.sin(a)), (0.56 * math.cos(a), 0.56 * math.sin(a)), 0.16)))
    return out

def _gear():       # 8-tooth cog with a round hole
    n = 8 * 12; o = []; i_ = []
    for j in range(n):
        a = 2 * math.pi * j / n; ph = (j % 12) / 12.0
        r = 0.76 if 0.2 <= ph < 0.6 else 0.56
        o.append((r * math.cos(a), r * math.sin(a))); i_.append((0.26 * math.cos(a), 0.26 * math.sin(a)))
    return [('ring', o, i_)]

def _crate():      # front-on cargo crate: square frame + diagonal brace + two plank panels split by gaps (no isometric/rhombus top)
    sq = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [('ring', sq(-0.64, -0.64, 0.64, 0.64), sq(-0.49, -0.49, 0.49, 0.49)),
            ('fan', _quad((-0.43, -0.43), (0.43, 0.43), 0.16)),
            ('fan', [(-0.42, -0.22), (-0.42, 0.42), (0.22, 0.42)]),
            ('fan', [(0.42, 0.22), (0.42, -0.42), (-0.22, -0.42)])]

def _bolt():       # angular power bolt
    return [('fan', [(0.12, 0.8), (0.42, 0.8), (0.16, 0.12), (0.42, 0.12), (-0.12, -0.8), (0.02, -0.12), (-0.26, -0.12)])]

def _leaf():       # pointed leaf + stem
    L = []
    for j in range(17):
        t = j / 16; y = -0.55 + 1.3 * t; L.append((0.42 * math.sin(math.pi * t) ** 0.8, y))
    for j in range(15, 0, -1):
        t = j / 16; y = -0.55 + 1.3 * t; L.append((-0.42 * math.sin(math.pi * t) ** 0.8, y))
    return [('fan', [(x * 0.9 + 0.05, y) for x, y in L]), ('fan', _quad((0.0, -0.5), (-0.18, -0.8), 0.1))]

def _spark():      # weld torch: short angled nozzle at lower-left + five short spark lines spraying up-right from its tip (no star)
    tip = (-0.16, -0.16)
    out = [('fan', _quad((-0.72, -0.72), (-0.24, -0.24), 0.28)), ('fan', _quad((-0.26, -0.26), (-0.19, -0.19), 0.16))]
    for ang, L in ((10, 0.52), (30, 0.74), (45, 0.86), (60, 0.74), (80, 0.52)):
        a = math.radians(ang); r0 = 0.14
        p0 = (tip[0] + r0 * math.cos(a), tip[1] + r0 * math.sin(a)); p1 = (tip[0] + L * math.cos(a), tip[1] + L * math.sin(a))
        out.append(('fan', _quad(p0, p1, 0.085)))
    return out

def _nut():        # hex nut
    o = []; i_ = []
    for j in range(6 * 8):
        a = 2 * math.pi * j / 48; k = int(j // 8); f = (j % 8) / 8
        a0, a1 = math.pi / 6 + k * math.pi / 3, math.pi / 6 + (k + 1) * math.pi / 3
        p0 = (0.74 * math.cos(a0), 0.74 * math.sin(a0)); p1 = (0.74 * math.cos(a1), 0.74 * math.sin(a1))
        o.append((p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f))
        aa = a0 + (a1 - a0) * f; i_.append((0.32 * math.cos(aa), 0.32 * math.sin(aa)))
    return [('ring', o, i_)]

def _chevrons(n):  # rank chevrons pointing up (open V bands, not closed rhombus shapes): captain = 3, co-captain = 2
    out = []; h = 0.34; w = 0.17; ys = [0.36, 0.0, -0.36][:n] if n == 3 else [0.2, -0.22]
    for y in ys:
        L, Tp, R_ = (-0.62, y - h * 0.62), (0.0, y + h * 0.55), (0.62, y - h * 0.62)
        out.append(('fan', _quad(L, Tp, w))); out.append(('fan', _quad(Tp, R_, w)))
        out.append(('fan', [(Tp[0] - w * 0.62, Tp[1] - w * 0.25), (Tp[0], Tp[1] + w * 0.5), (Tp[0] + w * 0.62, Tp[1] - w * 0.25), (Tp[0], Tp[1] - w * 0.6)]))   # mitre fill at the apex
    return out

def _rocket():     # ship-builder: upright rocket - rounded nose, body, two side fins, nozzle (all simple primitives)

    body = [(-0.2, -0.42), (0.2, -0.42), (0.2, 0.28)] + [(0.2 * math.cos(a), 0.28 + 0.46 * math.sin(a)) for a in [math.pi * i / 12 for i in range(1, 12)]] + [(-0.2, 0.28)]
    finL = [(-0.2, -0.05), (-0.2, -0.42), (-0.5, -0.62), (-0.46, -0.3)]
    finR = [(0.2, -0.05), (0.46, -0.3), (0.5, -0.62), (0.2, -0.42)]
    noz = [(-0.13, -0.48), (0.13, -0.48), (0.18, -0.66), (-0.18, -0.66)]
    return [('fan', body), ('fan', finL), ('fan', finR), ('fan', noz)]

BADGES = {'ore': _ore, 'wheel': _wheel, 'gear': _gear, 'crate': _crate, 'bolt': _bolt, 'leaf': _leaf, 'spark': _spark, 'nut': _nut, 'chevron3': lambda: _chevrons(3), 'chevron2': lambda: _chevrons(2), 'rocket': _rocket}
BADGE_DESC = {'ore': 'rough ore chunk (irregular lumpy rock, three chipped facets split by a vein-line gap, small chip)', 'wheel': 'three-spoke wheel', 'gear': 'eight-tooth gear with a round hole',
              'crate': 'front-on cargo crate (square frame, diagonal brace, two plank panels)', 'bolt': 'angular power bolt', 'leaf': 'pointed leaf with a stem',
              'spark': 'weld torch nozzle with five short spark lines spraying from its tip', 'nut': 'hex nut', 'chevron3': 'three stacked rank chevrons', 'chevron2': 'two stacked rank chevrons', 'rocket': 'upright rocket with two fins'}
