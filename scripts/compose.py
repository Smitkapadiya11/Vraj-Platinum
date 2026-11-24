"""Compose the final 360: real stitched view + smooth fitted sky + 3D-rendered balcony/room behind.
usage: python3 compose.py eq1 render.png out_prefix
"""
import cv2, numpy as np, sys

src, rpath, out = sys.argv[1], sys.argv[2], sys.argv[3]
R = cv2.imread(src + '.jpg').astype(np.float32)
Mr = cv2.imread(src + '_mask.png', 0)
H, W = Mr.shape
def grid(w, h):
    lat = ((0.5 - (np.arange(h) + 0.5) / h)[:, None] * np.pi).astype(np.float32)
    lon = ((((np.arange(w) + 0.5) / w - 0.5))[None, :] * 2 * np.pi).astype(np.float32)
    return np.repeat(lat, w, 1), np.repeat(lon, h, 0)
LAT, LON = grid(W, H)
LATs, LONs = grid(W // 4, H // 4)

# ---- real-coverage alpha (feathered, kept inside the valid area)
real_a = cv2.erode(Mr, np.ones((15, 15), np.uint8))
real_a = cv2.GaussianBlur(real_a.astype(np.float32) / 255, (0, 0), 9)

# ---- sky classification inside the real image
b, g, r = R[..., 0], R[..., 1], R[..., 2]
br = None
gray = cv2.cvtColor(R.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
del br
grad = cv2.GaussianBlur(np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0)) + np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1)), (0, 0), 3)
sky = (Mr > 0) & (b > r + 4) & ((r + g + b) > 360) & (grad < 9) & (LAT > np.radians(1.0))
n, lab, stats, _ = cv2.connectedComponentsWithStats(sky.astype(np.uint8), 8)
big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
sky = lab == big
# fill holes in the sky that are fully enclosed (haze blotches)
sky_u8 = sky.astype(np.uint8) * 255
sky_u8 = cv2.morphologyEx(sky_u8, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))

# ---- fit a smooth sky model  colour = f(elevation, azimuth)
ys, xs = np.where(sky_u8[::4, ::4] > 0)
ys *= 4; xs *= 4
e = LAT[ys, xs]; a = LON[ys, xs]
def feats(e, a):
    e1 = np.clip(e, 0, np.pi / 2)
    s = np.exp(-e1 / 0.09)                                  # haze near the horizon
    return np.stack([np.ones_like(e1), e1, e1 ** 2, e1 ** 3, s, np.cos(a) * (1 - e1 / 1.6), np.sin(a) * (1 - e1 / 1.6), s * np.cos(a), s * np.sin(a)], -1)
F = feats(e, a)
model = []
for ch in range(3):
    y = R[ys, xs, ch]
    coef, *_ = np.linalg.lstsq(F, y, rcond=None)
    model.append(coef)
FA = feats(LATs, LONs)
SKY = np.stack([FA @ c for c in model], -1).astype(np.float32)
del FA
SKY = cv2.resize(np.clip(SKY, 0, 255), (W, H), interpolation=cv2.INTER_CUBIC)
# gentle zenith: blend to the fitted zenith colour so the pole is clean
zen = np.array([feats(np.array([np.pi / 2]), np.array([0.0])) @ c for c in model]).ravel()
zw = np.clip((LAT - np.radians(70)) / np.radians(20), 0, 1)[..., None]
SKY = SKY * (1 - zw) + zen[None, None, :] * zw
SKY = SKY.astype(np.float32) + np.random.default_rng(1).normal(0, 0.8, SKY.shape).astype(np.float32)   # anti-banding

# replace the real sky with the model (removes stitching blotches), feathered inside the sky
sky_full = sky_u8 | (((Mr == 0) & (LAT > np.radians(8))).astype(np.uint8) * 255)
sky_full = cv2.morphologyEx(sky_full, cv2.MORPH_CLOSE, np.ones((61, 61), np.uint8))
sky_a = cv2.erode(sky_full, np.ones((9, 9), np.uint8))
sky_a = cv2.GaussianBlur(sky_a.astype(np.float32) / 255, (0, 0), 5)
# nothing in this view rises above ~5° (the skyline is far away): above that it is all sky, so use the clean model everywhere
sky_a = np.maximum(sky_a, np.clip((LAT - np.radians(4.5)) / np.radians(3), 0, 1))[..., None]
REAL = R * (1 - sky_a) + SKY * sky_a

# ---- fallback layer for areas nobody saw: sky model above the horizon, extended ground below
fb = SKY.copy()
small = cv2.resize(REAL.astype(np.uint8), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
hole = cv2.resize((Mr == 0).astype(np.uint8) * 255, (W // 8, H // 8), interpolation=cv2.INTER_NEAREST)
inp = cv2.inpaint(small, hole, 12, cv2.INPAINT_TELEA)
inp = cv2.GaussianBlur(cv2.resize(inp, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 6).astype(np.float32)
below = np.clip((np.radians(3) - LAT) / np.radians(6), 0, 1)[..., None]
fb = fb * (1 - below) + inp * below

# ---- 3D render of the balcony + living room (equirect, same centre)
rend = cv2.imread(rpath, cv2.IMREAD_UNCHANGED)
rend = cv2.resize(rend, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
ra = (rend[..., 3:4] / 255)
rc = rend[..., :3]
# the slab soffit above the camera renders almost black (no bounce light): paint it as light concrete,
# brighter towards the open side, so looking up feels like a real balcony ceiling
lum = rc.mean(-1, keepdims=True)
soff = ((LAT > np.radians(30)) & (rend[..., 3] > 250))[..., None] & (lum < 60)
shade = (0.62 + 0.25 * np.clip(np.cos(LON), 0, 1) * np.clip((np.radians(80) - LAT) / np.radians(50), 0, 1))[..., None]
conc = np.array([186, 192, 198], np.float32)[None, None, :] * shade
rc = np.where(soff, conc, rc)
# grade the render toward the photo's warm late-afternoon look
rc = np.clip((rc - 128) * 0.92 + 128, 0, 255) * np.array([0.96, 1.0, 1.05])[None, None, :]

# the balcony side walls of the render win over the photo's outermost edges (keeps a clean frame)
wall = ((ra[..., 0] > 0.9) & (np.abs(LON) > np.radians(70))).astype(np.float32)
wall = cv2.GaussianBlur(wall, (0, 0), 6)
real_a = real_a * (1 - wall)
img = fb * (1 - ra) + rc * ra
img = img * (1 - real_a[..., None]) + REAL * real_a[..., None]
img = np.clip(img, 0, 255).astype(np.uint8)
cv2.imwrite(out + '.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 86, cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
cv2.imwrite(out + '_m.jpg', cv2.resize(img, (4096, 2048), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 84, cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
cv2.imwrite(out + '_t.jpg', cv2.resize(img, (512, 256), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 80])
cv2.imwrite(out + '_preview.jpg', cv2.resize(img, (1600, 800), interpolation=cv2.INTER_AREA))
print('ok', img.shape)
