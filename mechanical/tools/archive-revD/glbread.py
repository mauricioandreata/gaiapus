import json, struct, numpy as np
def load(path):
    b = open(path, "rb").read(); l = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + l]); off = 20 + l; bl = struct.unpack("<I", b[off:off + 4])[0]; binc = b[off + 8: off + 8 + bl]
    return j, binc
def mat(n):
    if "matrix" in n: return np.array(n["matrix"]).reshape(4, 4).T
    M = np.eye(4); t = n.get("translation", [0, 0, 0]); s = n.get("scale", [1, 1, 1]); x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    M[:3, :3] = R * np.array(s); M[:3, 3] = t; return M
def part_boxes(path):
    j, _ = load(path); nodes, acc, meshes = j["nodes"], j["accessors"], j["meshes"]
    root = j["scenes"][0]["nodes"][0]; out = {}
    def walk(i, P, top):
        n = nodes[i]; M = P @ mat(n)
        if "mesh" in n:
            for pr in meshes[n["mesh"]]["primitives"]:
                a = acc[pr["attributes"]["POSITION"]]
                for c in [[x, y, z] for x in (a["min"][0], a["max"][0]) for y in (a["min"][1], a["max"][1]) for z in (a["min"][2], a["max"][2])]:
                    p = (M @ np.array(c + [1]))[:3] * 1000
                    lo, hi = out.setdefault(top, [np.full(3, 1e9), np.full(3, -1e9)])
                    out[top][0] = np.minimum(lo, p); out[top][1] = np.maximum(hi, p)
        for c in n.get("children", []): walk(c, M, top)
    R = mat(nodes[root])
    for c in nodes[root].get("children", []): walk(c, R, nodes[c].get("name", "?"))
    return out
