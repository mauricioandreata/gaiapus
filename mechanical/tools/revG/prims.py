"""Analytic meshes in the case frame (mm): boxes, cylinders, cones, discs."""
import numpy as np
def box(x0, y0, z0, x1, y1, z1):
    v = np.array([[x, y, z] for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)], float)
    f = np.array([[0,2,1],[1,2,3],[4,5,6],[5,7,6],[0,1,4],[1,5,4],[2,6,3],[3,6,7],[0,4,2],[2,4,6],[1,3,5],[3,7,5]])
    return v, f
def cyl(axis, c, r, a0, a1, n=48, r1=None):
    """solid of revolution along 'x'|'y'|'z' from a0 to a1; r1 = end radius (cone)"""
    r1 = r if r1 is None else r1
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = lambda rr, a: np.stack([np.full(n, a), c[0] + rr * np.cos(t), c[1] + rr * np.sin(t)], 1)
    v = np.vstack([ring(r, a0), ring(r1, a1), [[a0, c[0], c[1]], [a1, c[0], c[1]]]])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + i], [j, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
    f = np.array(f)
    order = {"x": [0, 1, 2], "y": [1, 0, 2], "z": [2, 0, 1]}[axis]
    out = np.zeros_like(v); out[:, order[0]], out[:, order[1]], out[:, order[2]] = v[:, 0], v[:, 1], v[:, 2]
    return out, f
def merge(*ms):
    V, F, k = [], [], 0
    for v, f in ms: V.append(v); F.append(f + k); k += len(v)
    return np.vstack(V), np.vstack(F)
