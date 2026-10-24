"""Proof renders for the CV-3 box bridge composited with the Refinery game GLB (CPU Cycles, OIDN, no tiling).
All inputs unpacked with `gltfpack -noq -kn -ke` first (Blender has no meshopt decoder).
blender -b -P render_bridge_proofs.py -- --ref REF_PLAIN [--bridge BRIDGE_PLAIN --t S] [--crane CRANE_PLAIN] [--fb FB_PLAIN] [--road ROAD_PLAIN]
    [--ht04 HT04_GAME_GLB] --out PNG --w W --h H --samples N (--phone tx,ty,tz,fw (world glTF) | --cam az,el,dist,tx,ty,tz --lens mm (Blender world))
World: Refinery at x 320; bridge GLB scene at the same place (its root already carries its Refinery offset); crane (311, 0, 17.5);
FB-05 at Truck_Park (318, 0, 13); flatbed road tiles from x 307 on z 13 (both lanes); HT-04 tipping (bed up) at Truck_Dump, under the span,
and a second HT-04 on the inbound lane z 9. --clip box_convey|box_path picks the bridge clip."""
import bpy, sys, os, math
from mathutils import Vector, Matrix, Euler
A = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
def g2b(v): return Vector((v[0], -v[2], v[1]))
def imp(path, at=(0, 0, 0)):
    before = set(bpy.data.objects); acts0 = set(bpy.data.actions); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.name.startswith('Icosphere'): o.hide_render = True
        if o.type == 'MESH':
            for slot in o.material_slots:
                m = slot.material
                if m.get('_done'): continue
                m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
                if 'Glow' in m.name and 'Red' not in m.name:
                    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = lin('#2fe3ff'); em.inputs['Strength'].default_value = 6.0
                    nt.links.new(em.outputs[0], out.inputs['Surface'])
                elif 'GlowRed' in m.name:
                    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = lin('#ff3020'); em.inputs['Strength'].default_value = 5.0
                    nt.links.new(em.outputs[0], out.inputs['Surface'])
                else:
                    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); ca = nt.nodes.new('ShaderNodeVertexColor')
                    ca.layer_name = o.data.color_attributes[0].name if o.data.color_attributes else ''
                    nt.links.new(ca.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.42
                    if 'Dust' in m.name:
                        nt.links.new(ca.outputs['Alpha'], b.inputs['Alpha']); m.blend_method = 'BLEND'
                    nt.links.new(b.outputs[0], out.inputs['Surface'])
                m['_done'] = 1
    bpy.context.view_layer.update()
    for o in new:
        if o.parent is None: o.location = o.location + g2b(at)
    return new, [a for a in bpy.data.actions if a not in acts0]
bpy.ops.mesh.primitive_plane_add(size=2000, location=(320, 0, -0.004)); gnd = bpy.context.object
gm = bpy.data.materials.new('ground'); gm.use_nodes = True; nt = gm.node_tree; b = nt.nodes['Principled BSDF']
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 8
cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = lin('#6f7175'); cr.color_ramp.elements[1].color = lin('#9a9ca0')
nt.links.new(nz.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.95
gnd.data.materials.append(gm)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.5; sun.data.angle = math.radians(1.5); sun.rotation_euler = Euler((math.radians(52), 0, math.radians(-38)))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.06, 0.08, 1)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(arg('samples', 24)); sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.use_auto_tile = False; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.resolution_x = int(arg('w', 393)); sc.render.resolution_y = int(arg('h', 852)); sc.render.resolution_percentage = 100
T = float(arg('t', 18.0)); F = int(round(T * 30))
# Refinery (tiers hidden as in game)
rn, _ = imp(arg('ref'), (320, 0, 0))
def hide_tree(o):
    o.hide_render = True
    for c in o.children: hide_tree(c)
for o in rn:
    if o.name.split('.')[0].startswith('Tier_') or o.get('hidden_by_default'): hide_tree(o)
if arg('bridge'):
    bn, bacts = imp(arg('bridge'), (320, 0, 0))
    barm = next(o for o in bn if o.type == 'ARMATURE')
    if barm.animation_data is None: barm.animation_data_create()
    for tr in list(barm.animation_data.nla_tracks): barm.animation_data.nla_tracks.remove(tr)
    act = next(a for a in bacts if a.name.startswith(arg('clip', 'box_convey'))); barm.animation_data.action = act
    print('BRIDGE', barm.name, barm.matrix_world.translation, 'action', act.name, act.frame_range)
if arg('crane'):
    cn, cacts = imp(arg('crane'), (311, 0, 17.5))
if arg('fb'):
    fn, _ = imp(arg('fb'), (318, 0, 13))
if arg('road'):
    for k in range(4):
        imp(arg('road'), (307 + 8 * k, 0, 13))
if arg('ht04'):
    from place_ht04 import place_ht04
    place_ht04(arg('ht04'), sc.collection, frame=40, at=(320, 0, 0), yaw_deg=180.0, tmp='/tmp/brp_ht04a.glb')
    place_ht04(arg('ht04'), sc.collection, frame=0, at=tuple(g2b((320 - 16.0, 0, 9))), yaw_deg=0.0, tmp='/tmp/brp_ht04b.glb')
sc.frame_set(F)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
if arg('phone'):
    tx, ty, tz, fw = (float(x) for x in arg('phone').split(','))
    asp = sc.render.resolution_x / sc.render.resolution_y; d = (fw / 2) / (math.tan(math.radians(19)) * asp)
    tgt = g2b((tx, ty, tz)); p = math.radians(18)
    cam.location = tgt + Vector((0, -d * math.cos(p), d * math.sin(p))); cam.rotation_euler = Euler((math.radians(90 - 18), 0, 0))
    cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(38); cam.data.clip_end = 3000
else:
    az, el, dist, tx, ty, tz = (float(x) for x in arg('cam').split(','))
    tgt = Vector((tx, ty, tz)); dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
    cam.location = tgt + dv * dist; cam.data.lens = float(arg('lens', 50)); cam.data.clip_end = 3000
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = arg('out'); bpy.ops.render.render(write_still=True); print('RENDERED', arg('out'))
