"""Shared Blender helpers for Art & Animation game props (FB-05, cargo box, Refinery crane).
Low-poly mesh builder: every face carries a vertex colour (linear RGB), a material slot (0 = SHM_Paint, 1 = SHM_GlowCyan)
and one bone. Blender coords: Z up; glTF export maps (x, y, z) -> (x, z, -y)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
# concept B palette (linear), sampled from the HT-04 / Mine game GLBs
P = dict(white=(0.79, 0.81, 0.85), white2=lin('#e8edf5'), graph=(0.02, 0.03, 0.04), graph2=lin('#3a4258'), graph1=lin('#2a3245'),
         steel=(0.39, 0.43, 0.48), satin=lin('#9aa3ad'), tyre=(0.02, 0.02, 0.02), cyan=(0.03, 0.77, 1.0), cyan_hi=(0.58, 0.96, 1.0),
         dust=(0.46, 0.42, 0.36), dust2=(0.33, 0.30, 0.25), amber=lin('#ffb020'), red=(0.75, 0.04, 0.03), cable=(0.05, 0.05, 0.055))
GLOW = (0.02842604, 0.768151164, 1.0)

class MB:
    def __init__(self):
        self.bm = bmesh.new(); self.col = []; self.mat = []; self.bone = []
    def _add(self, verts, faces, col, mat, bone):
        vs = [self.bm.verts.new(v) for v in verts]
        for f in faces:
            try: self.bm.faces.new([vs[i] for i in f])
            except ValueError: continue
            self.col.append(tuple(col)); self.mat.append(mat); self.bone.append(bone)
    def box(self, size, c, col, rot=(0, 0, 0), mat=0, bone='root', taper=1.0):
        sx, sy, sz = (s / 2 for s in size); R = Euler(rot).to_matrix(); C = Vector(c)
        V = []
        for z in (-sz, sz):
            k = taper if z > 0 else 1.0
            for x, y in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)): V.append(C + R @ Vector((x * k, y * k, z)))
        F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(V, F, col, mat, bone)
    def cyl(self, p0, p1, r, col, segs=8, mat=0, bone='root', caps=True, r1=None):
        p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0).normalized(); r1 = r if r1 is None else r1
        a = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0)); u = d.cross(a).normalized(); v = d.cross(u)
        V = [p0 + (u * math.cos(t) + v * math.sin(t)) * r for t in (i * math.tau / segs for i in range(segs))]
        V += [p1 + (u * math.cos(t) + v * math.sin(t)) * r1 for t in (i * math.tau / segs for i in range(segs))]
        F = [(i, (i + 1) % segs, segs + (i + 1) % segs, segs + i) for i in range(segs)]
        if caps: F += [tuple(reversed(range(segs))), tuple(range(segs, 2 * segs))]
        self._add(V, F, col, mat, bone)
    def quad(self, pts, col, mat=0, bone='root'):
        self._add([Vector(p) for p in pts], [(0, 1, 2, 3)], col, mat, bone)
    def text(self, body, size, loc, rot, col, mat=1, bone='root', res=1, align='CENTER'):
        cu = bpy.data.curves.new('tmp_txt', 'FONT'); cu.body = body; cu.size = size; cu.resolution_u = res
        cu.align_x = align; cu.align_y = 'CENTER'; cu.fill_mode = 'BOTH'
        ob = bpy.data.objects.new('tmp_txt', cu); bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        tb = bmesh.new(); tb.from_mesh(me); bmesh.ops.triangulate(tb, faces=tb.faces[:])
        idx = {v: i for i, v in enumerate(tb.verts)}
        self._add([M @ v.co for v in tb.verts], [[idx[v] for v in f.verts] for f in tb.faces], col, mat, bone)
        tb.free(); bpy.data.objects.remove(ob); bpy.data.curves.remove(cu); bpy.data.meshes.remove(me)
    def tris(self): return sum(len(f.verts) - 2 for f in self.bm.faces)
    def weather(self, seed=1, z0=0.0, z1=1.5, amt=0.45, noise=0.08):
        """dust creeping up from the ground + per-face grime jitter on paint faces (the 'weathered' vertex-colour pass)"""
        rr = random.Random(seed); self.bm.faces.ensure_lookup_table()
        for i, f in enumerate(self.bm.faces):
            if self.mat[i] != 0: continue
            c = Vector(self.col[i]); z = f.calc_center_median().z
            t = max(0.0, min(1.0, (z1 - z) / max(1e-6, z1 - z0))) ** 1.6 * amt + rr.uniform(0, noise)
            d = Vector(P['dust']); self.col[i] = tuple(c.lerp(d, min(0.85, t)) * rr.uniform(0.94, 1.04))
    def build(self, name, coll=None):
        me = bpy.data.meshes.new(name); self.bm.normal_update(); self.bm.to_mesh(me)
        me.materials.append(paint_mat()); me.materials.append(glow_mat())
        ca = me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
        for i, p in enumerate(me.polygons):
            p.material_index = self.mat[i]
            for li in p.loop_indices: ca.data[li].color = (*self.col[i], 1.0)
        ob = bpy.data.objects.new(name, me); (coll or bpy.context.scene.collection).objects.link(ob)
        groups = {}
        for i, p in enumerate(me.polygons):
            b = self.bone[i]
            if b not in groups: groups[b] = ob.vertex_groups.new(name=b)
            groups[b].add(list(p.vertices), 1.0, 'REPLACE')
        return ob

def paint_mat():
    m = bpy.data.materials.get('SHM_Paint')
    if m: return m
    m = bpy.data.materials.new('SHM_Paint'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    va = nt.nodes.new('ShaderNodeVertexColor'); va.layer_name = 'Color'; nt.links.new(va.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.42; b.inputs['Metallic'].default_value = 0.0; return m
def glow_mat():
    m = bpy.data.materials.get('SHM_GlowCyan')
    if m: return m
    m = bpy.data.materials.new('SHM_GlowCyan'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*GLOW, 1); b.inputs['Emission Color'].default_value = (*GLOW, 1)
    b.inputs['Emission Strength'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.5; b.inputs['Metallic'].default_value = 0.0; return m

def empty(name, loc, parent=None, extras=None, bone=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e); e.empty_display_size = 0.3
    if parent is not None:
        e.parent = parent
        if bone: e.parent_type = 'BONE'; e.parent_bone = bone
    e.location = loc; e.rotation_euler = rot
    for k, v in (extras or {}).items(): e[k] = v
    if parent is not None and bone:   # parent_type BONE offsets from the bone tail: re-place in world space
        bpy.context.view_layer.update(); W = parent.matrix_world @ Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        e.matrix_world = W
    return e

def export(path, anim=False, selection=None):
    kw = dict(filepath=path, export_format='GLB', export_extras=True, export_yup=True, export_apply=False, export_skins=True,
              export_morph=False, export_texcoords=False, export_normals=True, export_materials='EXPORT', export_animations=anim,
              export_cameras=False, export_lights=False)
    try: bpy.ops.export_scene.gltf(**kw, export_vertex_color='MATERIAL')
    except TypeError: bpy.ops.export_scene.gltf(**kw, export_colors=True)
