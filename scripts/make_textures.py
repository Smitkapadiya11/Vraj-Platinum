"""Clean, vector-drawn material textures for Vraj Platinum (public/tex).

No photo pixels are used: every map is drawn procedurally (anti-aliased by 4x supersampling, seamless by
construction via periodic FFT noise and wrap-around patterns), then paired with a tangent-space normal map.
The look is "architectural presentation model": near-flat finishes with only the detail an architect would
draw (panel joints, plank lines, paver grid, mowing stripes), coloured from the real site photos.

Palette (sampled from public/site/*.jpg, 23 Nov 2026, white-balanced to daylight):
  white plaster / balcony bands   #ECEAE5   (163833537 fascia, corrected from #E6E4ED shade cast)
  charcoal sand-finish piers      #5C5D61   (163833537 piers, #8A8892 in shade -> sunlit albedo)
  light grey stilts / soffits     #D3D3CF
  walnut fascia / vertical strip  #7A563D   (164615648 brown bands, 164556602 gate slats #52423B in shade)
  stone porcelain signage wall    #D4D0C8   (164615648 large-format slabs)
  champagne bronze panel/letters  #A8875F   (164556602 perforated panel, 164615648 letters)
  concrete pavers                 #BDB7AC   (163134291 walkway)
  lawn                            #64894A / #759A56 mowing stripes
  asphalt                         #4D5055

python3 scripts/make_textures.py
"""
import numpy as np, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public', 'tex')
rng = np.random.default_rng(7)


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def pnoise(n, scale, seed=None):
    """Periodic (tileable) smooth noise, n x n, features ~scale px; zero mean, unit std."""
    r = np.random.default_rng(seed) if seed is not None else rng
    f = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    spec = np.exp(-f * (scale ** 2) * 9.0) * (r.normal(size=(n, n)) + 1j * r.normal(size=(n, n)))
    a = np.real(np.fft.ifft2(spec))
    return (a - a.mean()) / (a.std() + 1e-9)


def down(a, k):
    """box-downsample by k (anti-aliasing for the supersampled drawings)"""
    h, w = a.shape[:2]
    return a.reshape(h // k, k, w // k, k, *a.shape[2:]).mean((1, 3))


def normal_from_height(hgt, strength):
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5 * strength
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5 * strength
    n = np.stack([-gx, gy, np.ones_like(hgt)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save_rgb(a, name, ext='jpg', q=90):
    im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    p = os.path.join(OUT, f'{name}.{ext}')
    im.save(p, quality=q) if ext == 'jpg' else im.save(p, optimize=True)
    print(f'{name}.{ext}', im.size, os.path.getsize(p) // 1024, 'KB')


def save_pair(albedo, height, name, strength, nq=88):
    save_rgb(albedo, name)
    save_rgb(normal_from_height(height, strength), name + '_n', 'jpg', nq)


def tone(base, var):
    return base[None, None, :] * (1 + var[..., None])


N = 1024

# 1) white plaster (tile 4 m): almost flat, soft large-scale trowel variation + very fine smooth stucco
v = 0.007 * pnoise(N, 220) + 0.004 * pnoise(N, 40) + 0.005 * pnoise(N, 3)
h = 0.6 * pnoise(N, 2.5) + 0.25 * pnoise(N, 8)
save_rgb(tone(hexrgb('#ECEAE5'), v), 'white')
save_rgb(tone(hexrgb('#D3D3CF'), v * 1.2), 'lightgrey')

# 2) charcoal sand-finish paint (tile 2 m): fine even grain, read as texture only under grazing sun
v = 0.02 * pnoise(N, 180) + 0.025 * pnoise(N, 2.2) + 0.012 * pnoise(N, 12)
h = pnoise(N, 1.8) + 0.4 * pnoise(N, 5)
save_rgb(tone(hexrgb('#5C5D61'), v), 'charcoal')
save_rgb(normal_from_height(down(h, 2), 0.7), 'charcoal_n', 'jpg', 80)

# 3) walnut wood (tile 1.2 m, grain vertical = along v): 8 boards, crisp joints, long fibres
S = 4
n = N * S
x = np.arange(n)[None, :].repeat(n, 0).astype(np.float32)
y = np.arange(n)[:, None].repeat(n, 1).astype(np.float32)
bw = n / 8
board = np.floor(x / bw)
brng = np.random.default_rng(3)
btone = brng.normal(0, 0.012, 8)
warp = pnoise(N, 90, 11)
warp = np.kron(warp, np.ones((S, S)))
fib = np.sin((x + warp * 14 + board * 37) / (bw / 14) * np.pi) * 0.5 + 0.5
fib = fib ** 3
fine = np.kron(pnoise(N, 1.2, 5), np.ones((S, S)))
jdist = np.minimum(x % bw, bw - (x % bw))
joint = 0.85 + 0.15 * np.clip(jdist / 2.0, 0, 1)
val = btone[board.astype(int) % 8] - 0.09 * fib + 0.03 * fine
alb = tone(hexrgb('#7A563D'), val) * joint[..., None]
hgt = (joint - 1) * 2 - 0.15 * fib
save_pair(down(alb, S), down(hgt, S), 'wood', 1.2)

# 4) stone porcelain cladding (tile 2.4 m x 2.4 m): 1200 x 600 slabs, running bond, 3 mm dark joints
n = N * S
x = np.arange(n)[None, :].repeat(n, 0).astype(np.float32)
y = np.arange(n)[:, None].repeat(n, 1).astype(np.float32)
sw, sh = n / 2, n / 4
row = np.floor(y / sh)
xs = (x + (row % 2) * sw / 2) % n
col = np.floor(xs / sw)
sid = (row * 2 + col).astype(int)
stone_t = np.random.default_rng(9).normal(0, 0.025, 64)
vein = np.kron(0.012 * pnoise(N, 60, 21) + 0.008 * pnoise(N, 6, 22), np.ones((S, S)))
jd = np.minimum(np.minimum(xs % sw, sw - xs % sw), np.minimum(y % sh, sh - y % sh))
joint = np.clip((jd - 9) / 6, 0, 1)
alb = tone(hexrgb('#D4D0C8'), stone_t[sid % 64] + vein) * (0.6 + 0.4 * joint)[..., None]
save_pair(down(alb, S), down((joint - 1) * 1.5, S), 'stone', 1.6)

# 5) champagne bronze, brushed horizontally, with a graded perforation field (tile 1.5 m)
n = N * S
x = np.arange(n)[None, :].repeat(n, 0).astype(np.float32)
y = np.arange(n)[:, None].repeat(n, 1).astype(np.float32)
brush = np.kron(np.repeat(np.random.default_rng(4).normal(0, 1, (N, 1)), N, 1), np.ones((S, S)))
brush = 0.03 * (brush + np.roll(brush, S, 0) + np.roll(brush, -S, 0)) / 3
pitch = n / 30
cx, cy = (x % pitch) - pitch / 2, (y % pitch) - pitch / 2
r = np.hypot(cx, cy)
grad = 0.5 + 0.5 * np.sin((np.floor(x / pitch) + np.floor(y / pitch)) / 80 * 2 * np.pi)  # diagonal wave of hole sizes
rad = pitch * (0.08 + 0.16 * grad)
hole = np.clip((rad - r) / 1.5, 0, 1)
alb = tone(hexrgb('#A8875F'), brush) * (1 - 0.6 * hole)[..., None]
save_pair(down(alb, S), down(-hole * 2 + brush * 4, S), 'bronze', 1.4)

# 6) concrete pavers (tile 2.4 m): 600 x 300 stack bond in two tones, chamfered joints
n = N * S
x = np.arange(n)[None, :].repeat(n, 0).astype(np.float32)
y = np.arange(n)[:, None].repeat(n, 1).astype(np.float32)
pw, ph = n / 4, n / 8
row = np.floor(y / ph)
xs = (x + (row % 2) * pw / 2) % n
pid = (row * 4 + np.floor(xs / pw)).astype(int)
ptone = np.random.default_rng(12).normal(0, 0.025, 64)
jd = np.minimum(np.minimum(xs % pw, pw - xs % pw), np.minimum(y % ph, ph - y % ph))
joint = np.clip((jd - 8) / 7, 0, 1)
grit = np.kron(0.03 * pnoise(N, 1.5, 31), np.ones((S, S)))
alb = tone(hexrgb('#BDB7AC'), ptone[pid % 64] + grit) * (0.62 + 0.38 * joint)[..., None]
save_pair(down(alb, S), down(joint * 1.5 + grit * 3, S), 'paver', 1.4)

# 7) lawn (tile 4 m): two 2 m mowing stripes + soft clumps + fine blades
x = np.arange(N)[None, :].repeat(N, 0)
stripe = (np.sin(x / N * 2 * np.pi) > 0).astype(np.float32)
stripe = np.clip(np.convolve(np.r_[stripe[0, -16:], stripe[0], stripe[0, :16]], np.ones(33) / 33, 'valid'), 0, 1)[None, :].repeat(N, 0)
a, b = hexrgb('#64894A'), hexrgb('#759A56')
base = a[None, None, :] * (1 - stripe[..., None]) + b[None, None, :] * stripe[..., None]
var = 0.02 * pnoise(N, 70, 41) + 0.035 * pnoise(N, 1.6, 42)
save_rgb(base * (1 + var[..., None]), 'lawn')

# 8) asphalt (tile 6 m): smooth dark, faint fine aggregate, soft patching
v = 0.035 * pnoise(N, 1.3, 51) + 0.03 * pnoise(N, 160, 52)
save_rgb(tone(hexrgb('#4D5055'), v), 'asphalt')
