"""Preview of a 160 x 60 m patch shaded with the shipped tiles (decoded from the KTX2 files).
blender -b -P render_preview.py -- --tex <dir with decoded PNGs> --out <dir>
Two renders: top-down ortho of the full 160x60 m, and a game-like oblique (~55 deg pitch) view.
UVs = world XY / 10 m (detail + normal), world XY / 76 m (macro, x2 multiplier, linear)."""
import bpy, sys, os, math, argparse
a = argparse.ArgumentParser(); a.add_argument('--tex'); a.add_argument('--out'); a.add_argument('--spp', type=int, default=16)
A = a.parse_args(sys.argv[sys.argv.index('--') + 1:])
T_DETAIL, T_MACRO = 10.0, 76.0
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = A.spp; sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.6, 0.7, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.35
bpy.ops.mesh.primitive_plane_add(size=1); pl = bpy.context.object; pl.scale = (400, 400, 1)
m = bpy.data.materials.new('G'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
bsdf = N['Principled BSDF']; bsdf.inputs['Roughness'].default_value = 0.92
tc = N.new('ShaderNodeTexCoord')
def img(name, tile, cs):
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / tile, 1 / tile, 1)
    L.new(tc.outputs['Object'], mp.inputs[0])
    t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(A.tex, name)); t.image.colorspace_settings.name = cs
    t.extension = 'REPEAT'; t.interpolation = 'Cubic'; L.new(mp.outputs[0], t.inputs[0]); return t
pl.scale = (1, 1, 1); bpy.ops.object.select_all(action='DESELECT')
pl.data.vertices[0].co = (-400, -400, 0); pl.data.vertices[1].co = (400, -400, 0); pl.data.vertices[2].co = (-400, 400, 0); pl.data.vertices[3].co = (400, 400, 0)
col = img('ground_basecolor_1024.png', T_DETAIL, 'sRGB'); mac = img('ground_macro_256.png', T_MACRO, 'Non-Color'); nrm = img('ground_normal_512.png', T_DETAIL, 'Non-Color')
mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 2.0; L.new(mac.outputs['Color'], mul.inputs[0])
mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
L.new(col.outputs['Color'], mx.inputs[6]); L.new(mul.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], bsdf.inputs['Base Color'])
nm = N.new('ShaderNodeNormalMap'); L.new(nrm.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs[0], bsdf.inputs['Normal'])
pl.data.materials.append(m)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(50), math.radians(-12), math.radians(35))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
# 1) top-down ortho, exactly 160 x 60 m
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 160; cam.location = (0, 0, 100); cam.rotation_euler = (0, 0, 0)
sc.render.resolution_x, sc.render.resolution_y = 1600, 600
sc.render.filepath = os.path.join(A.out, 'top.png'); bpy.ops.render.render(write_still=True)
# 2) oblique game-like view looking across the patch
cam.data.type = 'PERSP'; cam.data.lens = 28; cam.location = (0, -62, 34); cam.rotation_euler = (math.radians(58), 0, 0)
sc.render.resolution_x, sc.render.resolution_y = 1600, 800
sc.render.filepath = os.path.join(A.out, 'persp.png'); bpy.ops.render.render(write_still=True)
