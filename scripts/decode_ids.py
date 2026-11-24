"""Decode raw flat-ID renders (Cycles emission colours, see blender/photoreal/render_ids.py) into id maps.
usage: python3 scripts/decode_ids.py <raw_dir>  -> blender/out/ids/id_XXXX.png (R = id & 255, G = id >> 8)"""
import sys, os, glob, json
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'blender', 'out', 'ids')
ids = json.load(open(os.path.join(ROOT, 'blender', 'out', 'flat_ids.json')))
os.makedirs(OUT, exist_ok=True)
for p in sorted(glob.glob(os.path.join(sys.argv[1], 'raw_*.png'))):
    f = int(os.path.basename(p)[4:8])
    im = np.array(Image.open(p).convert('RGBA')).astype(np.int32)
    r, g, al = im[..., 0], im[..., 1], im[..., 3]
    idx = np.clip(np.round((r - 7) / 14), 0, 17) + 18 * np.clip(np.round((g - 7) / 12), 0, 30)
    idx = np.where(al > 128, idx, 0).astype(np.int32)
    idx[idx > len(ids)] = 0
    out = np.dstack([(idx & 255).astype(np.uint8), (idx >> 8).astype(np.uint8), np.zeros_like(idx, np.uint8)])
    Image.fromarray(out, 'RGB').save(os.path.join(OUT, f'id_{f:04d}.png'), optimize=True)
print('decoded', len(glob.glob(os.path.join(OUT, 'id_*.png'))))
