"""Shared Blender helpers for the Vraj Platinum asset pipeline (Blender 4.2+/5.x, bpy module or blender -b)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'blender', 'out')
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def hex2lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


_mats = {}
PROCEDURAL = True  # False for realtime (glTF) exports: procedural nodes don't survive glTF


def mat(name, color='#cccccc', rough=0.6, metal=0.0, emit=None, emit_strength=0.0, alpha=1.0, fn=None):
    """Principled material, cached by name. `fn(nt, bsdf)` may add procedural detail."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*hex2lin(color), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*hex2lin(emit), 1)
        b.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    if fn and PROCEDURAL:
        fn(nt, b)
    m['hex'] = color
    m['rough'] = rough
    m['metal'] = metal
    _mats[name] = m
    return m


def reset_mats():
    _mats.clear()


def box(name, x0, x1, y0, y1, z0, z1, m, bevel=0.0, top=None, coll=None):
    """Axis aligned box. Optional `top` material for the +Z face (section cut look)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.data.materials.append(m)
    if top is not None:
        ob.data.materials.append(top)
        for p in ob.data.polygons:
            if p.normal.z > 0.9:
                p.material_index = 1
    if bevel > 0:
        bev = ob.modifiers.new('bev', 'BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
    return ob


def cyl(name, r, z0, z1, m, x=0, y=0, seg=24, r2=None, coll=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=z1 - z0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, (z0 + z1) / 2))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.data.materials.append(m)
    for p in ob.data.polygons:
        p.use_smooth = abs(p.normal.z) < 0.5
    return ob


def sphere(name, r, x, y, z, m, sub=2, sx=1, sy=1, sz=1, coll=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co.x = v.co.x * sx + x
        v.co.y = v.co.y * sy + y
        v.co.z = v.co.z * sz + z
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.data.materials.append(m)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def apply_all(objs):
    """Apply modifiers + transforms for a list of objects."""
    for o in objs:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            try:
                bpy.ops.object.select_all(action='DESELECT')
                o.select_set(True)
                bpy.ops.object.modifier_apply(modifier=md.name)
            except Exception as e:
                print('modifier apply failed', o.name, e)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def join(objs, name):
    objs = [o for o in objs if o.type == 'MESH']
    if not objs:
        return None
    apply_all(objs)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob


def export_glb(path, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True,
                              export_apply=True, export_yup=True, export_texcoords=True,
                              export_normals=True, export_materials='EXPORT',
                              export_cameras=False, export_lights=False, export_extras=True)
    print('exported', path)


# ---- procedural material helpers -------------------------------------------------

def proc_tiles(c1, c2, grout, sx=0.6, sy=1.2, vein=True):
    def fn(nt, b):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        br = nt.nodes.new('ShaderNodeTexBrick')
        br.offset = 0.5
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Mortar Size'].default_value = 0.004
        br.inputs['Brick Width'].default_value = sy
        br.inputs['Row Height'].default_value = sx
        br.inputs['Color1'].default_value = (*hex2lin(c1), 1)
        br.inputs['Color2'].default_value = (*hex2lin(c2), 1)
        br.inputs['Mortar'].default_value = (*hex2lin(grout), 1)
        nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
        col = br.outputs['Color']
        if vein:
            nz = nt.nodes.new('ShaderNodeTexNoise')
            nz.inputs['Scale'].default_value = 2.2
            nz.inputs['Detail'].default_value = 8
            nz.inputs['Distortion'].default_value = 2.5
            nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
            ramp = nt.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position = 0.48
            ramp.color_ramp.elements[1].position = 0.52
            ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
            ramp.color_ramp.elements[1].color = (0.82, 0.82, 0.83, 1)
            nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
            mix = nt.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 0.6
            nt.links.new(col, mix.inputs[6])
            nt.links.new(ramp.outputs['Color'], mix.inputs[7])
            col = mix.outputs[2]
        nt.links.new(col, b.inputs['Base Color'])
    return fn


def proc_wood(c1, c2, scale=6.0, axis='X'):
    def fn(nt, b):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1, 12, 1) if axis == 'X' else (12, 1, 1)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        wv = nt.nodes.new('ShaderNodeTexWave')
        wv.inputs['Scale'].default_value = scale
        wv.inputs['Distortion'].default_value = 6
        wv.inputs['Detail'].default_value = 3
        nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (*hex2lin(c1), 1)
        ramp.color_ramp.elements[1].color = (*hex2lin(c2), 1)
        nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    return fn


def proc_noise(c1, c2, scale=30.0):
    def fn(nt, b):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale
        nz.inputs['Detail'].default_value = 6
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (*hex2lin(c1), 1)
        ramp.color_ramp.elements[1].color = (*hex2lin(c2), 1)
        nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    return fn
