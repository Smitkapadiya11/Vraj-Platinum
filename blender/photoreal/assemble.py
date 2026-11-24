"""Assemble the photoreal render scene for Vraj Platinum (Cycles).

Run after mk_modules.py:
    python3 blender/photoreal/assemble.py            -> blender/out/photoreal_scene.blend

Contents
  TOWERS   6 towers (floor modules x14, ground, roof, planters) with procedural PBR materials
  SITE     campus (gates, signage, garden, road) + props (palms, trees, cars, lamps, benches, shrubs)
  CONTEXT  720 real OpenStreetMap buildings with a procedural facade (window grid, plaster tints,
           rooftop tanks / solar), real land-use ground map, ~4000 trees by species
  FLATS    one box per flat (336), hidden in beauty renders, used for the flat-ID pass
  CAM      48-frame orbit (+ the rig empty), lens 55 mm, 2400x1500
Lighting presets: set_time('day' | 'sunset' | 'night') in lighting.py
"""
import sys, os, json, math, random
import bpy, bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
ROOT = os.path.dirname(BL)
sys.path.insert(0, BL); sys.path.insert(0, HERE)
import bcommon  # noqa
from bcommon import hex2lin  # noqa

OUT = os.path.join(BL, 'out')
D = lambda f: json.load(open(os.path.join(ROOT, 'src', 'data', f)))
S, CTX, TREES, PROPS = D('site.json'), D('context.json'), D('trees.json'), D('props.json')
GH, FH, NF = S['groundH'], S['floorH'], S['floors']
random.seed(7)


def soft_reset():
    """Clear the scene without touching preferences/add-ons (keeps a live MCP connection alive)."""
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.node_groups,
                 bpy.data.cameras, bpy.data.lights, bpy.data.worlds, bpy.data.curves, bpy.data.fonts):
        for d in list(coll):
            try:
                coll.remove(d)
            except Exception:
                pass


soft_reset()
bcommon._mats.clear()
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c


def append(blend, names=None):
    path = os.path.join(OUT, blend)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if names is None or n in names]
    return {o.name: o for o in dst.objects if o}


def inst(src, c, loc=(0, 0, 0), rz=0.0, s=1.0):
    o = src.copy()
    o.location = Vector(loc) + Vector(src.location)
    o.rotation_euler = (0, 0, rz)
    o.scale = (s, s, s)
    c.objects.link(o)
    return o


# ------------------------------------------------------------------ towers
C_T = coll('TOWERS')
mods = append('pr_towers.blend')
for b in S['blocks']:
    bid = b['id']
    fl, gr, rf, pl = (mods.get(f'{bid}_{k}') for k in ('floor', 'ground', 'roof', 'planter'))
    for f in range(NF):
        inst(fl, C_T, (0, 0, GH + f * FH))
    if gr:
        C_T.objects.link(gr)
    if rf:
        inst(rf, C_T, (0, 0, GH + NF * FH))
    if pl:
        for f in S['planterFloors']:
            inst(pl, C_T, (0, 0, GH + (f - 1) * FH))

# ------------------------------------------------------------------ site + props
C_S = coll('SITE')
for o in append('pr_site.blend').values():
    C_S.objects.link(o)
C_PP = coll('PROPS_SRC')
C_P = coll('PROPS')
props = append('pr_props.blend')
for o in props.values():
    C_PP.objects.link(o)
for kind, lst in PROPS.items():
    src = props.get(kind)
    if not src:
        continue
    for p in lst:
        inst(src, C_P, (p['x'], p['y'], 0), p.get('r', 0), p.get('s', 1))
C_PP.hide_render = True
for o in C_PP.objects:
    o.hide_set(True)

# ------------------------------------------------------------------ context buildings (OSM)
C_C = coll('CONTEXT')


def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k == 'inputs':
            for kk, vv in v.items():
                n.inputs[kk].default_value = vv
        else:
            setattr(n, k, v)
    return n


def facade_material():
    """Procedural apartment facade: storeys every 3 m, window grid with reflective glass,
    plaster tint per building (cream / beige / pale grey / pale pink), stained bands, lit windows at night."""
    m = bpy.data.materials.new('ctx_wall')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = node(nt, 'ShaderNodeOutputMaterial')
    uv = node(nt, 'ShaderNodeUVMap', uv_map='facade')
    sep = node(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs[0], sep.inputs[0])
    seed = node(nt, 'ShaderNodeAttribute', attribute_name='seed')
    lv = node(nt, 'ShaderNodeAttribute', attribute_name='levels')
    # plaster tint from seed
    ramp = node(nt, 'ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    cols = ['#E9E1D2', '#DCCFB8', '#D6D3CD', '#E7D6CC', '#EFEDE6', '#CDBFA8']
    cr.elements[0].color = (*hex2lin(cols[0]), 1)
    cr.elements[1].position = 0.99
    cr.elements[1].color = (*hex2lin(cols[-1]), 1)
    for i, c in enumerate(cols[1:-1]):
        e = cr.elements.new((i + 1) / (len(cols) - 1))
        e.color = (*hex2lin(c), 1)
    nt.links.new(seed.outputs['Fac'], ramp.inputs[0])
    # window mask: storey 3 m, window band 0.9..2.3 m, bays 3.3 m with 2.0 m windows
    def frac(inp, div, name):
        mth = node(nt, 'ShaderNodeMath', operation='DIVIDE', inputs={1: div})
        nt.links.new(inp, mth.inputs[0])
        fr = node(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(mth.outputs[0], fr.inputs[0])
        return fr.outputs[0]

    def band(val, a, b):
        g1 = node(nt, 'ShaderNodeMath', operation='GREATER_THAN', inputs={1: a})
        g2 = node(nt, 'ShaderNodeMath', operation='LESS_THAN', inputs={1: b})
        nt.links.new(val, g1.inputs[0]); nt.links.new(val, g2.inputs[0])
        mm = node(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(g1.outputs[0], mm.inputs[0]); nt.links.new(g2.outputs[0], mm.inputs[1])
        return mm.outputs[0]
    fy = frac(sep.outputs['Y'], 3.0, 'fy')
    fx = frac(sep.outputs['X'], 3.3, 'fx')
    wy = band(fy, 0.30, 0.78)
    wx = band(fx, 0.18, 0.82)
    win = node(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(wy, win.inputs[0]); nt.links.new(wx, win.inputs[1])
    # no windows on the ground storey (shops / parking) -> keep simple: mask y > 3
    gy = node(nt, 'ShaderNodeMath', operation='GREATER_THAN', inputs={1: 3.0})
    nt.links.new(sep.outputs['Y'], gy.inputs[0])
    win2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(win.outputs[0], win2.inputs[0]); nt.links.new(gy.outputs[0], win2.inputs[1])
    # balcony slab shadow line under each storey
    slab = band(fy, 0.0, 0.07)
    # weathering noise
    noise = node(nt, 'ShaderNodeTexNoise', inputs={'Scale': 0.35, 'Detail': 6.0})
    nt.links.new(uv.outputs[0], noise.inputs['Vector'])
    dirt = node(nt, 'ShaderNodeMapRange', inputs={1: 0.35, 2: 0.75, 3: 0.82, 4: 1.0})
    nt.links.new(noise.outputs['Fac'], dirt.inputs[0])
    plaster = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY', inputs={'Factor': 1.0})
    nt.links.new(ramp.outputs['Color'], plaster.inputs[6])
    nt.links.new(dirt.outputs[0], plaster.inputs[7])
    slabmix = node(nt, 'ShaderNodeMix', data_type='RGBA', inputs={'Factor': 0.0})
    nt.links.new(slab, slabmix.inputs['Factor'])
    nt.links.new(plaster.outputs[2], slabmix.inputs[6])
    slabmix.inputs[7].default_value = (0.32, 0.31, 0.30, 1)
    wall = node(nt, 'ShaderNodeBsdfPrincipled', inputs={'Roughness': 0.88})
    nt.links.new(slabmix.outputs[2], wall.inputs['Base Color'])
    glass = node(nt, 'ShaderNodeBsdfPrincipled', inputs={'Base Color': (0.025, 0.03, 0.035, 1), 'Roughness': 0.06, 'Metallic': 0.0, 'Coat Weight': 0.0})
    glass.inputs['Specular IOR Level'].default_value = 0.8
    # night: some windows lit (warm), driven by the scene property 'night'
    lit_noise = node(nt, 'ShaderNodeTexWhiteNoise', noise_dimensions='3D')
    cell = node(nt, 'ShaderNodeVectorMath', operation='SNAP', inputs={1: (3.3, 3.0, 1.0)})
    nt.links.new(uv.outputs[0], cell.inputs[0])
    addseed = node(nt, 'ShaderNodeVectorMath', operation='ADD')
    nt.links.new(cell.outputs[0], addseed.inputs[0])
    comb = node(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(seed.outputs['Fac'], comb.inputs['Z'])
    nt.links.new(comb.outputs[0], addseed.inputs[1])
    nt.links.new(addseed.outputs[0], lit_noise.inputs['Vector'])
    litk = node(nt, 'ShaderNodeMath', operation='LESS_THAN', inputs={1: 0.38})
    nt.links.new(lit_noise.outputs['Value'], litk.inputs[0])
    nightv = node(nt, 'ShaderNodeAttribute', attribute_type='VIEW_LAYER', attribute_name='night')
    em = node(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(litk.outputs[0], em.inputs[0]); nt.links.new(nightv.outputs['Fac'], em.inputs[1])
    em2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY', inputs={1: 6.0})
    nt.links.new(em.outputs[0], em2.inputs[0])
    nt.links.new(em2.outputs[0], glass.inputs['Emission Strength'])
    glass.inputs['Emission Color'].default_value = (1.0, 0.62, 0.32, 1)
    mix = node(nt, 'ShaderNodeMixShader')
    nt.links.new(win2.outputs[0], mix.inputs['Fac'])
    nt.links.new(wall.outputs[0], mix.inputs[1])
    nt.links.new(glass.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def simple_mat(name, color, rough=0.85, metal=0.0, noise=None):
    m = bcommon.mat(name, color, rough, metal)
    if noise:
        nt = m.node_tree
        b = nt.nodes.get('Principled BSDF')
        tex = node(nt, 'ShaderNodeTexNoise', inputs={'Scale': noise, 'Detail': 8.0})
        mr = node(nt, 'ShaderNodeMapRange', inputs={1: 0.3, 2: 0.7, 3: 0.85, 4: 1.08})
        nt.links.new(tex.outputs['Fac'], mr.inputs[0])
        mx = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY', inputs={'Factor': 1.0})
        mx.inputs[6].default_value = (*hex2lin(color), 1)
        nt.links.new(mr.outputs[0], mx.inputs[7])
        nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    return m


M_WALL = facade_material()
M_ROOF = simple_mat('ctx_roof', '#B9B3A8', 0.92, noise=0.6)
M_SHED = simple_mat('ctx_shed', '#DADDDF', 0.45, 0.4, noise=0.2)
M_TANK = simple_mat('ctx_tank', '#151515', 0.6)
M_SOLAR = bcommon.mat('ctx_solar', '#16243A', 0.12, 0.5)
M_FRAME = bcommon.mat('ctx_frame', '#9BA0A6', 0.35, 0.9)

bm = bmesh.new()
uvl = bm.loops.layers.uv.new('facade')
seed_l = bm.faces.layers.float.new('seed')
lv_l = bm.faces.layers.float.new('levels')
extras = []   # (kind, x, y, z, sx, sy, sz)
for rec in CTX:
    ring, h, lv, kind = rec
    pts = [(ring[i], -ring[i + 1]) for i in range(0, len(ring), 2)]
    if len(pts) < 3:
        continue
    # ccw
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if area < 0:
        pts = pts[::-1]
    sd = random.random()
    top = h + (0.0 if kind else 1.0)
    vb = [bm.verts.new((x, y, 0)) for x, y in pts]
    vt = [bm.verts.new((x, y, top)) for x, y in pts]
    u = random.random() * 20
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        f = bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
        L = (Vector(pts[j]) - Vector(pts[i])).length
        for loop, uvv in zip(f.loops, ((u, 0), (u + L, 0), (u + L, top), (u, top))):
            loop[uvl].uv = uvv
        f[seed_l] = sd; f[lv_l] = lv
        f.material_index = 2 if kind == 1 else 0
        u += L
    try:
        f = bm.faces.new(vt)
        f.material_index = 2 if kind == 1 else 1
        f[seed_l] = sd
    except ValueError:
        pass
    # roof clutter: black water tanks on low-rise, solar rows on towers
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    if kind == 0 and lv <= 5 and random.random() < 0.85:
        for k in range(random.choice((1, 1, 2))):
            extras.append(('tank', cx + random.uniform(-1.5, 1.5), cy + random.uniform(-1.5, 1.5), top))
    elif kind == 0 and lv >= 10:
        extras.append(('solar', cx, cy, top))
me = bpy.data.meshes.new('context')
bm.to_mesh(me)
bm.free()
me.materials.append(M_WALL); me.materials.append(M_ROOF); me.materials.append(M_SHED)
ctx_obj = bpy.data.objects.new('context', me)
C_C.objects.link(ctx_obj)
# roof clutter
tk = bpy.data.meshes.new('tank')
bmt = bmesh.new()
bmesh.ops.create_cone(bmt, cap_ends=True, segments=16, radius1=0.62, radius2=0.62, depth=1.25)
bmesh.ops.translate(bmt, verts=bmt.verts, vec=(0, 0, 0.62 + 0.3))
bmt.to_mesh(tk); bmt.free()
tk.materials.append(M_TANK)
sp = bpy.data.meshes.new('solar')
bms = bmesh.new()
for r in range(4):
    bmesh.ops.create_cube(bms, size=1.0, matrix=__import__('mathutils').Matrix.LocRotScale(Vector((0, (r - 1.5) * 2.4, 1.2)), __import__('mathutils').Euler((math.radians(18), 0, 0)), Vector((9.0, 1.9, 0.06))))
bms.to_mesh(sp); bms.free()
sp.materials.append(M_SOLAR)
C_X = coll('CONTEXT_ROOF', C_C)
for kind, x, y, z in extras:
    o = bpy.data.objects.new(kind, tk if kind == 'tank' else sp)
    o.location = (x, y, z)
    o.rotation_euler = (0, 0, random.uniform(0, math.pi) if kind == 'tank' else 0)
    C_X.objects.link(o)

# night: random lit windows on the project's own glass (warm interiors), driven by the scene property 'night'
gm = bpy.data.materials.get('glass')
if gm and gm.use_nodes:
    nt_ = gm.node_tree
    pb = nt_.nodes.get('Principled BSDF')
    if pb:
        geo = node(nt_, 'ShaderNodeNewGeometry')
        snap = node(nt_, 'ShaderNodeVectorMath', operation='SNAP', inputs={1: (3.4, 3.4, 3.0)})
        nt_.links.new(geo.outputs['Position'], snap.inputs[0])
        wn = node(nt_, 'ShaderNodeTexWhiteNoise', noise_dimensions='3D')
        nt_.links.new(snap.outputs[0], wn.inputs['Vector'])
        lt = node(nt_, 'ShaderNodeMath', operation='LESS_THAN', inputs={1: 0.55})
        nt_.links.new(wn.outputs['Value'], lt.inputs[0])
        nv = node(nt_, 'ShaderNodeAttribute', attribute_type='VIEW_LAYER', attribute_name='night')
        m1 = node(nt_, 'ShaderNodeMath', operation='MULTIPLY')
        nt_.links.new(lt.outputs[0], m1.inputs[0]); nt_.links.new(nv.outputs['Fac'], m1.inputs[1])
        m2 = node(nt_, 'ShaderNodeMath', operation='MULTIPLY', inputs={1: 9.0})
        nt_.links.new(m1.outputs[0], m2.inputs[0])
        nt_.links.new(m2.outputs[0], pb.inputs['Emission Strength'])
        pb.inputs['Emission Color'].default_value = (1.0, 0.7, 0.42, 1)

# ------------------------------------------------------------------ ground (real land-use map) + detail
C_G = coll('GROUND')


def ground_plane(name, size, img_path, z):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    o = bpy.context.active_object
    o.name = name
    for c in o.users_collection:
        c.objects.unlink(o)
    C_G.objects.link(o)
    m = bpy.data.materials.new(name + '_m')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tex = node(nt, 'ShaderNodeTexImage', interpolation='Cubic')
    tex.image = bpy.data.images.load(img_path)
    tex.extension = 'EXTEND'
    # fine detail so the map reads as real ground up close: two noise octaves modulate value
    n1 = node(nt, 'ShaderNodeTexNoise', inputs={'Scale': 900.0, 'Detail': 10.0, 'Roughness': 0.6})
    n2 = node(nt, 'ShaderNodeTexNoise', inputs={'Scale': 120.0, 'Detail': 4.0})
    mr1 = node(nt, 'ShaderNodeMapRange', inputs={1: 0.25, 2: 0.75, 3: 0.78, 4: 1.15})
    mr2 = node(nt, 'ShaderNodeMapRange', inputs={1: 0.3, 2: 0.7, 3: 0.9, 4: 1.08})
    nt.links.new(n1.outputs['Fac'], mr1.inputs[0]); nt.links.new(n2.outputs['Fac'], mr2.inputs[0])
    mul = node(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(mr1.outputs[0], mul.inputs[0]); nt.links.new(mr2.outputs[0], mul.inputs[1])
    mx = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY', inputs={'Factor': 1.0})
    nt.links.new(tex.outputs['Color'], mx.inputs[6])
    nt.links.new(mul.outputs[0], mx.inputs[7])
    nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    # water (blue in the map) -> glossy
    sepc = node(nt, 'ShaderNodeSeparateColor')
    nt.links.new(tex.outputs['Color'], sepc.inputs[0])
    d = node(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(sepc.outputs[2], d.inputs[0]); nt.links.new(sepc.outputs[0], d.inputs[1])
    wmr = node(nt, 'ShaderNodeMapRange', inputs={1: 0.04, 2: 0.10, 3: 0.92, 4: 0.08})
    nt.links.new(d.outputs[0], wmr.inputs[0])
    nt.links.new(wmr.outputs[0], b.inputs['Roughness'])
    bump = node(nt, 'ShaderNodeBump', inputs={'Strength': 0.25, 'Distance': 0.05})
    nt.links.new(n1.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs[0], b.inputs['Normal'])
    o.data.materials.append(m)
    return o


ground_plane('ground_far', 4096, os.path.join(BL, 'assets', 'ground_far_4k.jpg'), -0.25)
ground_plane('ground_near', 1200, os.path.join(BL, 'assets', 'ground_near_6k.jpg'), -0.03)

# ------------------------------------------------------------------ trees (species prototypes + GN scatter)
C_TP = coll('TREE_PROTOS')
C_TR = coll('TREES')


def proto(name, parts):
    bmx = bmesh.new()
    for kind, r, loc, sc, col in parts:
        tmp = bmesh.new()
        if kind == 'trunk':
            bmesh.ops.create_cone(tmp, cap_ends=True, segments=7, radius1=r[0], radius2=r[1], depth=sc)
            bmesh.ops.translate(tmp, verts=tmp.verts, vec=Vector(loc) + Vector((0, 0, sc / 2)))
        else:
            bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=r)
            for v in tmp.verts:
                n = v.co.normalized()
                v.co = Vector((v.co.x * sc[0], v.co.y * sc[1], v.co.z * sc[2])) + n * random.uniform(-0.18, 0.18) * r
            bmesh.ops.translate(tmp, verts=tmp.verts, vec=loc)
        for f in tmp.faces:
            f.material_index = col
        me_ = bpy.data.meshes.new('tmp'); tmp.to_mesh(me_); tmp.free()
        bmx.from_mesh(me_)
        bpy.data.meshes.remove(me_)
    me_ = bpy.data.meshes.new(name)
    bmx.to_mesh(me_); bmx.free()
    me_.materials.append(simple_mat('bark', '#4E4034', 0.9, noise=3))
    me_.materials.append(simple_mat('foliage', '#4C6B33', 0.75, noise=2.5))
    me_.materials.append(simple_mat('foliage2', '#5F7F3C', 0.75, noise=2.5))
    o = bpy.data.objects.new(name, me_)
    C_TP.objects.link(o)
    return o


TP = {
    'r': proto('TREE_r', [('trunk', (0.22, 0.14), (0, 0, 0), 3.0, 0), ('crown', 2.6, (0, 0, 4.6), (1, 1, 0.78), 1),
                          ('crown', 1.8, (1.3, -0.6, 5.4), (1, 1, 0.85), 2), ('crown', 1.6, (-1.2, 0.8, 5.0), (1, 1, 0.8), 1)]),
    'b': proto('TREE_b', [('crown', 1.6, (0, 0, 1.1), (1, 1, 0.7), 1), ('crown', 1.3, (1.3, 0.5, 0.95), (1, 1, 0.7), 2),
                          ('crown', 1.2, (-0.9, -0.9, 0.9), (1, 1, 0.75), 1)]),
    't': proto('TREE_t', [('trunk', (0.16, 0.1), (0, 0, 0), 3.6, 0), ('crown', 1.45, (0, 0, 5.9), (1, 1, 2.1), 2)]),
}
C_TP.hide_render = True
for o in C_TP.objects:
    o.hide_set(True)

for sp_, arr in TREES.items():
    pts = [(arr[i], -arr[i + 1], arr[i + 2]) for i in range(0, len(arr), 3)]
    tme = bpy.data.meshes.new(f'trees_{sp_}')
    tme.vertices.add(len(pts))
    tme.vertices.foreach_set('co', [c for x, y, s in pts for c in (x, y, 0.0)])
    a = tme.attributes.new('tscale', 'FLOAT', 'POINT')
    a.data.foreach_set('value', [s for _, _, s in pts])
    tob = bpy.data.objects.new(f'trees_{sp_}', tme)
    C_TR.objects.link(tob)
    ng = bpy.data.node_groups.new(f'scatter_{sp_}', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput')
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
    oi = ng.nodes.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = TP[sp_]
    oi.transform_space = 'RELATIVE'
    attr = ng.nodes.new('GeometryNodeInputNamedAttribute'); attr.data_type = 'FLOAT'; attr.inputs['Name'].default_value = 'tscale'
    rnd = ng.nodes.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT'
    rnd.inputs['Max'].default_value = 6.283
    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(rnd.outputs['Value'], comb.inputs['Z'])
    ng.links.new(gi.outputs[0], iop.inputs['Points'])
    ng.links.new(oi.outputs['Geometry'], iop.inputs['Instance'])
    ng.links.new(attr.outputs['Attribute'], iop.inputs['Scale'])
    ng.links.new(comb.outputs[0], iop.inputs['Rotation'])
    ng.links.new(iop.outputs[0], go.inputs[0])
    md = tob.modifiers.new('scatter', 'NODES')
    md.node_group = ng

# ------------------------------------------------------------------ flat boxes for the ID pass
C_F = coll('FLATS')
M_ID = bpy.data.materials.new('flat_id')
M_ID.use_nodes = True
nt = M_ID.node_tree
nt.nodes.clear()
oinfo = node(nt, 'ShaderNodeObjectInfo')
emi = node(nt, 'ShaderNodeEmission', inputs={'Strength': 1.0})
nt.links.new(oinfo.outputs['Color'], emi.inputs['Color'])
o_ = node(nt, 'ShaderNodeOutputMaterial')
nt.links.new(emi.outputs[0], o_.inputs['Surface'])
flat_ids = []
for b in S['blocks']:
    bx0, bx1, by0, by1 = b['rect']
    for fl in b['flats']:
        x0, x1, y0, y1 = fl['rect']
        e = 1.35  # balconies project ~1.3 m beyond the block outline
        x0 -= e if abs(x0 - bx0) < 0.3 else 0.02
        x1 += e if abs(x1 - bx1) < 0.3 else -0.02
        y0 -= e if abs(y0 - by0) < 0.3 else 0.02
        y1 += e if abs(y1 - by1) < 0.3 else -0.02
        for f in range(1, NF + 1):
            uid = f"{fl['tower']}-{f}{fl['no'][1:]}"
            z0 = GH + (f - 1) * FH
            ob = bcommon.box(f'flat_{uid}', x0, x1, y0, y1, z0 + 0.02, z0 + FH - 0.02, M_ID)
            for c in ob.users_collection:
                c.objects.unlink(ob)
            C_F.objects.link(ob)
            flat_ids.append(uid)
            ob['uid'] = uid
            ob['idx'] = len(flat_ids)
C_F.hide_render = True
json.dump(flat_ids, open(os.path.join(OUT, 'flat_ids.json'), 'w'))

# ------------------------------------------------------------------ camera orbit
NFR = 48
tgt = bpy.data.objects.new('cam_target', None)
tgt.location = (0, 0, 22)
scene.collection.objects.link(tgt)
camd = bpy.data.cameras.new('orbit')
camd.lens = 55
camd.sensor_width = 36
camd.clip_start = 1.0
camd.clip_end = 6000
cam = bpy.data.objects.new('orbit_cam', camd)
scene.collection.objects.link(cam)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
R, Hc, A0 = 300.0, 170.0, math.radians(-30)   # start south-east, over the 100 ft road
for i in range(NFR):
    a = A0 + 2 * math.pi * i / NFR
    cam.location = (R * math.cos(a), R * math.sin(a), Hc)
    cam.keyframe_insert('location', frame=i)
if cam.animation_data and cam.animation_data.action:
    try:
        for fc in cam.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = 'LINEAR'
    except Exception:
        pass
scene.camera = cam
scene.frame_start, scene.frame_end = 0, NFR - 1
r = scene.render
r.engine = 'CYCLES'
r.resolution_x, r.resolution_y, r.resolution_percentage = 2400, 1500, 100
r.image_settings.file_format = 'JPEG'
r.image_settings.quality = 92
scene.cycles.samples = 160
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

import lighting  # noqa
lighting.set_time('day')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'photoreal_scene.blend'), compress=True)
print('saved scene', len(flat_ids), 'flats', len(CTX), 'buildings')
