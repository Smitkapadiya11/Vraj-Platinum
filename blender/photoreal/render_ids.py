"""Flat-ID pass for every orbit frame: each flat box emits a unique colour, everything else is a holdout,
so the visible flat under any pixel can be looked up in the web viewer.

python3 render_ids.py [width] [frames]  -> blender/out/ids/id_XXXX.png  (R = id & 255, G = id >> 8, 0 = none)
"""
import sys, os, json
import numpy as np
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'out')
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
W = int(a[0]) if a else 1200
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'photoreal_scene.blend'))
sc = bpy.context.scene
frames = [int(x) for x in a[1].split(',')] if len(a) > 1 else list(range(sc.frame_start, sc.frame_end + 1))
ids = json.load(open(os.path.join(OUT, 'flat_ids.json')))


def lin(v):
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


# encode index i (1-based) as two well-separated 8-bit levels, decoded back to i below
def code(i):
    return (i % 18) * 14 + 7, (i // 18) * 12 + 7


for o in bpy.data.collections['FLATS'].objects:
    r, g = code(o['idx'])
    o.color = (lin(r), lin(g), lin(7), 1)
vl = sc.view_layers[0]
for lc in vl.layer_collection.children:
    lc.holdout = lc.name != 'FLATS'
    lc.exclude = lc.name in ('TREE_PROTOS', 'PROPS_SRC')
bpy.data.collections['FLATS'].hide_render = False
sc.world.node_tree.nodes.clear()
sc.render.film_transparent = True
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 1
sc.cycles.use_denoising = False
sc.cycles.use_adaptive_sampling = False
sc.cycles.pixel_filter_type = 'BOX'
sc.cycles.filter_width = 0.01
sc.cycles.max_bounces = 0
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0
sc.view_settings.gamma = 1
sc.render.resolution_x = W
sc.render.resolution_y = int(W * 1500 / 2400)
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '8'
os.makedirs(os.path.join(OUT, 'ids'), exist_ok=True)
from PIL import Image
for f in frames:
    sc.frame_set(f)
    tmp = os.path.join(OUT, 'ids', f'raw_{f:04d}.png')
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    im = np.array(Image.open(tmp).convert('RGBA')).astype(np.int32)
    r, g, al = im[..., 0], im[..., 1], im[..., 3]
    idx = np.clip(np.round((r - 7) / 14), 0, 17) + 18 * np.clip(np.round((g - 7) / 12), 0, 30)
    idx = np.where(al > 128, idx, 0).astype(np.int32)
    idx[idx > len(ids)] = 0
    outp = np.dstack([(idx & 255).astype(np.uint8), (idx >> 8).astype(np.uint8), np.zeros_like(idx, np.uint8)])
    Image.fromarray(outp, 'RGB').save(os.path.join(OUT, 'ids', f'id_{f:04d}.png'), optimize=True)
    os.remove(tmp)
    print('frame', f, 'flats visible', len(np.unique(idx)) - 1)
