import bpy,math,sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
def imp(p,dx):
    before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p); new=[o for o in bpy.data.objects if o not in before]
    keep=[o for o in new if o.parent and o.parent.name.startswith(('Ship_Placeholder','Cargo_Door')) and o.type=='MESH']
    for o in keep:
        mw=o.matrix_world.copy(); o.parent=None; o.matrix_world=mw
    for o in new:
        if o not in keep: bpy.data.objects.remove(o)
    for o in keep:
        o.location.x+=dx; o.location.y+=13.0*0  # glTF z-13 -> blender y +13
        o.location.y-=13.0 if False else 0
    return keep
import os
A=imp(os.environ.get('LV1_GLB','/workspace/lv2/pad_lv1d_raw.glb'),-11.0); B=imp(os.environ.get('LV2_GLB','/workspace/lv2/pad_lv2_raw.glb'),11.0)
for grp in (A,B):   # centre each ship (hull + its door) on the ship axis together, not per object
    hull=max(grp,key=lambda o:len(o.data.vertices)); bb=[hull.matrix_world@Vector(c) for c in hull.bound_box]; cy=(min(v.y for v in bb)+max(v.y for v in bb))/2
    for o in grp: o.location.y-=cy
for o in A+B:
    m=bpy.data.materials.new('vc'); m.use_nodes=True; nt=m.node_tree; bs=nt.nodes['Principled BSDF']
    a=nt.nodes.new('ShaderNodeVertexColor'); a.layer_name=o.data.color_attributes[0].name if o.data.color_attributes else 'Color'
    nt.links.new(a.outputs['Color'],bs.inputs['Base Color']); bs.inputs['Metallic'].default_value=0.5; bs.inputs['Roughness'].default_value=0.42
    o.data.materials.clear(); o.data.materials.append(m)
# astronaut 1.8 m between ships
def prim(op,loc,col,**k):
    op(location=loc,**k); o=bpy.context.object; m=bpy.data.materials.new('a'); m.diffuse_color=col; m.use_nodes=True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=col; o.data.materials.append(m); return o
W=(0.92,0.92,0.9,1); V=(0.9,0.55,0.1,1)
x0=0.0
prim(bpy.ops.mesh.primitive_cylinder_add,(x0-0.13,-6,0.42),W,radius=0.11,depth=0.84)
prim(bpy.ops.mesh.primitive_cylinder_add,(x0+0.13,-6,0.42),W,radius=0.11,depth=0.84)
prim(bpy.ops.mesh.primitive_cylinder_add,(x0,-6,1.12),W,radius=0.24,depth=0.62)
prim(bpy.ops.mesh.primitive_cube_add,(x0,-5.75,1.15),W,size=0.4).scale=(1,0.45,1.2)
prim(bpy.ops.mesh.primitive_cylinder_add,(x0-0.32,-6,1.05),W,radius=0.08,depth=0.6)
prim(bpy.ops.mesh.primitive_cylinder_add,(x0+0.32,-6,1.05),W,radius=0.08,depth=0.6)
prim(bpy.ops.mesh.primitive_uv_sphere_add,(x0,-6,1.62),W,radius=0.18)
prim(bpy.ops.mesh.primitive_uv_sphere_add,(x0,-6.09,1.63),V,radius=0.12)
# ground
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0.24)); g=bpy.context.object; gm=bpy.data.materials.new('g'); gm.use_nodes=True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.25,0.25,0.26,1); g.data.materials.append(gm)
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(50),0,math.radians(-35))); bpy.context.object.data.energy=3.2
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.06,0.065,0.08,1); w.node_tree.nodes['Background'].inputs[1].default_value=4
bpy.ops.object.camera_add(location=(0,-120,21),rotation=(math.radians(90),0,0)); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=46; sc.camera=cam
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=1600; sc.render.resolution_y=1700; sc.view_settings.view_transform='AgX'
if os.environ.get('CLOSE'):   # cargo-section close-up
    cam.location=(0,-60,15.0); cam.data.ortho_scale=float(os.environ.get('CLOSE'))
sc.render.filepath=sys.argv[-1]; bpy.ops.render.render(write_still=True)
