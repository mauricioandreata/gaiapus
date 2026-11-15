"""Shaded orthographic views of the case (no boards) for the drawings, cached as .npz (image + extent in case mm)."""
import os, sys, numpy as np
from preview import read, render
VIEWS = {  # name: (az, el, u-range(case), v-range(case), u-offset, v-offset)
    "front": (0, 0, (-62, 62), (-36, 126), -145.0, 42.0),
    "right": (90, 0, (-40, 70), (-36, 126), 125.0, 42.0),     # u = -y (front on the left)
    "top": (0, 90, (-62, 62), (-40, 70), -145.0, 125.0),       # u = x, v = -y (front down)
    "bottom": (0, -90, (-62, 62), (-70, 40), -145.0, -125.0),  # u = x, v = y (front up)
}
def build(glb, out, ppm=9.0):
    T = read(glb)
    case = [it for it in T if it[0][:, :, 2].min() > 0.05 and it[0][:, :, 1].min() > -0.11]
    for name, (az, el, ur, vr, uo, vo) in VIEWS.items():
        lo = np.array([(ur[0] - uo) / 1000, (vr[0] - vo) / 1000]); hi = np.array([(ur[1] - uo) / 1000, (vr[1] - vo) / 1000])
        res = int(max(ur[1] - ur[0], vr[1] - vr[0]) * ppm)
        img, zb, (l, h, s) = render(case, None, az=az, el=el, res=res, crop=(lo, hi), ret=True)
        H, W = img.shape[:2]
        ext = [l[0] * 1000 + uo, (l[0] + W / s) * 1000 + uo, l[1] * 1000 + vo, (l[1] + H / s) * 1000 + vo]
        np.savez_compressed(os.path.join(out, "view_%s.npz" % name), img=img.astype(np.float16), ext=np.array(ext))
        print(name, img.shape, np.round(ext, 1), flush=True)
if __name__ == "__main__": build(sys.argv[1], sys.argv[2])
