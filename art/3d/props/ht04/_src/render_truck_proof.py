"""Truck / road proof renders (CPU Cycles, OIDN). Inputs must be unpacked first: gltfpack -i X.glb -o X_plain.glb -noq -kn -ke
blender -b -P render_truck_proof.py -- --out PNG --w W --h H --samples N --glb PLAIN[@x,z,yaw_deg] [--glb ...]
   [--road SEG_PLAIN --road_tiles x0,n,z] [--engine wb] [--fill 0..1] [--anim CLIP@FRAME] (--cam az,el,dist,tx,ty,tz --lens mm | --phone tx,ty,tz,frame_w)   (cam/phone targets in glTF coords)
--phone = game camera: 38 deg vertical FOV, 18 deg look-down, distance = (frame_w/2)/(tan 19 deg * aspect).
--engine wb (10/24, QA render hold): Workbench instead of Cycles (vertex colours, studio light, sun shadow, cavity) - a light review proof.
--fill: value of every 'fill' shape key (HT-04 bed heap); --anim: pose every armature with that clip at that frame (30 fps)."""
import bpy, sys, math
from mathutils import Vector, Matrix, Euler
A = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
def args(k): return [A[i + 1] for i, a in enumerate(A) if a == '--' + k]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
def g2b(v): return Vector((v[0], -v[2], v[1]))
def imp(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.name.startswith('Icosphere'): o.hide_render = True
        if o.get('hidden_by_default') or o.name.startswith('Tier_'): [setattr(x, 'hide_render', True) for x in [o] + list(o.children_recursive)]   # station tiers off (as proof_phone --tiers 0)
        if o.type == 'MESH':
            for slot in o.material_slots:
                m = slot.material; rough = 0.42
                try: rough = m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value
                except Exception: pass
                if 'Glass' in m.name: continue   # SHM_Glass: keep the imported principled (base colour + roughness, no vertex colours)
                m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
                if 'Glow' in m.name:
                    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = lin('#2fe3ff'); em.inputs['Strength'].default_value = 6.0
                    nt.links.new(em.outputs[0], out.inputs['Surface'])
                else:
                    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); ca = nt.nodes.new('ShaderNodeVertexColor')
                    ca.layer_name = o.data.color_attributes[0].name if o.data.color_attributes else ''
                    nt.links.new(ca.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = 0.0
                    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return new
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.003)); gnd = bpy.context.object
gm = bpy.data.materials.new('ground'); gm.use_nodes = True; nt = gm.node_tree; b = nt.nodes['Principled BSDF']
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 8
cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = lin('#6f7175'); cr.color_ramp.elements[1].color = lin('#9a9ca0')
nt.links.new(nz.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.95
gnd.data.materials.append(gm)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.5; sun.data.angle = math.radians(1.5); sun.rotation_euler = Euler((math.radians(52), 0, math.radians(-38)))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.06, 0.08, 1)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(arg('samples', 32)); sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.resolution_x = int(arg('w', 1200)); sc.render.resolution_y = int(arg('h', 900)); sc.render.resolution_percentage = 100
for spec in args('glb'):
    path, _, pl = spec.partition('@'); new = imp(path)
    x, z, yd = (float(v) for v in (pl or '0,0,0').split(','))
    bpy.context.view_layer.update()
    for o in new:
        if o.parent is None: o.matrix_world = Matrix.Translation(g2b((x, 0, z))) @ Matrix.Rotation(math.radians(yd), 4, 'Z') @ o.matrix_world
if arg('road'):
    x0, n, rz = (float(v) for v in arg('road_tiles', '-24,6,-9').split(','))
    for k in range(int(n)):
        new = imp(arg('road')); bpy.context.view_layer.update()
        for o in new:
            if o.parent is None: o.matrix_world = Matrix.Translation(g2b((x0 + 8 * k, 0, rz))) @ o.matrix_world
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 3000
if arg('phone'):
    tx, ty, tz, fw = (float(x) for x in arg('phone').split(','))
    asp = sc.render.resolution_x / sc.render.resolution_y; d = (fw / 2) / (math.tan(math.radians(19)) * asp)
    tgt = g2b((tx, ty, tz)); p = math.radians(18)
    cam.location = tgt + Vector((0, -d * math.cos(p), d * math.sin(p))); cam.rotation_euler = Euler((math.radians(90 - 18), 0, 0))
    cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(38)
else:
    az, el, dist, tx, ty, tz = (float(x) for x in arg('cam').split(','))
    tgt = g2b((tx, ty, tz)); dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
    cam.location = tgt + dv * dist; cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    if arg('lens'): cam.data.lens = float(arg('lens'))
    else: cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(38)
if arg('fill') is not None:
    for o in bpy.data.objects:
        kb = o.data.shape_keys.key_blocks if o.type == 'MESH' and o.data.shape_keys else []
        for k in kb:
            if k.name == 'fill': k.value = float(arg('fill'))
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o.animation_data:
        if arg('anim'):
            nm, _, fr = arg('anim').partition('@'); act = bpy.data.actions.get(nm) or next((a for a in bpy.data.actions if a.name.startswith(nm)), None)
            o.animation_data.action = act; sc.frame_set(int(fr or 0))
        else:
            o.animation_data.action = None
            for pb in o.pose.bones: pb.matrix_basis.identity()
if arg('engine') == 'wb':
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = arg('wblight', 'STUDIO'); sh.color_type = 'VERTEX'   # --wblight FLAT: unlit albedo (neutral-light colour check)
    sh.show_shadows = True; sh.shadow_intensity = 0.55; sh.show_cavity = True; sh.cavity_type = 'WORLD'; sh.cavity_ridge_factor = 0.0; sh.show_specular_highlight = False
    if sh.light == 'FLAT': sh.show_shadows = False; sh.show_cavity = False
    sc.display.light_direction = (0.45, -0.5, 0.75); sc.display.render_aa = '8'
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    gme = gnd.data; ca = gme.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for d in ca.data: d.color = lin('#8a8c90')
    for o in bpy.data.objects:
        if o.type == 'MESH' and o is not gnd and not o.data.color_attributes:   # glow / glass parts without COLOR_0: show their material colour
            m = o.material_slots[0].material if o.material_slots else None
            c = list(m.diffuse_color) if m else [1, 1, 1, 1]
            try:
                for nd in m.node_tree.nodes:
                    if nd.type == 'BSDF_PRINCIPLED': c = list(nd.inputs['Base Color'].default_value)   # e.g. SHM_DepositGlow veins
                    if nd.type == 'EMISSION': c = list(nd.inputs['Color'].default_value)
            except Exception: pass
            a_ = o.data.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
            for d in a_.data: d.color = c
    for o in bpy.data.objects:     # multi-material meshes (Mine Deposit_0N: rock with COLOR_0 + SHM_DepositGlow veins without): the importer
        if o.type != 'MESH' or o is gnd or len(o.material_slots) < 2 or not o.data.color_attributes: continue   # fills the veins white
        ca_ = o.data.color_attributes[0]
        for poly in o.data.polygons:
            m = o.material_slots[poly.material_index].material
            if m and 'Glow' in m.name:
                bs = next((nd for nd in m.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
                if bs is None: continue
                for li in poly.loop_indices: ca_.data[li].color = list(bs.inputs['Base Color'].default_value)
sc.render.filepath = arg('out'); bpy.ops.render.render(write_still=True); print('RENDERED', arg('out'))
