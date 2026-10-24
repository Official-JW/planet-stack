#!/usr/bin/env python3
"""Bake the game-palette shade fix into a GLB: ST10B_Paint emissiveFactor = sky tint (0x9fb4d8 linear) x k.
A material value, not lighting.  python3 set_paint_emissive.py in.glb out.glb k"""
import json, struct, sys
src, dst, k = sys.argv[1], sys.argv[2], float(sys.argv[3])
b = open(src, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); rest = b[20 + n:]
for m in j['materials']:
    if m['name'] == 'ST10B_Paint': m['emissiveFactor'] = [round(0.3467 * k, 5), round(0.4564 * k, 5), round(0.6867 * k, 5)]
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + len(rest)) + struct.pack('<I4s', len(js), b'JSON') + js + rest
open(dst, 'wb').write(out); print('EMIS', k, dst, len(out))
