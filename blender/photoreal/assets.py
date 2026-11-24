"""Upgrade the assembled scene with free CC0 Poly Haven assets (downloaded once into <work>/assets):
  - real tree models for the three tree species (instanced through the existing geometry-node scatter)
  - photographic aerial ground detail (grass / dry soil / asphalt) multiplied over the real land-use map
  - a thin atmospheric haze volume over the neighbourhood (aerial perspective)
Every step is optional: anything that fails to download keeps the procedural fallback.
"""
import os, json, urllib.request, math
import bpy
from mathutils import Vector

UA = {'User-Agent': 'VrajPlatinum-render/1.0'}


def _get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
    open(path, 'wb').write(data)
    return path


def _files(asset):
    return json.loads(urllib.request.urlopen(urllib.request.Request(f'https://api.polyhaven.com/files/{asset}', headers=UA), timeout=60).read())


def texture(work, asset, res='2k'):
    f = _files(asset)
    d = f.get('Diffuse') or f.get('diffuse') or f.get('Color')
    url = d[res]['jpg']['url']
    return _get(url, os.path.join(work, 'assets', 'tex', f'{asset}_{res}.jpg'))


def model(work, asset, res='1k'):
    f = _files(asset)['gltf'][res]['gltf']
    base = os.path.join(work, 'assets', 'models', asset)
    main = _get(f['url'], os.path.join(base, os.path.basename(f['url'])))
    for rel, inc in f.get('include', {}).items():
        _get(inc['url'], os.path.join(base, rel))
    return main


def import_tree(path, name, height):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    if not meshes:
        return None
    for o in new:
        o.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    zs = [v.co.z for v in ob.data.vertices]
    xs = [v.co.x for v in ob.data.vertices]; ys = [v.co.y for v in ob.data.vertices]
    h = max(zs) - min(zs)
    s = height / max(h, 0.01)
    cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
    for v in ob.data.vertices:
        v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - z0) * s))
    for o in new:
        if o != ob and o.name in bpy.data.objects:
            bpy.data.objects.remove(o)
    ob.name = name + '_ph'
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    bpy.data.collections['TREE_PROTOS'].objects.link(ob)
    ob.hide_render = True
    return ob


def upgrade_trees(work, log):
    spec = {'r': ('island_tree_02', 7.5), 'b': ('shrub_02', 2.2), 't': ('jacaranda_tree', 9.0)}
    for sp, (asset, hgt) in spec.items():
        try:
            ob = import_tree(model(work, asset), f'TREE_{sp}', hgt)
            proto = bpy.data.objects.get(f'TREE_{sp}')
            if ob and proto:
                proto.data = ob.data
                log.append(f'tree {sp} <- {asset}')
        except Exception as e:
            log.append(f'tree {sp} failed: {e}')


def upgrade_ground(work, log):
    try:
        grass = bpy.data.images.load(texture(work, 'aerial_grass_rock'))
        soil = bpy.data.images.load(texture(work, 'dirt_aerial_02'))
        asph = bpy.data.images.load(texture(work, 'aerial_asphalt_01'))
    except Exception as e:
        log.append(f'ground textures failed: {e}')
        return
    import numpy as np

    def mean(img):
        px = np.empty(len(img.pixels), np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(-1, 4)[:, :3]
        return float(px.mean())
    means = {grass.name: mean(grass), soil.name: mean(soil), asph.name: mean(asph)}
    for name, tile in (('ground_near_m', 9.0), ('ground_far_m', 14.0)):
        m = bpy.data.materials.get(name)
        if not m:
            continue
        nt = m.node_tree
        b = nt.nodes.get('Principled BSDF')
        mapimg = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1 / tile, 1 / tile, 1)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])

        def tex(img):
            t = nt.nodes.new('ShaderNodeTexImage')
            t.image = img
            nt.links.new(mp.outputs[0], t.inputs['Vector'])
            # normalise to mean 1 so the detail keeps the real map colour
            d = nt.nodes.new('ShaderNodeVectorMath'); d.operation = 'SCALE'
            nt.links.new(t.outputs['Color'], d.inputs[0])
            d.inputs['Scale'].default_value = 1.0 / max(means[img.name], 0.02)
            return d.outputs[0]
        g, s_, a = tex(grass), tex(soil), tex(asph)
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(mapimg.outputs['Color'], sep.inputs[0])
        # greenness -> grass ; low saturation & dark -> asphalt ; else soil
        gr = nt.nodes.new('ShaderNodeMath'); gr.operation = 'SUBTRACT'
        nt.links.new(sep.outputs[1], gr.inputs[0]); nt.links.new(sep.outputs[0], gr.inputs[1])
        gk = nt.nodes.new('ShaderNodeMapRange'); gk.inputs[1].default_value = -0.005; gk.inputs[2].default_value = 0.03
        nt.links.new(gr.outputs[0], gk.inputs[0])
        lum = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(mapimg.outputs['Color'], lum.inputs[0])
        ak = nt.nodes.new('ShaderNodeMapRange'); ak.inputs[1].default_value = 0.075; ak.inputs[2].default_value = 0.045
        nt.links.new(lum.outputs[0], ak.inputs[0])
        m1 = nt.nodes.new('ShaderNodeMix'); m1.data_type = 'RGBA'
        nt.links.new(gk.outputs[0], m1.inputs['Factor']); nt.links.new(s_, m1.inputs[6]); nt.links.new(g, m1.inputs[7])
        m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'
        nt.links.new(ak.outputs[0], m2.inputs['Factor']); nt.links.new(m1.outputs[2], m2.inputs[6]); nt.links.new(a, m2.inputs[7])
        # final = map colour x detail
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        nt.links.new(mapimg.outputs['Color'], mul.inputs[6]); nt.links.new(m2.outputs[2], mul.inputs[7])
        nt.links.new(mul.outputs[2], b.inputs['Base Color'])
        log.append(f'ground detail on {name}')


def add_haze(log, density=0.00032):
    if bpy.data.objects.get('HAZE'):
        return
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 200))
    o = bpy.context.active_object
    o.name = 'HAZE'
    o.scale = (4000, 4000, 400)
    m = bpy.data.materials.new('haze')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (0.78, 0.82, 0.9, 1)
    v.inputs['Density'].default_value = density
    v.inputs['Anisotropy'].default_value = 0.45
    nt.links.new(v.outputs[0], out.inputs['Volume'])
    o.data.materials.append(m)
    o.visible_shadow = True
    log.append('haze volume')


def upgrade(work):
    log = []
    upgrade_trees(work, log)
    upgrade_ground(work, log)
    add_haze(log)
    return log
