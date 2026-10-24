"""Planet Stack - role-kit GLB (hand tools + badge medallions), one shared vertex-colour material, no images.
blender -b -P export_kit.py -t 4 -- OUT.glb      (then gltfpack -c for meshopt + quantization)
Every tool node's origin = the grip centre; local +Z = handle axis (thumb side), +X = finger direction.
Attach it to the right-hand socket.  Badge nodes are 0.046 m medallions facing +Z."""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import role_kit as RK
from role_kit import S, RT, Kit, kit_mats, TOOLS, badge
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else os.path.join(HERE, '..', 'glb', '_kit_raw.glb'))
import mc_common as mc
mc.reset()

def h2l(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]

VC = bpy.data.materials.new('RoleKit_VC'); VC.use_nodes = True
nt = VC.node_tree; bsdf = nt.nodes['Principled BSDF']; att = nt.nodes.new('ShaderNodeVertexColor'); att.layer_name = 'Col'
nt.links.new(att.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = 0.45; bsdf.inputs['Metallic'].default_value = 0.0

GRAPH, SHELL = '#2b3038', '#eceef1'
x0 = 0.0
for key in RT.ORDER:
    R = RT.ROLES[key]; M = kit_mats(key)
    col = {id(M['paint']): R['accent'], id(M['steel']): '#9aa1a9', id(M['rubber']): '#1b1e23', id(M['screen']): '#59dcff',
           id(M['aglow']): R['accent'], id(M['graph']): GRAPH, id(M['shell']): SHELL}
    for nm, fn in (('Tool', lambda K: TOOLS[R['tool']](K, M, Matrix.Identity(4))),
                   ('Badge', lambda K: badge(K, M, R['badge'], Vector((0, 0, 0)), (0, 0, 1), (0, 1, 0), R=0.046, name='Badge'))):
        root = bpy.data.objects.new(f'{nm}_{key}', None); bpy.context.scene.collection.objects.link(root)
        K = Kit(root); fn(K)
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        import bmesh
        bm = bmesh.new()
        for ob in K.parts:
            if ob.type != 'MESH': continue
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); me.transform(ob.matrix_basis)
            c = h2l(col.get(id(ob.data.materials[0]) if ob.data.materials else 0, GRAPH))
            ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
            for d in ca.data: d.color = c
            bm.from_mesh(me); bpy.data.meshes.remove(me)
        for ob in list(K.parts): bpy.data.objects.remove(ob, do_unlink=True)
        me = bpy.data.meshes.new(f'{nm}_{key}'); bm.to_mesh(me); bm.free()
        me.materials.append(VC)
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(f'{nm}_{key}', me); bpy.context.scene.collection.objects.link(ob)
        bpy.data.objects.remove(root, do_unlink=True); ob.name = f'{nm}_{key}'
        ob.location = (x0, 0 if nm == 'Tool' else -0.4, 0)
    x0 += 0.6
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_apply=True, export_vertex_color='ACTIVE' if bpy.app.version >= (4, 2, 0) else 'MATERIAL',
                          export_attributes=False, export_yup=True, export_texcoords=False, export_normals=True, export_materials='EXPORT')
print('EXPORTED', OUT)
for o in bpy.data.objects: print('OBJ', o.name, len(o.data.polygons))
