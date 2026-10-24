"""Minimal plain-GLB (no extensions, gltfpack -noq output) reader/writer for skinned props, plus merge of extra geometry into the
skinned primitive. Used by the HT-04 / FB-05 detail pass (art/3d/props/ht04/_src/detail_pass.py)."""
import json, struct, numpy as np
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
class GLB:
    def __init__(self, path):
        b = open(path, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]
        self.j = json.loads(b[20:20 + n]); o = 20 + n; bl = struct.unpack('<I', b[o:o + 4])[0]; self.bin = b[o + 8:o + 8 + bl]
    def acc(self, i):
        a = self.j['accessors'][i]; bv = self.j['bufferViews'][a['bufferView']]; dt = CT[a['componentType']]; nc = NC[a['type']]
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); st = bv.get('byteStride', 0); isz = np.dtype(dt).itemsize * nc
        if st and st != isz:
            raw = np.frombuffer(self.bin, np.uint8, count=st * (a['count'] - 1) + isz, offset=off)
            arr = np.stack([np.frombuffer(raw[k * st:k * st + isz].tobytes(), dt) for k in range(a['count'])])
        else: arr = np.frombuffer(self.bin, dt, count=a['count'] * nc, offset=off).reshape(a['count'], nc)
        return arr.copy()
    def node_local(self, n):
        N = self.j['nodes'][n]
        if 'matrix' in N: return np.array(N['matrix']).reshape(4, 4).T
        t = N.get('translation', [0, 0, 0]); r = N.get('rotation', [0, 0, 0, 1]); s = N.get('scale', [1, 1, 1])
        x, y, z, w = r
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        M = np.eye(4); M[:3, :3] = R * np.array(s); M[:3, 3] = t; return M
    def world(self, n):
        par = {c: i for i, N in enumerate(self.j['nodes']) for c in N.get('children', [])}
        M = self.node_local(n)
        while n in par: n = par[n]; M = self.node_local(n) @ M
        return M
    def name(self, n): return self.j['nodes'][n].get('name')
    def find(self, name): return next(i for i, N in enumerate(self.j['nodes']) if N.get('name') == name)
    def skin_mats(self, si=0):
        """per joint: (joint index in skin, node, J_world @ IBM) - maps mesh-space bind vertex -> world (rest)"""
        sk = self.j['skins'][si]; ibm = self.acc(sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        return [(k, n, self.world(n) @ ibm[k]) for k, n in enumerate(sk['joints'])]
    def save(self, path, prim_arrays, mi=0, pi=0):
        """rewrite the whole buffer: every accessor re-emitted; prim_arrays {attr|'indices'|('t',ti,attr): ndarray} replaces those of meshes[mi].primitives[pi]"""
        j = self.j; p = j['meshes'][mi]['primitives'][pi]; repl = {}
        for k, arr in prim_arrays.items():
            if k == 'indices': repl[p['indices']] = arr
            elif isinstance(k, tuple): repl[p['targets'][k[1]][k[2]]] = arr
            else: repl[p['attributes'][k]] = arr
        out = bytearray(); views = []
        for i, a in enumerate(j['accessors']):
            arr = repl.get(i)
            if arr is None: arr = self.acc(i)
            arr = np.ascontiguousarray(arr.astype(CT[a['componentType']]))
            while len(out) % 4: out.append(0)
            bvd = {'buffer': 0, 'byteOffset': len(out), 'byteLength': arr.nbytes}
            ob = j['bufferViews'][a['bufferView']]
            if 'target' in ob: bvd['target'] = ob['target']
            out += arr.tobytes(); views.append(bvd)
            a['bufferView'] = i; a.pop('byteOffset', None); a['count'] = int(arr.shape[0])
            if a['type'] in ('VEC3', 'VEC4', 'SCALAR', 'VEC2') and 'min' in a:
                a['min'] = [float(x) for x in arr.min(0).ravel()] if a['type'] != 'SCALAR' else [float(arr.min())]
                a['max'] = [float(x) for x in arr.max(0).ravel()] if a['type'] != 'SCALAR' else [float(arr.max())]
        while len(out) % 4: out.append(0)
        j['bufferViews'] = views; j['buffers'] = [{'byteLength': len(out)}]
        js = json.dumps(j, separators=(',', ':')).encode();
        while len(js) % 4: js += b' '
        tot = 12 + 8 + len(js) + 8 + len(out)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, tot)); f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack('<II', len(out), 0x004E4942)); f.write(bytes(out))
