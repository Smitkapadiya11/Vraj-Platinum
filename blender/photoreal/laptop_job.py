"""Background render job for a GPU machine.

blender -b --factory-startup -P blender/photoreal/laptop_job.py -- <work_dir> <kinds> <width> <samples> [frames]
  kinds   comma list of day,sunset,night
  frames  comma list or a-b range (default: all 48)
Writes <work_dir>/renders/<kind>/f_XXXX.jpg and <work_dir>/progress.json. Skips frames already rendered,
so it can be stopped and restarted at any time.
"""
import sys, os, json, time, traceback
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
OUT = os.path.join(BL, 'out')
sys.path.insert(0, HERE); sys.path.insert(0, BL)
a = sys.argv[sys.argv.index('--') + 1:]
WORK, KINDS, WIDTH, SPP = a[0], a[1].split(','), int(a[2]), int(a[3])
FR = a[4] if len(a) > 4 else '0-47'
if '-' in FR:
    f0, f1 = (int(x) for x in FR.split('-'))
    FRAMES = list(range(f0, f1 + 1))
else:
    FRAMES = [int(x) for x in FR.split(',')]
PROG = os.path.join(WORK, 'progress.json')
state = {'stage': 'start', 'done': [], 'errors': [], 'started': time.time()}


def save():
    state['t'] = time.time()
    json.dump(state, open(PROG, 'w'), indent=1)


try:
    scene_path = os.path.join(OUT, 'photoreal_scene.blend')
    if not os.path.exists(scene_path):
        state['stage'] = 'building modules'; save()
        exec(compile(open(os.path.join(HERE, 'mk_modules.py')).read(), os.path.join(HERE, 'mk_modules.py'), 'exec'), {'__file__': os.path.join(HERE, 'mk_modules.py'), '__name__': '__main__'})
        state['stage'] = 'assembling scene'; save()
        exec(compile(open(os.path.join(HERE, 'assemble.py')).read(), os.path.join(HERE, 'assemble.py'), 'exec'), {'__file__': os.path.join(HERE, 'assemble.py'), '__name__': '__main__'})
    bpy.ops.wm.open_mainfile(filepath=scene_path)
    import lighting
    sc = bpy.context.scene
    # GPU
    prefs = bpy.context.preferences.addons['cycles'].preferences
    used = 'CPU'
    for t in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            prefs.compute_device_type = t
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == t]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == t
                used = t
                break
        except Exception:
            continue
    sc.cycles.device = 'GPU' if used != 'CPU' else 'CPU'
    try:
        sc.cycles.denoiser = 'OPTIX' if used == 'OPTIX' else 'OPENIMAGEDENOISE'
    except Exception:
        pass
    state['device'] = used
    sc.render.resolution_x = WIDTH
    sc.render.resolution_y = int(WIDTH * 1500 / 2400)
    sc.cycles.samples = SPP
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 92
    sc.render.use_persistent_data = True
    for kind in KINDS:
        lighting.set_time(kind)
        d = os.path.join(WORK, 'renders', kind)
        os.makedirs(d, exist_ok=True)
        for f in FRAMES:
            p = os.path.join(d, f'f_{f:04d}.jpg')
            if os.path.exists(p):
                continue
            state['stage'] = f'rendering {kind} {f}'; save()
            t0 = time.time()
            sc.frame_set(f)
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            state['done'].append([kind, f, round(time.time() - t0, 1)])
            save()
    state['stage'] = 'finished'; save()
except Exception:
    state['stage'] = 'error'
    state['errors'].append(traceback.format_exc())
    save()
    raise
