"""Extract the exterior parts the pad's game ship needs from the committed starter ship master (46a9346).
The starter_ship folder is never edited: the master is read from git into /tmp first, e.g.
  git show 46a9346:art/3d/ship/starter_ship/starter_ship_master.glb > /tmp/starter_ship_master_46a9346.glb
  blender -b -t 4 -P lp_extract_starter.py -- /tmp/starter_ship_master_46a9346.glb starter_ship_46a9346_exterior.glb
Output: world-space meshes (starter frame: z up, ground z 0, cargo door 215 deg, airlock 275 deg), starter material names kept,
Draco-compressed (source file only; the game GLB is meshopt). No interior, suits, crates, nose/landing pods, masts or umbilicals."""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
KEEP = ('Hull', 'SteelBand', 'WeldRing', 'Nose', 'NoseCap', 'SolarBand', 'AftSkirt', 'AftSkirtLip', 'AftDome',
        'SkirtGlow', 'DeckGlow', 'BayGlow', 'UpperGlow', 'SolarGlowLo',
        'EngineBell', 'EngineBellLip', 'LegPad', 'LegStrut_body', 'LegStrut_rod', 'LegStrut_gland', 'LegBrace', 'LegFairing', 'LegKnuckle',
        'Raceway', 'RCSBlock', 'RadiatorTiles', 'AftTilesBack')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
keep = []
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name.split('.')[0] in KEEP:
        me = o.data.copy(); me.transform(o.matrix_world)
        n = bpy.data.objects.new(o.name, me); bpy.context.scene.collection.objects.link(n); keep.append(n)
for o in list(bpy.data.objects):
    if o not in keep: bpy.data.objects.remove(o)
print('KEPT', len(keep), sum(len(p.vertices) - 2 for o in keep for p in o.data.polygons))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
                          export_materials='EXPORT', export_image_format='NONE', export_texcoords=False, export_normals=True, export_animations=False, export_yup=True)
