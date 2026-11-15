"""Tiny glTF 2.0 (.glb) writer + merger for existing .glb files."""
import json, struct, numpy as np
from glbread import load

class GLB:
    def __init__(self):
        self.j = {"asset": {"version": "2.0", "generator": "gaiapus stake builder"}, "scene": 0, "scenes": [{"nodes": []}],
                  "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": [], "buffers": [{"byteLength": 0}]}
        self.bin = bytearray(); self.mat_ids = {}
    def _view(self, data, target=None):
        while len(self.bin) % 4: self.bin += b"\0"
        bv = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target: bv["target"] = target
        self.bin += data; self.j["bufferViews"].append(bv); return len(self.j["bufferViews"]) - 1
    def material(self, name, rgba, rough=0.7, metal=0.0, emissive=None):
        if name in self.mat_ids: return self.mat_ids[name]
        m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": list(rgba), "roughnessFactor": rough, "metallicFactor": metal}, "doubleSided": False}
        if rgba[3] < 1: m["alphaMode"] = "BLEND"; m["doubleSided"] = True
        if emissive: m["emissiveFactor"] = list(emissive)
        self.j["materials"].append(m); self.mat_ids[name] = len(self.j["materials"]) - 1; return self.mat_ids[name]
    def mesh(self, name, v, f, mat, smooth=True, parent=None):
        v = np.asarray(v, np.float32); f = np.asarray(f, np.uint32)
        fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
        if smooth:
            n = np.zeros_like(v); 
            for k in range(3): np.add.at(n, f[:, k], fn)
        else:  # flat: unweld
            v = v[f.reshape(-1)]; f = np.arange(len(v), dtype=np.uint32).reshape(-1, 3); n = np.repeat(fn, 3, axis=0)
        n = (n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-20)).astype(np.float32)
        acc = self.j["accessors"]
        pv = self._view(v.tobytes(), 34962); acc.append({"bufferView": pv, "componentType": 5126, "count": len(v), "type": "VEC3", "min": v.min(0).tolist(), "max": v.max(0).tolist()})
        nv = self._view(n.tobytes(), 34962); acc.append({"bufferView": nv, "componentType": 5126, "count": len(n), "type": "VEC3"})
        iv = self._view(f.tobytes(), 34963); acc.append({"bufferView": iv, "componentType": 5125, "count": int(f.size), "type": "SCALAR"})
        k = len(acc)
        self.j["meshes"].append({"name": name, "primitives": [{"attributes": {"POSITION": k - 3, "NORMAL": k - 2}, "indices": k - 1, "material": mat}]})
        return self.node(name, mesh=len(self.j["meshes"]) - 1, parent=parent)
    def node(self, name, mesh=None, matrix=None, parent=None):
        n = {"name": name}
        if mesh is not None: n["mesh"] = mesh
        if matrix is not None: n["matrix"] = [float(x) for x in np.asarray(matrix).T.reshape(-1)]
        self.j["nodes"].append(n); i = len(self.j["nodes"]) - 1
        if parent is None: self.j["scenes"][0]["nodes"].append(i)
        else: self.j["nodes"][parent].setdefault("children", []).append(i)
        return i
    def merge(self, path, parent):
        j, b = load(path)
        while len(self.bin) % 4: self.bin += b"\0"
        base = len(self.bin); self.bin += b
        o = {k: len(self.j.setdefault(k, [])) for k in ("bufferViews", "accessors", "meshes", "materials", "nodes", "images", "textures", "samplers")}
        for bv in j.get("bufferViews", []): bv = dict(bv); bv["buffer"] = 0; bv["byteOffset"] = bv.get("byteOffset", 0) + base; self.j["bufferViews"].append(bv)
        for a in j.get("accessors", []):
            a = dict(a)
            if "bufferView" in a: a["bufferView"] += o["bufferViews"]
            self.j["accessors"].append(a)
        for im in j.get("images", []):
            im = dict(im)
            if "bufferView" in im: im["bufferView"] += o["bufferViews"]
            self.j["images"].append(im)
        self.j["samplers"] += j.get("samplers", [])
        for t in j.get("textures", []):
            t = dict(t)
            if "source" in t: t["source"] += o["images"]
            if "sampler" in t: t["sampler"] += o["samplers"]
            self.j["textures"].append(t)
        def fixtex(d):
            for k_, val in list(d.items()):
                if isinstance(val, dict):
                    if k_.endswith("Texture") and "index" in val: val["index"] += o["textures"]
                    fixtex(val)
        for m in j.get("materials", []): m = json.loads(json.dumps(m)); fixtex(m); self.j["materials"].append(m)
        for me in j.get("meshes", []):
            me = json.loads(json.dumps(me))
            for p in me["primitives"]:
                p["attributes"] = {k_: v_ + o["accessors"] for k_, v_ in p["attributes"].items()}
                if "indices" in p: p["indices"] += o["accessors"]
                if "material" in p: p["material"] += o["materials"]
                p.pop("targets", None)
            self.j["meshes"].append(me)
        for n in j.get("nodes", []):
            n = dict(n)
            if "mesh" in n: n["mesh"] += o["meshes"]
            if "children" in n: n["children"] = [c + o["nodes"] for c in n["children"]]
            n.pop("camera", None); n.pop("skin", None)
            self.j["nodes"].append(n)
        for r in j["scenes"][j.get("scene", 0)]["nodes"]: self.j["nodes"][parent].setdefault("children", []).append(r + o["nodes"])
        for k_ in ("images", "textures", "samplers"):
            if not self.j[k_]: del self.j[k_]
    def save(self, path):
        while len(self.bin) % 4: self.bin += b"\0"
        self.j["buffers"][0]["byteLength"] = len(self.bin)
        js = json.dumps(self.j, separators=(",", ":")).encode()
        while len(js) % 4: js += b" "
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack("<II", len(self.bin), 0x004E4942)); f.write(self.bin)
