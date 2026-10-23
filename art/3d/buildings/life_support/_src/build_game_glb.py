"""Life Support game GLB: master .blend -> 10-20k tris, <=6 draw calls, shared SH_* palette, no Draco.
usage: blender -b life_support_master.blend -P build_game_glb.py -- --out raw.glb [--target 28000]
then:  gltfpack -i raw.glb -o life_support_game.glb -cc     (meshopt + quantization)
Materials: 4 merged SHM_* from _shared/shared_materials.json (vertex-coloured paint/metal + 2 glows; SH_* swatches baked to COLOR_0), plain metallic/roughness, no textures.
Removes: all text/stencils/plates' lettering, lamps & tiny greebles (<0.22 m), guy wires, fine cables, grating bars, bolts.
The astronaut, ground, reactor and far feeder live in the Stage collection and are never exported."""
import bpy, bmesh, json, os, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp/ls_game_raw.glb'); TARGET = int(A.get('target', 17000))
HERE = os.path.dirname(os.path.abspath(__file__))

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
J = json.load(open(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json')))
SW, MERGED, S2M = J['materials'], J['merged_materials'], J['swatch_to_merged']
SH = {}
for n, d in MERGED.items():
    m = bpy.data.materials.new(n); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
    if d.get('vertex_colors'):
        ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
    if 'emissive' in d:
        b.inputs['Emission Color'].default_value = lin(d['emissive']); b.inputs['Emission Strength'].default_value = d['emissive_strength']
    SH[n] = m
MAP = [  # master material name prefix -> shared swatch (SH_*), whose base colour becomes the vertex colour
    ('LS_RedLamp', 'SH_GlowRed'), ('LS_Red', 'SH_Red'), ('LS_White', 'SH_White'), ('LS_ShieldTile', 'SH_White'), ('LS_InkWhite', 'SH_White'),
    ('LS_Graphite', 'SH_Graphite'), ('LS_BandGraphite', 'SH_Graphite'), ('LS_Rubber', 'SH_Graphite'), ('LS_Ink', 'SH_Graphite'), ('LS_Void', 'SH_Graphite'),
    ('LS_Satin', 'SH_Steel'), ('LS_Chrome', 'SH_Steel'), ('LS_MLI', 'SH_Foil'), ('LS_Rad', 'SH_Radiator'), ('LS_SolarCells', 'SH_Solar'),
    ('LS_O2Band', 'SH_PipeO2'), ('LS_H2OBand', 'SH_PipeH2O'), ('LS_Slag', 'SH_Rock'), ('LS_Ilmenite', 'SH_Rock'), ('LS_IceRegolith', 'SH_Rock'), ('LS_Port', 'SH_Glass'),
    ('LS_CyanStrip', 'SH_GlowCyan'), ('LS_CyanSoft', 'SH_GlowCyan'), ('LS_Cyan', 'SH_GlowCyan'), ('LS_SightGlass', 'SH_GlowCyan'),
    ('LS_Lamp', 'SH_GlowWhite'), ('LS_StatusWhite', 'SH_GlowWhite'), ('LS_GreenLamp', 'SH_GlowWhite'), ('LS_ReactorPort', 'SH_GlowWhite'),
]
def shared_for(m):
    sw = None
    if m is not None:
        for p, s_ in MAP:
            if m.name.startswith(p): sw = s_; break
    if sw is None:
        c = m.diffuse_color if m else (1, 1, 1, 1); sw = 'SH_White' if 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2] > 0.35 else 'SH_Graphite'
        print('UNMAPPED', m.name if m else None, '->', sw)
    mm = S2M[sw]
    return SH[mm], (lin(SW[sw]['base']) if MERGED[mm].get('vertex_colors') else [1, 1, 1, 1])

DROP_NAMES = ('st_', 'bolt', 'rivet', 'guy', 'grate', 'grating', 'nozzle', 'louver', 'lamp', 'cable_tie', 'tie_', 'weld', 'seam', 'clamp', 'hinge', 'handle', 'rail_post', 'bracket')
KEEP_SMALL = ('haz', 'cyan', 'band', 'strip', 'beacon')
mine = [o for o in bpy.data.collections['Mine'].all_objects]
dg = bpy.context.evaluated_depsgraph_get()
keep, dropped = [], 0
for ob in mine:
    if ob.type not in ('MESH', 'CURVE', 'FONT'):
        continue
    nm = ob.name.lower()
    if ob.type == 'FONT' or nm.endswith('_t') or '_t.' in nm or nm.startswith('text'):
        dropped += 1; continue
    dims = ob.dimensions; big = max(dims)
    if any(nm.startswith(k) or ('_' + k) in nm for k in DROP_NAMES) and not any(k in nm for k in KEEP_SMALL):
        dropped += 1; continue
    if big < 0.22 and not any(k in nm for k in KEEP_SMALL):
        dropped += 1; continue
    if big < 1.0 and min(dims) < 0.03 and 'haz' not in nm and 'cyan' not in nm:   # wires / thin trims
        dropped += 1; continue
    keep.append(ob)
print('KEEP', len(keep), 'DROP', dropped)
# bake each kept object to a fresh mesh object in world space with shared materials
col = bpy.data.collections.new('Game'); bpy.context.scene.collection.children.link(col)
new = []
for ob in keep:
    e = ob.evaluated_get(dg); me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=False, depsgraph=dg)
    if me is None or len(me.polygons) == 0: continue
    me.transform(ob.matrix_world)
    if len(me.materials) == 0: me.materials.append(None)
    sm = [shared_for(m) for m in me.materials]
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        col_ = sm[min(poly.material_index, len(sm) - 1)][1]
        for li in poly.loop_indices: ca.data[li].color = col_
    for i, (m_, _) in enumerate(sm): me.materials[i] = m_
    no = bpy.data.objects.new('g_' + ob.name, me); col.objects.link(no); new.append(no)
for c in list(bpy.context.scene.collection.children):
    if c != col: bpy.context.scene.collection.children.unlink(c)
def tris(objs):
    t = 0
    for o in objs:
        for p in o.data.polygons: t += len(p.vertices) - 2
    return t
T0 = tris(new); print('TRIS after culling', T0)
# per-object budgeting: weld + planar dissolve, then collapse so the whole set lands under TARGET
for o in new:
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(4), verts=bm.verts, edges=bm.edges, delimit={'MATERIAL'})
    bm.to_mesh(o.data); bm.free()
T1 = tris(new); print('TRIS after planar', T1)
bpy.ops.object.select_all(action='DESELECT')
for o in new: o.select_set(True)
bpy.context.view_layer.objects.active = new[0]
bpy.ops.object.join(); J = bpy.context.view_layer.objects.active
# merge duplicate material slots
bpy.ops.object.material_slot_remove_unused()
ratio = 1.0
for it in range(6):
    t = tris([J])
    if t <= TARGET: break
    ratio = TARGET / t * 0.98
    mod = J.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'; mod.ratio = ratio; mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
print('TRIS final', tris([J]))
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in col.objects if o.type == 'MESH']
for o in parts:
    mats = [s.material for s in o.material_slots if s.material]
    used = {o.data.polygons[i].material_index for i in range(len(o.data.polygons))}
    o.name = (o.material_slots[list(used)[0]].material.name if used else 'part').replace('SHM_', 'LS_')
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.material_slot_remove_unused()
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
root = bpy.data.objects.new('LifeSupport', None); col.objects.link(root)
for o in parts: o.parent = root
print('PARTS', len(parts), sorted(o.name for o in parts))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                          export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False, export_vertex_color='ACTIVE', export_all_vertex_colors=False)
if A.get('blend'): bpy.ops.wm.save_as_mainfile(filepath=A['blend'], compress=True)
print('RAW', OUT, os.path.getsize(OUT))
