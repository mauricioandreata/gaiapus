"""Printable STLs, rev C, in print orientation. Usage: python3 build_parts.py OUT_DIR [--coarse] [--stl]  (3MF always; STL on request)  (numpy + scikit-image)"""
import os, sys, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import parts
from sdf import mesh, to_world, watertight, volume, write_stl, write_3mf
H = {"base": 0.3, "lid": 0.3, "button": 0.12, "plunger": 0.12, "light_bar": 0.12, "tip": 0.25}
FLIP = {"lid", "tip"}          # printed upside down (lid: top face on the bed, tip: sleeve on the bed)
out = sys.argv[1]; coarse = "--coarse" in sys.argv; os.makedirs(out, exist_ok=True)
for name, h in H.items():
    t = time.time(); h = 0.7 if coarse else h
    v, f = mesh(getattr(parts, name), *parts.BOUNDS[name], h)
    w, f2 = to_world(v, f); ok, bad = watertight(f2)
    w = w.copy()
    if name in FLIP: w[:, 2] = -w[:, 2]; w[:, 1] = -w[:, 1]
    if name == "light_bar": w = w[:, [0, 2, 1]] * np.array([1, 1, -1]); f2 = f2[:, ::-1]   # lie on its side
    w -= np.array([w[:, 0].mean(), w[:, 1].mean(), w[:, 2].min()])
    print("%-10s h=%.2f tris=%8d watertight=%s vol=%.1f cm3  size=%s mm  %.0fs" % (name, h, len(f2), ok, abs(volume(w, f2)) / 1000, (w.max(0) - w.min(0)).round(1), time.time() - t), flush=True)
    if volume(w, f2) < 0: f2 = f2[:, ::-1]
    if not coarse:
        fn = os.path.join(out, "gaiapus-revC-%s" % name.replace("_", "-"))
        write_3mf(fn + ".3mf", w, f2, "gaiapus revC " + name)
        if "--stl" in sys.argv: write_stl(fn + ".stl", w, f2, "gaiapus revC " + name)
