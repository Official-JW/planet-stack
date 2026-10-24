# Proof renders for crew_boarding.glb over the (read-only, unpacked) launch pad.
# Poses come from dump_poses.mjs (three r186 CPU skinning of the shipped GLB), so the proofs show exactly what the game plays.
# blender -b -t 4 -P render_proofs.py -- --pad /tmp/lp_plain.glb --poses /tmp/bpose6 --engine WORKBENCH|BLENDER_EEVEE_NEXT|CYCLES
#     --cam game|close|follow|focus --out DIR [--w 393 --h 852 --samples 24 --save-blend X.blend --fw 78.25]
#     focus cam: --focus X,Y,Z (glTF, = Board_Focus) --dist D : game orientation (38 deg vFOV, 18 deg look-down, game yaw) at distance D from the focus
# game cam: 38 deg vertical FOV, 18 deg look-down, aimed at Cam_Target glTF (0,4,-0.7), framed to frame_w across the portrait width.
import bpy, sys, json, math, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
A = {}
i = 0
while i < len(argv):
    A[argv[i].lstrip('-')] = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else '1'; i += 2 if i + 1 < len(argv) and not argv[i + 1].startswith('--') else 1
W, H = int(A.get('w', 393)), int(A.get('h', 852)); ENG = {'WORKBENCH': 'BLENDER_WORKBENCH', 'EEVEE': 'BLENDER_EEVEE_NEXT'}.get(A.get('engine', 'WORKBENCH'), A.get('engine', 'WORKBENCH')); CAM = A.get('cam', 'game')
OUT = A['out']; os.makedirs(OUT, exist_ok=True)
meta = json.load(open(A['poses'] + '.json')); V = meta['nverts']; T = meta['times']
P = np.fromfile(A['poses'] + '_pos.bin', np.float32).reshape(len(T), 4, V, 3)
mb = np.fromfile(A['poses'] + '_mesh.bin', np.uint8)
tri = np.frombuffer(mb[:meta['ntris'] * 12].tobytes(), np.uint32).reshape(-1, 3)
col = np.frombuffer(mb[meta['ntris'] * 12:].tobytes(), np.float32).reshape(-1, 3)
def g2b(p):  # glTF (x,y,z) -> Blender (x,-z,y)
    p = np.asarray(p, float); return np.stack([p[..., 0], -p[..., 2], p[..., 1]], -1)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=A.get('pad', '/tmp/lp_plain.glb'))
for o in list(sc.objects):
    if o.name.startswith('Tier_') or any(a.name.startswith('Tier_') for a in [o.parent] if a):
        o.hide_render = True; o.hide_viewport = True
    if o.type == 'CAMERA' or o.type == 'LIGHT': bpy.data.objects.remove(o)
# crew material: vertex colour (linear) -> Principled, roughness 0.42 (SHM_Paint)
mat = bpy.data.materials.new('SHM_Paint'); mat.use_nodes = True; nt = mat.node_tree
bs = nt.nodes['Principled BSDF']; at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'
nt.links.new(at.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.42; bs.inputs['Metallic'].default_value = 0.0
mat.diffuse_color = (0.85, 0.85, 0.82, 1)
crew = []
for k in range(4):
    me = bpy.data.meshes.new(f'Crew_{k+1}'); me.from_pydata(g2b(P[0, k]).tolist(), [], tri.tolist())
    a = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT'); a.data.foreach_set('color', np.c_[col, np.ones(len(col))].ravel().astype(np.float32))
    me.color_attributes.active_color = a; me.color_attributes.render_color_index = 0
    me.materials.append(mat); me.shade_smooth() if hasattr(me, 'shade_smooth') else None
    ob = bpy.data.objects.new(f'Crew_{k+1}', me); sc.collection.objects.link(ob); crew.append(ob)
def set_pose(ti):
    for k, ob in enumerate(crew):
        ob.data.vertices.foreach_set('co', g2b(P[ti, k]).astype(np.float32).ravel()); ob.data.update()
        ob.hide_render = not meta['visible'][ti][k]
# light + world
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35)); sun.data.angle = math.radians(1.0)
wd = bpy.data.worlds.new('W'); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.022, 0.03, 1); wd.node_tree.nodes['Background'].inputs[1].default_value = 1.0
# camera
cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(38); cd.clip_end = 1000.0; cam.rotation_euler = (math.radians(72), 0, 0)
asp = W / H; TGT = g2b([0, 4, -0.7])
def place(tgt_b, fw):
    d = (fw / 2) / (math.tan(math.radians(19)) * asp)
    cam.location = (tgt_b[0], tgt_b[1] - d * math.cos(math.radians(18)), tgt_b[2] + d * math.sin(math.radians(18)))
# close/follow target: centroid of visible crew (smoothed over time for follow)
cent = []
for ti in range(len(T)):
    vis = [k for k in range(4) if meta['visible'][ti][k]] or [3]
    c = g2b(P[ti, vis].reshape(-1, 3).mean(0)); cent.append(c)
cent = np.array(cent)
if CAM == 'follow' and len(T) > 3:
    sig = float(A.get('sigma', 2.0)) / max(T[1] - T[0], 1e-3); n = int(3 * sig) + 1; kx = np.exp(-0.5 * (np.arange(-n, n + 1) / sig) ** 2); kx /= kx.sum()
    pad = np.pad(cent, ((n, n), (0, 0)), mode='edge'); cent = np.stack([np.convolve(pad[:, j], kx, 'valid') for j in range(3)], 1)
# render settings
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100; r.image_settings.file_format = 'PNG'
r.engine = ENG
if ENG == 'CYCLES':
    sc.cycles.samples = int(A.get('samples', 24)); sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
elif ENG == 'BLENDER_WORKBENCH':
    # Workbench can't read node materials: bake each pad material's base colour into a 'Col' corner attribute so one ATTRIBUTE pass shows pad + crew
    for o in sc.objects:
        if o.type != 'MESH' or o.name.startswith('Crew_'): continue
        me = o.data
        if len(me.color_attributes):  # pad already carries its glTF COLOR_0 ('Color'); make it the active/render colour
            me.color_attributes.active_color = me.color_attributes[0]; me.color_attributes.render_color_index = 0; continue
        bc = []
        for m in me.materials:
            c = (0.6, 0.6, 0.6, 1)
            if m and m.use_nodes:
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if b: c = tuple(b.inputs['Base Color'].default_value)
            bc.append(c)
        bc = bc or [(0.6, 0.6, 0.6, 1)]
        a = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER'); cc = np.zeros((len(me.loops), 4), np.float32)
        for poly in me.polygons: cc[poly.loop_start:poly.loop_start + poly.loop_total] = bc[min(poly.material_index, len(bc) - 1)]
        a.data.foreach_set('color', cc.ravel()); me.color_attributes.active_color = a
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_shadows = True; sh.show_cavity = False
    sh.background_type = 'WORLD'; wd.color = (0.02, 0.022, 0.03)
    sc.display.shadow_focus = 0.6
else:
    try: sc.eevee.taa_render_samples = int(A.get('samples', 16))
    except Exception: pass
sc.view_settings.view_transform = 'Standard' if ENG == 'BLENDER_WORKBENCH' else 'AgX'
FW = float(A.get('fw', 78.25 if CAM == 'game' else 14.0))
for ti, t in enumerate(T):
    set_pose(ti)
    if CAM == 'focus':
        F = g2b([float(v) for v in A['focus'].split(',')]); d = float(A['dist'])
        cam.location = (F[0], F[1] - d * math.cos(math.radians(18)), F[2] + d * math.sin(math.radians(18)))
    else: place(TGT if CAM == 'game' else cent[ti] + np.array([0, 0, 2.0]), FW)
    r.filepath = os.path.join(OUT, A.get('pattern', 'f_%04d.png') % ti); bpy.ops.render.render(write_still=True)
    print('RENDERED', t, r.filepath, flush=True)
if 'save-blend' in A:
    set_pose(0); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(A['save-blend']), compress=True)
    print('SAVED', A['save-blend'])
