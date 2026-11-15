"""Rain gauge + clamp: pairwise overlaps (voxel) and minimum gaps between solids, incl. the bucket at both rest positions."""
import os, sys, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import params as P, parts, raingauge as RGm
R = P.RG; gx, gy, gz = R["pos"]
def cyl_z(cx, cy, r, z0, z1):
    return lambda x, y, z: np.maximum(np.hypot(x - cx, y - cy) - r, np.maximum(z0 - z, z - z1))
G = P.GLAND
SOL = {
    "rg_body": (RGm.rg_body, RGm.BOUNDS["rg_body"]),
    "rg_funnel": (RGm.rg_funnel, RGm.BOUNDS["rg_funnel"]),
    "bucket(+tilt)": (lambda x, y, z: RGm.rg_bucket(x, y, z, R["tilt"]), RGm.BOUNDS["rg_bucket"]),
    "bucket(-tilt)": (lambda x, y, z: RGm.rg_bucket(x, y, z, -R["tilt"]), RGm.BOUNDS["rg_bucket"]),
    "clamp_a": (RGm.clamp_a, RGm.BOUNDS["clamp_a"]),
    "clamp_b": (RGm.clamp_b, RGm.BOUNDS["clamp_b"]),
    "head base+neck": (parts.base, parts.BOUNDS["base"]),
    "head lid": (parts.lid, parts.BOUNDS["lid"]),
    "M8 gland (head)": (cyl_z(G[0], G[1], 6.4, -12, 0), ((G[0] - 7, G[1] - 7, -12), (G[0] + 7, G[1] + 7, 0))),
    "PVC tube": (cyl_z(0, P.CY, P.TUBE_OD / 2, -200, P.COLLAR_Z0 + P.SOCKET_DEPTH - 0.1), ((-16, P.CY - 16, -60), (16, P.CY + 16, P.COLLAR_Z0 + P.SOCKET_DEPTH))),
}
SKIP = {("bucket(+tilt)", "bucket(-tilt)"), ("PVC tube", "head base+neck")}
def pair(a, b, h=0.3):
    (fa, (la, ha)), (fb, (lb, hb)) = SOL[a], SOL[b]
    lo = np.maximum(la, lb) - 1.0; hi = np.minimum(ha, hb) + 1.0
    if (hi <= lo).any(): return 0.0, None
    xs, ys = np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h); X, Y = np.meshgrid(xs, ys, indexing="ij")
    ov = 0; gap = np.inf
    for z in np.arange(lo[2], hi[2], h):
        Z = np.full_like(X, z); da, db = fa(X, Y, Z), fb(X, Y, Z)
        ov += int(((da < -0.03) & (db < -0.03)).sum())
        m = da < 0
        if m.any(): gap = min(gap, float(db[m].min()))
    return ov * h ** 3, gap
if __name__ == "__main__":
    names = list(SOL); out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (a, b) in SKIP: continue
            v, g = pair(a, b)
            if g is None or g > 15: continue
            out.append((a, b, v, g)); print("%-16s %-16s overlap %8.3f mm3   min gap %6.2f mm" % (a, b, v, g), flush=True)
