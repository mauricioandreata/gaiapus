import numpy as np
from preview import read as _r
import preview
from glbread import load, mat
def read_named(path):
    j, b = load(path); out = []
    acc = None
    # reuse preview's accessor logic by temporarily walking with names
    CT = preview.CT; NC = preview.NC
    def acc(i):
        a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; n = NC[a["type"]]; dt = np.dtype(CT[a["componentType"]])
        stride = bv.get("byteStride", 0) or dt.itemsize * n; off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        raw = np.frombuffer(b, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * n, offset=off)
        arr = np.lib.stride_tricks.as_strided(raw.view(np.uint8), shape=(a["count"], dt.itemsize * n), strides=(stride, 1)).copy().view(dt)
        return arr.reshape(a["count"], n) if n > 1 else arr.reshape(-1)
    def walk(i, M, path):
        n = j["nodes"][i]; M = M @ mat(n); path = path + [n.get("name", "")]
        if "mesh" in n:
            for p in j["meshes"][n["mesh"]]["primitives"]:
                if p.get("mode", 4) != 4: continue
                v = acc(p["attributes"]["POSITION"]).astype(float); v = (np.c_[v, np.ones(len(v))] @ M.T)[:, :3]
                f = acc(p["indices"]).reshape(-1, 3) if "indices" in p else np.arange(len(v)).reshape(-1, 3)
                col = j["materials"][p["material"]]["pbrMetallicRoughness"].get("baseColorFactor", [0.7, 0.7, 0.7, 1]) if "material" in p else [0.7] * 4
                nrm = None
                if "NORMAL" in p["attributes"]:
                    nv = acc(p["attributes"]["NORMAL"]).astype(float) @ M[:3, :3].T; nrm = nv[f].mean(1)
                out.append((path, v[f], np.array(col), nrm))
        for c in n.get("children", []): walk(c, M, path)
    for r in j["scenes"][j.get("scene", 0)]["nodes"]: walk(r, np.eye(4), [])
    return out
