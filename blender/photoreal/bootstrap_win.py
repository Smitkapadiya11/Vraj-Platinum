"""One-line bootstrap for a Windows/Mac/Linux GPU machine, typed into Blender's Python console:

    import urllib.request as u;exec(u.urlopen('https://raw.githubusercontent.com/Smitkapadiya11/Vraj-Platinum/main/blender/photoreal/bootstrap_win.py').read())

Downloads the repo into ~/VrajPlatinum_render and defines:
    vp_start(kinds='day', width=1200, spp=64, frames='0')   -> launches a background Blender render job (GPU)
    vp_status()                                             -> prints progress.json
    vp_stop()                                               -> stops the job
"""
import os, io, json, zipfile, subprocess, urllib.request, shutil, time
import bpy

VP_WORK = os.path.join(os.path.expanduser('~'), 'VrajPlatinum_render')
os.makedirs(VP_WORK, exist_ok=True)
_zip = urllib.request.urlopen('https://codeload.github.com/Smitkapadiya11/Vraj-Platinum/zip/refs/heads/main').read()
_repo = os.path.join(VP_WORK, 'Vraj-Platinum-main')
if os.path.isdir(_repo):
    # keep built modules/scene between runs unless the scripts changed
    keep = os.path.join(_repo, 'blender', 'out')
    tmp_keep = os.path.join(VP_WORK, '_out_keep')
    if os.path.isdir(keep):
        shutil.rmtree(tmp_keep, ignore_errors=True)
        shutil.move(keep, tmp_keep)
    shutil.rmtree(_repo, ignore_errors=True)
zipfile.ZipFile(io.BytesIO(_zip)).extractall(VP_WORK)
VP_REPO = _repo
print('Vraj Platinum repo ready at', VP_REPO)
_proc = {'p': None}


def vp_start(kinds='day', width=1200, spp=64, frames='0', rebuild=False):
    out = os.path.join(VP_REPO, 'blender', 'out')
    if rebuild:
        shutil.rmtree(out, ignore_errors=True)
    job = os.path.join(VP_REPO, 'blender', 'photoreal', 'laptop_job.py')
    log = open(os.path.join(VP_WORK, 'job.log'), 'w')
    flags = 0x08000000 if os.name == 'nt' else 0   # CREATE_NO_WINDOW
    _proc['p'] = subprocess.Popen([bpy.app.binary_path, '-b', '--factory-startup', '-P', job, '--', VP_WORK, kinds, str(width), str(spp), str(frames)],
                                  stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
    print('render job started, pid', _proc['p'].pid)


def vp_status():
    p = os.path.join(VP_WORK, 'progress.json')
    s = json.load(open(p)) if os.path.exists(p) else {}
    alive = _proc['p'] is not None and _proc['p'].poll() is None
    print('running' if alive else 'not running', s.get('stage'), 'device', s.get('device'), 'done', len(s.get('done', [])), (s.get('done') or [''])[-1], (s.get('errors') or [''])[-1][-600:])
    return s


def vp_stop():
    if _proc['p'] and _proc['p'].poll() is None:
        _proc['p'].terminate()
        print('stopped')
