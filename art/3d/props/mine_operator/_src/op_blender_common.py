"""Blender helpers for the mine operator proofs: import the raw GLB, set the shared look, pick clips."""
import bpy, math
def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
def import_operator(path, loc=(0, 0, 0), rot_z=0.0):
    sc = bpy.context.scene; sc.render.fps = 30
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = next(o for o in new if o.name.startswith('MineOperator'))
    e = root.matrix_world.to_euler('XYZ')
    root.rotation_mode = 'XYZ'; root.location = loc; root.rotation_euler = (e.x, e.y, e.z + rot_z)
    for o in new:
        if o.name.startswith('Icosphere'): o.hide_render = True; o.hide_viewport = True
    arm = next(o for o in new if o.type == 'ARMATURE')
    for o in new:
        if o.type != 'MESH': continue
        for slot in o.material_slots:
            m = slot.material
            if m is None: continue
            nm = m.name
            m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
            out = nt.nodes.new('ShaderNodeOutputMaterial')
            if 'Glow' in nm:
                em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = lin('#2fe3ff'); em.inputs['Strength'].default_value = 6.0
                nt.links.new(em.outputs[0], out.inputs['Surface'])
            else:
                b = nt.nodes.new('ShaderNodeBsdfPrincipled'); ca = nt.nodes.new('ShaderNodeVertexColor')
                ca.layer_name = o.data.color_attributes[0].name if o.data.color_attributes else ''
                nt.links.new(ca.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.42; b.inputs['Metallic'].default_value = 0.0
                nt.links.new(b.outputs[0], out.inputs['Surface'])
            m.use_backface_culling = True
    return root, arm, new
def set_clip(arm, clip):
    if arm.animation_data is None: arm.animation_data_create()
    ad = arm.animation_data
    for tr in list(ad.nla_tracks): ad.nla_tracks.remove(tr)
    act = next(a for a in bpy.data.actions if a.name.split('_Op_')[0].split('_Armature')[0] == clip or a.name.startswith(clip + '_') or a.name == clip)
    ad.action = act
    return act
