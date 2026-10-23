"""Tiny tiling overlays for the video feed. Run from repo root."""
import numpy as np
from PIL import Image
OUT = "art/ui/earth_coms"
# Scanlines: 1x4 px, one dark line every 4 px (at 3x this is 4 device px; CSS draws it at background-size 1x2 pt).
a = np.zeros((4, 1, 4), np.uint8); a[2:, :, :3] = (4, 14, 20); a[2, :, 3] = 70; a[3, :, 3] = 40
Image.fromarray(a, "RGBA").save(f"{OUT}/fx_scanline_1x4.png", optimize=True)
# Static: 64x64 monochrome noise, alpha only, tileable (pure random is seamless).
rng = np.random.default_rng(7)
n = rng.random((64, 64))
alpha = (np.where(n > 0.5, (n - 0.5) * 2, 0) ** 1.6 * 150).astype(np.uint8)
rgba = np.zeros((64, 64, 4), np.uint8); rgba[..., :3] = (210, 245, 255); rgba[..., 3] = alpha
Image.fromarray(rgba, "RGBA").quantize(32, method=Image.Quantize.FASTOCTREE).save(f"{OUT}/fx_static_64.png", optimize=True)
