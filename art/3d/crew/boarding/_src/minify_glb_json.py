"""Round every float in a GLB's JSON chunk to 6 significant digits and re-serialise compactly. The BIN chunk is copied byte for byte.
Accessor min/max are rounded outward so bounds stay conservative."""
import sys, json, struct, math
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
jl = struct.unpack_from('<I', b, 12)[0]; J = json.loads(b[20:20 + jl])
rest = b[20 + jl:]
def r(x, mode=0):
    if isinstance(x, float):
        if x == 0 or not math.isfinite(x): return x
        e = 10 ** (5 - int(math.floor(math.log10(abs(x)))))
        v = (math.floor if mode < 0 else math.ceil if mode > 0 else round)(x * e) / e
        return int(v) if v == int(v) and abs(v) < 1e15 else v
    if isinstance(x, list): return [r(y, mode) for y in x]
    if isinstance(x, dict): return {k: (r(v, -1) if k == 'min' else r(v, 1) if k == 'max' else r(v, mode)) for k, v in x.items()}
    return x
J = r(J)
js = json.dumps(J, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack('<II', len(js), 0x4E4F534A) + js + rest
open(dst, 'wb').write(out)
print('json', jl, '->', len(js), 'total', len(b), '->', len(out))
