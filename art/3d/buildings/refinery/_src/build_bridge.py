"""CV-3 box bridge for the Refinery (separate GLB: refinery_bridge.glb).
A truss gantry over the RD-1 haul trails carrying an enclosed box conveyor from the south lift tower (process side) to the north
lowerator tower, which drops each HELIUM-3 box onto a tip-down roller chute and a pickup table beside the RC-1 crane (crane picks it
there and loads FB-05). Concept B: white panels, graphite structure, cyan light strips, panel lines, light weathering.
blender -b -P build_bridge.py -- OUT_RAW.glb [--box BOX_PLAIN.glb]
  BOX_PLAIN = art/3d/props/cargo_box/cargo_box_game.glb unpacked with `gltfpack -noq -kn -ke` (the existing HELIUM-3 crate is reused as-is).
Coordinates in this file: glTF metres relative to the GLB root (root sits at Refinery (-22, 0, 4.8)); helpers convert to Blender (x, -z, y)."""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'props', '_shared_src'))
from propgeo import MB, P, lin, empty, export
A = sys.argv[sys.argv.index('--') + 1:]
OUT = A[0]
def arg(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
BOX_PLAIN = arg('box', '/tmp/cargo_box_plain.glb')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30

# ---------------------------------------------------------------- layout (glTF, bridge-local; Refinery = local + ROOT)
ROOT = (-22.0, 0.0, 4.8)            # GLB root in Refinery coords (Refinery origin = Truck_Dump); world = Refinery + (320, 0, 0)
TZ = 9.4                            # tower centres at local z -9.4 / +9.4  (Refinery z -4.6 / 14.2)
TH = 1.55                           # tower half width (x and z)
UND = 7.2                           # truss underside (HT-04 bed fully up = 5.75 m, + 1 m = 6.75 -> 0.45 m extra)
BC_T = 7.5                          # bottom chord top
DECK = 7.6                          # deck plate top
RTOP = 8.1                          # roller top = box Base height on the bridge
TC = 10.4                           # top chord centre
CX = 0.45                           # conveyor centre line x
SPAN0, SPAN1 = -(TZ - TH), (TZ - TH)  # -7.85 .. 7.85
PICK = (3.7, 1.0, TZ)               # pickup table: box Base (Refinery (-18.3, 1.0, 14.2))
LOW_Y = 1.42                        # box Base height at the bottom of the north lowerator (exit level)
WHITE, WHITE2, GRAPH, GRAPH2, GRAPH1, STEEL, SATIN = P['white'], P['white2'], P['graph'], P['graph2'], P['graph1'], P['steel'], P['satin']
AMBER, CYAN = P['amber'], P['cyan']
CONC = lin('#8e9196'); CONC2 = lin('#777a7f'); GRATE = lin('#4a5160')

def B(v): return Vector((v[0], -v[2], v[1]))
class G(MB):
    """MB with glTF-space helpers"""
    def gbox(self, size, c, col, mat=0, bone='root', rot_y=0.0):
        self.box((size[0], size[2], size[1]), B(c), col, rot=(0, 0, -rot_y), mat=mat, bone=bone)
    def gseg(self, p0, p1, w, h, col, mat=0, bone='root'):
        """square-section member between two glTF points (w across, h vertical-ish)"""
        a, b = B(p0), B(p1); d = b - a; L = d.length
        if L < 1e-6: return
        q = d.to_track_quat('X', 'Z'); self.box((L, w, h), (a + b) / 2, col, rot=q.to_euler(), mat=mat, bone=bone)
    def gcyl(self, p0, p1, r, col, segs=8, mat=0, bone='root', caps=True):
        self.cyl(B(p0), B(p1), r, col, segs=segs, mat=mat, bone=bone, caps=caps)
    def gquad(self, pts, col, mat=0, bone='root'):
        self.quad([B(p) for p in pts], col, mat=mat, bone=bone)

S = G()   # static (Bridge_Static: SHM_Paint + SHM_GlowCyan)
M = G()   # moving, skinned (Bridge_Moving: rollers + 3 boxes)

# ---------------------------------------------------------------- towers (= the two pylons: 4 graphite legs, white clad lift shaft, footing)
def tower(zc, north):
    # footing: concrete pad + plinth, outside the truck lanes
    S.gbox((3.9, 0.22, 3.9), (0, 0.11, zc), CONC)
    S.gbox((3.5, 0.12, 3.5), (0, 0.28, zc), CONC2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (TH - 0.12), zc + sz * (TH - 0.12)
            S.gbox((0.5, 0.06, 0.5), (x, 0.37, z), STEEL)                      # base plate
            S.gbox((0.26, 11.05 - 0.4, 0.26), (x, 0.4 + (11.05 - 0.4) / 2, z), GRAPH)   # leg
    top = 11.05
    # cladding panels between the legs (0.08 thick), with door openings
    def wall_x(sx, openings):   # wall on x = sx*TH (faces +-x), spans z zc-TH..zc+TH
        x = sx * (TH - 0.05); z0, z1 = zc - TH + 0.13, zc + TH - 0.13
        ys = [0.4]; spans = []
        y0 = 0.4
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
    deck_open = [(RTOP - 0.1, RTOP + 1.75, CX - 0.85, CX + 0.85)]
    if north:
        # OPEN lowerator frame (the camera looks along the bridge, so a clad tower would hide the whole span): ring beams, guide rails,
        # X-bracing on the far (-x) face only, a turntable at the bottom; the box is seen dropping, turning and rolling out
        for y in (0.55, 3.2, BC_T - 0.15, top - 0.35):
            for sz in (-1, 1): S.gbox((2 * TH - 0.1, 0.16, 0.16), (0, y, zc + sz * (TH - 0.12)), GRAPH2)
            for sx in (-1, 1): S.gbox((0.16, 0.16, 2 * TH - 0.1), (sx * (TH - 0.12), y, zc), GRAPH2)
        for (y0, y1) in ((0.55, 3.2), (3.2, BC_T - 0.15)):
            S.gseg((-(TH - 0.12), y0, zc - TH + 0.12), (-(TH - 0.12), y1, zc + TH - 0.12), 0.07, 0.07, GRAPH1)
            S.gseg((-(TH - 0.12), y1, zc - TH + 0.12), (-(TH - 0.12), y0, zc + TH - 0.12), 0.07, 0.07, GRAPH1)
        for sx in (-1, 1):
            for sz in (-1, 1):
                S.gbox((0.06, BC_T - LOW_Y + 2.4, 0.06), (sx * 1.0, LOW_Y + (BC_T - LOW_Y + 2.4) / 2, zc + sz * 1.0), SATIN)   # guide rails
        S.gcyl((0, LOW_Y - 0.22, zc), (0, LOW_Y - 0.1, zc), 1.15, GRAPH, segs=12)                     # turntable
        S.gcyl((0, LOW_Y - 0.1, zc), (0, LOW_Y - 0.085, zc), 1.18, CYAN, segs=12, mat=1, caps=False)     # turntable cyan ring
        S.gbox((1.4, LOW_Y - 0.62, 1.4), (0, 0.4 + (LOW_Y - 0.62) / 2, zc), GRAPH1)                   # turntable drive base
        S.gbox((2 * TH + 0.1, 1.0, 0.08), (0, 1.0, zc - TH + 0.04), WHITE)                            # low skirt panels (far sides only)
        S.gbox((0.08, 1.0, 2 * TH + 0.1), (-TH + 0.04, 1.0, zc), WHITE)
        # head house over the deck entry: canopy + white side cheeks (open toward the camera)
        S.gbox((0.08, 1.8, 2 * TH - 0.2), (-TH + 0.04, top - 1.3, zc), WHITE)
        S.gbox((0.08, 0.7, 2 * TH - 0.2), (TH - 0.04, top - 0.75, zc), WHITE)
        S.gbox((2 * TH - 0.2, 0.7, 0.08), (0, top - 0.75, zc + TH - 0.04), WHITE)
    else:
        wall_z(1, deck_open); wall_z(-1, [(0.85, 2.6, CX - 0.85, CX + 0.85)])    # infeed from the process side (-z)
        wall_x(1, []); wall_x(-1, [])
    # roof + parapet + beacon
    S.gbox((2 * TH + 0.2, 0.18, 2 * TH + 0.2), (0, top - 0.16, zc), GRAPH2)
    S.gbox((2 * TH - 0.2, 0.12, 2 * TH - 0.2), (0, top - 0.01, zc), WHITE2)
    S.gbox((0.9, 0.5, 0.7), (-0.5, top + 0.3, zc), WHITE)                         # lift machine housing
    S.gbox((0.92, 0.04, 0.72), (-0.5, top + 0.57, zc), GRAPH2)
    S.gcyl((0.75, top + 0.05, zc + 0.9), (0.75, top + 0.75, zc + 0.9), 0.04, GRAPH, segs=6)   # beacon mast
    S.gbox((0.16, 0.14, 0.16), (0.75, top + 0.82, zc + 0.9), CYAN, mat=1)
    # panel lines (graphite seams) on the two camera-visible faces (+x and +z) and the cyan strip
    for y in ((2.2, 4.0, 5.8, 9.9) if not north else (10.45,)):
        S.gbox((0.02, 0.035, 2 * TH - 0.3), (TH + 0.003, y, zc), GRAPH2)
        S.gbox((2 * TH - 0.3, 0.035, 0.02), (0, y, zc + TH + 0.003), GRAPH2)
    if not north:
        S.gbox((0.02, top - 1.2, 0.035), (TH + 0.003, 0.4 + (top - 1.2) / 2, zc), GRAPH2)
        S.gbox((0.025, 3.6, 0.07), (TH + 0.012, 5.0, zc + 1.05), CYAN, mat=1)      # vertical cyan light strip
    else:
        for sx in (-1, 1): S.gbox((0.03, 5.5, 0.05), (sx * (TH - 0.12) + sx * 0.14, 4.6, zc + TH - 0.12), CYAN, mat=1)   # cyan strips on the camera-side legs
    S.gbox((2 * TH - 0.6, 0.06, 0.025), (0, top - 0.55, zc + TH + 0.012), CYAN, mat=1)
    # access ladder on the outer face (north tower: +z, camera side; south tower: -z), ground to the walkway level
    lz = zc + (TH + 0.3) * (1 if north else -1)
    for dx in (-0.25, 0.25):
        S.gbox((0.05, 7.4, 0.05), (-0.95 + dx, 0.4 + 3.7, lz), SATIN)
    for y in [0.9 + 0.6 * k for k in range(12)]:
        S.gbox((0.5, 0.04, 0.04), (-0.95, y, lz), SATIN)
    S.gbox((0.04, 7.3, 0.04), (-0.95, 0.4 + 3.65, lz + (0.32 if north else -0.32)), SATIN)       # cage spine
    if not north:
        S.gbox((0.6, 0.9, 0.04), (0, 1.6, zc + TH + 0.02), GRAPH2)                                  # service hatch
        S.text('CV-3', 0.42, B((TH + 0.016, 6.6, zc)), (math.pi / 2, 0, math.pi / 2), CYAN, mat=1)  # stencil
    else:
        S.text('CV-3', 0.36, B((TH + 0.006, top - 0.75, zc)), (math.pi / 2, 0, math.pi / 2), CYAN, mat=1)

tower(-TZ, False)
tower(TZ, True)

# ---------------------------------------------------------------- truss span (through Warren truss, 8 panels)
NP = 8; zs = [SPAN0 + (SPAN1 - SPAN0) * k / NP for k in range(NP + 1)]
for sx in (-1, 1):
    x = sx * (TH - 0.12)
    S.gseg((x, UND + 0.15, SPAN0 - 0.1), (x, UND + 0.15, SPAN1 + 0.1), 0.24, 0.3, WHITE2)         # bottom chord
    S.gseg((x, TC, SPAN0 - 0.1), (x, TC, SPAN1 + 0.1), 0.22, 0.24, WHITE2)                         # top chord
    for k, z in enumerate(zs):
        S.gseg((x, BC_T, z), (x, TC - 0.12, z), 0.14, 0.14, WHITE2)                               # posts
    for k in range(NP):
        za, zb = zs[k], zs[k + 1]
        if k % 2 == 0: S.gseg((x, BC_T, za), (x, TC - 0.1, zb), 0.1, 0.1, GRAPH1)                # diagonals
        else: S.gseg((x, TC - 0.1, za), (x, BC_T, zb), 0.1, 0.1, GRAPH1)
    S.gbox((0.02, 0.05, SPAN1 - SPAN0), (sx * (TH + 0.002), UND + 0.15, 0), GRAPH2)               # chord seam line
for z in zs[1:-1]:
    S.gseg((-(TH - 0.12), TC, z), ((TH - 0.12), TC, z), 0.1, 0.1, GRAPH1)                         # top struts
# fascia over the traffic lanes: amber / graphite chevrons on the camera-facing (+x) bottom chord, local z -6.6..6.0 (lanes)
n = 22; za0, za1 = -6.6, 6.0
for k in range(n):
    z0 = za0 + (za1 - za0) * k / n; z1 = za0 + (za1 - za0) * (k + 1) / n
    S.gquad([(TH + 0.005, UND + 0.04, z0), (TH + 0.005, UND + 0.04, z1), (TH + 0.005, UND + 0.26, z1), (TH + 0.005, UND + 0.26, z0)], AMBER if k % 2 == 0 else GRAPH)
# clearance plate under the deck (camera side), plain invented stencil
S.gbox((0.04, 0.36, 1.5), (TH + 0.05, UND - 0.2, 1.6), GRAPH2)
S.text('CLR 7.2m', 0.22, B((TH + 0.075, UND - 0.2, 1.6)), (math.pi / 2, 0, math.pi / 2), WHITE2, mat=0)
# deck: floor beams, plates
for z in zs:
    S.gseg((-(TH - 0.12), BC_T - 0.12, z), ((TH - 0.12), BC_T - 0.12, z), 0.12, 0.2, GRAPH)
S.gbox((2 * TH - 0.3, 0.1, SPAN1 - SPAN0), (0, DECK - 0.05, 0), GRAPH2)                           # deck plate
S.gbox((1.05, 0.02, SPAN1 - SPAN0), (-0.86, DECK + 0.01, 0), GRATE)                              # walkway grating
for z in [SPAN0 + 0.5 * k for k in range(1, int((SPAN1 - SPAN0) / 0.5))]:
    S.gbox((1.05, 0.012, 0.03), (-0.86, DECK + 0.025, z), GRAPH)                                 # grating lines
# walkway handrail (outer, west) + kick plate
xr = -(TH - 0.2)
S.gseg((xr, DECK + 1.05, SPAN0), (xr, DECK + 1.05, SPAN1), 0.05, 0.05, AMBER)
S.gseg((xr, DECK + 0.55, SPAN0), (xr, DECK + 0.55, SPAN1), 0.04, 0.04, SATIN)
S.gbox((0.02, 0.12, SPAN1 - SPAN0), (xr, DECK + 0.06, 0), AMBER)
for z in [SPAN0 + 1.0 * k for k in range(int(SPAN1 - SPAN0) + 1)]:
    S.gbox((0.05, 1.05, 0.05), (xr, DECK + 0.525, z), SATIN)
# conveyor frame: stringers, legs, side guards (white with graphite cap + panel seams), cyan status lights
GL, GR = CX - 0.78, CX + 0.78
for gx in (GL, GR):
    S.gbox((0.12, 0.3, SPAN1 - SPAN0), (gx, DECK + 0.2, 0), GRAPH)                               # stringer (roller axles)
    S.gbox((0.05, 0.5, SPAN1 - SPAN0), (gx + (0.06 if gx > CX else -0.06), RTOP + 0.2, 0), WHITE)   # side guard
    S.gbox((0.09, 0.04, SPAN1 - SPAN0), (gx + (0.06 if gx > CX else -0.06), RTOP + 0.47, 0), GRAPH2)  # guard cap
for z in [SPAN0 + 2.0 * k + 1.0 for k in range(int((SPAN1 - SPAN0) / 2.0))]:
    S.gbox((0.03, 0.46, 0.025), (GR + 0.09, RTOP + 0.2, z - 0.98), GRAPH2)                       # guard panel seams
    S.gbox((0.05, 0.08, 0.14), (GR + 0.1, RTOP + 0.34, z), CYAN, mat=1)                           # status lights (camera side)
S.gbox((0.025, 0.05, SPAN1 - SPAN0 - 0.4), (GR + 0.1, RTOP + 0.06, 0), CYAN, mat=1)               # cyan run strip along the guard foot
# cable tray under the walkway side
S.gbox((0.3, 0.08, SPAN1 - SPAN0), (-0.9, UND + 0.05, 0), GRAPH1)

# ---------------------------------------------------------------- south infeed stub (from the HELIUM-3 pack-out, -z) : static
S.gbox((1.9, 0.1, 3.4), (CX, 0.85, -TZ - TH - 1.7), GRAPH)
for dz in (-2.9, -0.7):
    for gx in (CX - 0.75, CX + 0.75):
        S.gbox((0.1, 0.8, 0.1), (gx, 0.4, -TZ - TH + dz), GRAPH1)
for k in range(8):
    S.gcyl((CX - 0.7, 0.93, -TZ - TH - 0.25 - k * 0.42), (CX + 0.7, 0.93, -TZ - TH - 0.25 - k * 0.42), 0.07, SATIN, segs=6, caps=False)
for gx in (CX - 0.85, CX + 0.85):
    S.gbox((0.05, 0.35, 3.4), (gx, 1.1, -TZ - TH - 1.7), WHITE)
S.gbox((2.2, 2.3, 1.0), (CX, 1.15, -TZ - TH - 3.7), WHITE)                                         # pack-out hood
S.gbox((2.24, 0.06, 1.04), (CX, 2.33, -TZ - TH - 3.7), GRAPH2)
S.gbox((1.6, 0.05, 0.02), (CX, 2.0, -TZ - TH - 3.19), CYAN, mat=1)

# ---------------------------------------------------------------- north transfer: tip-down roller chute (+x) + pickup table
X0 = TH                          # chute starts at the tower's east face
XT0, XT1 = PICK[0] - 1.35, PICK[0] + 1.4   # pickup table extent (2.35 .. 5.1)
def chute_y(x):                  # roller top height along the chute / table
    if x <= X0: return LOW_Y
    if x >= XT0: return PICK[1]
    return LOW_Y + (PICK[1] - LOW_Y) * (x - X0) / (XT0 - X0)
zc = TZ
for sz in (-1, 1):
    z = zc + sz * 0.8
    S.gseg((X0 - 0.05, LOW_Y - 0.2, z), (XT0, PICK[1] - 0.2, z), 0.1, 0.22, GRAPH)                 # chute stringers (tipped down)
    S.gseg((X0 - 0.05, LOW_Y + 0.22, z + sz * 0.06), (XT0, PICK[1] + 0.22, z + sz * 0.06), 0.05, 0.3, WHITE)   # chute guards
    S.gbox((XT1 - XT0, 0.22, 0.1), ((XT0 + XT1) / 2, PICK[1] - 0.2, z), GRAPH)                      # table stringers
    S.gbox((XT1 - XT0 - 0.3, 0.06, 0.06), ((XT0 + XT1) / 2 - 0.15, PICK[1] + 0.32, z + sz * 0.12), SATIN)   # side guide rails
    for x in (XT0 + 0.15, XT1 - 0.15, X0 + 0.3):
        y = chute_y(x) - 0.3
        S.gbox((0.12, y, 0.12), (x, y / 2, z), GRAPH1)                                             # legs
S.gbox((0.2, 0.42, 1.7), (XT1 + 0.05, PICK[1] + 0.12, zc), AMBER)                                  # end stop bumper
S.gbox((0.06, 0.12, 1.72), (XT1 + 0.16, PICK[1] + 0.12, zc), GRAPH)
S.gbox((XT1 - X0 + 0.4, 0.12, 2.3), ((X0 + XT1) / 2, 0.06, zc), CONC)                               # slab under chute + table
S.gbox((XT1 - XT0, 0.025, 0.04), ((XT0 + XT1) / 2, PICK[1] - 0.12, zc + 0.86), CYAN, mat=1)      # table cyan strip (camera side)
# ready lamp post + control box
S.gcyl((XT1 - 0.3, 0.12, zc + 1.35), (XT1 - 0.3, 2.3, zc + 1.35), 0.05, GRAPH, segs=6)
S.gbox((0.22, 0.22, 0.22), (XT1 - 0.3, 2.42, zc + 1.35), CYAN, mat=1)
S.gbox((0.5, 0.7, 0.32), (XT0 + 0.2, 0.75, zc + 1.4), WHITE)
S.gbox((0.3, 0.2, 0.02), (XT0 + 0.2, 0.9, zc + 1.565), CYAN, mat=1)
S.gbox((0.08, 0.6, 0.1), (XT0 + 0.2, 0.25, zc + 1.4), GRAPH1)

# ---------------------------------------------------------------- rollers (each its own bone; roller_spin clip)
R_R = 0.09
ROLL = []    # (bone name, head glTF, axis 'x' | 'z')
k = 0
z = SPAN0 + 0.2
while z < SPAN1 - 0.1:
    k += 1; nme = 'Roller_B%02d' % k; ROLL.append((nme, (CX, RTOP - R_R, z), 'x'))
    M.gcyl((CX - 0.72, RTOP - R_R, z), (CX + 0.72, RTOP - R_R, z), R_R, SATIN, segs=6, bone=nme, caps=False)
    z += 0.45
k = 0
x = X0 + 0.15
while x < XT1 - 0.1:
    k += 1; nme = 'Roller_T%02d' % k; y = chute_y(x) - R_R; ROLL.append((nme, (x, y, zc), 'z'))
    M.gcyl((x, y, zc - 0.74), (x, y, zc + 0.74), R_R, SATIN, segs=6, bone=nme, caps=False)
    x += 0.38

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
# box rest poses (a plausible frame): Box_1 on the pickup table, Box_2 mid-bridge, Box_3 in the south tower shaft
BOX_REST = {'Box_1': (PICK, 0.0), 'Box_2': ((CX, RTOP, 1.0), 90.0), 'Box_3': ((0.0, 1.2, -TZ), 90.0)}
for nme, (p, yaw) in BOX_REST.items(): bone(nme, p, 'Bridge_Base')
for nme, h, ax in ROLL: bone(nme, h, 'Bridge_Base')
bpy.ops.object.mode_set(mode='OBJECT')
ob_m = M.build('Bridge_Moving')
gi = {g.index: g.name for g in ob_m.vertex_groups}
for v in ob_m.data.vertices:
    g = gi[v.groups[0].group]
    if g in BOX_REST:
        p, yaw = BOX_REST[g]
        v.co = Matrix.Translation(B(p)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ v.co
if 'root' in ob_m.vertex_groups: ob_m.vertex_groups['root'].name = 'Bridge_Base'
ob_m.parent = arm; ob_m.matrix_parent_inverse = Matrix.Identity(4)
ob_m.location = (0, 0, 0)
md = ob_m.modifiers.new('Armature', 'ARMATURE'); md.object = arm
ob_s = S.build('Bridge_Static'); ob_s.parent = arm; ob_s.location = (0, 0, 0)
# the rest-pose box geometry was baked in armature space at the bone heads -> the skin bind is the rest pose.

# ---------------------------------------------------------------- box_convey clip (3 boxes, phase T/3 apart)
V = 1.5; TA = 1.0                # belt speed m/s, smooth ramp time at each end of a run
def run_time(d): return d / V + TA
def run_frac(t, d):              # distance fraction along a run of length d at time t (smoothstep velocity ramps, eased ends)
    T = run_time(d)
    if t <= 0: return 0.0
    if t >= T: return 1.0
    def ramp_dist(u):            # distance covered in the first u s of an accel ramp, v(u) = V*smoothstep(u/TA)
        x = u / TA; return V * TA * (x ** 3 - 0.5 * x ** 4)
    if t < TA: s = ramp_dist(t)
    elif t > T - TA: s = d - ramp_dist(T - t)
    else: s = ramp_dist(TA) + V * (t - TA)
    return s / d
def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
P0 = (0.0, 1.2, -TZ); P1 = (CX, RTOP, -TZ); P2 = (CX, RTOP, TZ); P3 = (0.0, LOW_Y, TZ); P4 = PICK
def dist(a, b): return (Vector(b) - Vector(a)).length
TURN = 1.2; DWELL = 3.0
SEG = [('rise', P0, P1, run_time(dist(P0, P1))), ('bridge', P1, P2, run_time(dist(P1, P2))), ('lower', P2, P3, run_time(dist(P2, P3))),
       ('turn', P3, P3, TURN), ('chute', P3, P4, run_time(dist(P3, P4))), ('dwell', P4, P4, DWELL)]
T_PATH = sum(s[3] for s in SEG)
CLIP = round(math.ceil(T_PATH + 0.6), 1)       # loop length (s)
OFF = CLIP / 3.0
def chute_pitch(xc):             # box tilts over the kink of the tip-down chute (deg, nose down toward +x)
    xa, xb = X0, XT0
    if xc <= xa - 1.15 or xc >= xb + 1.15: return 0.0
    ang = math.degrees(math.atan2(LOW_Y - PICK[1], XT0 - X0))
    u = (xc - (xa - 1.15)) / ((xb + 1.15) - (xa - 1.15))
    return ang * math.sin(math.pi * u)
def box_state(t):                # t in [0, CLIP): returns (pos, yaw_deg, pitch_deg, scale)
    t0 = 0.0
    if t < 0.05: return P0, 90.0, 0.0, 0.001                    # pop in, hidden at the bottom of the south shaft
    for name, a, b, d in SEG:
        if t < t0 + d:
            u = t - t0
            if name == 'turn': return a, 90.0 - 90.0 * smooth(u / d), 0.0, 1.0
            if name == 'dwell': return a, 0.0, 0.0, 1.0
            f = run_frac(u, dist(a, b)); p = Vector(a).lerp(Vector(b), f)
            yaw = 90.0 if name in ('rise', 'bridge', 'lower') else 0.0
            pitch = chute_pitch(p.x) if name == 'chute' else 0.0
            if name == 'chute':
                p.y = chute_y(p.x - 1.15) * 0.5 + chute_y(p.x + 1.15) * 0.5 if p.x > X0 - 1.15 else LOW_Y
                p.y = max(p.y, PICK[1])
            return tuple(p), yaw, pitch, 1.0
        t0 += d
    return P4, 0.0, 0.0, (1.0 if t < T_PATH + 0.05 else 0.001)   # picked: hidden (Coder swaps in the crane's real box)
EV = {}
t0 = 0.0
for name, a, b, d in SEG: EV[name] = [round(t0, 3), round(t0 + d, 3)]; t0 += d
print('CLIP', CLIP, 'T_PATH', round(T_PATH, 3), 'EV', EV)
FPS = 30; NF = int(round(CLIP * FPS))
act = bpy.data.actions.new('box_convey'); arm.animation_data_create(); arm.animation_data.action = act
pb = arm.pose.bones
for nme in BOX_REST: pb[nme].rotation_mode = 'XYZ'
for f in range(NF + 1):
    for i in range(3):
        nme = 'Box_%d' % (i + 1); rest_p, rest_yaw = BOX_REST[nme]
        t = (f / FPS - i * OFF) % CLIP
        p, yaw, pitch, s = box_state(t)
        # bone local axes = glTF axes; rest has yaw rest_yaw baked into the geometry around the head
        d = Vector(p) - Vector(rest_p)
        pb[nme].location = d
        # rotation about bone Y (= up) by (yaw - rest_yaw), then pitch about the box's own z (glTF) after the yaw
        R = Matrix.Rotation(math.radians(yaw - rest_yaw), 3, 'Y') @ Matrix.Rotation(math.radians(-pitch), 3, 'Z')
        pb[nme].rotation_euler = R.to_euler('XYZ')
        pb[nme].scale = (s, s, s)
        pb[nme].keyframe_insert('location', frame=f); pb[nme].keyframe_insert('rotation_euler', frame=f); pb[nme].keyframe_insert('scale', frame=f)
for fc in act.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
arm.animation_data.action = None
tr = arm.animation_data.nla_tracks.new(); tr.name = 'box_convey'; tr.strips.new('box_convey', 0, act); tr.mute = True
# ---------------------------------------------------------------- roller_spin clip (one turn, 0.4 s -> roller surface 1.41 m/s)
SPIN = 0.4
act2 = bpy.data.actions.new('roller_spin'); arm.animation_data.action = act2
NS = 12
for nme, h, ax in ROLL: pb[nme].rotation_mode = 'XYZ'
for kk in range(NS + 1):
    f = SPIN * FPS * kk / NS; a = math.tau * kk / NS
    for nme, h, ax in ROLL:
        # bridge rollers: top surface moves +z -> +rotation about x;  chute/table rollers: top moves +x -> -rotation about glTF z (= bone Z)
        pb[nme].rotation_euler = (a, 0, 0) if ax == 'x' else (0, 0, -a)
        pb[nme].keyframe_insert('rotation_euler', frame=f)
for fc in act2.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
arm.animation_data.action = None
tr2 = arm.animation_data.nla_tracks.new(); tr2.name = 'roller_spin'; tr2.strips.new('roller_spin', 0, act2); tr2.mute = True
for p_ in pb: p_.location = (0, 0, 0); p_.rotation_euler = (0, 0, 0); p_.scale = (1, 1, 1)

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
   'note': 'box Base on the pickup table (long axis +X, label +Z) where box_convey stops each box; RC-1 picks it here and drops on FB-05'})
gm('Box_Infeed', P0, {'kind': 'path', 'refinery_xyz': REF(P0), 'note': 'box appears here, hidden inside the south lift shaft'})
gm('Bridge_Entry', P1, {'kind': 'path', 'refinery_xyz': REF(P1)})
gm('Bridge_Exit', P2, {'kind': 'path', 'refinery_xyz': REF(P2)})
gm('Lowerator_Bottom', P3, {'kind': 'path', 'refinery_xyz': REF(P3)})
arm['prop'] = 'CV-3 box bridge: truss gantry over the RD-1 haul trails with an enclosed box conveyor to the RC-1 crane pickup table'
arm['origin_note'] = ('This GLB root node "Refinery_Bridge" is already translated to Refinery-local (-22, 0, 4.8). Add the GLB scene as a child of the '
                      'Refinery root (or at the Refinery station position, world (320, 0, 0) for station 2): no extra offset, yaw 0. '
                      'Bridge-local axes = Refinery axes (glTF, Y up, bridge runs along +Z toward the camera; +X = Cargo Dock / Launch Pad side).')
arm['placement_refinery'] = {'position': list(ROOT), 'yaw_deg': 0}
arm['placement_world'] = {'position': [ROOT[0] + 320, 0, ROOT[2]], 'yaw_deg': 0, 'assumes_refinery_at': [320, 0, 0]}
arm['footprint_refinery'] = {'south_tower_footing_xz': [[-23.95, -20.05], [-6.55, -2.65]], 'north_tower_footing_xz': [[-23.95, -20.05], [12.25, 16.15]],
                             'chute_table_xz': [[-20.65, -16.5], [13.05, 15.35]], 'deck_underside_y': UND, 'top_y': 11.9,
                             'haul_lanes_z': '0 and 9 (toe -1.8 .. 11.8): both footings outside, span clear 7.2 m (HT-04 bed up max 5.75 m)'}
arm['clearance_m'] = UND
arm['draws'] = 4
arm['clips'] = {'box_convey': {'duration_s': CLIP, 'loop': True, 'boxes': 3, 'phase_s': round(OFF, 3), 'speed_mps': V, 'ramp_s': TA,
                               'per_box_events_s': EV, 'pickup_arrive_s': EV['chute'][1], 'hidden_after_s': round(T_PATH + 0.05, 3),
                               'note': 'Box_N runs this timeline shifted by (N-1)*phase_s. Box rises hidden in the south shaft, crosses the bridge, drops in the north lowerator, turns 90 deg out of sight, rolls down the tip-down chute and stops on Pickup_Point, waits dwell s, then scales to 0 (the crane takes it: show the crane box from Pickup_Point at that moment).'},
                'roller_spin': {'duration_s': SPIN, 'loop': True, 'note': 'one roller turn; surface speed ~1.41 m/s. Play together with box_convey'}}
sc.frame_set(0)
export(OUT, anim=True)
print('WROTE', OUT, 'ROLLERS', len(ROLL), 'PICK_SOLVE', TH_, R_, L_)
