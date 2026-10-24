"""CV-3 box bridge for the Refinery (separate GLB: refinery_bridge.glb), v5 (10/24 Director option A: box end-on through the lowerator).
A Warren-truss gantry at yaw -32 deg: the open two-post lowerator (2.08 x 3.16 m frame, box + 0.15 m a side) stands in the flatbed median at
Refinery (9.0, 17.5), just right of the dump bay outline and fully inside the game view at 393x852 and 375x667; the span heads back to the RIGHT
from it, crossing ONLY flatbed lane E (z 13), to the clad south lift tower (between the U-turn / dump bay and lane E, off the right edge).
The box turns end-on (yaw 90, long axis along z) hidden in the south shaft and rides lengthwise over the 2.7 m-wide span, down the lowerator on a
moving carriage and west along the 2.7 m-wide ground conveyor; only on the 3.05 m pickup turntable does it turn (1 s ease-in-out) to yaw 0,
inside RC-1 reach (r 9.3, theta 0). In the Refinery game view (Cam_Target (313.1, 2.08, 13.55), frame_w 37.5) nothing of the bridge overlaps the
dump bay / Truck_Dump / hopper / intake (>= 6.3 px gap at 393x852, 10.6 px at 375x667); the span beyond the lowerator runs off the right edge.
Concept B: white panels, graphite structure, cyan light strips, panel lines, light weathering.
blender -b -P build_bridge.py -- OUT_RAW.glb [--box BOX_PLAIN.glb]     (env BR_LX = lowerator centre x, BR_EE = span end set-back, BR_LOWDUMP = json)
  BOX_PLAIN = art/3d/props/cargo_box/cargo_box_game.glb unpacked with `gltfpack -noq -kn -ke` (the existing HELIUM-3 crate is reused as-is).
Coordinates: glTF metres. 'Span frame' (x' across, y, z' along the span, south -> north) is mapped into the GLB frame with +x' -> camera
side n, +z' -> span direction d (a rotation at -32 deg, a reflection at +32: REFLECT handles windings / text); median parts are built
directly in the GLB frame (= Refinery axes, origin ROOT)."""
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
PHI = math.radians(-32.0)           # span yaw off the Refinery z axis: v4 mirrored to -32 deg (span heads back to the RIGHT from the lowerator)
DV = (math.sin(PHI), math.cos(PHI))  # span direction d (x, z), south tower -> lowerator
_SG = 1.0 if PHI >= 0 else -1.0
NV = (-_SG * math.cos(PHI), _SG * math.sin(PHI))   # +x' (conveyor / light side) -> camera side n (always +z)
REFLECT = (NV[0] * DV[1] - NV[1] * DV[0]) < 0      # v2/v3 (+32): span map is a reflection; v4 (-32): a rotation
CX = 0.0                            # v5: conveyor centred in the widened truss (walkway dropped: no room beside 2.71 m guides)
E_END = float(os.environ.get('BR_EE', 1.6))   # v5: truss ends this far (along d) before the lift centre: nothing fixed inside the lift carriage's shaft
S_Z = float(os.environ.get('BR_SZ', 7.0))   # south tower centre z: between the U-turn and flatbed lane E (toe z 10.2; rotated footing to z 9.69)
_TZ0 = (17.5 - CX * NV[1] - S_Z) / (2 * DV[1])
NT_REF = (float(os.environ.get('BR_LX', 9.0)), 17.5)   # lowerator centre in the flatbed median: right of the dump bay outline, fully on screen
S_REF = (round(NT_REF[0] - CX * NV[0] - 2 * _TZ0 * DV[0], 3), S_Z)                    # south tower centre (east, back right)
TZ = (NT_REF[1] - CX * NV[1] - S_Z) / (2 * DV[1])        # half distance between the tower centres along the span
M_REF = (NT_REF[0] - CX * NV[0] - TZ * DV[0], NT_REF[1] - CX * NV[1] - TZ * DV[1])   # span midpoint
ROOT = (round(M_REF[0], 2), 0.0, round(M_REF[1], 2))     # GLB root in Refinery coords (yaw 0)
MO = (M_REF[0] - ROOT[0], M_REF[1] - ROOT[2])            # span midpoint in the GLB frame
TH = 1.65                           # south tower half width; truss half width (v5 1.65: the end-on box crosses the span at 32 deg -> 2.41 m across it)
BHX, BHZ = 0.67, 1.2                # v5: box half extents in the GLB frame at yaw 90 (end-on: long axis along z)
GW = BHZ * abs(math.sin(PHI)) + BHX * abs(math.cos(PHI)) + 0.15   # span guide inner half gap: box half width across the span + 0.15 (1.355)
QX, QZ, PW = 0.93, 1.47, 0.22       # v5 lift posts (lowerator-local centres): near-left (-QX, +QZ) full height, far-right (+QX, -QZ) short; inner faces at box + 0.15
UND = 7.25                          # truss underside (HT-04 bed fully up = 5.75 m, + 1 m = 6.75 -> 0.45 m extra)
BC_T = 7.5; DECK = 7.6; RTOP = 8.1; TC = 10.4
SPAN0, SPAN1 = -(TZ - TH), TZ - E_END                     # truss ends: south tower face .. E_END short of the lift (v5: far-left truss corner kept off the dump bay outline)
NT = (NT_REF[0] - ROOT[0], NT_REF[1] - ROOT[2])           # lowerator centre, GLB frame
PICK_REF = (0.3, 1.0, 17.5)                               # pickup table box Base (median, crane-local (9.3, 1.0, 0))
PICK = (PICK_REF[0] - ROOT[0], PICK_REF[1], PICK_REF[2] - ROOT[2])
LOW_Y = 1.42                                              # box Base on the lift carriage at the bottom
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
            if REFLECT and XF['tm'] is None: faces = [tuple(reversed(list(f))) for f in faces]
        MB._add(self, verts, faces, col, mat, bone)
    def text(self, body, size, loc, rot, col, mat=1, bone='root', res=1, align='CENTER'):
        if XF['span'] and REFLECT: XF['tm'] = -Vector(loc).y
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
    wall_z(1, [(RTOP - 0.15, RTOP + 1.75, CX - GW - 0.05, CX + GW + 0.05)]); wall_z(-1, [])
    wall_x(1, []); wall_x(-1, [(0.85, 2.6, zc - 0.85, zc + 0.85)])
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
NP = max(4, int(round((SPAN1 - SPAN0) / 1.7))); zs = [SPAN0 + (SPAN1 - SPAN0) * k / NP for k in range(NP + 1)]
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
for z in zs[1:]: S.gseg((-(TH - 0.12), TC, z), ((TH - 0.12), TC, z), 0.1 if z < SPAN1 - 0.01 else 0.16, 0.1 if z < SPAN1 - 0.01 else 0.18, GRAPH1)   # v5: heavier end portal beam
n = max(8, int(round((SPAN1 - SPAN0) / 0.8))); za0, za1 = SPAN0 + 0.6, SPAN1 - 0.9          # amber / graphite chevron fascia (camera side)
for k in range(n):
    z0 = za0 + (za1 - za0) * k / n; z1 = za0 + (za1 - za0) * (k + 1) / n
    S.gquad([(TH + 0.005, UND + 0.04, z0), (TH + 0.005, UND + 0.04, z1), (TH + 0.005, UND + 0.26, z1), (TH + 0.005, UND + 0.26, z0)], AMBER if k % 2 == 0 else GRAPH)
ZP_E = (13.0 - M_REF[1] - CX * NV[1]) / DV[1]           # span z' above flatbed lane E (z 13)
for zp in (ZP_E,):                                        # clearance plate over flatbed lane E
    S.gbox((0.04, 0.34, 1.5), (TH + 0.05, UND + 0.19, zp), GRAPH2)          # on the chord face: nothing hangs below y 7.2
    S.text('CLR 7.2m', 0.21, B((TH + 0.075, UND + 0.19, zp)), (math.pi / 2, 0, math.pi / 2), WHITE2, mat=0)
for z in zs: S.gseg((-(TH - 0.12), BC_T - 0.12, z), ((TH - 0.12), BC_T - 0.12, z), 0.12, 0.2, GRAPH)
S.gbox((2 * TH - 0.3, 0.1, SL), (0, DECK - 0.05, SM), GRAPH2)
GL, GR = CX - GW - 0.025, CX + GW + 0.025                 # v5: guide walls 2.71 m apart (inner faces), box + 0.15 m a side across the span
for gx in (GL, GR):
    go = math.copysign(1.0, gx - CX)               # outward: beam + cap inner faces flush with the guide wall (box + 0.15)
    S.gbox((0.12, 0.3, SL), (gx + go * 0.035, DECK + 0.2, SM), GRAPH)
    S.gbox((0.05, 0.5, SL), (gx, RTOP + 0.2, SM), WHITE)
    S.gbox((0.09, 0.04, SL), (gx + go * 0.02, RTOP + 0.47, SM), GRAPH2)
for z in [SPAN0 + 2.0 * k + 1.0 for k in range(int(SL / 2.0))]:
    S.gbox((0.03, 0.46, 0.025), (GR + 0.04, RTOP + 0.2, z - 0.98), GRAPH2)
    S.gbox((0.04, 0.08, 0.14), (GR + 0.045, RTOP + 0.34, z), CYAN, mat=1)
S.gbox((0.02, 0.05, SL - 0.4), (GR + 0.035, RTOP + 0.06, SM), CYAN, mat=1)
S.gbox((0.3, 0.08, SL), (-0.9, UND + 0.05, SM), GRAPH1)
# transfer: the box runs on along d off the truss end onto the lift carriage (waiting at the top); the west guide carries on to the lift
ZT1 = TZ - 0.6                                             # west guide extension end (just short of the lift's west guide x -0.82 local)
S.gbox((0.05, 0.5, ZT1 - SPAN1 - 0.05), (GL, RTOP + 0.2, (SPAN1 + ZT1) / 2 - 0.025), WHITE)
S.gbox((0.09, 0.04, ZT1 - SPAN1 - 0.05), (GL - 0.02, RTOP + 0.47, (SPAN1 + ZT1) / 2 - 0.025), GRAPH2)
S.gbox((0.12, 0.3, ZT1 - SPAN1 - 0.05), (GL - 0.035, DECK + 0.2, (SPAN1 + ZT1) / 2 - 0.025), GRAPH)
# south pack-out hood on the east face (v2's long infeed stub would reach back over the RB-1 hopper / dump bay in the game view)
S.gbox((0.5, 2.1, 2.0), (-TH - 0.25, 1.45, -TZ), WHITE)          # on the far (-x', east) face: hidden behind the tower in the game view
S.gbox((0.54, 0.06, 2.04), (-TH - 0.25, 2.52, -TZ), GRAPH2)
S.gbox((0.02, 0.05, 1.5), (-TH - 0.51, 2.2, -TZ), CYAN, mat=1)
S.gbox((0.6, 0.3, 2.0), (-TH - 0.25, 0.25, -TZ), GRAPH1)
# span rollers (bones Roller_B##, axis n)
R_R = 0.09
ROLL = []    # (bone name, head glTF GLB frame, axis (glTF), sign)
k = 0; z = SPAN0 + 0.25
while z < SPAN1 - 0.1:
    k += 1; nme = 'Roller_B%02d' % k; ROLL.append((nme, SP((CX, RTOP - R_R, z)), (NV[0], 0.0, NV[1]), -1.0 if REFLECT else 1.0))
    M.gcyl((CX - GW + 0.05, RTOP - R_R, z), (CX + GW - 0.05, RTOP - R_R, z), R_R, SATIN, segs=6, bone=nme, caps=False)
    z += 1.2                     # 1.2 m pitch: always 2 rollers under the box (2.75 m long along the span); the side guards hide them
XF['span'] = False

# ================================================================ GLB FRAME (two-post lift in the median, ground conveyor, pickup turntable)
nx, nz = NT
def L(x, y, z): return (nx + x, y, nz + z)      # lowerator-local -> GLB frame
top = 10.8
LOW_F0 = len(S.bm.faces)
S.gbox((2.3, 0.22, 3.3), L(0, 0.11, 0), CONC)
S.gbox((2.1, 0.12, 3.1), L(0, 0.28, 0), CONC2)
POSTS = [(-QX, QZ, top), (QX, -QZ, 7.1)]        # near-left mast carries the head beam + carriage; far-right post stops under the truss end (box base 8.1)
for px, pz, ph in POSTS:
    S.gbox((0.42, 0.06, 0.42), L(px, 0.37, pz), STEEL)
    S.gbox((PW, ph - 0.4, PW), L(px, 0.4 + (ph - 0.4) / 2, pz), GRAPH)
S.gbox((0.36, 0.15, 0.36), L(QX, 7.175, -QZ), GRAPH2)                              # far-right bearing cap under the truss end (truss underside 7.25)
for y in (2.2, 4.4, 6.6, 8.8):                                                      # panel lines on the mast
    S.gbox((PW + 0.01, 0.03, PW + 0.01), L(-QX, y, QZ), GRAPH2)
S.gbox((0.05, 6.2, 0.02), L(-QX, 4.9, QZ + PW / 2 + 0.01), CYAN, mat=1)
# head beam from the mast top to the truss's west top-chord end (the span end hangs off it and the far-right post; above y 10.3 > box top 9.6)
S.gseg(L(-QX, top - 0.12, QZ), SP((-(TH - 0.12), TC, SPAN1)), 0.18, 0.22, GRAPH2)
S.gbox((0.4, 0.3, 0.4), L(-QX, top + 0.15, QZ), WHITE)                              # hoist head
S.gbox((0.42, 0.04, 0.42), L(-QX, top + 0.32, QZ), GRAPH2)
S.gbox((0.12, 0.1, 0.12), L(-QX, top + 0.39, QZ), CYAN, mat=1)
S.gbox((0.6, 0.34, 0.03), L(-QX, 9.75, QZ + PW / 2 + 0.015), WHITE)                # CV-3 sign on the mast's camera face
S.text('CV-3', 0.2, B(L(-QX, 9.68, QZ + PW / 2 + 0.032)), (math.pi / 2, 0, 0), CYAN, mat=1)
# west guide rails (box + 0.15), y 3.2..9.0 so the box leaves west under them at the bottom; tied back to the mast
for zz in (-0.6, 0.6):
    S.gbox((0.06, 5.8, 0.06), L(-0.84, 6.1, zz), SATIN)
for y in (3.2, 9.0):
    S.gseg(L(-0.84, y, -0.6), L(-0.84, y, QZ - PW / 2), 0.06, 0.08, GRAPH)
S.gbox((0.05, 0.4, 2.3), L(-0.845, 8.5, 0), WHITE)                                  # west guide at the top transfer level
S.gbox((1.3, 0.32, 0.05), L(-0.1, 8.48, 1.385), AMBER)                              # north end stop at the top (box nose at z +1.2)
S.gseg(L(-0.75, 8.48, 1.385), L(-QX + PW / 2, 8.48, 1.385), 0.06, 0.06, GRAPH)
# pit buffer under the carriage's bottom stop (carriage underside LOW_Y - 0.14)
S.gbox((1.1, LOW_Y - 0.6, 2.0), L(0, 0.4 + (LOW_Y - 0.6) / 2, 0), GRAPH)
S.gbox((1.0, 0.03, 1.9), L(0, LOW_Y - 0.185, 0), AMBER)
# lift carriage (moving, bone Lift_Carriage; rest = top, deck flush with the span rollers): cantilevered off the near-left mast
CAR_HX, CAR_HZ = 0.70, 1.25
M.gbox((2 * CAR_HX, 0.13, 2 * CAR_HZ), L(0, RTOP - 0.07, 0), GRAPH1, bone='Lift_Carriage')
for zz in (-0.8, -0.4, 0.0, 0.4, 0.8): M.gbox((1.3, 0.012, 0.05), L(0, RTOP - 0.012, zz), SATIN, bone='Lift_Carriage')   # flush below the deck top
M.gbox((0.03, 0.04, 2.3), L(CAR_HX + 0.01, RTOP - 0.06, 0), CYAN, mat=1, bone='Lift_Carriage')
M.gbox((0.16, 0.49, 0.3), L(-0.68, RTOP - 0.385, 1.18), GRAPH, bone='Lift_Carriage')       # arm to the mast (below the deck)
M.gseg(L(-0.6, RTOP - 0.62, 1.18), L(0.4, RTOP - 0.15, 1.18), 0.1, 0.1, GRAPH, bone='Lift_Carriage')
LOW_F1 = len(S.bm.faces)
if os.environ.get('BR_LOWDUMP'):              # lift body polygons (Refinery coords) for the edge-spare measurement
    import json as _j; S.bm.faces.ensure_lookup_table()
    _j.dump([[[round(v.co.x + ROOT[0], 4), round(v.co.z, 4), round(-v.co.y + ROOT[2], 4)] for v in S.bm.faces[i].verts] for i in range(LOW_F0, LOW_F1)], open(os.environ['BR_LOWDUMP'], 'w'))
# ground conveyor (box end-on, broadside travel west) + pickup turntable
X0 = nx - 0.82                                  # conveyor start: the lift's west side
TR = 1.525                                      # pickup turntable radius (3.05 m): box turn circle r 1.374
XTE = PICK[0] + TR + 0.18                       # conveyor end / guide end, clear of the turn circle
XTW = PICK[0] - TR - 0.2                        # end stop face
def chute_y(x):
    if x >= X0: return LOW_Y
    if x <= XTE: return PICK[1]
    return PICK[1] + (LOW_Y - PICK[1]) * (x - XTE) / (X0 - XTE)
zc = nz; GG = BHZ + 0.15                         # ground guide inner faces z +-1.35
S.gbox((X0 - XTW + 0.5, 0.12, 3.2), ((X0 + XTW - 0.5) / 2, 0.06, zc), CONC)
for sz in (-1, 1):
    zg = zc + sz * (GG + 0.025)
    S.gseg((X0 - 0.25, LOW_Y - 0.2, zg), (XTE, PICK[1] - 0.2, zg), 0.1, 0.22, GRAPH)
    S.gseg((X0 - 0.25, LOW_Y + 0.25, zg), (XTE, PICK[1] + 0.25, zg), 0.05, 0.4, WHITE)
    S.gseg((X0 - 0.25, LOW_Y + 0.47, zg + sz * 0.02), (XTE, PICK[1] + 0.47, zg + sz * 0.02), 0.09, 0.04, GRAPH2)
    x = X0 - 0.4
    while x > XTE + 0.2:
        y = chute_y(x) - 0.31; S.gbox((0.12, y - 0.12, 0.12), (x, 0.12 + (y - 0.12) / 2, zg), GRAPH1); x -= 2.0
S.gseg((X0 - 0.3, LOW_Y + 0.08, zc + GG + 0.055), (XTE + 0.1, PICK[1] + 0.08, zc + GG + 0.055), 0.02, 0.05, CYAN, mat=1)
S.gbox((1.2, PICK[1] - 0.3, 1.2), (PICK[0], 0.12 + (PICK[1] - 0.3) / 2, zc), GRAPH1)          # turntable pedestal
S.gcyl((PICK[0], PICK[1] - 0.22, zc), (PICK[0], PICK[1] - 0.02, zc), TR, GRAPH, segs=16)
S.gcyl((PICK[0], PICK[1] - 0.06, zc), (PICK[0], PICK[1] - 0.02, zc), TR + 0.03, CYAN, segs=16, mat=1, caps=False)
S.gbox((0.2, 0.42, 1.7), (XTW - 0.1, PICK[1] + 0.12, zc), AMBER)                              # end stop
S.gbox((0.12, 0.9, 0.12), (XTW - 0.1, 0.55, zc), GRAPH1)
S.gcyl((XTW - 0.1, 0.1, zc + 1.45), (XTW - 0.1, 2.4, zc + 1.45), 0.05, GRAPH, segs=6)        # lamp post
S.gbox((0.16, 0.12, 0.16), (XTW - 0.1, 2.47, zc + 1.45), CYAN, mat=1)
S.gbox((0.5, 0.7, 0.2), (XTE + 0.45, 0.75, zc + 1.55), WHITE)                                  # control box
S.gbox((0.3, 0.2, 0.02), (XTE + 0.45, 0.9, zc + 1.655), CYAN, mat=1)
S.gbox((0.08, 0.4, 0.1), (XTE + 0.45, 0.2, zc + 1.55), GRAPH1)
k = 0; x = X0 - 0.15
while x > XTE + 0.15:
    k += 1; nme = 'Roller_T%02d' % k; y = chute_y(x) - R_R; ROLL.append((nme, (x, y, zc), (0.0, 0.0, 1.0), 1.0))
    M.gcyl((x, y, zc - GG + 0.05), (x, y, zc + GG - 0.05), R_R, SATIN, segs=6, bone=nme, caps=False)
    x -= 0.6                     # 0.6 m pitch: always 2 rollers under the 1.34 m-long (end-on) box

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
YAW_B = 90.0                                         # v5: end-on (long axis along z) from the south shaft to the pickup turntable
P0 = SP((0.0, 1.2, -TZ)); P1 = SP((CX, RTOP, -TZ)); P2 = SP((CX, RTOP, TZ)); P3 = (nx, LOW_Y, nz); P4 = PICK
BOX_REST = {'Box_1': (PICK, 0.0), 'Box_2': (SP((CX, RTOP, 0.0)), YAW_B), 'Box_3': (P0, YAW_B)}
for nme, (p, yaw) in BOX_REST.items(): bone(nme, p, 'Bridge_Base')
for nme, h, ax, sg in ROLL: bone(nme, h, 'Bridge_Base')
bone('Lift_Carriage', (nx, RTOP, nz), 'Bridge_Base')
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
def run_time(d, v=None): return d / (v or V) + TA
def run_frac(t, d, T=None):
    T = T or run_time(d); vv = d / (T - TA)
    if t <= 0: return 0.0
    if t >= T: return 1.0
    def ramp_dist(u): x = u / TA; return vv * TA * (x ** 3 - 0.5 * x ** 4)
    if t < TA: s = ramp_dist(t)
    elif t > T - TA: s = d - ramp_dist(T - t)
    else: s = ramp_dist(TA) + vv * (t - TA)
    return s / d
def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def dist(a, b): return (Vector(b) - Vector(a)).length
TURN = 1.0; SETTLE = 0.087; DWELL = 3.0      # v5: ~1 s ease-in-out table turn 90 -> 0, done 0.087 s before Pickup arrival / RC-1 cycle start
V_LOW, V_UP = 2.0, 3.0                       # v5 lift carriage: down with the box, back up empty
T_ARR_TARGET = 33.887             # v3 arrival kept (box_path 33.9 s, box_convey 38 s, phase 12.667 s); the hidden rise in the south shaft takes up the slack
T_LOW = run_time(dist(P2, P3), V_LOW)
_t = run_time(dist(P1, P2)) + T_LOW + run_time(dist(P3, P4)) + TURN + SETTLE
T_RISE = T_ARR_TARGET - _t
assert run_time(dist(P0, P1)) - 1e-6 < T_RISE < 12.6, T_RISE   # never faster than 1.5 m/s; out of the shaft before the next box appears (phase 12.667)
SEG = [('rise', P0, P1, T_RISE), ('bridge', P1, P2, run_time(dist(P1, P2))), ('lower', P2, P3, T_LOW),
       ('ground_conveyor', P3, P4, run_time(dist(P3, P4))), ('table_turn', P4, P4, TURN), ('settle', P4, P4, SETTLE)]
T_ARR = sum(s[3] for s in SEG)                    # arrival on Pickup_Point
T_PATH = T_ARR + DWELL
CLIP = round(math.ceil(T_PATH + 0.6), 1)
OFF = CLIP / 3.0
ANG = math.degrees(math.atan2(LOW_Y - PICK[1], X0 - XTE))
def chute_pitch(xc):             # +deg = nose (-x end) down while the box straddles the tip-down kinks
    xa, xb = XTE, X0
    if xc <= xa - BHX or xc >= xb + BHX: return 0.0
    u = (xc - (xa - BHX)) / ((xb + BHX) - (xa - BHX))
    return ANG * math.sin(math.pi * u)
def route(t):                    # t in [0, T_PATH]: (pos, yaw, pitch)
    t0 = 0.0
    for name, a, b, d in SEG:
        if t < t0 + d:
            u = t - t0
            if name == 'table_turn': return a, YAW_B + (0.0 - YAW_B) * smooth(u / d), 0.0
            if name == 'settle': return a, 0.0, 0.0
            f = run_frac(u, dist(a, b), d); p = Vector(a).lerp(Vector(b), f)
            if name == 'ground_conveyor':
                th = chute_pitch(p.x); tn = math.tan(math.radians(th))      # rest the tilted base on the chute: touches, never sinks in
                us = [BHX * (2 * k / 20.0 - 1) for k in range(21)] + [u for u in (X0 - p.x, XTE - p.x) if abs(u) <= BHX]
                p.y = max(chute_y(p.x + u) - u * tn for u in us)
                return tuple(p), YAW_B, th
            return tuple(p), YAW_B, 0.0
        t0 += d
    return P4, 0.0, 0.0
def box_state(t):                # box_convey: t in [0, CLIP) -> (pos, yaw, pitch, scale)
    if t < 0.25: return P0, YAW_B, 0.0, 0.001   # hidden in the shaft >= 2 samples of gltfpack's 10 Hz resample, so the hidden hop from Pickup_Point to the infeed never shows a growing box
    if t < T_PATH + 0.05: p, y, pi = route(min(t, T_PATH)); return p, y, pi, 1.0
    return P4, 0.0, 0.0, 0.001   # picked: hidden (Coder swaps in the crane's real box)
EV = {}; t0 = 0.0; EVF = {}
for name, a, b, d in SEG: EV[name] = [round(t0, 3), round(t0 + d, 3)]; EVF[name] = (t0, t0 + d); t0 += d
# lift carriage: waits at the top, rides down under the box, waits until the box has run clear west, returns up empty
_g0 = EVF['ground_conveyor'][0]; _dg = dist(P3, P4); _tg = EVF['ground_conveyor'][1] - _g0
T_CLR = next(_g0 + k / 300.0 for k in range(3000) if run_frac(k / 300.0, _dg, _tg) * _dg >= BHX + CAR_HX + 0.05)
T_UP = run_time(dist(P2, P3), V_UP)
T_CAR = (EVF['lower'][0], EVF['lower'][1], T_CLR, T_CLR + T_UP)          # box-timeline times: down start, down end, up start, up end
def car_dy_box(t):                # carriage offset below the top (<= 0) on one box's timeline
    a, b, c, d = T_CAR; H = dist(P2, P3)
    if t <= a or t >= d: return 0.0
    if t < b: return -H * run_frac(t - a, H, b - a)
    if t < c: return -H
    return -H + H * run_frac(t - c, H, d - c)
APPROACH = (GW + BHZ + CAR_HZ) / V + 1.0     # conservative: the next box can reach the carriage's shaft at most this long before its 'lower' starts
assert T_CAR[3] - T_CAR[0] + APPROACH < 38.0 / 3.0, (T_CAR, APPROACH)    # carriage back at the top before the next box (phase 12.667 s) arrives
EV['lift_carriage'] = {'down': [round(T_CAR[0], 3), round(T_CAR[1], 3)], 'up': [round(T_CAR[2], 3), round(T_CAR[3], 3)]}
EV['dwell'] = [round(T_ARR, 3), round(T_PATH, 3)]
DIST = {name: round(dist(a, b), 3) for name, a, b, d in SEG}
print('CLIP', CLIP, 'T_ARR', round(T_ARR, 3), 'EV', EV, 'DIST', DIST)
FPS = 30
pb = arm.pose.bones
for nme in BOX_REST: pb[nme].rotation_mode = 'QUATERNION'
def key_box(nme, f, p, yaw, pitch, s):
    rest_p, rest_yaw = BOX_REST[nme]
    pb[nme].location = Vector(p) - Vector(rest_p)
    R = Matrix.Rotation(math.radians(pitch), 3, 'Z') @ Matrix.Rotation(math.radians(yaw), 3, 'Y') @ Matrix.Rotation(math.radians(-rest_yaw), 3, 'Y')   # chute tilt about the world z axis
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
pb['Lift_Carriage'].rotation_mode = 'QUATERNION'
def key_car(f, dy):
    pb['Lift_Carriage'].location = (0.0, dy, 0.0); pb['Lift_Carriage'].keyframe_insert('location', frame=f)
for f in range(NF + 1):
    for i in range(3):
        nme = 'Box_%d' % (i + 1); t = (f / FPS - i * OFF) % CLIP
        p, yaw, pitch, s = box_state(t); key_box(nme, f, p, yaw, pitch, s)
    key_car(f, min(car_dy_box((f / FPS - i * OFF) % CLIP) for i in range(3)))
finish(act, 'box_convey')
# box_path: ONE box (Box_1) from the infeed to Pickup_Point, scrubbable (time = progress * duration), Box_2/3 hidden
act3 = bpy.data.actions.new('box_path'); arm.animation_data.action = act3
NF3 = int(math.ceil(T_ARR * FPS))
for f in range(NF3 + 1):
    t = min(f / FPS, T_ARR); p, yaw, pitch = route(t); key_box('Box_1', f, p, yaw, pitch, 1.0); key_car(f, car_dy_box(t))
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
   'note': 'box Base on the pickup turntable (3.05 m) in the flatbed median (long axis +X, label +Z); the table turns each box 90 -> 0 deg (table_turn) just before it settles here; box_convey / box_path stop each box here; RC-1 picks it (cycle start 33.89 s, latch 0.9-1.3 s later) and drops on FB-05'})
gm('Box_Infeed', P0, {'kind': 'path', 'refinery_xyz': REF(P0), 'note': 'box appears here, hidden inside the south lift shaft'})
gm('Bridge_Entry', P1, {'kind': 'path', 'refinery_xyz': REF(P1)})
gm('Bridge_Exit', P2, {'kind': 'path', 'refinery_xyz': REF(P2), 'note': 'top of the open lowerator in the median'})
gm('Lowerator_Bottom', P3, {'kind': 'path', 'refinery_xyz': REF(P3), 'note': 'carriage bottom: box (still yaw %.1f, end-on) rolls off west onto the ground conveyor' % YAW_B})
def rot_fp(cx, cz, h):
    xs = [cx + a * h * NV[0] + b * h * DV[0] for a in (-1, 1) for b in (-1, 1)]; zz = [cz + a * h * NV[1] + b * h * DV[1] for a in (-1, 1) for b in (-1, 1)]
    return [[round(min(xs), 2), round(max(xs), 2)], [round(min(zz), 2), round(max(zz), 2)]]
SC = SP((0, 0, -TZ)); SC_REF = (SC[0] + ROOT[0], SC[2] + ROOT[2])
FOOT = {'south_tower_footing_xz': rot_fp(SC_REF[0], SC_REF[1], 1.95), 'south_tower_centre_xz': [round(SC_REF[0], 3), round(SC_REF[1], 3)],
        'lowerator_footing_xz': [[round(NT_REF[0] - 1.15, 3), round(NT_REF[0] + 1.15, 3)], [NT_REF[1] - 1.65, NT_REF[1] + 1.65]], 'lowerator_centre_xz': list(NT_REF),
        'ground_conveyor_table_slab_xz': [[round(XTW - 0.5 + ROOT[0], 2), round(X0 + ROOT[0], 2)], [round(nz - 1.6 + ROOT[2], 2), round(nz + 1.6 + ROOT[2], 2)]],
        'pickup_turntable': {'centre_xz': [PICK_REF[0], PICK_REF[2]], 'diameter_m': 2 * TR},
        'span_yaw_deg': round(math.degrees(PHI), 2), 'span_tower_to_tower_m': round(2 * TZ, 3), 'truss_length_m': round(SL, 3),
        'deck_underside_y': UND, 'top_y': 11.9}
print('FOOT', FOOT, 'ROOT', ROOT, 'TZ', TZ)
arm['prop'] = 'CV-3 box bridge v5: -32 deg diagonal truss gantry from a south tower back-right of the dump bay, crossing only flatbed lane E, to an open two-post lowerator with a moving carriage in the flatbed median right of the dump bay (fully on screen); then a ground conveyor west to the pickup turntable beside RC-1. The box rides end-on (yaw 90) the whole way and turns to yaw 0 only on the turntable.'
arm['origin_note'] = ('This GLB root node "Refinery_Bridge" is already translated to Refinery-local (%.2f, 0, %.2f), yaw 0. Add the GLB scene as a child of the '
                      'Refinery root (or at the Refinery station position, world (320, 0, 0) for station 2) with no extra offset. GLB axes = Refinery axes '
                      '(glTF, Y up); the span itself runs at yaw %.0f deg from the south tower (east of the dump bay, Refinery (%.1f, %.1f)) to the lowerator in the flatbed median '
                      '(Refinery (%.1f, %.1f), +X = Cargo Dock / Launch Pad side).' % (ROOT[0], ROOT[2], math.degrees(PHI), SC_REF[0], SC_REF[1], NT_REF[0], NT_REF[1]))
arm['placement_refinery'] = {'position': list(ROOT), 'yaw_deg': 0}
arm['placement_world'] = {'position': [ROOT[0] + 320, 0, ROOT[2]], 'yaw_deg': 0, 'assumes_refinery_at': [320, 0, 0]}
arm['footprint_refinery'] = FOOT
arm['clearance'] = {'deck_underside_y': UND, 'lowest_vertex_over_lanes_y': 7.249, 'ht04_bed_up_max_y': 5.75, 'required_y': 6.75, 'spare_m': round(UND - 6.75, 2),
                    'lanes': 'span crosses only flatbed lane E z 13 (10.2..15.8); lowest bridge vertex over it 7.249 (all clip samples). RD-1 outbound z 0, U-turn, inbound z 9 and the HT-04 dump pose (bed up 5.75): no bridge part inside or over them. Flatbed W z 22 (19.2..24.8): untouched. Footings: south tower x %.2f..%.2f z %.2f..%.2f, lowerator + ground conveyor slab in the median z 15.9..19.1' % tuple(FOOT['south_tower_footing_xz'][0] + FOOT['south_tower_footing_xz'][1]),
                    'game_view': 'Refinery camera (313.1, 2.08, 13.55), frame_w 37.5: no bridge vertex inside the dump bay / Truck_Dump / hopper / intake outline (gap >= 6.3 px at 393x852, 10.6 px at 375x667); lowerator fully on screen (right spare 10.3 px / 8.2 px; box in the lift 11.5 / 8.5 px); whole Refinery + bridge + crane top / bottom spare 64.2 / 70.9 px at 393x852, 10.2 / 13.8 px at 375x667; the span beyond it and the south tower run off the right edge',
                    'crane': 'every part of the bridge above y 3.0 is >= 16.9 m from the RC-1 mast (311, 17.5), far outside the 11.25 m jib tip. Inside that radius only the pickup table, the west end of the ground conveyor, end stop, lamp (top y 2.53, z 18.8) and control box, all at or below the box top under the hook path.'}
arm['draws'] = 4
arm['clips'] = {'box_convey': {'duration_s': CLIP, 'loop': True, 'boxes': 3, 'phase_s': round(OFF, 3), 'speed_mps': V, 'lowerator_descent_mps': V_LOW, 'ramp_s': TA,
                               'per_box_events_s': EV, 'pickup_arrive_s': round(T_ARR, 3), 'hidden_after_s': round(T_PATH + 0.05, 3),
                               'note': 'Box_N runs this timeline shifted by (N-1)*phase_s: rises hidden in the south shaft, crosses the bridge, rides the lift carriage down the open lowerator, rides the ground conveyor west (all end-on, yaw 90), turns to yaw 0 on the pickup turntable (table_turn, 1 s ease-in-out) and settles on Pickup_Point, waits dwell, then scales to 0 (show the crane box from Pickup_Point at that moment).'},
                'box_path': {'duration_s': round(NF3 / FPS, 3), 'loop': False, 'boxes': 1, 'box': 'Box_1', 'events_s': {k_: v_ for k_, v_ in EV.items() if k_ != 'dwell'},
                             'segment_length_m': DIST, 'note': 'one box, scrubbable: set time = progress * duration_s (Box_2/3 scaled to 0). Yaw 90 (end-on) until table_turn, 1 s ease-in-out to yaw 0, at rest on Pickup_Point from pickup_arrive_s. Lift_Carriage moves with it (events lift_carriage).'},
                'roller_spin': {'duration_s': SPIN, 'loop': True, 'note': 'one roller turn; surface speed ~1.41 m/s. Play together with box_convey or box_path'}}
sc.frame_set(0)
kw = dict(filepath=OUT, export_format='GLB', export_extras=True, export_yup=True, export_apply=False, export_skins=True, export_morph=False,
          export_texcoords=False, export_normals=True, export_materials='EXPORT', export_animations=True, export_cameras=False, export_lights=False,
          export_vertex_color='MATERIAL', export_optimize_animation_size=True, export_optimize_animation_keep_anim_armature=False)
bpy.ops.export_scene.gltf(**kw)      # = propgeo.export(anim=True) + drop constant bone channels per clip (JSON size)
print('WROTE', OUT, 'ROLLERS', len(ROLL), 'PICK_SOLVE', TH_, R_, L_)
