"""Planet Stack - Drill Rig (first 3D test model).
Generator for Blender 4.2 LTS, run headless:
  blender -b -P build_drill_rig.py -- --glb out.glb --blend out.blend [--render outdir]
Game axes (glTF): 1 unit = 1 m, +Y up, model front faces +Z, origin = centre of base at ground.
Inside Blender we work Z-up; G(x, y, z) maps game coords -> Blender coords (x, -z, y).
All geometry is original. Colours are vertex colours (no textures) with a soft baked gradient.
"""
import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
GLB, BLEND, RENDER = arg('--glb'), arg('--blend'), arg('--render')
random.seed(7)

# ---------------------------------------------------------------- palette (sRGB hex)
PAL = dict(
    graphite='#2a3245', graphite2='#3a4258', steel='#5b667e', steel_lt='#8794ad',
    pale='#c9d3e6', white='#e8edf5', amber='#ffb020', orange='#e8701a',
    cyan='#3ad0ff', cyan_hi='#7ff3ff', lens='#1a1f2b', hole='#0b0e16',
    lens_cyan='#1d4a5c', lens_amber='#6a4210', rock='#6f6d6b', rock_dk='#5f5d5c', platinum='#d9dee6')

def hex2rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def srgb2lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def G(x, y, z):
    return Vector((x, -z, y))

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start, scene.frame_end = 0, 60

# ---------------------------------------------------------------- materials
def mat_body(name, rough=0.72):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.use_backface_culling = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    va = nt.nodes.new('ShaderNodeVertexColor'); va.layer_name = 'Col'
    nt.links.new(va.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    return m

def mat_glow(name, hexc, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.use_backface_culling = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    c = srgb2lin(hex2rgb(hexc)) + (1,)
    bsdf.inputs['Base Color'].default_value = c
    bsdf.inputs['Emission Color'].default_value = c
    bsdf.inputs['Emission Strength'].default_value = strength
    bsdf.inputs['Roughness'].default_value = 0.4
    return m

M_BODY = mat_body('M_Body')
M_CYAN = mat_glow('M_GlowCyan', PAL['cyan'], 2.0)
M_AMBER = mat_glow('M_GlowAmber', PAL['amber'], 2.5)

# ---------------------------------------------------------------- part helpers
PARTS = {}   # group name -> list of objects

def finish_bm(bm, name, group, col, mat, bevel=0.0, sharp_deg=35.0, grad=0.18):
    """Bevel, write a mesh object, record colour info for later vertex colouring."""
    if bevel > 0:
        edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0) > math.radians(40)]
        if edges:
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=1, profile=0.5,
                            affect='EDGES', clamp_overlap=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.validate()
    # sharp edges where faces bend more than sharp_deg -> crisp low-poly facets
    bm2 = bmesh.new(); bm2.from_mesh(me)
    for e in bm2.edges:
        if (not e.is_manifold) or e.calc_face_angle(0) > math.radians(sharp_deg):
            e.smooth = False
    bm2.to_mesh(me); bm2.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(mat)
    ob['col'] = col; ob['grad'] = grad
    PARTS.setdefault(group, []).append(ob)
    return ob

def box(group, size, center, col, mat=None, bevel=0.03, name='box', rot=None):
    """size/center in game coords (x, y-up, z-front)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    S = Matrix.Diagonal((size[0], size[2], size[1], 1))
    M = Matrix.Translation(G(*center)) @ (rot.to_4x4() if rot else Matrix()) @ S
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return finish_bm(bm, name, group, col, mat or M_BODY, bevel)

def basis_from(p0, p1, up=None):
    a, b = G(*p0), G(*p1)
    x = (b - a); L = x.length; x.normalize()
    up = Vector((0, 0, 1)) if up is None else up
    if abs(x.dot(up)) > 0.95: up = Vector((1, 0, 0)) if abs(x.x) < 0.9 else Vector((0, 1, 0))
    y = up.cross(x).normalized(); z = x.cross(y).normalized()
    R = Matrix((x, y, z)).transposed()
    return a, b, L, R

def beam(group, p0, p1, w, h, col, mat=None, bevel=0.015, name='beam', up=None):
    """Box from p0 to p1 (game coords), cross-section w (side) x h (up-ish)."""
    a, b, L, R = basis_from(p0, p1, up)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    M = Matrix.Translation((a + b) / 2) @ R.to_4x4() @ Matrix.Diagonal((L, w, h, 1))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return finish_bm(bm, name, group, col, mat or M_BODY, bevel)

def cyl(group, center, r, h, col, axis='y', segs=12, mat=None, bevel=0.02, name='cyl', r2=None, grad=0.18):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=h)
    rot = {'y': Matrix(), 'x': Matrix.Rotation(math.pi / 2, 4, 'Y'),
           'z': Matrix.Rotation(math.pi / 2, 4, 'X')}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(G(*center)) @ rot, verts=bm.verts)
    return finish_bm(bm, name, group, col, mat or M_BODY, bevel, grad=grad)

def tube(group, center, r_out, r_in, h, col, segs=16, name='tube', mat=None):
    bm = bmesh.new()
    vs = []
    for ring_r, yy in ((r_out, -h / 2), (r_out, h / 2), (r_in, h / 2), (r_in, -h / 2)):
        vs.append([bm.verts.new(G(center[0] + ring_r * math.cos(2 * math.pi * i / segs), center[1] + yy,
                                  center[2] + ring_r * math.sin(2 * math.pi * i / segs))) for i in range(segs)])
    for k in range(4):
        A, B = vs[k], vs[(k + 1) % 4]
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((A[i], A[j], B[j], B[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish_bm(bm, name, group, col, mat or M_BODY, 0.0)

def sphere(group, center, r, col, mat=None, subdiv=2, name='sph', scale=(1, 1, 1), jitter=0.0, sharp=35):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    if jitter:
        for v in bm.verts: v.co *= 1 + random.uniform(-jitter, jitter)
    M = Matrix.Translation(G(*center)) @ Matrix.Diagonal((scale[0], scale[2], scale[1], 1))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return finish_bm(bm, name, group, col, mat or M_BODY, 0.0, sharp_deg=sharp)

def poly_prism(group, pts2d, origin, u, v, n, depth, col, name='prism', mat=None):
    """Extrude 2-D polygon (in u,v plane at origin, game coords) by depth along n."""
    o, u, v, n = Vector(origin), Vector(u), Vector(v), Vector(n)
    bm = bmesh.new()
    f = [bm.verts.new(G(*(o + u * x + v * y))) for x, y in pts2d]
    b = [bm.verts.new(G(*(o + u * x + v * y + n * depth))) for x, y in pts2d]
    bm.faces.new(f); bm.faces.new(list(reversed(b)))
    k = len(pts2d)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((f[i], b[i], b[j], f[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish_bm(bm, name, group, col, mat or M_BODY, 0.0, grad=0.08)

def clip_poly(poly, x0, x1):
    def clip(pts, keep, inter):
        out = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            if keep(p):
                out.append(p)
                if not keep(q): out.append(inter(p, q))
            elif keep(q): out.append(inter(p, q))
        return out
    def ix(xc):
        return lambda p, q: (xc, p[1] + (q[1] - p[1]) * (xc - p[0]) / (q[0] - p[0]))
    poly = clip(poly, lambda p: p[0] >= x0, ix(x0))
    if poly: poly = clip(poly, lambda p: p[0] <= x1, ix(x1))
    return poly

def hazard(group, origin, u, v, n, length, height, stripe=0.22, depth=0.012):
    """Diagonal amber/graphite hazard band on a plane. u along band, v up the band, n outwards."""
    i = -int(height / stripe) - 2
    while i * stripe < length + stripe:
        p = [(i * stripe, 0), ((i + 1) * stripe, 0), ((i + 1) * stripe + height, height), (i * stripe + height, height)]
        cp = clip_poly(p, 0, length)
        if len(cp) >= 3:
            poly_prism(group, cp, origin, u, v, n, depth,
                       PAL['amber'] if i % 2 == 0 else PAL['graphite'], 'hazard')
        i += 1

def auger(group, axis_xz, y0, y1, r_in, r_out, pitch, th, col, segs_per_turn=20):
    turns = (y1 - y0) / pitch
    n = int(turns * segs_per_turn)
    bm = bmesh.new(); rings = []
    for k in range(n + 1):
        a = 2 * math.pi * k / segs_per_turn
        y = y0 + (y1 - y0) * k / n
        ring = []
        for rr, dy in ((r_in, -th / 2), (r_out, -th / 2), (r_out, th / 2), (r_in, th / 2)):
            ring.append(bm.verts.new(G(axis_xz[0] + rr * math.cos(a), y + dy, axis_xz[1] + rr * math.sin(a))))
        rings.append(ring)
    for k in range(n):
        A, B = rings[k], rings[k + 1]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((A[i], A[j], B[j], B[i]))
    bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish_bm(bm, 'auger', group, col, M_BODY, 0.0, sharp_deg=50, grad=0.25)

def frustum_shell(group, c, y0, y1, b_half, t_half, wall, col, name='hopper'):
    """Open-top square hopper with wall thickness (visible inside)."""
    bm = bmesh.new()
    def ring(h, y):
        return [bm.verts.new(G(c[0] + sx * h, y, c[1] + sz * h)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ob_, ot = ring(b_half, y0), ring(t_half, y1)
    it, ib = ring(t_half - wall, y1), ring(b_half - wall, y0 + wall)
    for A, B in ((ob_, ot), (ot, it), (it, ib)):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((A[i], A[j], B[j], B[i]))
    bm.faces.new(list(reversed(ob_))); bm.faces.new(ib)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # inner faces point inwards: recalc makes the solid consistent
    return finish_bm(bm, name, group, col, M_BODY, 0.0, grad=0.3)

# ================================================================= MODEL
MAST_Z = -0.6; MH = 0.75          # mast centre z and half width
AX = (0.0, 0.85)                  # drill axis (x, z)
DECK = 0.5                        # pad top height

# ---------------- Base (static)
G_BASE = 'Base'
# pad: chamfered octagon slab
bm = bmesh.new()
oct_pts = []
for sx, sz in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
    pass
c = 0.55; hw = 2.5
pts = [(hw - c, hw), (-hw + c, hw), (-hw, hw - c), (-hw, -hw + c), (-hw + c, -hw), (hw - c, -hw), (hw, -hw + c), (hw, hw - c)]
poly_prism(G_BASE, [(x, -z) for x, z in pts], (0, 0, 0), (1, 0, 0), (0, 0, -1), (0, 1, 0), 0.42, PAL['graphite2'], 'pad')
# deck plate (slightly inset)
c2 = 0.45; hw2 = 2.38
pts2 = [(hw2 - c2, hw2), (-hw2 + c2, hw2), (-hw2, hw2 - c2), (-hw2, -hw2 + c2), (-hw2 + c2, -hw2), (hw2 - c2, -hw2), (hw2, -hw2 + c2), (hw2, hw2 - c2)]
poly_prism(G_BASE, [(x, -z) for x, z in pts2], (0, 0.42, 0), (1, 0, 0), (0, 0, -1), (0, 1, 0), 0.08, PAL['steel_lt'], 'deck')
# deck grating seams (thin dark lines)
for k in (-1.2, 0.0, 1.2):
    box(G_BASE, (4.3, 0.012, 0.035), (0, DECK + 0.006, k - 0.6 if k else 1.75), PAL['steel'], bevel=0, name='seam')
# hazard bands on the four sides of the pad
for side in range(4):
    ang = side * math.pi / 2
    n = Vector((math.sin(ang), 0, math.cos(ang)))
    u = Vector((math.cos(ang), 0, -math.sin(ang)))
    L = 2 * (hw - c)
    org = n * hw - u * (L / 2) + Vector((0, 0.1, 0))
    hazard(G_BASE, org, u, (0, 1, 0), n, L, 0.22, stripe=0.2)
# outriggers + jacks + feet
for sx, sz in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
    p0 = (sx * 1.9, 0.33, sz * 1.9); p1 = (sx * 3.05, 0.33, sz * 3.05)
    beam(G_BASE, p0, p1, 0.34, 0.26, PAL['white'], bevel=0.03, name='outrigger')
    hazard(G_BASE, Vector((sx * 2.55, 0.22, sz * 2.55)) + Vector((sx, 0, -sz)).normalized() * 0.0 + Vector((sx, 0, sz)).normalized() * 0.0
           + Vector((-sz, 0, sx)).normalized() * 0.0 + Vector((0, 0, 0)) + Vector((sz, 0, -sx)).normalized() * -0.0
           + Vector((0, 0, 0)), Vector((sx, 0, sz)).normalized(), (0, 1, 0), Vector((-sz, 0, sx)).normalized() * (1 if sx * sz > 0 else 1),
           0.0, 0.0) if False else None
    jx, jz = sx * 3.15, sz * 3.15
    cyl(G_BASE, (jx, 0.5, jz), 0.17, 0.62, PAL['steel_lt'], name='jack')
    cyl(G_BASE, (jx, 0.86, jz), 0.21, 0.12, PAL['graphite'], name='jackcap')
    cyl(G_BASE, (jx, 0.07, jz), 0.44, 0.14, PAL['graphite2'], segs=10, name='foot', bevel=0.03)
    # amber collar on each jack
    cyl(G_BASE, (jx, 0.62, jz), 0.185, 0.1, PAL['amber'], name='jackband', bevel=0.0)
# drill collar on the deck + dark hole
tube(G_BASE, (AX[0], DECK + 0.26, AX[1]), 0.66, 0.5, 0.52, PAL['graphite'], segs=16, name='collar')
tube(G_BASE, (AX[0], DECK + 0.535, AX[1]), 0.70, 0.46, 0.06, PAL['amber'], segs=16, name='collarrim')
cyl(G_BASE, (AX[0], DECK + 0.03, AX[1]), 0.5, 0.04, PAL['hole'], segs=16, bevel=0, name='hole', grad=0)
# mast foot
box(G_BASE, (2.0, 0.45, 2.0), (0, DECK + 0.225, MAST_Z), PAL['white'], bevel=0.06, name='mastfoot')
box(G_BASE, (2.06, 0.1, 2.06), (0, DECK + 0.05, MAST_Z), PAL['graphite'], bevel=0.02, name='mastfoot_trim')

# ---------------- Rig (vibrates while digging)
G_MAST = 'Mast'
TOP = 8.7
y_lo = DECK + 0.45
for sx in (-1, 1):
    for sz in (-1, 1):
        box(G_MAST, (0.18, TOP - y_lo, 0.18), (sx * MH, (TOP + y_lo) / 2, MAST_Z + sz * MH), PAL['white'], bevel=0.035, name='post')
levels = [y_lo + 0.2 + i * 1.3 for i in range(7)]
for y in levels:
    for (a, b) in (((-MH, MAST_Z - MH), (MH, MAST_Z - MH)), ((-MH, MAST_Z + MH), (MH, MAST_Z + MH)),
                   ((-MH, MAST_Z - MH), (-MH, MAST_Z + MH)), ((MH, MAST_Z - MH), (MH, MAST_Z + MH))):
        beam(G_MAST, (a[0], y, a[1]), (b[0], y, b[1]), 0.1, 0.1, PAL['graphite2'], name='rung')
for i in range(len(levels) - 1):
    y0, y1 = levels[i], levels[i + 1]
    flip = 1 if i % 2 == 0 else -1
    # back face (z = MAST_Z - MH), left (x=-MH), right (x=+MH): zig-zag diagonals
    beam(G_MAST, (-MH * flip, y0, MAST_Z - MH), (MH * flip, y1, MAST_Z - MH), 0.07, 0.07, PAL['steel'], name='diag')
    beam(G_MAST, (-MH, y0, MAST_Z - MH * flip), (-MH, y1, MAST_Z + MH * flip), 0.07, 0.07, PAL['steel'], name='diag')
    beam(G_MAST, (MH, y0, MAST_Z + MH * flip), (MH, y1, MAST_Z - MH * flip), 0.07, 0.07, PAL['steel'], name='diag')
# carriage rails on the front face
for sx in (-1, 1):
    box(G_MAST, (0.12, TOP - y_lo - 0.4, 0.14), (sx * 0.42, (TOP + y_lo) / 2, MAST_Z + MH + 0.12), PAL['steel_lt'], bevel=0.02, name='rail')
# crown block + sheave
box(G_MAST, (1.9, 0.55, 1.9), (0, TOP + 0.27, MAST_Z), PAL['white'], bevel=0.07, name='crown')
box(G_MAST, (1.96, 0.1, 1.96), (0, TOP + 0.05, MAST_Z), PAL['graphite'], bevel=0.02, name='crown_trim')
cyl(G_MAST, (0, TOP + 0.85, MAST_Z + 0.2), 0.36, 0.16, PAL['graphite'], axis='x', segs=14, name='sheave')
cyl(G_MAST, (0, TOP + 0.85, MAST_Z + 0.2), 0.12, 0.3, PAL['steel_lt'], axis='x', segs=10, name='hub')
for sx in (-1, 1):
    box(G_MAST, (0.08, 0.55, 0.3), (sx * 0.17, TOP + 0.75, MAST_Z + 0.2), PAL['white'], bevel=0.02, name='sheave_cheek')
hazard(G_MAST, Vector((-0.95, TOP + 0.3, MAST_Z + 0.95)), (1, 0, 0), (0, 1, 0), (0, 0, 1), 1.9, 0.2, stripe=0.18)
# status lamp housing + dark lens (on the crown, front-left)
LAMP_C = (-0.62, TOP + 0.77, MAST_Z + 0.55)
cyl(G_MAST, (LAMP_C[0], TOP + 0.6, LAMP_C[2]), 0.17, 0.12, PAL['graphite'], segs=12, name='lamp_base')
sphere(G_MAST, LAMP_C, 0.16, PAL['lens_cyan'], subdiv=2, name='lamp_lens')
# antenna
cyl(G_MAST, (0.65, TOP + 0.95, MAST_Z - 0.55), 0.025, 0.8, PAL['steel_lt'], segs=6, name='antenna', bevel=0)
sphere(G_MAST, (0.65, TOP + 1.37, MAST_Z - 0.55), 0.06, PAL['white'], subdiv=1, name='antenna_tip')
# He-3 tank (left side) + cabinet
TX, TZ = -1.72, -0.15
cyl(G_MAST, (TX, DECK + 1.15, TZ), 0.56, 1.9, PAL['white'], segs=16, name='tank', bevel=0.0)
sphere(G_MAST, (TX, DECK + 2.1, TZ), 0.56, PAL['white'], subdiv=2, scale=(1, 0.55, 1), name='tank_top', sharp=60)
cyl(G_MAST, (TX, DECK + 0.12, TZ), 0.62, 0.24, PAL['graphite'], segs=16, name='tank_saddle')
cyl(G_MAST, (TX, DECK + 2.5, TZ), 0.1, 0.14, PAL['steel_lt'], segs=8, name='tank_valve')
beam(G_MAST, (TX + 0.45, DECK + 1.9, TZ), (-MH, DECK + 1.9, TZ), 0.09, 0.09, PAL['steel_lt'], name='pipe')
box(G_MAST, (0.9, 0.95, 0.6), (-1.6, DECK + 0.475, 1.35), PAL['graphite2'], bevel=0.05, name='cabinet')
box(G_MAST, (0.7, 0.62, 0.03), (-1.6, DECK + 0.55, 1.66), PAL['pale'], bevel=0.01, name='cabinet_door')
box(G_MAST, (0.22, 0.05, 0.04), (-1.6, DECK + 0.72, 1.69), PAL['graphite'], bevel=0.0, name='cabinet_handle')
hazard(G_MAST, Vector((-2.05, DECK + 0.06, 1.655)), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.9, 0.14, stripe=0.12)

# Helium-3 glow strips (own node)
G_HE = 'HeliumStrip'
for sx in (-1, 1):
    box(G_HE, (0.05, 6.6, 0.03), (sx * MH, (TOP + y_lo) / 2 + 0.2, MAST_Z + MH + 0.1), PAL['cyan'], mat=M_CYAN, bevel=0, name='he_strip')
for yy in (DECK + 0.65, DECK + 1.55):
    tube(G_HE, (TX, yy, TZ), 0.585, 0.54, 0.08, PAL['cyan'], segs=16, name='he_ring', mat=M_CYAN)
box(G_HE, (0.5, 0.06, 0.02), (-1.6, DECK + 0.8, 1.665), PAL['cyan'], mat=M_CYAN, bevel=0, name='he_cab')

# ---------------- Carriage (slides on the rails)
G_CAR = 'Carriage'
CAR_Y = 5.4
CZ = AX[1]
box(G_CAR, (1.25, 1.1, 0.16), (0, CAR_Y + 0.25, MAST_Z + MH + 0.27), PAL['steel'], bevel=0.03, name='car_plate')
box(G_CAR, (1.05, 0.95, 0.85), (0, CAR_Y + 0.35, CZ + 0.02), PAL['white'], bevel=0.09, name='motor')
box(G_CAR, (1.1, 0.12, 0.9), (0, CAR_Y + 0.86, CZ + 0.02), PAL['graphite'], bevel=0.03, name='motor_cap')
for k in range(4):
    box(G_CAR, (0.06, 0.16, 0.7), (-0.33 + k * 0.22, CAR_Y + 1.0, CZ + 0.02), PAL['graphite2'], bevel=0.0, name='fin')
cyl(G_CAR, (0, CAR_Y - 0.17, CZ), 0.34, 0.2, PAL['graphite'], segs=14, name='gearbox')
cyl(G_CAR, (0.62, CAR_Y + 0.35, CZ + 0.02), 0.22, 0.32, PAL['steel_lt'], axis='x', segs=12, name='motor_side')
hazard(G_CAR, Vector((-0.5, CAR_Y - 0.05, CZ + 0.46)), (1, 0, 0), (0, 1, 0), (0, 0, 1), 1.0, 0.18, stripe=0.14)
box(G_CAR, (0.6, 0.07, 0.02), (0, CAR_Y + 0.5, CZ + 0.455), PAL['cyan'], mat=M_CYAN, bevel=0, name='motor_glow')
box(G_CAR, (0.3, 0.22, 0.02), (0.22, CAR_Y + 0.3, CZ + 0.455), PAL['graphite'], bevel=0, name='motor_vent')
for sx in (-1, 1):   # rail shoes
    box(G_CAR, (0.24, 0.5, 0.14), (sx * 0.42, CAR_Y + 0.25, MAST_Z + MH + 0.12), PAL['graphite'], bevel=0.02, name='shoe')
# hose from motor to mast (static-looking loop)
beam(G_CAR, (-0.5, CAR_Y + 0.6, CZ - 0.2), (-0.7, CAR_Y + 0.8, MAST_Z + MH + 0.25), 0.08, 0.08, PAL['graphite'], name='hose')

# ---------------- Bit (spins)
G_BIT = 'Bit'
BIT_TOP = CAR_Y - 0.27
TIP = DECK + 0.2
cyl(G_BIT, (AX[0], BIT_TOP - 0.15, AX[1]), 0.17, 0.3, PAL['steel'], segs=8, name='coupling')
for k in range(2):
    cyl(G_BIT, (AX[0], BIT_TOP - 1.0 - k * 1.1, AX[1]), 0.135, 0.12, PAL['amber'] if k == 0 else PAL['graphite'], segs=8, name='rod_joint', bevel=0.0)
cyl(G_BIT, (AX[0], (BIT_TOP - 0.3 + 2.6) / 2, AX[1]), 0.095, BIT_TOP - 0.3 - 2.6, PAL['steel_lt'], segs=8, name='rod', bevel=0)
cyl(G_BIT, (AX[0], (2.65 + TIP + 0.25) / 2, AX[1]), 0.15, 2.65 - TIP - 0.25, PAL['steel_lt'], segs=10, name='core', bevel=0)
auger(G_BIT, AX, TIP + 0.3, 2.6, 0.13, 0.4, 0.62, 0.07, PAL['steel_lt'])
cyl(G_BIT, (AX[0], TIP + 0.14, AX[1]), 0.3, 0.28, PAL['graphite'], segs=10, r2=0.06, name='tip', bevel=0)
# carbide teeth on the flight end
for k in range(3):
    a = 2 * math.pi * k / 3
    box(G_BIT, (0.1, 0.12, 0.1), (AX[0] + 0.34 * math.cos(a), TIP + 0.3, AX[1] + 0.34 * math.sin(a)), PAL['amber'], bevel=0.0, name='tooth')

# ---------------- Hopper (right side) with conveyor and chute
G_HOP = 'Hopper'
HX, HZ = 1.85, -0.35
HY0, HY1 = 2.45, 3.6
frustum_shell(G_HOP, (HX, HZ), HY0, HY1, 0.32, 0.78, 0.07, PAL['white'])
box(G_HOP, (1.62, 0.1, 1.62), (HX, HY1 + 0.03, HZ), PAL['graphite'], bevel=0.02, name='rim') if False else None
for sx, sz in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
    beam(G_HOP, (HX + sx * 0.55, DECK, HZ + sz * 0.55), (HX + sx * 0.62, HY1 - 0.35, HZ + sz * 0.62), 0.12, 0.12, PAL['steel'], name='hop_leg')
for y in (1.35,):
    for (a, b) in (((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
        beam(G_HOP, (HX + a[0] * 0.57, y, HZ + a[1] * 0.57), (HX + b[0] * 0.57, y, HZ + b[1] * 0.57), 0.08, 0.08, PAL['graphite2'], name='hop_brace')
# rim trim (4 beams)
for (a, b) in (((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
    beam(G_HOP, (HX + a[0] * 0.8, HY1 + 0.03, HZ + a[1] * 0.8), (HX + b[0] * 0.8, HY1 + 0.03, HZ + b[1] * 0.8), 0.1, 0.1, PAL['graphite'], name='hop_rim')
# hazard band on the sloped front face of the hopper
front_bot = Vector((HX, HY0, HZ + 0.32)); front_top = Vector((HX, HY1, HZ + 0.78))
vdir = (front_top - front_bot).normalized(); slope_len = (front_top - front_bot).length
nrm = Vector((0, -vdir.z, vdir.y)) * -1
nrm = Vector((0, -vdir.z, vdir.y)) if Vector((0, -vdir.z, vdir.y)).z > 0 else Vector((0, vdir.z, -vdir.y))
band_h = 0.26; t0 = slope_len - band_h - 0.04
w_at = 0.32 + (0.78 - 0.32) * (t0 / slope_len)
hazard(G_HOP, front_bot + vdir * t0 + Vector((-w_at + 0.06, 0, 0)) + nrm * 0.004, (1, 0, 0), vdir, nrm, 2 * w_at - 0.12, band_h, stripe=0.16)
# discharge spout + chute to the right
box(G_HOP, (0.42, 0.32, 0.42), (HX, HY0 - 0.12, HZ), PAL['graphite'], bevel=0.03, name='spout')
beam(G_HOP, (HX + 0.15, HY0 - 0.25, HZ), (HX + 1.25, 1.35, HZ), 0.46, 0.08, PAL['steel'], name='chute')
for sz in (-1, 1):
    beam(G_HOP, (HX + 0.15, HY0 - 0.12, HZ + sz * 0.24), (HX + 1.25, 1.48, HZ + sz * 0.24), 0.05, 0.22, PAL['white'], name='chute_side')
# inclined conveyor from collar to hopper
c0 = (AX[0] + 0.55, DECK + 0.75, AX[1] - 0.05); c1 = (HX - 0.55, HY1 + 0.15, HZ + 0.25)
beam(G_HOP, c0, c1, 0.42, 0.12, PAL['graphite'], name='conveyor')
a, b, L, R = basis_from(c0, c1)
side = R.col[1]  # blender-space side vector
for s in (-1, 1):
    off = side * (0.23 * s)
    p0 = Vector(c0) + Vector((off.x, off.z, -off.y)) + Vector((0, 0.06, 0)); p1 = Vector(c1) + Vector((off.x, off.z, -off.y)) + Vector((0, 0.06, 0))
    beam(G_HOP, tuple(p0), tuple(p1), 0.05, 0.14, PAL['amber'], name='conv_rail')
# conveyor support leg
beam(G_HOP, (1.0, DECK, 0.45), ((c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2 - 0.08, (c0[2] + c1[2]) / 2), 0.1, 0.1, PAL['steel'], name='conv_leg')
# hopper lamp post, housing and dark lens
HL_C = (HX + 0.7, HY1 + 0.42, HZ + 0.7)
cyl(G_HOP, (HL_C[0], HY1 + 0.16, HL_C[2]), 0.05, 0.3, PAL['steel_lt'], segs=6, name='hl_post', bevel=0)
cyl(G_HOP, (HL_C[0], HY1 + 0.3, HL_C[2]), 0.13, 0.08, PAL['graphite'], segs=10, name='hl_base')
sphere(G_HOP, HL_C, 0.12, PAL['lens_amber'], subdiv=2, name='hl_lens')

# ---------------- OreFill (rides up and down inside the hopper)
G_ORE = 'OreFill'
FILL_TOP_HALF = 0.70
bm = bmesh.new()
N = 6
grid = {}
for i in range(N + 1):
    for j in range(N + 1):
        x = -FILL_TOP_HALF + 2 * FILL_TOP_HALF * i / N
        z = -FILL_TOP_HALF + 2 * FILL_TOP_HALF * j / N
        edge = min(i, j, N - i, N - j)
        hmax = 0.32
        h = 0.0 if edge == 0 else hmax * (1 - ((x / FILL_TOP_HALF) ** 2 + (z / FILL_TOP_HALF) ** 2) * 0.5) + random.uniform(-0.03, 0.03)
        grid[i, j] = bm.verts.new(G(HX + x, h, HZ + z))
for i in range(N):
    for j in range(N):
        bm.faces.new((grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]))
bot = [bm.verts.new(G(HX + sx * FILL_TOP_HALF, -0.25, HZ + sz * FILL_TOP_HALF)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
finish_bm(bm, 'ore_heap', G_ORE, PAL['rock'], M_BODY, 0.0, sharp_deg=10, grad=0.35)
for k in range(11):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(0.1, 0.5)
    x, z = r * math.cos(a), r * math.sin(a)
    hh = 0.32 * (1 - ((x / FILL_TOP_HALF) ** 2 + (z / FILL_TOP_HALF) ** 2) * 0.5)
    he3 = k % 3 == 0
    sphere(G_ORE, (HX + x, hh + 0.02, HZ + z), random.uniform(0.11, 0.17),
           PAL['cyan'] if he3 else (PAL['platinum'] if k % 3 == 1 else PAL['rock_dk']),
           mat=M_CYAN if he3 else M_BODY, subdiv=0, jitter=0.15, name='chunk', sharp=0)

# ---------------- lamp bulbs (animated by scale)
G_SL = 'StatusLamp'; sphere(G_SL, LAMP_C, 0.175, PAL['cyan'], mat=M_CYAN, subdiv=2, name='status_bulb')
G_HL = 'HopperLamp'; sphere(G_HL, HL_C, 0.135, PAL['amber'], mat=M_AMBER, subdiv=2, name='hopper_bulb')

# ================================================================= vertex colours + join
def colourise(ob):
    me = ob.data
    col = hex2rgb(ob['col']); grad = ob['grad']
    if me.materials and me.materials[0].name.startswith('M_Glow'):
        col, grad = (1.0, 1.0, 1.0), 0.0          # glow parts: keep base colour pure
    zs = [v.co.z for v in me.vertices]
    z0, z1 = min(zs), max(zs); span = max(z1 - z0, 1e-4)
    attr = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for li, loop in enumerate(me.loops):
        z = me.vertices[loop.vertex_index].co.z
        t = (z - z0) / span
        g = (1 - grad) + grad * t                     # soft per-part gradient (darker at its base)
        if grad > 0: g *= 0.9 + 0.1 * min(max(z / 9.5, 0), 1)      # gentle whole-rig gradient
        if z < 0.35 and grad > 0 and col != (1.0, 1.0, 1.0): g *= 0.85 + 0.15 * (z / 0.35)   # contact AO near the ground
        attr.data[li].color_srgb = (col[0] * g, col[1] * g, col[2] * g, 1.0)
    me.color_attributes.active_color = attr

def join_group(name):
    obs = PARTS[name]
    for ob in obs: colourise(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs: ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.data.name = name
    return ob

def place(ob, origin_game, parent, parent_origin_game=(0, 0, 0)):
    o = G(*origin_game)
    ob.data.transform(Matrix.Translation(-o))
    ob.location = o - G(*parent_origin_game)
    ob.parent = parent
    return ob

def empty(name, loc_game, parent=None, parent_loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); scene.collection.objects.link(e)
    e.location = G(*loc_game) - G(*parent_loc); e.parent = parent
    e.empty_display_size = 0.5
    return e

ROOT = empty('DrillRig', (0, 0, 0))
RIG = empty('Rig', (0, 0, 0), ROOT)
base = place(join_group('Base'), (0, 0, 0), ROOT)
mast = place(join_group('Mast'), (0, 0, 0), RIG)
he = place(join_group('HeliumStrip'), (0, 0, 0), RIG)
CAR_O = (AX[0], CAR_Y, AX[1])
car = place(join_group('Carriage'), CAR_O, RIG)
BIT_O = (AX[0], BIT_TOP, AX[1])
bit = place(join_group('Bit'), BIT_O, car, CAR_O)
hop = place(join_group('Hopper'), (HX, 0, HZ), RIG)
FILL_FULL_Y = HY1 - 0.08
ORE_O = (HX, 0, HZ)
ore = place(join_group('OreFill'), ORE_O, hop, (HX, 0, HZ))
sl = place(join_group('StatusLamp'), LAMP_C, RIG)
hl = place(join_group('HopperLamp'), HL_C, hop, (HX, 0, HZ))

# ore level helpers: heap sits at y (local to hopper) with xz scale matching interior width
def ore_pose(level):   # level 0..1 (1 = heaped full)
    y = HY0 + 0.2 + (FILL_FULL_Y - HY0 - 0.2) * level
    inner_half = (0.32 - 0.07) + ((0.78 - 0.07) - (0.32 - 0.07)) * (y - HY0) / (HY1 - HY0)
    s = max(min(inner_half / FILL_TOP_HALF, 1.0), 0.3)
    return Vector((0, 0, y)), Vector((s, s, 0.6 + 0.4 * level))

# ================================================================= animation clips
REST = {o.name: (o.location.copy(), o.rotation_euler.copy(), o.scale.copy()) for o in (RIG, car, bit, sl, hl, ore)}

def fc(action, path, idx, keys, interp='LINEAR', group=None):
    f = action.fcurves.new(path, index=idx)
    f.keyframe_points.add(len(keys))
    for k, (fr, val) in enumerate(keys):
        p = f.keyframe_points[k]; p.co = (fr, val); p.interpolation = interp
    return f

def clip(obj, clip_name, frames, loc=None, rot=None, scl=None, interp='LINEAR'):
    """loc/rot/scl: functions t(0..1) -> 3-tuple offsets/abs values; sampled each frame."""
    act = bpy.data.actions.new(f'{obj.name}_{clip_name}')
    L0, R0, S0 = REST[obj.name]
    rng = range(frames + 1)
    for path, fn, base in (('location', loc, L0), ('rotation_euler', rot, R0), ('scale', scl, S0)):
        for i in range(3):
            if fn is None:
                keys = [(0, base[i]), (frames, base[i])]
            else:
                keys = [(f, fn(f / frames)[i] + (base[i] if path != 'scale' else 0)) for f in rng]
            fc(act, path, i, keys, interp if (fn is not None and path == 'scale' and interp == 'CONSTANT') else 'LINEAR')
    if obj.animation_data is None: obj.animation_data_create()
    tr = obj.animation_data.nla_tracks.new(); tr.name = clip_name
    st = tr.strips.new(clip_name, 0, act); st.name = clip_name
    return act

TAU = 2 * math.pi
ORE_IDLE = ore_pose(0.62); ORE_FULL = ore_pose(1.0)
def ore_loc(p): return lambda t: (p[0].x - REST['OreFill'][0].x, p[0].y - REST['OreFill'][0].y, p[0].z - REST['OreFill'][0].z)
def ore_scl(p): return lambda t: tuple(p[1])
ZERO = lambda t: (0, 0, 0)
ONE = lambda t: (1, 1, 1)
OFF = lambda t: (0.8, 0.8, 0.8)

ORDER = ['full', 'dig', 'idle']   # idle pushed last = top track = rest pose
for name in ORDER:
    if name == 'idle':
        n = 60
        clip(RIG, name, n, loc=ZERO, rot=ZERO)
        clip(car, name, n, loc=ZERO)
        clip(bit, name, n, rot=lambda t: (0, 0, -TAU * t))          # 1 slow turn / 2 s
        clip(sl, name, n, scl=lambda t: (1.0 + 0.12 * math.sin(TAU * t),) * 3)   # soft pulse
        clip(hl, name, n, scl=OFF)
        clip(ore, name, n, loc=ore_loc(ORE_IDLE), scl=ore_scl(ORE_IDLE))
    elif name == 'dig':
        n = 30
        clip(RIG, name, n, loc=lambda t: (0.012 * math.sin(TAU * 7 * t), 0.009 * math.sin(TAU * 11 * t + 1), 0),
             rot=lambda t: (0.0016 * math.sin(TAU * 9 * t), 0.0012 * math.sin(TAU * 5 * t + 0.5), 0))
        clip(car, name, n, loc=lambda t: (0, 0, -0.28 * (1 - math.cos(TAU * t)) / 2))
        clip(bit, name, n, rot=lambda t: (0, 0, -TAU * 3 * t))      # 3 fast turns / 1 s
        clip(sl, name, n, scl=lambda t: (1.0 + 0.15 * math.sin(TAU * 2 * t),) * 3)
        clip(hl, name, n, scl=OFF)
        clip(ore, name, n, loc=ore_loc(ORE_IDLE), scl=ore_scl(ORE_IDLE))
    else:   # full
        n = 30
        clip(RIG, name, n, loc=ZERO, rot=ZERO)
        clip(car, name, n, loc=ZERO)
        clip(bit, name, n, rot=ZERO)                                # stopped
        clip(sl, name, n, scl=OFF)                                  # status lamp dark
        clip(hl, name, n, scl=lambda t: (1.15,) * 3 if (t < 0.5 or t >= 1.0) else (0.8,) * 3, interp='CONSTANT')
        clip(ore, name, n, loc=ore_loc(ORE_FULL), scl=ore_scl(ORE_FULL))

for o in (RIG, car, bit, sl, hl, ore):
    o.animation_data.action = None

# ================================================================= export
def export_nodes():
    bpy.ops.object.select_all(action='DESELECT')
    for o in [ROOT] + list(ROOT.children_recursive): o.select_set(True)

scene.frame_set(0)
if GLB:
    export_nodes()
    kw = dict(filepath=GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
              export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
              export_optimize_animation_size=False, export_materials='EXPORT', export_cameras=False,
              export_lights=False, export_extras=False, export_texcoords=False, export_normals=True,
              export_frame_range=False, export_anim_slide_to_zero=True,
              export_optimize_animation_keep_anim_object=True)
    try:
        bpy.ops.export_scene.gltf(export_vertex_color='MATERIAL', **kw)
    except TypeError:
        bpy.ops.export_scene.gltf(export_colors=True, **kw)
    print('EXPORTED', GLB)

# ================================================================= render-only props (not exported)
def build_stage():
    grp = 'Stage'
    # ground
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
    me = bpy.data.meshes.new('Ground'); bm.to_mesh(me); bm.free()
    g = bpy.data.objects.new('Ground', me); scene.collection.objects.link(g)
    m = bpy.data.materials.new('M_Ground'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 0.6
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = srgb2lin(hex2rgb('#7f7d7b')) + (1,)
    ramp.color_ramp.elements[1].color = srgb2lin(hex2rgb('#9a9896')) + (1,)
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95
    me.materials.append(m)
    # rocks + small craters
    rockm = mat_body('M_Rock', 0.95)
    random.seed(3)
    stage = []
    for k in range(14):
        a = random.uniform(0, TAU); r = random.uniform(5.5, 13)
        sz = random.uniform(0.15, 0.6)
        ob = sphere(grp, (r * math.cos(a), sz * 0.25, r * math.sin(a)), sz, '#76736f', mat=rockm, subdiv=1, jitter=0.25,
                    scale=(1, 0.6, 1.2), name='rock', sharp=0)
        stage.append(ob)
    # 1.8 m astronaut scale reference
    suit = mat_body('M_Suit', 0.6)
    AXp, AZp = 3.9, 2.6
    parts = [
        cyl(grp, (AXp - 0.12, 0.42, AZp), 0.11, 0.84, '#e8edf5', segs=10, mat=suit, name='legL'),
        cyl(grp, (AXp + 0.12, 0.42, AZp), 0.11, 0.84, '#e8edf5', segs=10, mat=suit, name='legR'),
        box(grp, (0.26, 0.12, 0.34), (AXp - 0.12, 0.06, AZp + 0.04), '#3a4258', mat=suit, bevel=0.03, name='bootL'),
        box(grp, (0.26, 0.12, 0.34), (AXp + 0.12, 0.06, AZp + 0.04), '#3a4258', mat=suit, bevel=0.03, name='bootR'),
        box(grp, (0.56, 0.62, 0.36), (AXp, 1.14, AZp), '#e8edf5', mat=suit, bevel=0.08, name='torso'),
        box(grp, (0.46, 0.6, 0.24), (AXp, 1.18, AZp - 0.28), '#c9d3e6', mat=suit, bevel=0.05, name='pack'),
        cyl(grp, (AXp - 0.36, 1.12, AZp), 0.08, 0.56, '#e8edf5', segs=8, mat=suit, name='armL'),
        cyl(grp, (AXp + 0.36, 1.12, AZp), 0.08, 0.56, '#e8edf5', segs=8, mat=suit, name='armR'),
        box(grp, (0.5, 0.06, 0.36), (AXp, 0.86, AZp), '#e8701a', mat=suit, bevel=0.01, name='belt'),
        sphere(grp, (AXp, 1.6, AZp), 0.2, '#e8edf5', mat=suit, subdiv=2, name='helmet'),
        sphere(grp, (AXp, 1.6, AZp + 0.06), 0.165, '#1a1f2b', mat=suit, subdiv=2, scale=(1, 0.8, 1), name='visor'),
    ]
    for ob in parts + stage + [o for o in PARTS.get('Stage', []) if o not in parts and o not in stage]:
        pass
    for ob in PARTS.get('Stage', []): colourise(ob)
    # sun (hard shadow) + world
    sun_d = bpy.data.lights.new('Sun', 'SUN'); sun_d.energy = 4.2; sun_d.angle = math.radians(0.4)
    sun_d.color = srgb2lin(hex2rgb('#fff4e4'))
    sun = bpy.data.objects.new('Sun', sun_d); scene.collection.objects.link(sun)
    src = G(-0.55, 0.78, 0.6).normalized()
    sun.rotation_euler = (-src).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('W'); scene.world = w; w.use_nodes = True
    wn = w.node_tree; bg = wn.nodes['Background']
    lp = wn.nodes.new('ShaderNodeLightPath'); mix = wn.nodes.new('ShaderNodeMixRGB')
    mix.inputs['Color1'].default_value = srgb2lin(hex2rgb('#5a6680')) + (1,)   # ambient fill
    mix.inputs['Color2'].default_value = srgb2lin(hex2rgb('#0b1222')) + (1,)   # visible sky
    wn.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac']); wn.links.new(mix.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.55

def look(cam, target_game, pos_game):
    t, p = G(*target_game), G(*pos_game)
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()

def set_clip(name, frame):
    for o in (RIG, car, bit, sl, hl, ore):
        for tr in o.animation_data.nla_tracks:
            tr.mute = (tr.name != name)
    scene.frame_set(frame)

if RENDER:
    os.makedirs(RENDER, exist_ok=True)
    build_stage()
    camd = bpy.data.cameras.new('Cam'); camd.lens = 50
    cam = bpy.data.objects.new('Cam', camd); scene.collection.objects.link(cam); scene.camera = cam
    r = scene.render; r.engine = 'CYCLES'
    scene.cycles.device = 'CPU'; scene.cycles.samples = int(arg('--samples', '48')); scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    r.image_settings.file_format = 'PNG'
    TGT = (0.2, 4.3, 0.0)
    shots = []
    for k in range(8):
        a = math.radians(k * 45); e = math.radians(16); d = 21
        shots.append((f'turn_{k * 45:03d}', TGT, (TGT[0] + d * math.sin(a) * math.cos(e), TGT[1] + d * math.sin(e), TGT[2] + d * math.cos(a) * math.cos(e)), 800, 800, 'idle', 0, 50))
    shots.append(('closeup', (0.5, 2.4, 0.3), (4.6, 4.6, 8.6), 1600, 800, 'idle', 0, 50))
    shots.append(('pose_dig', TGT, (11, 7.5, 17), 800, 800, 'dig', 15, 50))
    shots.append(('pose_full', (1.5, 3.0, 0.0), (8.5, 7.5, 9.5), 800, 800, 'full', 3, 50))
    only = arg('--only')
    for name, tgt, pos, w_, h_, cl, fr, lens in shots:
        if only and name not in only.split(','): continue
        r.resolution_x, r.resolution_y = w_, h_
        camd.lens = lens if name != 'closeup' else 32
        look(cam, tgt, pos); set_clip(cl, fr)
        r.filepath = os.path.join(RENDER, name + '.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', name)
    set_clip('idle', 0)

if BLEND:
    for o in (RIG, car, bit, sl, hl, ore):
        for tr in o.animation_data.nla_tracks: tr.mute = False
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    print('SAVED', BLEND)
