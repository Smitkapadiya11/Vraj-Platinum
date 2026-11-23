"""Builds tileable PBR-ish albedo textures from the real Vraj Platinum site photos (public/site/*.jpg).
Lighting is flattened (divide by a large blur), then the tile is made seamless with an offset cross-fade."""
import numpy as np, os
from PIL import Image, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE, OUT = os.path.join(ROOT, 'public', 'site'), os.path.join(ROOT, 'public', 'tex')
rng = np.random.default_rng(3)

def load(name, box):
    return np.asarray(Image.open(os.path.join(SITE, name + '.jpg')).convert('RGB').crop(box)).astype(np.float32) / 255

def flatten(a, r=40):
    blur = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255
    return a / np.maximum(blur, 0.02)  # ~1.0 mean detail

def seamless(a):
    h, w = a.shape[:2]
    b = np.roll(np.roll(a, h // 2, 0), w // 2, 1)
    y = np.abs(np.linspace(-1, 1, h))[:, None]; x = np.abs(np.linspace(-1, 1, w))[None, :]
    m = np.clip(np.maximum(x, y) * 1.6 - 0.6, 0, 1)[..., None]  # 0 centre -> 1 edges
    return a * (1 - m) + b * m

def save(a, name, size=512):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
    im.save(os.path.join(OUT, name + '.jpg'), quality=86)
    print(name, im.size)

def tint(detail, rgb, amount=1.0):
    d = detail.mean(2, keepdims=True)
    d = 1 + (d - 1) * amount
    return d * np.array(rgb, np.float32)[None, None, :] / 255

def noise(h, w, scales=(4, 16, 64), amp=(0.5, 0.3, 0.2)):
    out = np.zeros((h, w), np.float32)
    for s, a in zip(scales, amp):
        n = rng.random((s, s)).astype(np.float32)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
        out += (n - 0.5) * a
    return out

# 1) textured (sand-finish) paint — colours sampled from the real piers/walls in 163833537
pier = np.asarray(Image.open(os.path.join(SITE, '163833537.jpg')).convert('RGB').crop((1010, 320, 1070, 600))).reshape(-1, 3)
ch_rgb = tuple(int(v * 1.12) for v in np.median(pier, 0))
print('pier colour', ch_rgb)
sand = 1 + noise(512, 512, (64, 256, 512), (0.05, 0.12, 0.22)) + noise(512, 512, (6, 24), (0.06, 0.04))
spk = (rng.random((512, 512)) > 0.985) * -0.18
detail = seamless((sand + spk)[..., None].repeat(3, 2))
save(tint(detail, (104, 106, 111), 1.0), 'charcoal')
save(tint(detail, (233, 231, 226), 0.5), 'white')
save(tint(detail, (196, 196, 192), 0.6), 'lightgrey')
# 3) concrete walkway pavers (photo 163134291)
pv = flatten(load('163134291', (900, 1400, 1110, 1580)), 30)
pv = np.asarray(Image.fromarray(np.clip(pv * 127, 0, 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS)).astype(np.float32) / 127
pv = tint(seamless(pv), (170, 168, 162), 0.9)
g = np.ones((512, 512, 1), np.float32); g[::128, :] = 0.78; g[:, ::128] = 0.78
save(pv * g, 'paver')
# 4) stone cladding on the entrance walls (photo 164556602, beige limestone band)
st = flatten(load('164556602', (120, 1040, 470, 1105)), 20)
st = np.asarray(Image.fromarray(np.clip(st * 127, 0, 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS)).astype(np.float32) / 127
st = tint(seamless(st), (198, 192, 180), 0.8) * (1 + noise(512, 512)[..., None] * 0.12)
jt = np.ones((512, 512, 1), np.float32); jt[::256, :] = 0.72; jt[:, ::171] = 0.72
save(st * jt, 'stone')
# 5) bronze perforated signage panel (photo 164556602)
br = flatten(load('164556602', (70, 1150, 420, 1320)), 60)
save(tint(seamless(np.asarray(Image.fromarray(np.clip(br * 127, 0, 255).astype(np.uint8)).resize((512, 512))).astype(np.float32) / 127), (150, 120, 92), 1.0), 'bronze')
# 6) wood cladding / gates (vertical grain, colour sampled from the gate slats)
h = w = 512
yy = np.linspace(0, 1, h)[:, None]
grain = np.sin((np.arange(w)[None, :] / 5.0 + noise(h, w, (2, 8, 32), (6, 3, 1)) * 3) ) * 0.06 + noise(h, w, (8, 64, 256), (0.15, 0.1, 0.08))
wood = (1 + grain)[..., None] * np.array([139, 90, 58], np.float32)[None, None, :] / 255
save(seamless(wood), 'wood')
# 7) lawn
ln = 1 + noise(512, 512, (8, 64, 256), (0.25, 0.2, 0.25))
save(seamless(ln[..., None] * np.array([88, 128, 52], np.float32)[None, None, :] / 255), 'lawn')
# 8) asphalt
asph = 1 + noise(512, 512, (16, 128, 512), (0.15, 0.15, 0.3))
save(asph[..., None] * np.array([66, 68, 72], np.float32)[None, None, :] / 255, 'asphalt')
