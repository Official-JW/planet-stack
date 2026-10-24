"""CV-3 box bridge for the Refinery (separate GLB: refinery_bridge.glb), v2 (10/24 Director review of 1fdee46).
A Warren-truss gantry crossing the RD-1 haul trails (outbound z 0, U-turn, inbound z 9) and the eastbound flatbed lane (z 13) on a
32 deg diagonal. It carries an enclosed box conveyor from the clad south lift tower (process side, screen centre) to an OPEN lowerator
frame in the flatbed median (screen right, toward the Cargo Dock), which lowers each HELIUM-3 box, turns it to yaw 0 and rolls it west
down a tip-down chute onto a pickup table in the median, inside RC-1 reach (r 9.3 m, theta 0); the crane drops it on FB-05.
The whole bridge stays outside the RC-1 slew envelope (jib tip r 11.25 around (311, 17.5) world): nearest part above y 3 is 12.39 m away; only the low pickup table, chute, lamp (y 2.53) and control box sit inside it.
Concept B: white panels, graphite structure, cyan light strips, panel lines, light weathering.
blender -b -P build_bridge.py -- OUT_RAW.glb [--box BOX_PLAIN.glb]
  BOX_PLAIN = art/3d/props/cargo_box/cargo_box_game.glb unpacked with `gltfpack -noq -kn -ke` (the existing HELIUM-3 crate is reused as-is).
Coordinates: glTF metres. 'Span frame' (x' across, y, z' along the span, south -> north) is built with the v1 code and mapped into the
GLB frame by a reflection (+x' -> camera side n, +z' -> span direction d); median parts are built directly in the GLB frame (= Refinery
axes, origin ROOT)."""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix, Euler, Quaternion
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'props', '_shared_src'))
from propgeo import MB, P, lin, empty, export
A = sys.argv[sys.argv.index('--') + 1:]
OUT = A[0]
def arg(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
BOX_PLAIN = arg('box', '/tmp/cargo_box_plain.glb')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30

# ---------------------------------------------------------------- layout (Refinery coords: origin Truck_Dump; world = Refinery + (320, 0, 0))
PHI = math.radians(32.0)            # span yaw off the Refinery z axis (Director: 30-40 deg)
DV = (math.sin(PHI), math.cos(PHI))  # span direction d (x, z), south tower -> lowerator
NV = (-math.cos(PHI), math.sin(PHI)) # +x' (conveyor / light side) -> camera side n
CX = 0.45                           # conveyor centre line x' (walkway on -x', away from the camera)
NT_REF = (7.0, 17.5)                # lowerator centre (flatbed median z 15.8..19.2, world x 327)
S_Z = -5.6                          # south tower centre z (outbound lane toe z -2.8; rotated footing reaches z -2.91)
TZ = (NT_REF[1] - CX * NV[1] - S_Z) / (2 * DV[1])        # half distance between the tower centres along the span
M_REF = (NT_REF[0] - CX * NV[0] - TZ * DV[0], NT_REF[1] - CX * NV[1] - TZ * DV[1])   # span midpoint
ROOT = (round(M_REF[0], 2), 0.0, round(M_REF[1], 2))     # GLB root in Refinery coords (yaw 0)
MO = (M_REF[0] - ROOT[0], M_REF[1] - ROOT[2])            # span midpoint in the GLB frame
TH = 1.55                           # south tower half width; truss half width
THN = 1.4                           # lowerator half width (footing 3.2 m fits the 3.4 m median)
UND = 7.2                           # truss underside (HT-04 bed fully up = 5.75 m, + 1 m = 6.75 -> 0.45 m extra)
BC_T = 7.5; DECK = 7.6; RTOP = 8.1; TC = 10.4
SPAN0, SPAN1 = -(TZ - TH), TZ - 0.42                      # truss ends: south tower face .. inside the lowerator frame
NT = (NT_REF[0] - ROOT[0], NT_REF[1] - ROOT[2])           # lowerator centre, GLB frame
PICK_REF = (0.3, 1.0, 17.5)                               # pickup table box Base (median, crane-local (9.3, 1.0, 0))
PICK = (PICK_REF[0] - ROOT[0], PICK_REF[1], PICK_REF[2] - ROOT[2])
LOW_Y = 1.42                                              # box Base at the lowerator bottom (turntable)
WHITE, WHITE2, GRAPH, GRAPH2, GRAPH1, STEEL, SATIN = P['white'], P['white2'], P['graph'], P['graph2'], P['graph1'], P['steel'], P['satin']
AMBER, CYAN = P['amber'], P['cyan']
CONC = lin('#8e9196'); CONC2 = lin('#777a7f'); GRATE = lin('#4a5160')

def B(v): return Vector((v[0], -v[2], v[1]))
def SP(p):  # span frame (x', y, z') -> GLB frame (glTF)
    x, y, z = p
    return (MO[0] + x * NV[0] + z * DV[0], y, MO[1] + x * NV[1] + z * DV[1])
XF = {'span': False, 'tm': None}
def _xf_b(v):   # Blender-space vertex built in the span frame -> GLB frame (Blender space)
    gx, gy, gz = v.x, v.z, -v.y
    if XF['tm'] is not None: gz = 2 * XF['tm'] - gz       # text: local mirror first, so reflection o mirror = rotation (text reads right)
    return B(SP((gx, gy, gz)))
class G(MB):
    """MB with glTF-space helpers and the span-frame reflection"""
    def _add(self, verts, faces, col, mat, bone):
        if XF['span']:
            verts = [_xf_b(Vector(v)) for v in verts]
            if XF['tm'] is None: faces = [tuple(reversed(list(f))) for f in faces]
        MB._add(self, verts, faces, col, mat, bone)
    def text(self, body, size, loc, rot, col, mat=1, bone='root', res=1, align='CENTER'):
        if XF['span']: XF['tm'] = -Vector(loc).y
        MB.text(self, body, size, loc, rot, col, mat=mat, bone=bone, res=res, align=align)
        XF['tm'] = None
    def gbox(self, size, c, col, mat=0, bone='root', rot_y=0.0):
        self.box((size[0], size[2], size[1]), B(c), col, rot=(0, 0, -rot_y), mat=mat, bone=bone)
    def gseg(self, p0, p1, w, h, col, mat=0, bone='root'):
        a, b = B(p0), B(p1); d = b - a; L = d.length
        if L < 1e-6: return
        q = d.to_track_quat('X', 'Z'); self.box((L, w, h), (a + b) / 2, col, rot=q.to_euler(), mat=mat, bone=bone)
    def gcyl(self, p0, p1, r, col, segs=8, mat=0, bone='root', caps=True):
        self.cyl(B(p0), B(p1), r, col, segs=segs, mat=mat, bone=bone, caps=caps)
    def gquad(self, pts, col, mat=0, bone='root'):
        self.quad([B(p) for p in pts], col, mat=mat, bone=bone)

S = G()   # static (Bridge_Static: SHM_Paint + SHM_GlowCyan)
M = G()   # moving, skinned (Bridge_Moving: rollers + 3 boxes)

# ================================================================ SPAN FRAME (south tower, truss, infeed)
XF['span'] = True
def south_tower(zc):
    S.gbox((3.9, 0.22, 3.9), (0, 0.11, zc), CONC)
    S.gbox((3.5, 0.12, 3.5), (0, 0.28, zc), CONC2)
    top = 11.05
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (TH - 0.12), zc + sz * (TH - 0.12)
            S.gbox((0.5, 0.06, 0.5), (x, 0.37, z), STEEL)
            S.gbox((0.26, top - 0.4, 0.26), (x, 0.4 + (top - 0.4) / 2, z), GRAPH)
    def wall_x(sx, openings):
        x = sx * (TH - 0.05); z0, z1 = zc - TH + 0.13, zc + TH - 0.13
        spans = []; y0 = 0.4
        for (oy0, oy1, oz0, oz1) in openings:
            spans.append((y0, oy0, z0, z1)); spans.append((oy0, oy1, z0, oz0)); spans.append((oy0, oy1, oz1, z1)); y0 = oy1
        spans.append((y0, top - 0.25, z0, z1))
        for (a, b, c, d) in spans:
            if b - a > 0.01 and d - c > 0.01: S.gbox((0.08, b - a, d - c), (x, (a + b) / 2, (c + d) / 2), WHITE)
    def wall_z(sz, openings):
        z = zc + sz * (TH - 0.05); x0, x1 = -TH + 0.13, TH - 0.13
        y0 = 0.4; spans = []
        for (oy0, oy1, ox0, ox1) in openings:
            spans.append((y0, oy0, x0, x1)); spans.append((oy0, oy1, x0, ox0)); spans.append((oy0, oy1, ox1, x1)); y0 = oy1
        spans.append((y0, top - 0.25, x0, x1))
        for (a, b, c, d) in spans:
            if b - a > 0.01 and d - c > 0.01: S.gbox((d - c, b - a, 0.08), ((c + d) / 2, (a + b) / 2, z), WHITE)
    wall_z(1, [(RTOP - 0.1, RTOP + 1.75, CX - 0.85, CX + 0.85)]); wall_z(-1, [(0.85, 2.6, CX - 0.85, CX + 0.85)])
    wall_x(1, []); wall_x(-1, [])
    S.gbox((2 * TH + 0.2, 0.18, 2 * TH + 0.2), (0, top - 0.16, zc), GRAPH2)
    S.gbox((2 * TH - 0.2, 0.12, 2 * TH - 0.2), (0, top - 0.01, zc), WHITE2)
    S.gbox((0.9, 0.5, 0.7), (-0.5, top + 0.3, zc), WHITE)
    S.gbox((0.92, 0.04, 0.72), (-0.5, top + 0.57, zc), GRAPH2)
    S.gcyl((0.75, top + 0.05, zc + 0.9), (0.75, top + 0.75, zc + 0.9), 0.04, GRAPH, segs=6)
    S.gbox((0.16, 0.14, 0.16), (0.75, top + 0.82, zc + 0.9), CYAN, mat=1)
    for y in (2.2, 4.0, 5.8, 9.9):     # panel lines on the camera faces (+x' and +z')
        S.gbox((0.02, 0.035, 2 * TH - 0.3), (TH + 0.003, y, zc), GRAPH2)
        S.gbox((2 * TH - 0.3, 0.035, 0.02), (0, y, zc + TH + 0.003), GRAPH2)
    S.gbox((0.02, top - 1.2, 0.035), (TH + 0.003, 0.4 + (top - 1.2) / 2, zc), GRAPH2)
    S.gbox((0.025, 3.6, 0.07), (TH + 0.012, 5.0, zc + 1.05), CYAN, mat=1)
    S.gbox((2 * TH - 0.6, 0.06, 0.025), (0, top - 0.55, zc + TH + 0.012), CYAN, mat=1)
    lz = zc - (TH + 0.3)                # ladder on the outer (-z') face
    for dx in (-0.25, 0.25): S.gbox((0.05, 7.4, 0.05), (-0.95 + dx, 0.4 + 3.7, lz), SATIN)
    for y in [0.9 + 0.6 * k for k in range(12)]: S.gbox((0.5, 0.04, 0.04), (-0.95, y, lz), SATIN)
    S.gbox((0.04, 7.3, 0.04), (-0.95, 0.4 + 3.65, lz - 0.32), SATIN)
    S.gbox((0.6, 0.9, 0.04), (0, 1.6, zc + TH + 0.02), GRAPH2)                                      # service hatch
    S.text('CV-3', 0.42, B((TH + 0.016, 6.6, zc)), (math.pi / 2, 0, math.pi / 2), CYAN, mat=1)
south_tower(-TZ)

# truss span (through Warren truss)
NP = 12; zs = [SPAN0 + (SPAN1 - SPAN0) * k / NP for k in range(NP + 1)]
SL = SPAN1 - SPAN0; SM = (SPAN0 + SPAN1) / 2
for sx in (-1, 1):
    x = sx * (TH - 0.12)
    S.gseg((x, UND + 0.15, SPAN0 - 0.1), (x, UND + 0.15, SPAN1), 0.24, 0.3, WHITE2)
    S.gseg((x, TC, SPAN0 - 0.1), (x, TC, SPAN1), 0.22, 0.24, WHITE2)
    for z in zs: S.gseg((x, BC_T, z), (x, TC - 0.12, z), 0.14, 0.14, WHITE2)
    for k in range(NP):
        za, zb = zs[k], zs[k + 1]
        if k % 2 == 0: S.gseg((x, BC_T, za), (x, TC - 0.1, zb), 0.1, 0.1, GRAPH1)
        else: S.gseg((x, TC - 0.1, za), (x, BC_T, zb), 0.1, 0.1, GRAPH1)
    S.gbox((0.02, 0.05, SL), (sx * (TH + 0.002), UND + 0.15, SM), GRAPH2)
for z in zs[1:-1]: S.gseg((-(TH - 0.12), TC, z), ((TH - 0.12), TC, z), 0.1, 0.1, GRAPH1)
n = 30; za0, za1 = SPAN0 + 0.6, SPAN1 - 0.9          # amber / graphite chevron fascia (camera side)
for k in range(n):
    z0 = za0 + (za1 - za0) * k / n; z1 = za0 + (za1 - za0) * (k + 1) / n
    S.gquad([(TH + 0.005, UND + 0.04, z0), (TH + 0.005, UND + 0.04, z1), (TH + 0.005, UND + 0.26, z1), (TH + 0.005, UND + 0.26, z0)], AMBER if k % 2 == 0 else GRAPH)
for zp in (-6.0, 4.6):                                    # clearance plates over the haul lanes
    S.gbox((0.04, 0.34, 1.5), (TH + 0.05, UND + 0.19, zp), GRAPH2)          # on the chord face: nothing hangs below y 7.2
    S.text('CLR 7.2m', 0.21, B((TH + 0.075, UND + 0.19, zp)), (math.pi / 2, 0, math.pi / 2), WHITE2, mat=0)
for z in zs: S.gseg((-(TH - 0.12), BC_T - 0.12, z), ((TH - 0.12), BC_T - 0.12, z), 0.12, 0.2, GRAPH)
S.gbox((2 * TH - 0.3, 0.1, SL), (0, DECK - 0.05, SM), GRAPH2)
S.gbox((1.05, 0.02, SL), (-0.86, DECK + 0.01, SM), GRATE)
for z in [SPAN0 + 1.0 * k for k in range(1, int(SL))]: S.gbox((1.05, 0.012, 0.03), (-0.86, DECK + 0.025, z), GRAPH)
xr = -(TH - 0.2)
S.gseg((xr, DECK + 1.05, SPAN0), (xr, DECK + 1.05, SPAN1), 0.05, 0.05, AMBER)
S.gseg((xr, DECK + 0.55, SPAN0), (xr, DECK + 0.55, SPAN1), 0.04, 0.04, SATIN)
S.gbox((0.02, 0.12, SL), (xr, DECK + 0.06, SM), AMBER)
for z in [SPAN0 + 1.5 * k for k in range(int(SL / 1.5) + 1)]: S.gbox((0.05, 1.05, 0.05), (xr, DECK + 0.525, z), SATIN)
GL, GR = CX - 0.78, CX + 0.78
for gx in (GL, GR):
    S.gbox((0.12, 0.3, SL), (gx, DECK + 0.2, SM), GRAPH)
    S.gbox((0.05, 0.5, SL), (gx + (0.06 if gx > CX else -0.06), RTOP + 0.2, SM), WHITE)
    S.gbox((0.09, 0.04, SL), (gx + (0.06 if gx > CX else -0.06), RTOP + 0.47, SM), GRAPH2)
for z in [SPAN0 + 2.0 * k + 1.0 for k in range(int(SL / 2.0))]:
    S.gbox((0.03, 0.46, 0.025), (GR + 0.09, RTOP + 0.2, z - 0.98), GRAPH2)
    S.gbox((0.05, 0.08, 0.14), (GR + 0.1, RTOP + 0.34, z), CYAN, mat=1)
S.gbox((0.025, 0.05, SL - 0.4), (GR + 0.1, RTOP + 0.06, SM), CYAN, mat=1)
S.gbox((0.3, 0.08, SL), (-0.9, UND + 0.05, SM), GRAPH1)
# south infeed stub (from the HELIUM-3 pack-out, -z')
S.gbox((1.9, 0.1, 3.4), (CX, 0.85, -TZ - TH - 1.7), GRAPH)
for dz in (-2.9, -0.7):
    for gx in (CX - 0.75, CX + 0.75): S.gbox((0.1, 0.8, 0.1), (gx, 0.4, -TZ - TH + dz), GRAPH1)
for k in range(8):
    S.gcyl((CX - 0.7, 0.93, -TZ - TH - 0.25 - k * 0.42), (CX + 0.7, 0.93, -TZ - TH - 0.25 - k * 0.42), 0.07, SATIN, segs=6, caps=False)
for gx in (CX - 0.85, CX + 0.85): S.gbox((0.05, 0.35, 3.4), (gx, 1.1, -TZ - TH - 1.7), WHITE)
S.gbox((2.2, 2.3, 1.0), (CX, 1.15, -TZ - TH - 3.7), WHITE)
S.gbox((2.24, 0.06, 1.04), (CX, 2.33, -TZ - TH - 3.7), GRAPH2)
S.gbox((1.6, 0.05, 0.02), (CX, 2.0, -TZ - TH - 3.19), CYAN, mat=1)
# span rollers (bones Roller_B##, axis n)
R_R = 0.09
ROLL = []    # (bone name, head glTF GLB frame, axis (glTF), sign)
k = 0; z = SPAN0 + 0.25
while z < SPAN1 - 0.1:
    k += 1; nme = 'Roller_B%02d' % k; ROLL.append((nme, SP((CX, RTOP - R_R, z)), (NV[0], 0.0, NV[1]), -1.0))
    M.gcyl((CX - 0.72, RTOP - R_R, z), (CX + 0.72, RTOP - R_R, z), R_R, SATIN, segs=6, bone=nme, caps=False)
    z += 1.2                     # 1.2 m pitch: always 2 rollers under a 2.4 m box; the side guards hide them from the game camera
XF['span'] = False

# ================================================================ GLB FRAME (lowerator in the median, chute, pickup table)
nx, nz = NT
def L(x, y, z): return (nx + x, y, nz + z)      # lowerator-local -> GLB frame
top = 11.05
S.gbox((3.2, 0.22, 3.2), L(0, 0.11, 0), CONC)
S.gbox((2.95, 0.12, 2.95), L(0, 0.28, 0), CONC2)
lg = THN - 0.12
for sx in (-1, 1):
    for sz in (-1, 1):
        S.gbox((0.46, 0.06, 0.46), L(sx * lg, 0.37, sz * lg), STEEL)
        S.gbox((0.26, top - 0.4, 0.26), L(sx * lg, 0.4 + (top - 0.4) / 2, sz * lg), GRAPH)
for y in (0.55, 3.2, BC_T - 0.15, top - 0.35):                # ring beams
    for sz in (-1, 1): S.gbox((2 * THN - 0.1, 0.16, 0.16), L(0, y, sz * lg), GRAPH2)
    for sx in (-1, 1): S.gbox((0.16, 0.16, 2 * THN - 0.1), L(sx * lg, y, 0), GRAPH2)
for (y0, y1) in ((0.55, 3.2), (3.2, BC_T - 0.15)):            # X-bracing on the far faces (+x and -z below the deck)
    S.gseg(L(lg, y0, -lg), L(lg, y1, lg), 0.07, 0.07, GRAPH1); S.gseg(L(lg, y1, -lg), L(lg, y0, lg), 0.07, 0.07, GRAPH1)
S.gseg(L(-lg, 3.2, -lg), L(lg, BC_T - 0.15, -lg), 0.07, 0.07, GRAPH1); S.gseg(L(-lg, BC_T - 0.15, -lg), L(lg, 3.2, -lg), 0.07, 0.07, GRAPH1)
for sx in (-1, 1):
    for sz in (-1, 1):
        S.gbox((0.06, BC_T - LOW_Y + 2.4, 0.06), L(sx * 1.06, LOW_Y + (BC_T - LOW_Y + 2.4) / 2, sz * 1.06), SATIN)   # guide rails
S.gcyl(L(0, LOW_Y - 0.22, 0), L(0, LOW_Y - 0.1, 0), 1.12, GRAPH, segs=12)                # turntable
S.gcyl(L(0, LOW_Y - 0.1, 0), L(0, LOW_Y - 0.085, 0), 1.15, CYAN, segs=12, mat=1, caps=False)
S.gbox((1.4, LOW_Y - 0.62, 1.4), L(0, 0.4 + (LOW_Y - 0.62) / 2, 0), GRAPH1)
S.gbox((2 * THN + 0.1, 1.0, 0.08), L(0, 1.0, -THN + 0.04), WHITE)                      # low skirts on the far sides (-z, +x)
S.gbox((0.08, 1.0, 2 * THN + 0.1), L(THN - 0.04, 1.0, 0), WHITE)
# head house over the deck entry: canopy + white cheeks (open toward the camera and the span)
S.gbox((0.08, 1.8, 2 * THN - 0.2), L(THN - 0.04, top - 1.3, 0), WHITE)
S.gbox((0.08, 0.7, 2 * THN - 0.2), L(-THN + 0.04, top - 0.75, 0), WHITE)
S.gbox((2 * THN - 0.2, 0.7, 0.08), L(0, top - 0.75, THN - 0.04), WHITE)
S.gbox((2 * THN + 0.2, 0.18, 2 * THN + 0.2), L(0, top - 0.16, 0), GRAPH2)
S.gbox((2 * THN - 0.2, 0.12, 2 * THN - 0.2), L(0, top - 0.01, 0), WHITE2)
S.gbox((0.9, 0.5, 0.7), L(0.4, top + 0.3, -0.2), WHITE)
S.gbox((0.92, 0.04, 0.72), L(0.4, top + 0.57, -0.2), GRAPH2)
S.gcyl(L(-0.75, top + 0.05, 0.8), L(-0.75, top + 0.75, 0.8), 0.04, GRAPH, segs=6)
S.gbox((0.16, 0.14, 0.16), L(-0.75, top + 0.82, 0.8), CYAN, mat=1)
S.gbox((0.02, 0.035, 2 * THN - 0.3), L(-THN - 0.003, 10.45, 0), GRAPH2)
S.gbox((2 * THN - 0.3, 0.035, 0.02), L(0, 10.45, THN + 0.003), GRAPH2)
for sx in (-1, 1): S.gbox((0.05, 5.5, 0.03), L(sx * lg, 4.6, lg + 0.14), CYAN, mat=1)   # cyan strips on the camera-side legs
S.gbox((2 * THN - 0.6, 0.06, 0.025), L(0, top - 0.55, THN + 0.012), CYAN, mat=1)
S.gbox((0.025, 0.06, 2 * THN - 0.6), L(-THN - 0.012, top - 0.55, 0), CYAN, mat=1)
S.text('CV-3', 0.34, B(L(-THN - 0.006, top - 0.78, 0)), (math.pi / 2, 0, -math.pi / 2), CYAN, mat=1)
lx = nx + THN + 0.3                                       # ladder on the far (+x) face, ground to the deck
for dz in (-0.25, 0.25): S.gbox((0.05, 7.4, 0.05), (lx, 0.4 + 3.7, nz + dz), SATIN)
for y in [0.9 + 0.6 * k for k in range(12)]: S.gbox((0.04, 0.04, 0.5), (lx, y, nz), SATIN)
S.gbox((0.04, 7.3, 0.04), (lx + 0.32, 0.4 + 3.65, nz), SATIN)
# tip-down chute (west, -x) + pickup table, all in the median
X0 = nx - THN                    # chute top at the lowerator's west face
XTE, XTW = PICK[0] + 1.35, PICK[0] - 1.4   # pickup table east / west ends
def chute_y(x):
    if x >= X0: return LOW_Y
    if x <= XTE: return PICK[1]
    return PICK[1] + (LOW_Y - PICK[1]) * (x - XTE) / (X0 - XTE)
zc = nz
for sz in (-1, 1):
    z = zc + sz * 0.8
    S.gseg((X0 + 0.05, LOW_Y - 0.2, z), (XTE, PICK[1] - 0.2, z), 0.1, 0.22, GRAPH)
    S.gseg((X0 + 0.05, LOW_Y + 0.22, z + sz * 0.06), (XTE, PICK[1] + 0.22, z + sz * 0.06), 0.05, 0.3, WHITE)
    S.gbox((XTE - XTW, 0.22, 0.1), ((XTE + XTW) / 2, PICK[1] - 0.2, z), GRAPH)
    S.gbox((XTE - XTW - 0.3, 0.06, 0.06), ((XTE + XTW) / 2 + 0.15, PICK[1] + 0.32, z + sz * 0.12), SATIN)
    for x in (XTW + 0.15, XTE - 0.15, (XTE + X0) / 2, X0 - 0.3):
        y = chute_y(x) - 0.3
        S.gbox((0.12, y, 0.12), (x, y / 2, z), GRAPH1)
S.gbox((0.2, 0.42, 1.7), (XTW - 0.05, PICK[1] + 0.12, zc), AMBER)                       # end stop bumper
S.gbox((0.06, 0.12, 1.72), (XTW - 0.16, PICK[1] + 0.12, zc), GRAPH)
S.gbox((X0 - XTW + 0.4, 0.12, 2.3), ((X0 + XTW) / 2, 0.06, zc), CONC)                     # slab (z 16.35..18.65, median)
S.gbox((XTE - XTW, 0.025, 0.04), ((XTE + XTW) / 2, PICK[1] - 0.12, zc + 0.86), CYAN, mat=1)
S.gseg((X0, LOW_Y - 0.02, zc + 0.86), (XTE, PICK[1] - 0.02, zc + 0.86), 0.04, 0.025, CYAN, mat=1)
S.gcyl((XTW + 0.3, 0.12, zc + 1.3), (XTW + 0.3, 2.3, zc + 1.3), 0.05, GRAPH, segs=6)       # ready lamp post
S.gbox((0.22, 0.22, 0.22), (XTW + 0.3, 2.42, zc + 1.3), CYAN, mat=1)
S.gbox((0.5, 0.7, 0.3), (XTE - 0.2, 0.75, zc + 1.3), WHITE)                               # control box
S.gbox((0.3, 0.2, 0.02), (XTE - 0.2, 0.9, zc + 1.455), CYAN, mat=1)
S.gbox((0.08, 0.6, 0.1), (XTE - 0.2, 0.25, zc + 1.3), GRAPH1)
k = 0; x = X0 - 0.15
while x > XTW + 0.1:
    k += 1; nme = 'Roller_T%02d' % k; y = chute_y(x) - R_R; ROLL.append((nme, (x, y, zc), (0.0, 0.0, 1.0), 1.0))
    M.gcyl((x, y, zc - 0.74), (x, y, zc + 0.74), R_R, SATIN, segs=6, bone=nme, caps=False)
    x -= 0.4

# ---------------------------------------------------------------- boxes: the existing HELIUM-3 cargo box, 3 copies (bones Box_1..3)
def import_box():
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=BOX_PLAIN); new = [o for o in bpy.data.objects if o not in before]
    me_ob = next(o for o in new if o.type == 'MESH'); bpy.context.view_layer.update()
    Mw = me_ob.matrix_world.copy(); me = me_ob.data
    ca = me.color_attributes[0] if me.color_attributes else None
    out = []
    for p in me.polygons:
        vs = [Mw @ me.vertices[i].co for i in p.vertices]
        if ca is not None:
            if ca.domain == 'CORNER': c = ca.data[p.loop_indices[0]].color
            else: c = ca.data[p.vertices[0]].color
            col = (c[0], c[1], c[2])
        else: col = WHITE2
        mat = 1 if (me.materials and 'Glow' in me.materials[p.material_index].name) else 0
        out.append((vs, col, mat))
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    return out
BOXF = import_box()
print('BOX FACES', len(BOXF))
for i in range(1, 4):
    for vs, col, mat in BOXF:
        M._add([v.copy() for v in vs], [list(range(len(vs)))], col, mat, 'Box_%d' % i)   # modelled at the origin, moved to rest below

S.weather(seed=21, z0=0.0, z1=3.0, amt=0.4, noise=0.05)
print('STATIC TRIS', S.tris(), 'MOVING TRIS', M.tris())

# ---------------------------------------------------------------- armature (bones point +Z: bone local axes = glTF x, y, z)
ad = bpy.data.armatures.new('Bridge_Armature'); arm = bpy.data.objects.new('Refinery_Bridge', ad); sc.collection.objects.link(arm)
arm.location = B(ROOT)
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
def bone(n, head_g, parent=None):
    eb = ad.edit_bones.new(n); h = B(head_g); eb.head = h; eb.tail = h + Vector((0, 0, 0.4)); eb.roll = 0
    if parent: eb.parent = ad.edit_bones[parent]
    return eb
bone('Bridge_Base', (0, 0, 0))
YAW_B = math.degrees(math.atan2(-DV[1], DV[0]))      # box yaw with its long axis along the span (-58 deg)
P0 = SP((0.0, 1.2, -TZ)); P1 = SP((CX, RTOP, -TZ)); P2 = SP((CX, RTOP, TZ)); P3 = (nx, LOW_Y, nz); P4 = PICK
BOX_REST = {'Box_1': (PICK, 0.0), 'Box_2': (SP((CX, RTOP, 0.0)), YAW_B), 'Box_3': (P0, YAW_B)}
for nme, (p, yaw) in BOX_REST.items(): bone(nme, p, 'Bridge_Base')
for nme, h, ax, sg in ROLL: bone(nme, h, 'Bridge_Base')
bpy.ops.object.mode_set(mode='OBJECT')
ob_m = M.build('Bridge_Moving')
gi = {g.index: g.name for g in ob_m.vertex_groups}
for v in ob_m.data.vertices:
    g = gi[v.groups[0].group]
    if g in BOX_REST:
        p, yaw = BOX_REST[g]
        v.co = Matrix.Translation(B(p)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ v.co
if 'root' in ob_m.vertex_groups: ob_m.vertex_groups['root'].name = 'Bridge_Base'
ob_m.parent = arm; ob_m.matrix_parent_inverse = Matrix.Identity(4); ob_m.location = (0, 0, 0)
md = ob_m.modifiers.new('Armature', 'ARMATURE'); md.object = arm
ob_s = S.build('Bridge_Static'); ob_s.parent = arm; ob_s.location = (0, 0, 0)

# ---------------------------------------------------------------- box route + timing
V = 1.5; TA = 1.0
def run_time(d): return d / V + TA
def run_frac(t, d):
    T = run_time(d)
    if t <= 0: return 0.0
    if t >= T: return 1.0
    def ramp_dist(u): x = u / TA; return V * TA * (x ** 3 - 0.5 * x ** 4)
    if t < TA: s = ramp_dist(t)
    elif t > T - TA: s = d - ramp_dist(T - t)
    else: s = ramp_dist(TA) + V * (t - TA)
    return s / d
def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def dist(a, b): return (Vector(b) - Vector(a)).length
TURN = 1.2; DWELL = 3.0
SEG = [('rise', P0, P1, run_time(dist(P0, P1))), ('bridge', P1, P2, run_time(dist(P1, P2))), ('lower', P2, P3, run_time(dist(P2, P3))),
       ('turn', P3, P3, TURN), ('chute', P3, P4, run_time(dist(P3, P4)))]
T_ARR = sum(s[3] for s in SEG)                    # arrival on Pickup_Point
T_PATH = T_ARR + DWELL
CLIP = round(math.ceil(T_PATH + 0.6), 1)
OFF = CLIP / 3.0
ANG = math.degrees(math.atan2(LOW_Y - PICK[1], X0 - XTE))
def chute_pitch(xc):             # +deg = nose (-x end) down while the box straddles the tip-down kinks
    xa, xb = XTE, X0
    if xc <= xa - 1.15 or xc >= xb + 1.15: return 0.0
    u = (xc - (xa - 1.15)) / ((xb + 1.15) - (xa - 1.15))
    return ANG * math.sin(math.pi * u)
def route(t):                    # t in [0, T_PATH]: (pos, yaw, pitch)
    t0 = 0.0
    for name, a, b, d in SEG:
        if t < t0 + d:
            u = t - t0
            if name == 'turn': return a, YAW_B + (0.0 - YAW_B) * smooth(u / d), 0.0
            f = run_frac(u, dist(a, b)); p = Vector(a).lerp(Vector(b), f)
            if name == 'chute':
                p.y = max(PICK[1], 0.5 * (chute_y(p.x - 1.15) + chute_y(p.x + 1.15)) if p.x < X0 + 1.15 else LOW_Y)
                return tuple(p), 0.0, chute_pitch(p.x)
            return tuple(p), YAW_B, 0.0
        t0 += d
    return P4, 0.0, 0.0
def box_state(t):                # box_convey: t in [0, CLIP) -> (pos, yaw, pitch, scale)
    if t < 0.05: return P0, YAW_B, 0.0, 0.001
    if t < T_PATH + 0.05: p, y, pi = route(min(t, T_PATH)); return p, y, pi, 1.0
    return P4, 0.0, 0.0, 0.001   # picked: hidden (Coder swaps in the crane's real box)
EV = {}; t0 = 0.0
for name, a, b, d in SEG: EV[name] = [round(t0, 3), round(t0 + d, 3)]; t0 += d
EV['dwell'] = [round(T_ARR, 3), round(T_PATH, 3)]
DIST = {name: round(dist(a, b), 3) for name, a, b, d in SEG}
print('CLIP', CLIP, 'T_ARR', round(T_ARR, 3), 'EV', EV, 'DIST', DIST)
FPS = 30
pb = arm.pose.bones
for nme in BOX_REST: pb[nme].rotation_mode = 'QUATERNION'
def key_box(nme, f, p, yaw, pitch, s):
    rest_p, rest_yaw = BOX_REST[nme]
    pb[nme].location = Vector(p) - Vector(rest_p)
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y') @ Matrix.Rotation(math.radians(pitch), 3, 'Z') @ Matrix.Rotation(math.radians(-rest_yaw), 3, 'Y')
    pb[nme].rotation_quaternion = R.to_quaternion()
    pb[nme].scale = (s, s, s)
    for ch in ('location', 'rotation_quaternion', 'scale'): pb[nme].keyframe_insert(ch, frame=f)
def finish(act, name):
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    arm.animation_data.action = None
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 0, act); tr.mute = True
arm.animation_data_create()
# box_convey: 3 boxes, phase CLIP/3
act = bpy.data.actions.new('box_convey'); arm.animation_data.action = act
NF = int(round(CLIP * FPS))
prevq = {}
for f in range(NF + 1):
    for i in range(3):
        nme = 'Box_%d' % (i + 1); t = (f / FPS - i * OFF) % CLIP
        p, yaw, pitch, s = box_state(t); key_box(nme, f, p, yaw, pitch, s)
finish(act, 'box_convey')
# box_path: ONE box (Box_1) from the infeed to Pickup_Point, scrubbable (time = progress * duration), Box_2/3 hidden
act3 = bpy.data.actions.new('box_path'); arm.animation_data.action = act3
NF3 = int(math.ceil(T_ARR * FPS))
for f in range(NF3 + 1):
    t = min(f / FPS, T_ARR); p, yaw, pitch = route(t); key_box('Box_1', f, p, yaw, pitch, 1.0)
    if f in (0, NF3):
        for nme in ('Box_2', 'Box_3'): key_box(nme, f, BOX_REST[nme][0], BOX_REST[nme][1], 0.0, 0.001)
finish(act3, 'box_path')
# roller_spin (one turn, 0.4 s -> roller surface 1.41 m/s)
SPIN = 0.4
act2 = bpy.data.actions.new('roller_spin'); arm.animation_data.action = act2
NS = 12
for nme, h, ax, sg in ROLL: pb[nme].rotation_mode = 'QUATERNION'
for kk in range(NS + 1):
    f = SPIN * FPS * kk / NS; a = math.tau * kk / NS
    for nme, h, ax, sg in ROLL:
        pb[nme].rotation_quaternion = Quaternion(Vector(ax), sg * a)   # bone local axes = glTF axes; top surface moves along the box travel
        pb[nme].keyframe_insert('rotation_quaternion', frame=f)
finish(act2, 'roller_spin')
for p_ in pb: p_.location = (0, 0, 0); p_.rotation_quaternion = (1, 0, 0, 0); p_.scale = (1, 1, 1)

# ---------------------------------------------------------------- markers + extras
def gm(nme, p_local, ex):
    e = bpy.data.objects.new(nme, None); sc.collection.objects.link(e); e.parent = arm; e.location = B(p_local); e.empty_display_size = 0.3
    for k_, v_ in ex.items(): e[k_] = v_
    return e
REF = lambda p: [round(p[0] + ROOT[0], 3), round(p[1] + ROOT[1], 3), round(p[2] + ROOT[2], 3)]
CR = (311.0 - 320.0, 0.0, 17.5)
hx, hy, hz = REF(PICK)[0] - CR[0], PICK[1] + 1.5, REF(PICK)[2] - CR[2]
TH_, R_, L_ = math.atan2(-hz, hx), math.hypot(hx, hz), 9.65 - hy - 0.95
gm('Pickup_Point', PICK, {'kind': 'crane_target', 'box_base': True, 'box_yaw_deg': 0,
   'refinery_xyz': REF(PICK), 'world_xyz': [REF(PICK)[0] + 320, PICK[1], REF(PICK)[2]],
   'crane_local_xyz': [round(REF(PICK)[0] - CR[0], 3), PICK[1], round(REF(PICK)[2] - CR[2], 3)],
   'crane_solve': {'theta_rad': round(TH_, 4), 'r_m': round(R_, 3), 'L_m': round(L_, 3), 'limits_ok': bool(2.6 <= R_ <= 10.3 and 0.6 <= L_ <= 8.3)},
   'note': 'box Base on the pickup table in the flatbed median (long axis +X, label +Z); box_convey / box_path stop each box here; RC-1 picks it and drops on FB-05'})
gm('Box_Infeed', P0, {'kind': 'path', 'refinery_xyz': REF(P0), 'note': 'box appears here, hidden inside the south lift shaft'})
gm('Bridge_Entry', P1, {'kind': 'path', 'refinery_xyz': REF(P1)})
gm('Bridge_Exit', P2, {'kind': 'path', 'refinery_xyz': REF(P2), 'note': 'top of the open lowerator in the median'})
gm('Lowerator_Bottom', P3, {'kind': 'path', 'refinery_xyz': REF(P3), 'note': 'turntable: box turns from yaw %.1f to 0' % YAW_B})
def rot_fp(cx, cz, h):
    xs = [cx + a * h * NV[0] + b * h * DV[0] for a in (-1, 1) for b in (-1, 1)]; zz = [cz + a * h * NV[1] + b * h * DV[1] for a in (-1, 1) for b in (-1, 1)]
    return [[round(min(xs), 2), round(max(xs), 2)], [round(min(zz), 2), round(max(zz), 2)]]
SC = SP((0, 0, -TZ)); SC_REF = (SC[0] + ROOT[0], SC[2] + ROOT[2])
FOOT = {'south_tower_footing_xz': rot_fp(SC_REF[0], SC_REF[1], 1.95), 'south_tower_centre_xz': [round(SC_REF[0], 3), round(SC_REF[1], 3)],
        'lowerator_footing_xz': [[NT_REF[0] - 1.6, NT_REF[0] + 1.6], [NT_REF[1] - 1.6, NT_REF[1] + 1.6]], 'lowerator_centre_xz': list(NT_REF),
        'chute_table_slab_xz': [[round(XTW - 0.2 + ROOT[0], 2), round(X0 + 0.2 + ROOT[0], 2)], [round(nz - 1.15 + ROOT[2], 2), round(nz + 1.15 + ROOT[2], 2)]],
        'span_yaw_deg': round(math.degrees(PHI), 2), 'span_tower_to_tower_m': round(2 * TZ, 3), 'truss_length_m': round(SL, 3),
        'deck_underside_y': UND, 'top_y': 11.9}
print('FOOT', FOOT, 'ROOT', ROOT, 'TZ', TZ)
arm['prop'] = 'CV-3 box bridge: 32 deg diagonal truss gantry over the RD-1 haul trails + flatbed lane E, box conveyor to an open lowerator and a pickup table in the flatbed median beside RC-1'
arm['origin_note'] = ('This GLB root node "Refinery_Bridge" is already translated to Refinery-local (%.2f, 0, %.2f), yaw 0. Add the GLB scene as a child of the '
                      'Refinery root (or at the Refinery station position, world (320, 0, 0) for station 2) with no extra offset. GLB axes = Refinery axes '
                      '(glTF, Y up); the span itself runs at yaw %.0f deg from the south tower (process side, Refinery z %.1f) to the lowerator in the flatbed median '
                      '(Refinery (%.1f, %.1f), +X = Cargo Dock / Launch Pad side).' % (ROOT[0], ROOT[2], math.degrees(PHI), SC_REF[1], NT_REF[0], NT_REF[1]))
arm['placement_refinery'] = {'position': list(ROOT), 'yaw_deg': 0}
arm['placement_world'] = {'position': [ROOT[0] + 320, 0, ROOT[2]], 'yaw_deg': 0, 'assumes_refinery_at': [320, 0, 0]}
arm['footprint_refinery'] = FOOT
arm['clearance'] = {'deck_underside_y': UND, 'ht04_bed_up_max_y': 5.75, 'required_y': 6.75, 'spare_m': round(UND - 6.75, 2),
                    'lanes': 'RD-1 outbound z 0 (toe -2.8..2.8), U-turn, inbound z 9 (toe to 11.8), flatbed E z 13 (10.2..15.8) and W z 22 (19.2..24.8): no footing, leg or slab inside any of them',
                    'crane': 'every part of the bridge above y 3.0 stays > 11.25 m (RC-1 jib tip) from the mast (311, 17.5): nearest 12.39 m. Inside that radius only the pickup table, chute, end stop, lamp (top y 2.53, z 18.8) and control box, all at or below the box top under the hook path; the swing to FB-05 (theta 0 to 0.66) clears the span.'}
arm['draws'] = 4
arm['clips'] = {'box_convey': {'duration_s': CLIP, 'loop': True, 'boxes': 3, 'phase_s': round(OFF, 3), 'speed_mps': V, 'ramp_s': TA,
                               'per_box_events_s': EV, 'pickup_arrive_s': round(T_ARR, 3), 'hidden_after_s': round(T_PATH + 0.05, 3),
                               'note': 'Box_N runs this timeline shifted by (N-1)*phase_s: rises hidden in the south shaft, crosses the bridge, drops in the open lowerator, turns to yaw 0 on the turntable, rolls down the chute, stops on Pickup_Point, waits dwell, then scales to 0 (show the crane box from Pickup_Point at that moment).'},
                'box_path': {'duration_s': round(NF3 / FPS, 3), 'loop': False, 'boxes': 1, 'box': 'Box_1', 'events_s': {k_: v_ for k_, v_ in EV.items() if k_ != 'dwell'},
                             'segment_length_m': DIST, 'note': 'one box, scrubbable: set time = progress * duration_s (Box_2/3 scaled to 0). Ends on Pickup_Point at yaw 0.'},
                'roller_spin': {'duration_s': SPIN, 'loop': True, 'note': 'one roller turn; surface speed ~1.41 m/s. Play together with box_convey or box_path'}}
sc.frame_set(0)
kw = dict(filepath=OUT, export_format='GLB', export_extras=True, export_yup=True, export_apply=False, export_skins=True, export_morph=False,
          export_texcoords=False, export_normals=True, export_materials='EXPORT', export_animations=True, export_cameras=False, export_lights=False,
          export_vertex_color='MATERIAL', export_optimize_animation_size=True, export_optimize_animation_keep_anim_armature=False)
bpy.ops.export_scene.gltf(**kw)      # = propgeo.export(anim=True) + drop constant bone channels per clip (JSON size)
print('WROTE', OUT, 'ROLLERS', len(ROLL), 'PICK_SOLVE', TH_, R_, L_)
