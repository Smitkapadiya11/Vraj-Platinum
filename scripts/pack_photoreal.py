"""Pack rendered orbit frames + flat-ID maps for the web viewer.

python3 scripts/pack_photoreal.py <renders_dir> [kinds]
  renders_dir/<kind>/f_XXXX.jpg (any size, 16:10)   ids from blender/out/ids/id_XXXX.png
-> public/pr/<kind>/f_XXXX.webp (<=2400 w), public/pr/m/<kind>/f_XXXX.webp (1600 w), public/pr/ids/, public/pr/manifest.json
"""
import sys, os, json, glob, shutil
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
kinds = sys.argv[2].split(',') if len(sys.argv) > 2 else [k for k in ('day', 'sunset', 'night') if os.path.isdir(os.path.join(src, k))]
OUT = os.path.join(ROOT, 'public', 'pr')
IDS = os.path.join(ROOT, 'blender', 'out', 'ids')
ids = json.load(open(os.path.join(ROOT, 'blender', 'out', 'flat_ids.json')))
os.makedirs(os.path.join(OUT, 'ids'), exist_ok=True)
nfr = len(glob.glob(os.path.join(IDS, 'id_*.png')))
W = H = None
for k in kinds:
    for sub, w in (('', 2400), ('m', 1600)):
        d = os.path.join(OUT, sub, k)
        os.makedirs(d, exist_ok=True)
    for f in range(nfr):
        p = os.path.join(src, k, f'f_{f:04d}.jpg')
        if not os.path.exists(p):
            continue
        im = cv2.imread(p)
        if W is None:
            W = min(2400, im.shape[1]); H = round(W * im.shape[0] / im.shape[1])
        big = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA) if im.shape[1] != W else im
        cv2.imwrite(os.path.join(OUT, k, f'f_{f:04d}.webp'), big, [cv2.IMWRITE_WEBP_QUALITY, 80])
        mw = min(1600, W)
        cv2.imwrite(os.path.join(OUT, 'm', k, f'f_{f:04d}.webp'), cv2.resize(im, (mw, round(mw * H / W)), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_WEBP_QUALITY, 74])
# ids + best frames
best_u, best_t = {}, {}
score_u = {}
tower_score = {}
for f in range(nfr):
    p = os.path.join(IDS, f'id_{f:04d}.png')
    shutil.copy(p, os.path.join(OUT, 'ids', f'id_{f:04d}.png'))
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)[..., ::-1].astype(np.int32)
    idx = a[..., 0] + 256 * a[..., 1]
    h, w = idx.shape
    yy, xx = np.mgrid[0:h, 0:w]
    centre = 1.0 - np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) * 0.5
    vals = idx.ravel(); cw = centre.ravel()
    sums = np.bincount(vals, weights=cw, minlength=len(ids) + 1)
    for i in range(1, len(ids) + 1):
        s = sums[i]
        if s > score_u.get(i, 0):
            score_u[i] = s; best_u[ids[i - 1]] = f
    ts = {}
    for i in np.nonzero(sums[1:])[0] + 1:
        tw = ids[i - 1].split('-')[0]
        ts[tw] = ts.get(tw, 0) + sums[i]
    for tw, s in ts.items():
        if s > tower_score.get(tw, (0, 0))[0]:
            tower_score[tw] = (s, f)
best_t = {tw: f for tw, (s, f) in tower_score.items()}
idh, idw = idx.shape
man = {'frames': nfr, 'kinds': kinds, 'ids': ids, 'w': W, 'h': H, 'idw': idw, 'idh': idh,
       'base': '/pr', 'mobileBase': '/pr/m', 'best': {**best_u, **best_t}}
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'))
tot = sum(os.path.getsize(p) for p in glob.glob(os.path.join(OUT, '**', '*.*'), recursive=True))
print('packed', kinds, nfr, 'frames', W, H, 'total MB', round(tot / 1e6, 1), 'tower best', best_t)
