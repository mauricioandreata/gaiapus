"""Printable STL of base, lid, button and tip. Usage: python3 build_parts.py OUT_DIR [--coarse]
Lid is exported top-face-down; base/button/tip flat on the bed.  (needs numpy, scikit-image)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
import time, numpy as np
import parts
from sdf import mesh, to_world, watertight, volume, write_stl
H = {"base": 0.3, "lid": 0.3, "button": 0.12, "tip": 0.25}
out = sys.argv[1]
coarse = "--coarse" in sys.argv
for name in ("button", "lid", "base", "tip"):
    t = time.time(); h = 0.7 if coarse else H[name]
    lo, hi = parts.BOUNDS[name]
    v, f = mesh(getattr(parts, name), lo, hi, h)
    w, f2 = to_world(v, f)
    ok, bad = watertight(f2)
    bb = (v.min(0).round(2), v.max(0).round(2))
    print(f"{name:7s} h={h} tris={len(f2):8d} watertight={ok} badedges={bad} vol={volume(w, f2)/1000:.1f} cm3 bbox(case)={bb[0]}..{bb[1]} {time.time()-t:.0f}s", flush=True)
    if not coarse:
        if name == "lid":   # print orientation: top face down
            w = w.copy(); w[:, 2] = -w[:, 2] + w[:, 2].max(); w[:, 1] *= -1; f2 = f2   # rotate 180 deg about x (y,z -> -y,-z): det +1
        elif name == "button":
            w = w.copy(); w[:, 2] -= w[:, 2].min()
        elif name == "tip":   # sleeve on the bed, cone up
            w = w.copy(); w[:, 2] = -w[:, 2] + w[:, 2].max(); w[:, 1] *= -1
        else:
            w = w.copy(); w[:, 2] -= w[:, 2].min()
        write_stl(f"{out}/gaiapus-revB-{name}.stl", w, f2, "gaiapus revB " + name)
