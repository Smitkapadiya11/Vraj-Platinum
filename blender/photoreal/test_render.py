"""Quick preview: python3 test_render.py <frame> <day|sunset|night> <width> <samples> <out.png>"""
import sys, os
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
frame, kind, w, spp, out = int(a[0]), a[1], int(a[2]), int(a[3]), a[4]
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(HERE), 'out', 'photoreal_scene.blend'))
import lighting
lighting.set_time(kind)
sc = bpy.context.scene
sc.frame_set(frame)
sc.render.resolution_x = w
sc.render.resolution_y = int(w * 1500 / 2400)
sc.cycles.samples = spp
sc.cycles.device = 'CPU'
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
