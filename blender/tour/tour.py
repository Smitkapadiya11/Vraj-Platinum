"""Vraj Platinum demo-flat 360 tour (type A, living-room balcony on the road side).

Runs inside an interactive Blender (MCP bridge) or headless:
    import tour; tour.build(repo, work); tour.render_all(work, width=4096, spp=160)
Builds the furnished flat from src/data/plans.json (via blender/pano360.py), upgrades it with CC0 Poly Haven
furniture, polished vitrified floor, oak slat wall and warm show-flat lighting, and lights it with the real
stitched Surat view (tour/env2.jpg) as the world. Each node renders an RGBA equirect (world transparent,
window glass alpha) so the real photo view is composited behind the windows afterwards, untouched.
"""
import bpy, os, sys, json, math, time
from mathutils import Vector, Matrix

NODES_PX = {
    # name: (plan x px, plan y px, eye height m, label)
    'living':  (1385, 470, 1.45, 'Living room'),
    'dining':  (1258, 515, 1.45, 'Kitchen & dining'),
    'master':  (1140, 500, 1.45, 'Master bedroom'),
    'bed2':    (1050, 440, 1.45, 'Bedroom 2'),
}
PH = {  # procedural group type -> (Poly Haven asset, target width m, depth m)
    'sofa3': ('sofa_02', 2.2, 0.92),
    'armchair': ('mid_century_lounge_chair', 0.8, 0.85),
    'coffee': ('modern_coffee_table_02', 1.0, 0.6),
    'plant': ('potted_plant_01', 0.55, 0.55),
}
G = {}
PLACED = []
FIX = {}  # per-asset extra yaw (deg) after visual check


def soft_reset():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.collections,
                 bpy.data.images, bpy.data.node_groups, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for d in list(coll):
            try:
                coll.remove(d)
            except Exception:
                pass


def _scipy_shim():
    """Blender's bundled Python has no scipy; pano360 only needs a box binary_dilation."""
    try:
        import scipy.ndimage  # noqa
        return
    except Exception:
        pass
    import types
    import numpy as np

    def binary_dilation(a, structure):
        k0, k1 = structure.shape
        r0, r1 = k0 // 2, k1 // 2
        p = np.pad(a.astype(np.int32), ((r0, r0), (r1, r1)))
        c = np.pad(p.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        s = c[k0:, k1:] - c[:-k0, k1:] - c[k0:, :-k1] + c[:-k0, :-k1]
        return s > 0
    sp = types.ModuleType('scipy'); nd = types.ModuleType('scipy.ndimage')
    nd.binary_dilation = binary_dilation; sp.ndimage = nd
    sys.modules['scipy'] = sp; sys.modules['scipy.ndimage'] = nd


def build(repo, work):
    _scipy_shim()
    BL = os.path.join(repo, 'blender')
    for p in (BL, os.path.join(BL, 'photoreal')):
        if p not in sys.path:
            sys.path.insert(0, p)
    import bcommon
    bcommon.reset = soft_reset
    if hasattr(bcommon, '_mats'):
        bcommon._mats.clear()
    src = open(os.path.join(BL, 'pano360.py')).read()
    i = src.index('# ---------------------------------------------------------------- 360 balcony render')
    j = src.index("cam = bpy.data.cameras.new('pano')")
    part = src[:j]
    part = part.replace("    def place(s, x, y, rot):\n",
                        "    def place(s, x, y, rot):\n        PLACED.append((s.name, x, y, rot, [o.name for o in s.parts]))\n")
    PLACED.clear()
    G.clear()
    G.update({'__file__': os.path.join(BL, 'pano360.py'), '__name__': '__main__', 'PLACED': PLACED})
    old = sys.argv
    sys.argv = ['blender', 'A']
    try:
        exec(compile(part, os.path.join(BL, 'pano360.py'), 'exec'), G)
    finally:
        sys.argv = old
    for o in list(bpy.data.objects):
        if o.name.startswith('shrub') or o.name.startswith('floor_fb'):
            bpy.data.objects.remove(o)
    log = []
    upgrade_materials(work, log)
    upgrade_furniture(work, log)
    lights(log)
    world(work, log)
    settings()
    return log


# ------------------------------------------------------------------ materials
def _ph_tex(work, asset, kind='Diffuse', res='2k'):
    import assets
    f = assets._files(asset)
    d = f.get(kind)
    if not d:
        return None
    url = d[res]['jpg']['url'] if 'jpg' in d[res] else d[res]['png']['url']
    return assets._get(url, os.path.join(work, 'assets', 'tex', f'{asset}_{kind}_{res}.' + url.rsplit('.', 1)[-1]))


def _img_mat(m, path, scale, rough=None, nor=None):
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / scale, 1 / scale, 1 / scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    t.projection = 'BOX'; t.projection_blend = 0.2
    nt.links.new(mp.outputs[0], t.inputs['Vector'])
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if rough is not None:
        for l in list(b.inputs['Roughness'].links):
            nt.links.remove(l)
        b.inputs['Roughness'].default_value = rough
    return t


def upgrade_materials(work, log):
    M = G.get('M', {})
    # polished large-format vitrified tiles (real sample flat): glossy, crisp grout
    t = M.get('tile')
    if t:
        b = next(n for n in t.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(b.inputs['Roughness'].links):
            t.node_tree.links.remove(l)
        b.inputs['Roughness'].default_value = 0.08
        if 'Coat Weight' in b.inputs:
            b.inputs['Coat Weight'].default_value = 0.35
            b.inputs['Coat Roughness'].default_value = 0.04
        log.append('floor polished')
    for key, asset, sc, r in (('oak', 'oak_veneer_01', 0.9, 0.45), ('walnut', 'black_walnut_veneer_01', 0.9, 0.4)):
        m = M.get(key)
        try:
            p = _ph_tex(work, asset)
            if m and p:
                _img_mat(m, p, sc, r)
                log.append(f'{key} <- {asset}')
        except Exception as e:
            log.append(f'{key} failed {e}')
    w = M.get('wall')
    if w:
        b = next(n for n in w.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs['Base Color'].default_value = (0.86, 0.84, 0.80, 1)
        b.inputs['Roughness'].default_value = 0.75
    s = M.get('sofa')
    if s:  # fallback sofa fabric if a model fails: soft burnt orange velvet sheen
        b = next(n for n in s.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        if 'Sheen Weight' in b.inputs:
            b.inputs['Sheen Weight'].default_value = 0.6


# ------------------------------------------------------------------ furniture
def _import_model(work, asset):
    import assets
    path = assets.model(work, asset)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    names = [o.name for o in new]
    meshes = [o for o in new if o.type == 'MESH']
    for o in new:
        o.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    keep = ob.name
    for n in names:
        o = bpy.data.objects.get(n)
        if o is not None and n != keep:
            bpy.data.objects.remove(o)
    vs = [v.co for v in ob.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for v in ob.data.vertices:
        v.co -= c
    return ob, mx - mn


def upgrade_furniture(work, log):
    cache = {}
    for name, x, y, rot, parts in PLACED:
        t = name.rstrip('0123456789')
        if t not in PH:
            continue
        asset, tw, td = PH[t]
        try:
            if asset not in cache:
                cache[asset] = _import_model(work, asset)
                cache[asset][0].hide_render = True
                cache[asset][0].hide_viewport = True
            proto, dim = cache[asset]
            ob = bpy.data.objects.new(f'{name}_ph', proto.data)
            bpy.context.scene.collection.objects.link(ob)
            swap = (dim.x > dim.y) != (tw > td)
            bw, bd = (dim.y, dim.x) if swap else (dim.x, dim.y)
            s = min(tw / max(bw, 1e-3), td / max(bd, 1e-3))
            yaw = (90 if swap else 0) + 180 + FIX.get(asset, 0)
            ob.matrix_world = (Matrix.Translation((x, y, 0)) @ Matrix.Rotation(-math.radians(rot), 4, 'Z')
                               @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Scale(s, 4))
            for pn in parts:
                o = bpy.data.objects.get(pn)
                if o:
                    bpy.data.objects.remove(o)
            log.append(f'{name} <- {asset} x{s:.2f}')
        except Exception as e:
            log.append(f'{name} failed {e}')


# ------------------------------------------------------------------ lighting / world
def lights(log):
    sc = bpy.context.scene
    H = G.get('H', 2.95)
    led = bpy.data.materials.new('downlight')
    led.use_nodes = True
    b = next(n for n in led.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (1, 1, 1, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.86, 0.68, 1)
    b.inputs['Emission Strength'].default_value = 12
    n = 0
    for r in G['rooms']:
        if r['kind'] not in ('living', 'bed', 'kitchen', 'pass'):
            continue
        x0, x1, y0, y1 = r['m']
        nx, ny = max(1, round((x1 - x0) / 1.3)), max(1, round((y1 - y0) / 1.3))
        for i in range(nx):
            for j in range(ny):
                px = x0 + (i + 0.5) * (x1 - x0) / nx
                py = y0 + (j + 0.5) * (y1 - y0) / ny
                L = bpy.data.lights.new('dl', 'SPOT')
                L.energy = 55 if r['kind'] != 'pass' else 30
                L.color = (1.0, 0.84, 0.66)
                L.spot_size = math.radians(110); L.spot_blend = 0.9
                L.shadow_soft_size = 0.06
                lo = bpy.data.objects.new('dl', L)
                lo.location = (px, py, H - 0.02)
                sc.collection.objects.link(lo)
                bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.01, location=(px, py, H - 0.006))
                d = bpy.context.active_object
                d.name = 'dl_disc'
                d.data.materials.append(led)
                n += 1
    # the old per-room area lights: softer fill
    for o in bpy.data.objects:
        if o.name.startswith('roomlight'):
            o.data.energy *= 0.45
    sun = bpy.data.objects.get('sun')
    if sun:   # late afternoon, sun behind the building (the road side is in shade, like the photos)
        sun.rotation_euler = (math.radians(65), 0, math.radians(0))
        sun.data.energy = 2.0
    log.append(f'{n} downlights')


def world(work, log):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('surat_view')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    p = os.path.join(work, 'tour', 'env2.jpg')
    env.image = bpy.data.images.load(p)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(-90))   # image centre = looking out of the balcony (-Y)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 2.2
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    log.append('world = real stitched Surat view')


def settings():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'GPU'
    cy.use_denoising = True
    cy.max_bounces = 8
    cy.transparent_max_bounces = 16
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Base Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = 0.35
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = t
            prefs.get_devices()
            if any(d.type == t for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == t
                break
        except Exception:
            continue


def node_positions():
    X, Y = G['X'], G['Y']
    out = {}
    for k, (px, py, z, label) in NODES_PX.items():
        out[k] = dict(pos=[X(px), Y(py), z], label=label)
    # balcony node: same spot as the real photos (camera 0.35 m behind the railing)
    wx, wy = X(1430.0), Y(632.0)
    out['balcony'] = dict(pos=[wx, wy - 1.25 + 0.35, 1.5], label='Balcony')
    return out


def camera(pos):
    sc = bpy.context.scene
    cam = bpy.data.objects.get('tourcam')
    if not cam:
        cd = bpy.data.cameras.new('tourcam')
        cd.type = 'PANO'
        try:
            cd.panorama_type = 'EQUIRECTANGULAR'
        except Exception:
            cd.cycles.panorama_type = 'EQUIRECTANGULAR'
        cam = bpy.data.objects.new('tourcam', cd)
        sc.collection.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (math.radians(90), 0, math.radians(180))   # look out of the balcony (-Y)
    sc.camera = cam
    return cam


def render(work, name, width=4096, spp=160):
    sc = bpy.context.scene
    nodes = node_positions()
    camera(nodes[name]['pos'])
    sc.cycles.samples = spp
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = width, width // 2, 100
    od = os.path.join(work, 'tour', 'out')
    os.makedirs(od, exist_ok=True)
    sc.render.filepath = os.path.join(od, f'{name}.png')
    t = time.time()
    bpy.ops.render.render(write_still=True)
    json.dump(nodes, open(os.path.join(work, 'tour', 'nodes.json'), 'w'), indent=1)
    return round(time.time() - t, 1)
