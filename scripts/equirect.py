"""Stitch phone stills + video frames into a true equirectangular (2:1) panorama.

Camera rotations/focals are estimated with OpenCV's detail pipeline (SIFT + ray bundle
adjustment + horizontal wave correction) and every image is warped with a spherical
warper whose scale is W/(2*pi), so the output is a real equirectangular image
(u = longitude, v = latitude) that can be wrapped on a sphere.
"""
import cv2, numpy as np, sys, glob, json

out = sys.argv[1]
files = sys.argv[2:]
W = 6144; H = W // 2
SCALE = W / (2 * np.pi)

full = [cv2.imread(f) for f in files]
work_mp = 0.6
imgs, work_scales = [], []
for im in full:
    s = min(1.0, np.sqrt(work_mp * 1e6 / (im.shape[0] * im.shape[1])))
    work_scales.append(s)
    imgs.append(cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA))

sift = cv2.SIFT_create(4000)
feats = [cv2.detail.computeImageFeatures2(sift, im) for im in imgs]
matcher = cv2.detail_BestOf2NearestMatcher(False, 0.45)
pm = matcher.apply2(feats)
matcher.collectGarbage()
keep = cv2.detail.leaveBiggestComponent(feats, pm, 0.8)
keep = [int(k) for k in np.array(keep).ravel()]
print('kept', len(keep), 'of', len(files), [files[k].split('/')[-1] for k in keep])
feats = [feats[k] for k in keep]; imgs = [imgs[k] for k in keep]; full = [full[k] for k in keep]
work_scales = [work_scales[k] for k in keep]
pm = matcher.apply2(feats)

est = cv2.detail_HomographyBasedEstimator()
ok, cams = est.apply(feats, pm, None)
assert ok, 'estimation failed'
for c in cams: c.R = c.R.astype(np.float32)
ba = cv2.detail_BundleAdjusterRay()
ba.setConfThresh(0.8)
ba.setRefinementMask(np.ones((3, 3), np.uint8))
ok, cams = ba.apply(feats, pm, cams)
assert ok, 'bundle adjust failed'
Rs = cv2.detail.waveCorrect([np.copy(c.R) for c in cams], cv2.detail.WAVE_CORRECT_HORIZ)
for c, R in zip(cams, Rs): c.R = R

SEAM = 0.2
def Kfull(c, ws):
    K = c.K().astype(np.float32)
    K[0, 0] /= ws; K[1, 1] /= ws; K[0, 2] /= ws; K[1, 2] /= ws   # back to full-res pixels
    return K
# low-res pass: exposure gains + seams
lw = cv2.PyRotationWarper('spherical', SCALE * SEAM)
lc, li, lm = [], [], []
for im, c, ws in zip(full, cams, work_scales):
    K = Kfull(c, ws); K[:2] *= SEAM
    small = cv2.resize(im, None, fx=SEAM, fy=SEAM, interpolation=cv2.INTER_AREA)
    co, wi = lw.warp(small, K, c.R, cv2.INTER_LINEAR, cv2.BORDER_REFLECT)
    m = np.full(small.shape[:2], 255, np.uint8)
    _, wm = lw.warp(m, K, c.R, cv2.INTER_NEAREST, cv2.BORDER_CONSTANT)
    lc.append(co); li.append(wi); lm.append(wm)
comp = cv2.detail.ExposureCompensator_createDefault(cv2.detail.ExposureCompensator_GAIN)
comp.feed(corners=lc, images=li, masks=lm)
finder = cv2.detail_GraphCutSeamFinder('COST_COLOR')
seams = finder.find([x.astype(np.float32) for x in li], lc, [m.copy() for m in lm])
del li

blender = cv2.detail_MultiBandBlender(0, 6)
blender.prepare((-W // 2, 0, W, H))
warper = cv2.PyRotationWarper('spherical', SCALE)
info = []
for i, (im, c, ws) in enumerate(zip(full, cams, work_scales)):
    K = Kfull(c, ws)
    corner, wimg = warper.warp(im, K, c.R, cv2.INTER_LINEAR, cv2.BORDER_REFLECT)
    m = np.full(im.shape[:2], 255, np.uint8)
    m = cv2.erode(m, np.ones((5, 5), np.uint8))
    _, wm = warper.warp(m, K, c.R, cv2.INTER_NEAREST, cv2.BORDER_CONSTANT)
    comp.apply(i, corner, wimg, wm)
    seam = cv2.resize(cv2.dilate(seams[i], None), (wm.shape[1], wm.shape[0]), interpolation=cv2.INTER_LINEAR_EXACT)
    wm = cv2.bitwise_and(seam, wm)
    blender.feed(wimg.astype(np.int16), wm, corner)
    info.append({'f': files[keep[i]].split('/')[-1], 'focal': float(K[0, 0]), 'corner': [int(corner[0]), int(corner[1])], 'size': [wimg.shape[1], wimg.shape[0]]})
    del wimg, wm
res, rmask = blender.blend(None, None)
res = np.clip(res, 0, 255).astype(np.uint8)
cv2.imwrite(out + '.jpg', res, [cv2.IMWRITE_JPEG_QUALITY, 92])
cv2.imwrite(out + '_mask.png', rmask)
json.dump(info, open(out + '.json', 'w'), indent=1)
ys, xs = np.where(rmask > 0)
print('coverage px x', xs.min(), xs.max(), 'y', ys.min(), ys.max(), '-> deg lon', (xs.max() - xs.min()) / W * 360, 'lat top', 90 - ys.min() / H * 180, 'bottom', 90 - ys.max() / H * 180)
