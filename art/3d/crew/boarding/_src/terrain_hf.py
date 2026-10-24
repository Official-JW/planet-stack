# v4.1 hotfix: Pad_Base top heightfield (pad-local glTF x/z, 2 cm grid) for the walk.
#   node terrain_tris.mjs qa3d-next/models/launch_pad_82131aba.glb /tmp/hf_padbase.f32  (run from /home/box/apps/gltftools)
#   python3 terrain_hf.py /tmp/hf_padbase.f32 /tmp/hf_grid.npz
import sys, numpy as np
from scipy.ndimage import maximum_filter
T = np.fromfile(sys.argv[1], np.float32).reshape(-1, 3, 3).astype(float)
x0, z0, dx = -14.0, -13.0, 0.02; nx = nz = 1200
H = np.full((nx, nz), -1.0); X = x0 + dx * np.arange(nx); Z = z0 + dx * np.arange(nz)
for a, b, c in T:
    i0 = max(0, int((min(a[0], b[0], c[0]) - x0) / dx)); i1 = min(nx - 1, int((max(a[0], b[0], c[0]) - x0) / dx) + 1)
    j0 = max(0, int((min(a[2], b[2], c[2]) - z0) / dx)); j1 = min(nz - 1, int((max(a[2], b[2], c[2]) - z0) / dx) + 1)
    if i1 < i0 or j1 < j0: continue
    gx, gz = np.meshgrid(X[i0:i1 + 1], Z[j0:j1 + 1], indexing='ij'); v0 = b - a; v1 = c - a; d = v0[0] * v1[2] - v1[0] * v0[2]
    if abs(d) < 1e-10: continue
    px = gx - a[0]; pz = gz - a[2]; u = (px * v1[2] - v1[0] * pz) / d; w = (v0[0] * pz - px * v0[2]) / d
    m = (u >= -1e-6) & (w >= -1e-6) & (u + w <= 1 + 1e-6); y = a[1] + u * v0[1] + w * v1[1]
    sub = H[i0:i1 + 1, j0:j1 + 1]; sub[m] = np.maximum(sub[m], y[m])
r = 6; yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
np.savez(sys.argv[2], H=H, HF=maximum_filter(H, footprint=(xx ** 2 + yy ** 2) <= r * r), x0=x0, z0=z0, dx=dx)
