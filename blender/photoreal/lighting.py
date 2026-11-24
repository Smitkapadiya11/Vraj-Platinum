"""Time-of-day presets for the photoreal scene: day, sunset, night.
Sun positions are for Sarthana, Surat (21.23 N) in late November.
"""
import math
import bpy
from mathutils import Vector

PRESETS = {
    #          sun elev, azimuth (deg from north, clockwise), sun strength, sky strength, sun colour, exposure, night
    'day':    dict(elev=36.0, az=128.0, sun=4.2, sky=0.32, col=(1.0, 0.96, 0.9), expo=-0.9, night=0.0),
    'sunset': dict(elev=5.0, az=247.0, sun=2.4, sky=0.6, col=(1.0, 0.62, 0.34), expo=-0.4, night=0.35),
    'night':  dict(elev=-20.0, az=250.0, sun=0.0, sky=0.0, col=(0.6, 0.7, 1.0), expo=0.9, night=1.0),
}


def _sky_node(nt):
    n = nt.nodes.new('ShaderNodeTexSky')
    for t in ('MULTIPLE_SCATTERING', 'NISHITA'):
        try:
            n.sky_type = t
            break
        except Exception:
            continue
    for k, v in (('air_density', 1.0), ('aerosol_density', 2.2), ('dust_density', 2.2), ('ozone_density', 1.0), ('altitude', 30.0)):
        if hasattr(n, k):
            setattr(n, k, v)
    if hasattr(n, 'sun_disc'):
        n.sun_disc = False
    return n


def set_time(kind='day'):
    p = PRESETS[kind]
    sc = bpy.context.scene
    sc['night'] = p['night']
    for vl in sc.view_layers:
        vl['night'] = p['night']
    w = sc.world or bpy.data.worlds.new('world')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    e, a = math.radians(p['elev']), math.radians(p['az'])
    if kind != 'night':
        sky = _sky_node(nt)
        sky.sun_elevation = max(e, math.radians(0.5))
        # Blender sky: rotation 0 = sun on -Y; geographic azimuth is clockwise from +Y (north)
        sky.sun_rotation = math.pi - a if False else (a + math.pi) % (2 * math.pi)
        nt.links.new(sky.outputs[0], bg.inputs['Color'])
        bg.inputs['Strength'].default_value = p['sky']
    else:
        grad = nt.nodes.new('ShaderNodeTexGradient')
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Rotation'].default_value = (0, math.radians(-90), 0)
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
        nt.links.new(mp.outputs[0], grad.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (0.035, 0.05, 0.1, 1)
        ramp.color_ramp.elements[1].color = (0.004, 0.007, 0.02, 1)
        nt.links.new(grad.outputs['Fac'], ramp.inputs[0])
        nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
        bg.inputs['Strength'].default_value = 1.0
    # sun lamp (shadows)
    sun = bpy.data.objects.get('SUN')
    if not sun:
        ld = bpy.data.lights.new('SUN', 'SUN')
        sun = bpy.data.objects.new('SUN', ld)
        sc.collection.objects.link(sun)
    to_sun = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    if kind == 'night':   # moonlight from high up
        to_sun = Vector((0.3, -0.4, 0.86)).normalized()
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    sun.data.energy = p['sun'] if kind != 'night' else 0.06
    sun.data.color = p['col']
    sun.data.angle = math.radians(0.6 if kind != 'sunset' else 1.2)
    sc.view_settings.exposure = p['expo']
    try:
        sc.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    # night-only lights: warm street lamps (props named lamp*) via emission on their 'lamphead' style materials
    for m in bpy.data.materials:
        if m.name.startswith(('lamp', 'bulb', 'lobbyglow')) and m.use_nodes:
            b = m.node_tree.nodes.get('Principled BSDF')
            if b:
                b.inputs['Emission Strength'].default_value = 25.0 * p['night'] if m.name != 'lobbyglow' else 1.5 + 12 * p['night']
                if m.name != 'lobbyglow':
                    b.inputs['Emission Color'].default_value = (1.0, 0.78, 0.5, 1)
    return p
