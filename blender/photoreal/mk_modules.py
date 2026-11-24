"""Re-run the web asset scripts (towers.py, site.py) with full procedural materials and save the
resulting objects to .blend libraries for the photoreal render scene, instead of glTF.

python3 blender/photoreal/mk_modules.py   ->  blender/out/pr_towers.blend, pr_site.blend, pr_props.blend
"""
import sys, os, shutil
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
ROOT = os.path.dirname(BL)
sys.path.insert(0, BL)
import bcommon  # noqa: E402

OUT = os.path.join(BL, 'out')
os.makedirs(OUT, exist_ok=True)
NAMES = {'towers.glb': 'pr_towers.blend', 'site.glb': 'pr_site.blend', 'props.glb': 'pr_props.blend'}


def fake_export(path, objs):
    dst = os.path.join(OUT, NAMES[os.path.basename(path)])
    objs = [o for o in objs if o]
    for o in objs:
        o.use_fake_user = True
    bpy.data.libraries.write(dst, set(objs), fake_user=True, compress=True)
    print('saved', dst, len(objs), [o.name for o in objs][:12])


bcommon.export_glb = fake_export


def soft_reset():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.collections, bpy.data.images, bpy.data.node_groups):
        for d in list(coll):
            try:
                coll.remove(d)
            except Exception:
                pass


bcommon.reset = soft_reset   # never reload factory settings (would drop add-ons such as the MCP bridge)
# keep the web data files untouched (the scripts also write json)
keep = [os.path.join(ROOT, 'src', 'data', f) for f in ('balconies.json', 'props.json')]
backup = {k: open(k).read() for k in keep}
try:
    for script in ('towers.py', 'site.py'):
        src = open(os.path.join(BL, script)).read().replace('bcommon.PROCEDURAL = False', 'bcommon.PROCEDURAL = True')
        bcommon._mats.clear()
        exec(compile(src, os.path.join(BL, script), 'exec'), {'__file__': os.path.join(BL, script), '__name__': '__main__'})
finally:
    for k, v in backup.items():
        open(k, 'w').write(v)
