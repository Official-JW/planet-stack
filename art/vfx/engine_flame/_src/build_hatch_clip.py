# Writes ../hatch_close.glb: an animation-only glTF (no meshes, no textures) for the crew-hatch lid on the cargo ship.
# One node, Hatch_Lid_Hinge, sits on the lid hinge in Ship_Placeholder-local space (launch_pad_game.glb md5 82131aba);
# clip "hatch_close" turns it -100 deg about the hinge axis in 0.8 s with easeInOutCubic baked into 25 LINEAR keys (30 fps).
# hatch_close.js applies that rotation to the lid's own vertices inside the existing ship mesh, so it adds 0 draw calls.
import json, math, struct, os
HINGE = [4.5423, 21.900, 2.6225]           # ship-local glTF (Blender LU*5.245 at z KZ+0.02, LAD_A 330 deg); matches the hinge-rod island centroid
AXIS = [0.5, 0.0, -0.8660254]              # LT (ladder tangent) in glTF
CLOSE_DEG, DUR, FPS = -100.0, 0.8, 30
ease = lambda x: 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
N = int(round(DUR * FPS)) + 1
times = [DUR * i / (N - 1) for i in range(N)]
quats = []
for t in times:
    a = math.radians(CLOSE_DEG) * ease(t / DUR); s = math.sin(a / 2)
    quats += [AXIS[0] * s, AXIS[1] * s, AXIS[2] * s, math.cos(a / 2)]
bin_ = struct.pack('<%df' % N, *times) + struct.pack('<%df' % (4 * N), *quats)
gl = {
  'asset': {'version': '2.0', 'generator': 'planet-stack art/vfx/engine_flame/_src/build_hatch_clip.py'},
  'scene': 0, 'scenes': [{'nodes': [0]}],
  'nodes': [{'name': 'Hatch_Lid_Hinge', 'translation': HINGE, 'extras': {
      'space': 'Ship_Placeholder local (launch_pad_game.glb md5 82131abae3a8e97427635fd2513155fa)',
      'hinge_axis': AXIS, 'open_deg': 100, 'closed_deg': 0,
      'drives': 'lid + 2 ribs (rotate with the hinge), 2 hold-open struts (follow the lid, foot fixed); all are islands in the merged ship mesh, no separate nodes',
      'vertex_ranges_mesh_5_md5_82131aba': {'lid': [8392, 8399], 'ribs': [8400, 8415], 'struts': [8428, 8443], 'hinge_rod_static': [8416, 8427]},
      'select_rule': 'islands with centroid in hinge frame (u = LU, t = axis, z = up): |t| < 0.66, -0.1 < u < 0.3, 0.15 < z < 0.8, <= 16 verts; max z > 0.9 -> lid/rib, else strut',
      'timing': 'start at hatch close = Launch tap + 53.19 s; done 53.99 s; ignition 53.99 s (as the lid seats); lift-off 55.99 s; climb ends 63.99 s; landing burn 663.99 s; touchdown 671.99 s',
      'easing': 'easeInOutCubic baked into LINEAR keys', 'draw_calls_added': 0}}],
  'animations': [{'name': 'hatch_close', 'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'rotation'}}],
                  'samplers': [{'input': 0, 'output': 1, 'interpolation': 'LINEAR'}]}],
  'buffers': [{'byteLength': len(bin_)}],
  'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': 4 * N}, {'buffer': 0, 'byteOffset': 4 * N, 'byteLength': 16 * N}],
  'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': N, 'type': 'SCALAR', 'min': [0.0], 'max': [DUR]},
                {'bufferView': 1, 'componentType': 5126, 'count': N, 'type': 'VEC4'}],
}
js = json.dumps(gl, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4); bin_ += b'\0' * (-len(bin_) % 4)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hatch_close.glb')
with open(out, 'wb') as f:
    f.write(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + 8 + len(bin_)))
    f.write(struct.pack('<I4s', len(js), b'JSON') + js + struct.pack('<I4s', len(bin_), b'BIN\0') + bin_)
print(out, os.path.getsize(out))
