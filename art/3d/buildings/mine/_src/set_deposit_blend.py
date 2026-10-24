# gltfpack turns alpha-1 BLEND materials back into OPAQUE. Re-set alphaMode BLEND on the deposit materials ONLY
# (SHM_DepositRock, SHM_DepositGlow) by editing the GLB JSON chunk; the binary chunk is copied unchanged.
import json, struct, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
magic, ver, _ = struct.unpack_from('<III', b, 0); assert magic == 0x46546C67
jl, jt = struct.unpack_from('<II', b, 12); assert jt == 0x4E4F534A
js = json.loads(b[20:20 + jl]); rest = b[20 + jl:]
hit = []
for m in js['materials']:
    if m.get('name') in ('SHM_DepositRock', 'SHM_DepositGlow'): m['alphaMode'] = 'BLEND'; hit.append(m['name'])
    else: assert m.get('alphaMode', 'OPAQUE') == 'OPAQUE', m.get('name')
assert sorted(hit) == ['SHM_DepositGlow', 'SHM_DepositRock'], hit
j = json.dumps(js, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
out = struct.pack('<III', magic, ver, 12 + 8 + len(j) + len(rest)) + struct.pack('<II', len(j), jt) + j + rest
open(dst, 'wb').write(out); print('BLEND set on', hit)
