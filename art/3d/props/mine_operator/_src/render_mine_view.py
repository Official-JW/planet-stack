"""Hook for the Mine phone/hero proofs (exec'd inside build_mine.py --mode phone, after the camera is set).
env: OP_RAW (raw GLB), OP_STAGE = phone | hero | hero_test, OP_OUT (png path), OP_CLIP, OP_T (seconds),
     OP_POS = glTF x,z of Operator_Deck, OP_SAMPLES. Renders only; never writes into the Mine folder."""
import os as _os, sys as _sys, math as _m
from mathutils import Vector as _V
_sys.path.insert(0, '/workspace/planet-stack/art/3d/props/mine_operator/_src')
import op_blender_common as _C
_px, _pz = [float(v) for v in _os.environ.get('OP_POS', '14.0,1.2').split(',')]
_bx, _by = _px, -_pz                                    # glTF (x, z) -> Blender (x, -z)
_hz = LAY['height'](_bx, _by)
_hs = [LAY['height'](_bx + dx, _by + dy) for dx in (-1.12, 1.12) for dy in (-0.88, 0.88)]
print('OPDECK ground h centre %.3f legs %s' % (_hz, [round(h, 3) for h in _hs]), flush=True)
_root, _arm, _new = _C.import_operator(_os.environ['OP_RAW'], loc=(_bx, _by, min(_hs)), rot_z=0.0)
_C.set_clip(_arm, _os.environ.get('OP_CLIP', 'op_watch_rail'))
_t = float(_os.environ.get('OP_T', '1.0')); sc.frame_set(int(_t * 30))
_st = _os.environ.get('OP_STAGE', 'phone'); _out = _os.environ['OP_OUT']
sc.cycles.samples = int(_os.environ.get('OP_SAMPLES', A.get('ps', 64)))
if _st.startswith('hero'):
    _cam = sc.camera; _cam.data.sensor_fit = 'AUTO'; _cam.data.lens = 30
    _p = _V((20.5, -10.8, 4.2)); _tg = _V((9.0, -1.0, 2.7))
    _cam.location = _p; _cam.rotation_euler = (_tg - _p).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = (3840, 2160); sc.render.resolution_percentage = 25 if _st == 'hero_test' else 100
    sc.render.use_border = False; sc.render.filepath = _out
    sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2; sc.cycles.volume_bounces = 0; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
    bpy.ops.render.render(write_still=True); print('HERO done', _out, flush=True)
    raise SystemExit(0)
from bpy_extras.object_utils import world_to_camera_view as _w2c
_dg = bpy.context.evaluated_depsgraph_get(); _mo = bpy.data.objects['Op_Mesh'].evaluated_get(_dg)
_ws = [_mo.matrix_world @ _v.co for _v in _mo.data.vertices]
_ps = [_w2c(sc, sc.camera, _w) for _w in _ws]
print('OPDECK screen393 x %.1f..%.1f y %.1f..%.1f' % (min(p.x for p in _ps) * 393, max(p.x for p in _ps) * 393,
      (1 - max(p.y for p in _ps)) * 852, (1 - min(p.y for p in _ps)) * 852), flush=True)
if _st == 'phone_test':
    sc.render.resolution_percentage = 34; sc.render.filepath = _out; sc.cycles.samples = 12
    bpy.ops.render.render(write_still=True); raise SystemExit(0)
# phone: render only a border box around the deck (composited onto the shipped Mine phone render afterwards)
_bx0, _bx1, _by0, _by1 = [float(v) for v in _os.environ.get('OP_BORDER', '540,880,1030,1420').split(',')]   # px on 1179x2556
sc.render.use_border = True; sc.render.use_crop_to_border = False; sc.render.film_transparent = False
sc.render.border_min_x, sc.render.border_max_x = _bx0 / 1179, _bx1 / 1179
sc.render.border_min_y, sc.render.border_max_y = 1 - _by1 / 2556, 1 - _by0 / 2556
sc.render.filepath = _out
