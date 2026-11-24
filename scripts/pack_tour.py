"""Pack the demo-flat 360 walkthrough for the web.

usage: python3 scripts/pack_tour.py <renders_dir> <nodes.json> <env.jpg>
  renders_dir holds <node>_4096.png (RGBA equirect from blender/tour/tour.py: world transparent, window glass alpha)
  env.jpg     the real stitched Surat view (scripts/env_compose.py) placed behind every render
Writes public/site/tour/{d,m,t}/<node>.jpg and public/site/tour/tour.json (labels + floor hotspots).
"""
import sys, os, json, math, time
import cv2, numpy as np

rd, nodes_p, env_p = sys.argv[1:4]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public', 'site', 'tour')
nodes = json.load(open(nodes_p))
LINKS = {
    'balcony': ['living'],
    'living': ['balcony', 'dining'],
    'dining': ['living', 'master', 'bed2'],
    'master': ['dining', 'bed2'],
    'bed2': ['dining', 'master'],
}
ORDER = ['balcony', 'living', 'dining', 'master', 'bed2']
env = cv2.imread(env_p).astype(np.float32)
for sub in ('d', 'm', 't'):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
out_nodes = {}
for nid in ORDER:
    f = os.path.join(rd, f'{nid}_4096.png')
    if not os.path.exists(f):
        print('missing', f)
        continue
    r = cv2.imread(f, cv2.IMREAD_UNCHANGED).astype(np.float32)
    H, W = r.shape[:2]
    e = cv2.resize(env, (W, H), interpolation=cv2.INTER_AREA)
    a = r[..., 3:4] / 255.0
    img = np.clip(r[..., :3] * a + e * (1 - a), 0, 255).astype(np.uint8)
    q = [cv2.IMWRITE_JPEG_QUALITY, 84, cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    cv2.imwrite(os.path.join(OUT, 'd', f'{nid}.jpg'), img, q)
    cv2.imwrite(os.path.join(OUT, 'm', f'{nid}.jpg'), cv2.resize(img, (3072, 1536), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 80, cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
    cv2.imwrite(os.path.join(OUT, 't', f'{nid}.jpg'), cv2.resize(img, (1024, 512), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 72])
    pa = nodes[nid]['pos']
    hs = []
    for to in LINKS.get(nid, []):
        if to not in nodes:
            continue
        pb = nodes[to]['pos']
        dx, dy, dz = pb[0] - pa[0], pb[1] - pa[1], 0.05 - pa[2]   # floor spot under the target camera
        lon = math.atan2(-dx, -dy)          # 0 = image centre (camera looks -Y), + = right
        lat = math.atan2(dz, math.hypot(dx, dy))
        hs.append({'to': to, 'u': round(0.5 + lon / (2 * math.pi), 5), 'v': round(0.5 - lat / math.pi, 5)})
    out_nodes[nid] = {'label': nodes[nid]['label'], 'hs': hs}
    print(nid, img.shape, hs)
json.dump({'v': int(time.time()), 'base': '/site/tour/d', 'mobileBase': '/site/tour/m', 'thumbBase': '/site/tour/t', 'nodes': out_nodes},
          open(os.path.join(OUT, 'tour.json'), 'w'), indent=1)
print('ok', len(out_nodes))
