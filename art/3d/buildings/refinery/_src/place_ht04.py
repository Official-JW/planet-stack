"""Place the shared HT-04 (art/3d/props/ht04/ht04_game.glb) at the Refinery's Truck_Dump in its truck_dump pose (review renders only).
Blender can't import meshopt, so the GLB is first unpacked with `gltfpack -noq -kn -ke`. Truck_Dump = Blender origin; the truck
reverses into RB-1, so cab -X (yaw 180 deg about +Z; HT-04 forward = glTF +X). Used by build_refinery.py --ht04 PATH [--ht04frame N]."""
import bpy, os, math, subprocess
from mathutils import Matrix

GLTFPACK = os.environ.get('GLTFPACK', '/home/box/apps/gltftools/node_modules/.bin/gltfpack')

def place_ht04(path, coll, frame=None, fill=1.0, at=(0.0, 0.0, 0.0), yaw_deg=180.0, tmp='/tmp/rf_ht04_plain.glb'):
    subprocess.run([GLTFPACK, '-i', path, '-o', tmp, '-noq', '-kn', '-ke'], check=True, capture_output=True)
    before = set(bpy.data.objects); acts0 = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=tmp)
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.type == 'MESH' and o.parent is None and o.name.startswith('Icosphere'):   # importer's bone-shape helper
            new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    for o in new:   # keep the prop's material names out of the exporter's way (it creates its own SHM_Paint)
        for sl in getattr(o, 'material_slots', []):
            if sl.material and not sl.material.name.startswith('HT04_'): sl.material.name = 'HT04_' + sl.material.name
    arm = [o for o in new if o.type == 'ARMATURE' and o.name.startswith('Truck')][0]
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o)
    act = [a for a in bpy.data.actions if a not in acts0 and a.name.startswith('truck_dump')][0]
    f0, f1 = act.frame_range
    frame = 22 if frame is None else int(frame)   # 30 fps: bed ~29 deg up, load half slid out (load gone by ~30, bed peak ~40)
    if arm.animation_data: arm.animation_data_clear()
    for fc in act.fcurves:   # bake the clip's pose at `frame` as static pose values (no NLA / action left on the rig)
        bp, _, prop = fc.data_path.rpartition('.')
        tgt = arm.path_resolve(bp) if bp else arm
        if prop in ('location', 'rotation_quaternion', 'rotation_euler', 'scale'): getattr(tgt, prop)[fc.array_index] = fc.evaluate(frame)
    for o in new:
        if o.type == 'MESH' and o.data.shape_keys:
            for k in o.data.shape_keys.key_blocks:
                if k.name == 'fill': k.value = fill
    arm.matrix_world = Matrix.Translation(at) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    print('HT04 placed', arm.name, 'frame', frame, 'of', (f0, f1), 'objects', [o.name for o in new], flush=True)
    return arm, new, frame
