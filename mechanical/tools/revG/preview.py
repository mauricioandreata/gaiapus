"""Read a .glb back (all nodes, matrices, materials) and render it with a numpy z-buffer point splatter."""
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from glbread import load, mat
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
def read(path):
    j, b = load(path); tris = []
    def acc(i):
        a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; n = NC[a["type"]]; dt = np.dtype(CT[a["componentType"]])
        stride = bv.get("byteStride", 0) or dt.itemsize * n; off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        raw = np.frombuffer(b, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * n, offset=off)
        arr = np.lib.stride_tricks.as_strided(raw.view(np.uint8), shape=(a["count"], dt.itemsize * n), strides=(stride, 1)).copy().view(dt)
        return arr.reshape(a["count"], n) if n > 1 else arr.reshape(-1)
    def walk(i, M):
        n = j["nodes"][i]; M = M @ mat(n)
        if "mesh" in n:
            for p in j["meshes"][n["mesh"]]["primitives"]:
                if p.get("mode", 4) != 4: continue
                v = acc(p["attributes"]["POSITION"]).astype(float); v = (np.c_[v, np.ones(len(v))] @ M.T)[:, :3]
                f = acc(p["indices"]).reshape(-1, 3) if "indices" in p else np.arange(len(v)).reshape(-1, 3)
                col = j["materials"][p["material"]]["pbrMetallicRoughness"].get("baseColorFactor", [0.7, 0.7, 0.7, 1]) if "material" in p else [0.7] * 4
                nrm = None
                if "NORMAL" in p["attributes"]:
                    nv = acc(p["attributes"]["NORMAL"]).astype(float) @ M[:3, :3].T; nrm = nv[f].mean(1)
                tris.append((v[f], np.array(col), nrm) if nrm is not None else (v[f], np.array(col)))
        for c in n.get("children", []): walk(c, M)
    for r in j["scenes"][j.get("scene", 0)]["nodes"]: walk(r, np.eye(4))
    return tris
def _split(tris):
    out = []
    for it in tris:
        out.append((it[0], it[1], it[2] if len(it) > 2 else None))
    return out

def render(tris, path, az=-40, el=22, res=1400, crop=None, cut=None, title="", maxe=0.0006, edges=True, bg=(1, 1, 1), ret=False, cutz=None):
    a, e = np.radians(az), np.radians(el)
    R = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]]); R = Rx @ R
    L = np.array([-0.4, 0.8, 0.45]); L /= np.linalg.norm(L)
    tris = _split(tris)
    if cut is not None: tris = [(T[k], c, None if N is None else N[k]) for T, c, N in tris for k in [T[:, :, 0].max(1) < cut]]
    if cutz is not None: tris = [(T[k], c, None if N is None else N[k]) for T, c, N in tris for k in [T[:, :, 2].max(1) < cutz]]
    tris = [(T, c, N) for T, c, N in tris if len(T)]
    allp = np.vstack([(T.reshape(-1, 3) @ R.T)[:, :2] for T, c, N in tris])
    lo, hi = (allp.min(0), allp.max(0)) if crop is None else crop
    s = (res - 1) / max(hi - lo); W_, H_ = int((hi[0] - lo[0]) * s) + 1, int((hi[1] - lo[1]) * s) + 1
    zbuf = np.full(H_ * W_, -np.inf); img = np.ones((H_ * W_, 3))
    w = np.array([[1/3, 1/3, 1/3], [.7, .15, .15], [.15, .7, .15], [.15, .15, .7], [.5, .5, 0], [0, .5, .5], [.5, 0, .5]])
    maxe = min(maxe, 2.2 / s)
    for T, col, N in tris:
        if col[3] == 1:
            for _ in range(16):
                e_ = np.max([np.linalg.norm(T[:, a_] - T[:, b_], axis=1) for a_, b_ in ((0, 1), (1, 2), (2, 0))], axis=0)
                big = e_ > maxe
                if not big.any() or len(T) > 6_000_000: break
                B = T[big]; m01, m12, m20 = (B[:, 0] + B[:, 1]) / 2, (B[:, 1] + B[:, 2]) / 2, (B[:, 2] + B[:, 0]) / 2
                T = np.concatenate([T[~big], np.stack([B[:, 0], m01, m20], 1), np.stack([m01, B[:, 1], m12], 1), np.stack([m20, m12, B[:, 2]], 1), np.stack([m01, m12, m20], 1)])
                if N is not None: N = np.concatenate([N[~big]] + [N[big]] * 4)
        n = N if N is not None else np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-20)
        k = 0.45 + 0.55 * np.abs(n @ L)
        for chunk in range(0, len(T), 400000):
            Tc, kc = T[chunk:chunk + 400000], k[chunk:chunk + 400000]
            pts = np.einsum("sk,tkd->tsd", w, Tc).reshape(-1, 3); c = np.repeat(np.clip(col[:3][None] * kc[:, None], 0, 1), len(w), 0)
            if col[3] < 1: pts, c = pts[::5], c[::5]
            q = pts @ R.T; ij = ((q[:, :2] - lo) * s).astype(int)
            ok = (ij[:, 0] >= 0) & (ij[:, 1] >= 0) & (ij[:, 0] < W_) & (ij[:, 1] < H_)
            pix = (H_ - 1 - ij[ok, 1]) * W_ + ij[ok, 0]; z = q[ok, 2]; c = c[ok]
            o = np.lexsort((-z, pix)); pix, z, c = pix[o], z[o], c[o]; f = np.r_[True, pix[1:] != pix[:-1]]
            pix, z, c = pix[f], z[f], c[f]; better = z > zbuf[pix]
            zbuf[pix[better]] = z[better]; img[pix[better]] = c[better]
    img = img.reshape(H_, W_, 3); zb = zbuf.reshape(H_, W_)
    empty = ~np.isfinite(zb); img[empty] = bg
    if edges:
        zf = np.where(empty, -1e3, zb); e = np.zeros_like(empty)
        tol = 0.0035
        e[:, 1:] |= np.abs(zf[:, 1:] - zf[:, :-1]) > tol; e[1:, :] |= np.abs(zf[1:, :] - zf[:-1, :]) > tol
        img[e] = img[e] * 0.25
    if path: plt.imsave(path, np.clip(img, 0, 1))
    if ret: return img, zb, (lo, hi, s)

if __name__ == "__main__":
    tris = read(sys.argv[1]); print("meshes", len(tris), "tris", sum(len(t) for t, _ in tris))
    allv = np.vstack([t.reshape(-1, 3) for t, _ in tris]); print("bbox (m)", allv.min(0).round(4), allv.max(0).round(4))
