"""Planet Stack shared haul-road segment (Mine -> Refinery haul road, 10/23).
One 8.0 m tileable piece along +X with the two Refinery lanes: inbound (to the Refinery) centre glTF z +9, outbound (to the Mine) z 0.
Cross-section, colours and heights are the station roads' own (mine_layout._HALF / ROAD_HEX = refinery _RHALF / _RHEX):
4 m graded running surface (crown +2 cm), tyre tracks 1.25..1.65 m either side (0.4 m wide, centred +-1.45 like the Mine stub) (-2 cm, a flat darker worn band), foot at 2.0, berm crest +25 cm at 2.35, toe buried -4 cm at 2.8.
Both ends (x 0 and x 8) carry identical rows (wear pattern is 8 m periodic), so copies at x = x0 + 8 k join without a seam.
usage: blender -b -P build_haul_road_seg.py -- --out raw.glb
then:  gltfpack -i raw.glb -o haul_road_seg.glb -cc -kn -ke -vpf   (meshopt + quantization (float positions: ends exactly at x 0 / 8.0), no Draco)"""
import bpy, bmesh, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp/haul_road_seg_raw.glb')
L = 8.0; NSEG = 5                                    # 5 spans along X -> 6 rows (1.6 m)
LANES = [('inbound', 9.0, 0.045), ('outbound', 0.0, 0.045)]   # (name, glTF z of the centre line, surface height y)
HALF = [(0.0, 0.02, 'track'), (1.1, 0.0, 'track'), (1.25, -0.02, 'mark'), (1.65, -0.02, 'mark'), (1.8, 0.0, 'track'), (2.0, 0.0, 'foot'), (2.35, 0.25, 'crest'), (2.8, -0.04, 'toe')]
PROF = [(-o, dz, k) for o, dz, k in reversed(HALF[1:])] + HALF
HEX = {'track': '#a4a7ac', 'mark': '#878a8f', 'foot': '#9da0a5', 'crest': '#939499', 'toe': '#82858a', 'wear': '#76797e', 'polish': '#adb0b5'}
def srgb(h): h = h.lstrip('#'); return Vector([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
def lin(c): return Vector([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
bm = bmesh.new(); cl = bm.loops.layers.color.new('Col')
def wear(x, ph):   # 8 m periodic rut wear (0..1): darker, scuffed patches in the tyre tracks
    t = 2 * math.pi * x / L
    return max(0.0, min(1.0, 0.5 + 0.35 * math.sin(t + ph) + 0.25 * math.sin(3 * t + 2 * ph)))
for li, (nm, zc, ys) in enumerate(LANES):
    yb = -zc                                         # Blender Y = -glTF Z
    rows = []
    for i in range(NSEG + 1):
        x = L * i / NSEG; row = []
        for off, dz, kind in PROF:
            c = srgb(HEX[kind])
            if kind == 'mark': c = c.lerp(srgb(HEX['wear']), 0.35 + 0.5 * wear(x, li * 1.7 + (0.9 if off > 0 else 0.0)))
            if kind == 'track' and abs(off) < 0.01: c = c.lerp(srgb(HEX['polish']), 0.5 * wear(x, li * 2.3 + 3.1))
            z = dz if kind == 'toe' else ys + dz
            row.append((bm.verts.new((x, yb + off, z)), c))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(len(PROF) - 1):
            qd = (r0[k], r1[k], r1[k + 1], r0[k + 1]); f = bm.faces.new([v for v, _ in qd])
            for lp, (_, c) in zip(f.loops, qd): lp[cl] = (c.x, c.y, c.z, 1.0)   # BYTE_COLOR layer stores sRGB bytes
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
me = bpy.data.meshes.new('HaulRoad_Seg_mesh'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
me.color_attributes.active_color = me.color_attributes['Col']
m = bpy.data.materials.new('SHM_Paint'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
b.inputs['Metallic'].default_value = 0.0; b.inputs['Roughness'].default_value = 0.42; m.use_backface_culling = True
ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
me.materials.append(m)
ob = bpy.data.objects.new('HaulRoad_Seg', me); bpy.context.scene.collection.objects.link(ob)
ob['tile_len_m'] = L; ob['axis'] = '+X'; ob['origin'] = 'segment start (x 0) on the ground, inbound lane centre at z +9, outbound at z 0'
ob['lanes'] = 'inbound z +9 heading +X (Mine -> Refinery), outbound z 0 heading -X (Refinery -> Mine); 4 m running surface, 5.6 m berm toe to toe'
ob['tiling'] = 'place copies at position.x = x0 + 8*k, y 0, z 0, no rotation; ends match exactly (see README)'
ob['surface_y'] = 0.045
print('TRIS', sum(len(p.vertices) - 2 for p in me.polygons), 'VERTS', len(me.vertices))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                          export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False,
                          export_vertex_color='ACTIVE', export_all_vertex_colors=False)
print('RAW', OUT)
