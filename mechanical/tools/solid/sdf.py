"""Minimal SDF modelling (numpy) + marching cubes (skimage) -> closed triangle meshes."""
import numpy as np
from skimage.measure import marching_cubes

# ---- 2D ----
def rrect2(x, y, x0, y0, x1, y1, r):
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 - r, (y1 - y0) / 2 - r
    qx, qy = np.abs(x - cx) - hx, np.abs(y - cy) - hy
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
def circle2(x, y, cx, cy, r): return np.hypot(x - cx, y - cy) - r
def capsule2(x, y, cx, cy, L, W):     # obround along x
    a = L / 2 - W / 2
    return np.hypot(np.maximum(np.abs(x - cx) - a, 0), y - cy) - W / 2
# ---- 3D ----
def extrude(d2, z, z0, z1):
    wz = np.maximum(z0 - z, z - z1)
    return np.minimum(np.maximum(d2, wz), 0) + np.hypot(np.maximum(d2, 0), np.maximum(wz, 0))
def round_top(d2_shrunk, z, z0, zt, r):
    """extrusion from z0 to zt whose top edge is rounded with radius r (d2_shrunk = outline offset inward by r)"""
    w1, w2 = d2_shrunk, z - (zt - r)
    d = np.hypot(np.maximum(w1, 0), np.maximum(w2, 0)) + np.minimum(np.maximum(w1, w2), 0) - r
    return np.maximum(d, z0 - z)
U = np.minimum
def D(a, *b):
    for k in b: a = np.maximum(a, -k)
    return a
I = np.maximum

def mesh(fn, lo, hi, h):
    """evaluate fn(x,y,z) on a grid (slab by slab) and return verts (case frame), faces"""
    lo = np.array(lo, float) - 2 * h; hi = np.array(hi, float) + 2 * h
    n = np.ceil((hi - lo) / h).astype(int) + 1
    xs, ys, zs = [lo[i] + h * np.arange(n[i]) for i in range(3)]
    vol = np.empty((n[0], n[1], n[2]), np.float32)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    for k, z in enumerate(zs):
        vol[:, :, k] = fn(X, Y, np.full_like(X, z))
    vol[0], vol[-1], vol[:, 0], vol[:, -1], vol[:, :, 0], vol[:, :, -1] = 1, 1, 1, 1, 1, 1
    v, f, _, _ = marching_cubes(vol, 0.0, spacing=(h, h, h), gradient_direction="ascent")
    return v + lo, f.astype(np.int64)

def volume(v, f):
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0

def to_world(v, f):
    """case frame (KiCad-like, left-handed) -> right-handed mm (x, -y, z); fix winding so volume > 0"""
    w = v.copy(); w[:, 1] *= -1
    if volume(w, f) < 0: f = f[:, ::-1].copy()
    return w, f

def watertight(f):
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return bool((cnt == 2).all()), int((cnt != 2).sum())

def write_stl(path, v, f, name="gaiapus"):
    tri = v[f].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as fh:
        fh.write(name.encode()[:80].ljust(80, b" ")); fh.write(np.uint32(len(f)).tobytes()); fh.write(rec.tobytes())
