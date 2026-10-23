"""Render ONE shot from the saved starter_ship_master.blend (low-memory, one shot per Blender process).
blender -b starter_ship_master.blend -t 4 -P render_shot.py -- --shot hero|close|close4k|ports|turn_270 ... [--out DIR] [--nosplit 1]
Camera framings mirror build_starter_ship.py."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'mine_concepts', '_src')))
import bpy
from mc_common import shoot, argv
A = argv(); OUT = A.get('out', HERE); SHOT = A['shot']
sc = bpy.context.scene; cam = sc.camera
sc.render.use_persistent_data = False
sc.cycles.debug_use_spatial_splits = False if A.get('nosplit', '1') == '1' else sc.cycles.debug_use_spatial_splits
sc.render.threads_mode = 'FIXED'; sc.render.threads = int(A.get('threads', 4))
sc.cycles.tile_size = 512
def pw(deg, r, z): a = math.radians(deg); return (round(r * math.cos(a), 3), round(r * math.sin(a), 3), z)
TGT = (0.0, -3.0, 18.5)
CL_T, CL_P = pw(248, 3.0, 11.6), pw(254, 31.0, 7.4)
if SHOT.startswith('turn_'):
    k = int(SHOT[5:]); a = math.radians(k); dist, elev = 60, 10
    pos = (TGT[0] - dist * math.sin(a) * math.cos(math.radians(elev)), TGT[1] - dist * math.cos(a) * math.cos(math.radians(elev)),
           TGT[2] + dist * math.sin(math.radians(elev)))
    shoot(cam, os.path.join(OUT, 'turntable', f'turn_{k:03d}.png'), TGT, pos, 1100, 1100, 35, int(A.get('s', 40)))
elif SHOT == 'close':
    shoot(cam, os.path.join(OUT, 'turntable', 'closeup.png'), CL_T, CL_P, 1600, 1000, lens=20, samples=int(A.get('s', 96)))
elif SHOT == 'close4k':
    shoot(cam, os.path.join(OUT, 'starter_ship_closeup_ladder_airlock_hoist_3840x2160.png'), CL_T, CL_P, 3840, 2160, lens=20, samples=int(A.get('s', 64)))
elif SHOT == 'ports':
    shoot(cam, os.path.join(OUT, 'turntable', 'ports.png'), pw(215, 3.6, 21.55), pw(210, 11.5, 21.3), 1200, 800, lens=50, samples=int(A.get('s', 96)))
elif SHOT == 'hero':
    shoot(cam, os.path.join(OUT, 'starter_ship_hero_3840x2160.png'), (0.5, -4.0, 18.0), (-23.0, -50.0, 9.5), 3840, 2160, lens=22, samples=int(A.get('s', 64)))
