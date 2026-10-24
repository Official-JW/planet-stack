"""Planet Stack - crew role renders (lineup still + card hero renders).
blender -b -t 4 -P render_roles.py -- --mode lineup|card|preview --out DIR [--roles miner,mine_driver,...] [--engine CYCLES|WORKBENCH|EEVEE]
        [--samples 128] [--pct 100] [--save-blend X.blend]
lineup : 1920x1080, the given roles side by side on a neutral lunar-grey seamless ground, soft studio light. Writes lineup_raw.png +
         lineup_layout.json (screen x of each figure's centre / feet y, for the caption pass in make_cards.py).
card   : per role a 3/4 hero render (750x780, transparent film + shadow catcher ground) -> hero_<role>.png for make_cards.py.
preview: Workbench close-ups of the tool hand + helmet for clipping checks."""
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import role_kit as RK, roles_table as RT
import mc_common
from mc_common import hexc, _nodes, setup_render, shoot
from bpy_extras.object_utils import world_to_camera_view

av = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
A = {av[i].lstrip('-'): av[i + 1] for i in range(0, len(av) - 1, 2)}
MODE = A.get('mode', 'preview'); OUT = A.get('out', '/tmp/roles_out'); os.makedirs(OUT, exist_ok=True)
ROLES = A.get('roles', ','.join(RT.ORDER)).split(',')
ENG = A.get('engine', 'CYCLES'); SAMP = int(A.get('samples', 128))
sc = mc_common.reset()
cam = setup_render(SAMP)
sc.render.threads_mode = 'FIXED'; sc.render.threads = int(A.get('threads', 4)); sc.cycles.tile_size = 512
sc.cycles.adaptive_threshold = 0.015
if A.get('pct'): sc.render.resolution_percentage = int(A['pct'])
st = mc_common.coll('Stage')

# ---------------- world: neutral soft grey (studio bounce), not visible to camera in card mode
w = bpy.data.worlds.new('Studio'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = hexc('#5d6168'); bg.inputs['Strength'].default_value = 0.35

# ---------------- ground: seamless lunar-grey cyclorama (floor curving into a back wall), fine regolith grain
gm = bpy.data.materials.new('G_Lunar'); nt, gb = _nodes(gm); N, L = nt.nodes, nt.links
gb.inputs['Roughness'].default_value = 0.9
tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6
L.new(tc.outputs['Object'], nz.inputs['Vector'])
mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[6].default_value = hexc('#77767a'); mx.inputs[7].default_value = hexc('#8a8986')
L.new(nz.outputs['Fac'], mx.inputs['Factor']); L.new(mx.outputs[2], gb.inputs['Base Color'])
nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 140.0; nz2.inputs['Detail'].default_value = 3; L.new(tc.outputs['Object'], nz2.inputs['Vector'])
bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; L.new(nz2.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], gb.inputs['Normal'])
gm.diffuse_color = hexc('#808082')
bm = bmesh.new(); Wd, Rb, Y0 = 12.0, 3.0, 2.2
prof = [(-10.0, 0.0)] + [(Y0 * i / 8, 0.0) for i in range(1, 9)] + [(Y0 + Rb * math.sin(math.pi / 2 * i / 20), Rb * (1 - math.cos(math.pi / 2 * i / 20))) for i in range(1, 21)] + [(Y0 + Rb, 12.0)]
rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in [-Wd + 2 * Wd * i / 8 for i in range(9)]]
for r0, r1 in zip(rows, rows[1:]):
    for j in range(len(r0) - 1): bm.faces.new((r0[j], r1[j], r1[j + 1], r0[j + 1]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Cyc'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
cyc = bpy.data.objects.new('Cyc', me); st.objects.link(cyc); me.materials.append(gm)
if me.polygons[0].normal.z < 0: me.flip_normals()

def area(name, loc, target, size, energy, col='#ffffff', sy=None, spec=True, diff=True):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = hexc(col)[:3]; ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = sy or size
    lo = bpy.data.objects.new(name, ld); st.objects.link(lo); lo.location = loc
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    lo.visible_glossy = spec; lo.visible_diffuse = diff; return lo
# soft studio: big warm-neutral key front-left/high, cool fill right, two rims behind, a strip card for visor/clearcoat highlights
area('Key', (-3.2, -4.2, 4.6), (0, 0, 1.0), 3.2, 1500, '#fff6ec')
area('Fill', (4.2, -3.4, 2.2), (0, 0, 1.0), 3.5, 520, '#e6eeff')
area('RimL', (-3.0, 3.2, 3.0), (0, 0, 1.3), 1.6, 650, '#dbe8ff')
area('RimR', (3.2, 3.0, 3.2), (0, 0, 1.3), 1.6, 650, '#dbe8ff')
area('Top', (0, -0.5, 5.5), (0, 0, 0), 4.0, 400, '#ffffff')
area('VisorCard', (0.8, -3.0, 2.8), (0, 0, 1.6), 2.8, 60, '#ffffff', sy=0.4, diff=False)

def preview_colors():
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = True
    for m in bpy.data.materials:
        if m.use_nodes and 'Principled BSDF' in m.node_tree.nodes:
            b = m.node_tree.nodes['Principled BSDF']; c = list(b.inputs['Base Color'].default_value)
            if b.inputs['Emission Strength'].default_value > 1: c = list(b.inputs['Emission Color'].default_value)
            m.diffuse_color = c

if ENG == 'WORKBENCH': pass
elif ENG == 'EEVEE': sc.render.engine = 'BLENDER_EEVEE_NEXT'

lay = {}
if MODE == 'lineup':
    # all roles in one row; W x H frame, camera distance solved so the row fills ~92 % of the width
    n = len(ROLES); gap = float(A.get('gap', 0.95)); XOFF = float(A.get('xoff', 0.0))
    W_, H_ = int(A.get('w', 3200)), int(A.get('h', 1200)); LENS = float(A.get('lens', 70))
    for i, k in enumerate(ROLES):
        x = (i - (n - 1) / 2) * gap + XOFF
        RK.role_member(k, (x, 0, 0), math.radians(-14))
    if ENG == 'WORKBENCH': preview_colors()
    span = (n - 1) * gap + 0.9; hf = 2 * math.atan(18 / LENS); dist = span / 0.92 / 2 / math.tan(hf / 2)
    tgt = Vector((0, 0, 0.95)); pos = Vector((0, -dist, 0.95 + dist * math.tan(math.radians(3))))
    path = os.path.join(OUT, 'lineup_raw.png')
    sc.render.resolution_x, sc.render.resolution_y = W_, H_
    cam.data.sensor_fit = 'HORIZONTAL'; cam.data.sensor_width = 36
    cam.data.lens = LENS; cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
    for i, k in enumerate(ROLES):
        x = (i - (n - 1) / 2) * gap + XOFF
        top = world_to_camera_view(sc, cam, Vector((x, 0, 1.86))); feet = world_to_camera_view(sc, cam, Vector((x, 0, 0)))
        lay[k] = dict(x=feet.x * W_, feet_y=(1 - feet.y) * H_, top_y=(1 - top.y) * H_)
    json.dump(dict(w=W_, h=H_, figures=lay), open(os.path.join(OUT, 'lineup_layout.json'), 'w'), indent=1)
    shoot(cam, path, tuple(tgt), tuple(pos), W_, H_, lens=LENS, samples=SAMP)
elif MODE == 'portrait':
    # pick-screen card portrait: 3/4 front from the tool-hand side, helmet to mid-thigh, transparent film (420 x 432 = card window)
    cyc.is_shadow_catcher = True; cyc.visible_camera = False; sc.render.film_transparent = True
    SS = float(A.get('ss', 2))           # supersample: render SS x, cards3x.py downsizes with Lanczos
    for k in ROLES:
        root = RK.role_member(k, (0, 0, 0), 0.0)
        if ENG == 'WORKBENCH': preview_colors()
        a = math.radians(float(A.get('az', RT.ROLES[k].get('card_az', -24))))
        tgt = Vector((0, 0, float(A.get('tz', 1.2)))); d = float(A.get('dist', 2.75))
        pos = Vector((d * math.sin(a), -d * math.cos(a), float(A.get('cz', 1.42))))
        shoot(cam, os.path.join(OUT, f'portrait_{k}.png'), tuple(tgt), tuple(pos), int(420 * SS), int(432 * SS), lens=float(A.get('lens', 62)), samples=SAMP)
        for ob in [root] + list(root.children_recursive): bpy.data.objects.remove(ob, do_unlink=True)
elif MODE == 'card':
    cyc.is_shadow_catcher = True; sc.render.film_transparent = True
    for k in ROLES:
        root = RK.role_member(k, (0, 0, 0), 0.0)
        if ENG == 'WORKBENCH': preview_colors()
        a = math.radians(float(A.get('az', RT.ROLES[k].get('card_az', -30))))   # camera on the crew member's right (tool hand) side, 3/4 front
        tgt = Vector((0, 0, float(A.get('tz', 0.96)))); d = float(A.get('dist', 3.75))
        pos = Vector((d * math.sin(a), -d * math.cos(a), float(A.get('cz', 1.3))))
        shoot(cam, os.path.join(OUT, f'hero_{k}.png'), tuple(tgt), tuple(pos), int(A.get('w', 750)), int(A.get('h', 780)), lens=float(A.get('lens', 62)), samples=SAMP)
        if A.get('save-blend'): bpy.ops.wm.save_as_mainfile(filepath=A['save-blend'].replace('.blend', f'_{k}.blend'), compress=True)
        for ob in [root] + list(root.children_recursive): bpy.data.objects.remove(ob, do_unlink=True)
elif MODE == 'preview':
    for k in ROLES:
        root = RK.role_member(k, (0, 0, 0), 0.0)
        preview_colors()
        g = RK.GRIP.get('c') if False else None
        hb = [o for o in root.children if o.name.startswith('GlovePalm')]
        hc = min((sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8 for o in hb), key=lambda v: v.x)
        views = (('full', (0, 0, 1.05), (-1.9, -3.2, 1.45), 50, (600, 800)),
                 ('hand', tuple(hc), tuple(hc + Vector((-0.42, -0.4, 0.15))), 60, (600, 600)),
                 ('hand2', tuple(hc), tuple(hc + Vector((0.2, -0.55, -0.25))), 60, (600, 600)),
                 ('helmet', (0, 0, 1.62), (-0.95, -0.9, 1.85), 60, (600, 600)))
        for nm, tgt, pos, lens, wh in views:
            shoot(cam, os.path.join(OUT, f'pv_{k}_{nm}.png'), tgt, pos, *wh, lens=lens)
        for ob in [root] + list(root.children_recursive): bpy.data.objects.remove(ob, do_unlink=True)
elif MODE == 'game':
    # in-game-size proof: game camera 38 deg vertical FOV, 18 deg look-down, figures ~20 px tall at 375x667, on open lunar rock
    bpy.data.objects.remove(cyc, do_unlink=True)
    for o in [o for o in st.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o, do_unlink=True)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=400.0)
    me = bpy.data.meshes.new('Ground'); bm.to_mesh(me); bm.free(); gnd = bpy.data.objects.new('Ground', me); st.objects.link(gnd); me.materials.append(gm)
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3.2; sd.angle = math.radians(4); so = bpy.data.objects.new('Sun', sd); st.objects.link(so)
    so.rotation_euler = (math.radians(48), 0, math.radians(-35))
    bg.inputs['Strength'].default_value = 0.9
    sp = float(A.get('spacing', 2.4)); n = len(ROLES)
    for i, k in enumerate(ROLES): RK.role_member(k, ((i - (n - 1) / 2) * sp, 0, 0), 0.0)
    if ENG == 'WORKBENCH': preview_colors()
    cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24.0
    lens = 24.0 / (2 * math.tan(math.radians(19)))
    H = 1.86; px = float(A.get('px', 21)); d = 667 * H / (px * 2 * math.tan(math.radians(19)))
    tilt = math.radians(18); tgt = Vector((0, 0, 0.9))
    for view, sgn in (('front', -1), ('back', 1)):
        pos = tgt + Vector((0, sgn * d * math.cos(tilt), d * math.sin(tilt)))
        shoot(cam, os.path.join(OUT, f'game_{view}_375x667.png'), tuple(tgt), tuple(pos), 375, 667, lens=lens, samples=SAMP)
        bpy.context.view_layer.update()
        hs = []
        for i, k in enumerate(ROLES):
            x = (i - (n - 1) / 2) * sp
            a_ = world_to_camera_view(sc, cam, Vector((x, 0, 0))); b_ = world_to_camera_view(sc, cam, Vector((x, 0, H)))
            hs.append(dict(role=k, x=a_.x * 375, feet_y=(1 - a_.y) * 667, h_px=(b_.y - a_.y) * 667))
        json.dump(dict(dist_m=d, lens=lens, figures=hs), open(os.path.join(OUT, f'game_{view}_layout.json'), 'w'), indent=1)
elif MODE == 'badges':
    # close-up of the helmet badge (crew member's right temple) on each role, one 480x480 tile per role
    for i, k in enumerate(ROLES):
        x = i * 4.0; RK.role_member(k, (x, 0, 0), 0.0)
    if ENG == 'WORKBENCH': preview_colors()
    for i, k in enumerate(ROLES):
        x = i * 4.0; tgt = Vector((x - 0.08, 0.0, 1.67)); pos = Vector((x - 1.15, -0.7, 1.86))
        shoot(cam, os.path.join(OUT, f'badge_tile_{k}.png'), tuple(tgt), tuple(pos), 480, 480, lens=85, samples=SAMP)
if A.get('save-blend') and MODE == 'lineup': bpy.ops.wm.save_as_mainfile(filepath=A['save-blend'], compress=True)
print('DONE', MODE, flush=True)
