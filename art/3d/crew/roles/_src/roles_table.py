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
  tier      1 = starting four (built + carded in pass 1), 2 = later roles (defined, built later)
"""
ROLES = {
    'miner':         dict(name='Miner',         job='Mines ore at the Mine.',              accent='#ffc21a', tool='rock_pick',    extras=[],
                          badge='ore', arm_r=(0.26, 0.22, 0.95), roll=0.38, card_az=-14, tier=1),
    'mine_driver':   dict(name='Mine Driver',   job='Drives the mine truck.',              accent='#2fd36b', tool='drive_controller',   extras=['headset', 'accent_gloves'],
                          badge='wheel',   arm_r=(0.16, 0.30, 0.85), tier=1),
    'mechanic':      dict(name='Mechanic',      job='Upgrades and builds.',                accent='#f0443a', tool='big_wrench',   extras=['tool_belt'],
                          badge='gear',    arm_r=(0.2, 0.36, 1.3), roll=0.28, card_az=-15, tier=1),
    'cargo_manager': dict(name='Cargo Manager', job='Runs cargo and radios the crew.',     accent='#a066ff', tool='cargo_tablet', extras=['shoulder_radio'],
                          badge='crate',   arm_r=(0.42, 0.06, 1.12), tier=1),
    # ---- tier 2: defined now so the palette stays distinct; tools get built in the next pass
    'engineer':      dict(name='Engineer',      job='Keeps the base powered and running.', accent='#ff7a1f', tool='multimeter',   extras=[],
                          badge='bolt',    arm_r=(0.3, 0.16, 1.1), tier=2),
    'botanist':      dict(name='Botanist',      job='Grows food in the greenhouse.',       accent='#b6e62e', tool='plant_sampler', extras=[],
                          badge='leaf',    arm_r=(0.3, 0.16, 1.1), tier=2),
    'welder':        dict(name='Welder',        job='Welds and repairs hull plates.',      accent='#ff4fb0', tool='weld_torch',   extras=[],
                          badge='spark',   arm_r=(0.3, 0.16, 1.1), tier=2),
    'machinist':     dict(name='Machinist',     job='Machines parts in the workshop.',     accent='#4d6bff', tool='caliper',      extras=[],
                          badge='nut',     arm_r=(0.3, 0.16, 1.1), tier=2),
}
ORDER = ['miner', 'mine_driver', 'mechanic', 'cargo_manager', 'engineer', 'botanist', 'welder', 'machinist']

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

def _crate():      # isometric cargo cube: three faces with gaps
    s = 0.62; c30, s30 = math.cos(math.pi / 6) * s, 0.5 * s; g = 0.06
    top = [(0, g * 0.9), (c30 - g * 1.4, s30 + g * 0.1), (0, 2 * s30 - g * 0.6), (-c30 + g * 1.4, s30 + g * 0.1)]
    top = [(x, y + 0.08) for x, y in top]
    left = [(-c30, s30 - g * 0.4), (-g * 0.8, 0 - g * 0.2), (-g * 0.8, -2 * s30 + g * 0.2), (-c30, -s30 + g * 0.6)]
    right = [(g * 0.8, 0 - g * 0.2), (c30, s30 - g * 0.4), (c30, -s30 + g * 0.6), (g * 0.8, -2 * s30 + g * 0.2)]
    left = [(x, y + 0.08) for x, y in left]; right = [(x, y + 0.08) for x, y in right]
    return [('fan', top), ('fan', left), ('fan', right)]

def _bolt():       # angular power bolt
    return [('fan', [(0.12, 0.8), (0.42, 0.8), (0.16, 0.12), (0.42, 0.12), (-0.12, -0.8), (0.02, -0.12), (-0.26, -0.12)])]

def _leaf():       # pointed leaf + stem
    L = []
    for j in range(17):
        t = j / 16; y = -0.55 + 1.3 * t; L.append((0.42 * math.sin(math.pi * t) ** 0.8, y))
    for j in range(15, 0, -1):
        t = j / 16; y = -0.55 + 1.3 * t; L.append((-0.42 * math.sin(math.pi * t) ** 0.8, y))
    return [('fan', [(x * 0.9 + 0.05, y) for x, y in L]), ('fan', _quad((0.0, -0.5), (-0.18, -0.8), 0.1))]

def _spark():      # 4-point weld spark
    P = []
    for j in range(8):
        a = math.pi / 2 + j * math.pi / 4; r = 0.8 if j % 2 == 0 else 0.2
        P.append((r * math.cos(a), r * math.sin(a)))
    return [('fan', P)]

def _nut():        # hex nut
    o = []; i_ = []
    for j in range(6 * 8):
        a = 2 * math.pi * j / 48; k = int(j // 8); f = (j % 8) / 8
        a0, a1 = math.pi / 6 + k * math.pi / 3, math.pi / 6 + (k + 1) * math.pi / 3
        p0 = (0.74 * math.cos(a0), 0.74 * math.sin(a0)); p1 = (0.74 * math.cos(a1), 0.74 * math.sin(a1))
        o.append((p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f))
        aa = a0 + (a1 - a0) * f; i_.append((0.32 * math.cos(aa), 0.32 * math.sin(aa)))
    return [('ring', o, i_)]

BADGES = {'ore': _ore, 'wheel': _wheel, 'gear': _gear, 'crate': _crate, 'bolt': _bolt, 'leaf': _leaf, 'spark': _spark, 'nut': _nut}
BADGE_DESC = {'ore': 'rough ore chunk (irregular lumpy rock, three chipped facets split by a vein-line gap, small chip)', 'wheel': 'three-spoke wheel', 'gear': 'eight-tooth gear with a round hole',
              'crate': 'isometric cargo cube (three faces split by gaps)', 'bolt': 'angular power bolt', 'leaf': 'pointed leaf with a stem',
              'spark': 'four-point weld spark', 'nut': 'hex nut'}
