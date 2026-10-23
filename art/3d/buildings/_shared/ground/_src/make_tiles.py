"""numpy post-process for bake_ground.py output -> PNG masters + KTX2 game tiles (KTX-Software `ktx create`).
  python3 make_tiles.py /tmp/ground  art/3d/buildings/_shared/ground"""
import sys, os, subprocess, json
import numpy as np
from PIL import Image
SRC, DST = sys.argv[1], sys.argv[2]
KTX = os.environ.get('KTX', '/home/box/apps/gltftools/ktx'); TOKTX = os.path.join(KTX, 'bin', 'toktx')
ENV = dict(os.environ, LD_LIBRARY_PATH=os.path.join(KTX, 'lib'))
T_DETAIL, T_MACRO = 10.0, 76.0
def srgb(x): x = np.clip(x, 0, 1); return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
def seam(a):     # wrap-around step vs. the mean interior step (1.0 = the seam is as smooth as any other pixel pair)
    a = a.astype(np.float64); di = np.abs(np.diff(a, axis=1)).mean(); ds = np.abs(a[:, 0] - a[:, -1]).mean()
    dj = np.abs(np.diff(a, axis=0)).mean(); dt = np.abs(a[0] - a[-1]).mean(); return round(ds / di, 3), round(dt / dj, 3)
D = np.load(os.path.join(SRC, 'detail.npy'), allow_pickle=True).item(); M = np.load(os.path.join(SRC, 'macro.npy'), allow_pickle=True).item()
os.makedirs(os.path.join(DST, '_src', 'png'), exist_ok=True); P = os.path.join(DST, '_src', 'png')
rep = {}
# ---- base colour (sRGB)
col = D['color'][..., :3].astype(np.float64)
# De-band: the detail tile must not carry structure at its own repeat scale, or a 10 m grid of blobs shows from
# the game camera. Remove luminance wavelengths >= ~2.5 m (k <= 4 cycles/tile, cosine taper k 2..5) with a periodic
# FFT high-pass, keeping chroma and the mean. The 76 m macro tile supplies the large-scale variation instead.
lw = np.array([0.2126, 0.7152, 0.0722]); Lum = col @ lw
K = np.fft.fftfreq(Lum.shape[0]) * Lum.shape[0]; kr = np.hypot(K[:, None], K[None, :])
keep = np.clip((kr - 2.0) / 3.0, 0, 1); keep = 0.5 - 0.5 * np.cos(np.pi * keep); keep[0, 0] = 1.0
Lhp = np.real(np.fft.ifft2(np.fft.fft2(Lum) * keep))
col = col * (np.clip(Lhp, 1e-4, None) / np.clip(Lum, 1e-4, None))[..., None]
rep['deband_lum_std_before_after'] = [round(float(Lum.std() / Lum.mean()), 4), round(float(Lhp.std() / Lhp.mean()), 4)]
col8 = (srgb(col) * 255 + 0.5).astype(np.uint8)
Image.fromarray(col8).save(os.path.join(P, 'ground_basecolor_1024.png'))
rep['basecolor_mean_linear'] = [round(float(v), 4) for v in col.reshape(-1, 3).mean(0)]
rep['basecolor_mean_srgb8'] = [int(v) for v in col8.reshape(-1, 3).mean(0).round()]
rep['seam_basecolor'] = seam(col8.mean(2))
# ---- normal (OpenGL / three.js: +X right, +Y up = +v; tangent-space, linear)
h = D['height'][..., 0].astype(np.float64) * 0.08 * 0.4          # M_ground Bump: distance 0.08 m, strength 0.4
px = T_DETAIL / h.shape[0]
gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * px)
gv = -(np.roll(h, -1, 0) - np.roll(h, 1, 0)) / (2 * px)          # row 0 = top = high v
n = np.stack([-gx, -gv, np.ones_like(h)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
n512 = n.reshape(512, 2, 512, 2, 3).mean((1, 3)); n512 /= np.linalg.norm(n512, axis=-1, keepdims=True)
for nm, nn in (('1024', n), ('512', n512)):
    Image.fromarray(((nn * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).save(os.path.join(P, 'ground_normal_%s.png' % nm))
rep['normal_mean_tilt_deg'] = round(float(np.degrees(np.arccos(n[..., 2])).mean()), 2)
rep['seam_normal'] = seam(n512[..., 0])
# ---- macro variation (linear luminance multiplier, mean 1, stored as mult / 2 so 0.5 = x1.0)
f = M['fields']; a, b, c = f[..., 0], f[..., 1], f[..., 2]
def ss(x, e0, e1): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
mult = (0.66 + 0.68 * ss(a, 0.3, 0.7)) * (1.0 - 0.14 * ss(b, 0.35, 0.65)) * (0.94 + 0.12 * c)
mult /= mult.mean(); mult = np.clip(mult, 0.55, 1.45)
m8 = (mult / 2 * 255 + 0.5).astype(np.uint8)
Image.fromarray(np.stack([m8] * 3, -1)).save(os.path.join(P, 'ground_macro_256.png'))
rep['macro_mult_range'] = [round(float(mult.min()), 3), round(float(mult.max()), 3)]; rep['seam_macro'] = seam(m8)
# ---- KTX2 (KTX-Software 4.4.2 `ktx create`; mipmaps generated with WRAP edge sampling so the mips stay seamless too)
def ktx(out, src, fmt, args):
    o = os.path.join(DST, out)
    cmd = [os.path.join(KTX, 'bin', 'ktx'), 'create', '--format', fmt, '--generate-mipmap', '--mipmap-filter', 'lanczos4', '--mipmap-wrap', 'wrap'] + args + [src, o]
    subprocess.run(cmd, check=True, env=ENV); return os.path.getsize(o)
NORM = os.environ.get('NORMAL_RES', '512')
rep['ktx2_bytes'] = {
    'ground_basecolor_1024.ktx2': ktx('ground_basecolor_1024.ktx2', os.path.join(P, 'ground_basecolor_1024.png'), 'R8G8B8_SRGB',
                                      ['--encode', 'basis-lz', '--clevel', '5', '--qlevel', os.environ.get('QC', '255')]),
    'ground_normal_%s.ktx2' % NORM: ktx('ground_normal_%s.ktx2' % NORM, os.path.join(P, 'ground_normal_%s.png' % NORM), 'R8G8B8_UNORM',
                                    ['--assign-tf', 'linear', '--encode', 'uastc', '--uastc-quality', '3', '--uastc-rdo', '--uastc-rdo-l', os.environ.get('RDO', '1.0'), '--zstd', '20']),
    'ground_macro_256.ktx2': ktx('ground_macro_256.ktx2', os.path.join(P, 'ground_macro_256.png'), 'R8G8B8_UNORM',
                                 ['--assign-tf', 'linear', '--encode', 'basis-lz', '--clevel', '5', '--qlevel', '255']),
}
rep['ktx2_total_bytes'] = sum(rep['ktx2_bytes'].values())
json.dump(rep, open(os.path.join(DST, '_src', 'tiles_report.json'), 'w'), indent=1); print(json.dumps(rep, indent=1))
