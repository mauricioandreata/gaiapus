#!/usr/bin/env python3
"""Independent check of routed copper (exact geometry, no grid): per-net connectivity, clearance between
different nets (tracks/vias vs everything), copper-to-edge. Zones are ignored (KiCad fills them).
python3 verify_pcb.py board.kicad_pcb [clearance] [edge]"""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbmodel as pm

def pt_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)
def seg_seg(a, b, c, d):
    def orient(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0) and o1 and o2 and o3 and o4: return 0.0
    return min(pt_seg(*a, *c, *d), pt_seg(*b, *c, *d), pt_seg(*c, *a, *b), pt_seg(*d, *a, *b))
def rect_edges(cx, cy, hw, hh):
    P = [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]
    return [(P[i], P[(i + 1) % 4]) for i in range(4)]
def core(o):   # ('seg', a, b, r) | ('rect', cx, cy, hw, hh)
    return o
def dist(A, B):
    if A[0] == "rect" and B[0] == "rect":
        dx = max(abs(A[1] - B[1]) - A[3] - B[3], 0); dy = max(abs(A[2] - B[2]) - A[4] - B[4], 0); return math.hypot(dx, dy)
    if A[0] == "rect": A, B = B, A
    if B[0] == "rect":
        _, a, b, r = A; _, cx, cy, hw, hh = B
        inside = lambda p: abs(p[0] - cx) <= hw and abs(p[1] - cy) <= hh
        if inside(a) or inside(b): return 0.0
        return max(0.0, min(seg_seg(a, b, e0, e1) for e0, e1 in rect_edges(cx, cy, hw, hh)) - r)
    _, a, b, r1 = A; _, c, d, r2 = B
    return max(0.0, seg_seg(a, b, c, d) - r1 - r2)

def main():
    path = sys.argv[1]; CLR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15; EDGE = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    bd = pm.load(path); t = bd["text"]; nets = bd["nets"]
    items = []   # (layerset, shape, net, kind, label)
    for p in bd["pads"]:
        net = p.net or f"__npth_{p.ref}_{p.x:.2f}"           # unconnected / hole pads are still copper or holes
        items.append(((p.layers | {"In1", "In2"}) if p.th else p.layers, ("rect", p.x, p.y, p.w / 2, p.h / 2), net, "hole" if p.kind == "np_thru_hole" else "pad", f"{p.ref}.{p.num or 'hole'}"))
    for m in re.finditer(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width ([-\d.]+)\) \(layer "(F|B|In1|In2)\.Cu"\) \(net (\d+)\)', t):
        x1, y1, x2, y2, w = map(float, m.groups()[:5])
        items.append(({m.group(6)}, ("seg", (x1, y1), (x2, y2), w / 2), nets[int(m.group(7))], "track", f"track@{x1:.1f},{y1:.1f}"))
    for m in re.finditer(r'\(via \(at ([-\d.]+) ([-\d.]+)\) \(size ([-\d.]+)\) \(drill [-\d.]+\) \(layers "F.Cu" "B.Cu"\) \(net (\d+)\)', t):
        x, y, d = map(float, m.groups()[:3])
        items.append(({"F", "B", "In1", "In2"}, ("seg", (x, y), (x, y), d / 2), nets[int(m.group(4))], "via", f"via@{x:.1f},{y:.1f}"))
    # spatial buckets
    def bbox(s):
        if s[0] == "rect": return s[1] - s[3], s[2] - s[4], s[1] + s[3], s[2] + s[4]
        return min(s[1][0], s[2][0]) - s[3], min(s[1][1], s[2][1]) - s[3], max(s[1][0], s[2][0]) + s[3], max(s[1][1], s[2][1]) + s[3]
    BK = 2.0; grid = {}
    for k, it in enumerate(items):
        x1, y1, x2, y2 = bbox(it[1])
        for gx in range(int((x1 - 1) // BK), int((x2 + 1) // BK) + 1):
            for gy in range(int((y1 - 1) // BK), int((y2 + 1) // BK) + 1):
                grid.setdefault((gx, gy), []).append(k)
    pairs = set()
    for cell in grid.values():
        for i in range(len(cell)):
            for j in range(i + 1, len(cell)):
                pairs.add((min(cell[i], cell[j]), max(cell[i], cell[j])))
    parent = list(range(len(items)))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    viol = []
    for i, j in pairs:
        A, B = items[i], items[j]
        if not (A[0] & B[0]): continue
        d = dist(A[1], B[1])
        if A[2] == B[2]:
            if d <= 1e-6: parent[find(i)] = find(j)
        else:
            if A[3] in ("pad", "hole") and B[3] in ("pad", "hole") and A[4].split(".")[0] == B[4].split(".")[0]: continue   # same footprint
            need = 0.25 if "hole" in (A[3], B[3]) else CLR
            if d < need - 0.005: viol.append((round(d, 3), A[4], A[2].split('/')[-1], B[4], B[2].split('/')[-1]))
    # pads of the same footprint+number are one copper piece (electrode combs)
    first = {}
    for k, it in enumerate(items):
        if it[3] == "pad":
            key = it[4]
            if key in first: parent[find(k)] = find(first[key])
            else: first[key] = k
    unconn = {}
    for k, it in enumerate(items):
        if it[3] != "pad" or it[2].startswith(("unconnected", "__npth")): continue
        unconn.setdefault(it[2], set()).add(find(k))
    bad_nets = {n.split('/')[-1]: len(s) for n, s in unconn.items() if len(s) > 1}
    polys = pm.chain(bd["edge_polylines"]); edge = []
    for p in polys:
        for a, b in zip(p, p[1:]): edge.append(("seg", a, b, 0.0))
    for (cx, cy, r) in bd["holes"]: edge.append(("seg", (cx, cy), (cx, cy), r))
    edge_v = []
    for it in items:
        if it[3] == "pad": continue
        dmin = min(dist(it[1], e) for e in edge)
        if dmin < EDGE - 0.01: edge_v.append((round(dmin, 3), it[4], it[2].split('/')[-1]))
    nt = sum(1 for it in items if it[3] == "track"); nv = sum(1 for it in items if it[3] == "via")
    print(f"{os.path.basename(path)}: {nt} tracks, {nv} vias, {len(pairs)} pairs checked")
    print(f"  nets not fully connected (pieces): {bad_nets or 'none'}")
    print(f"  clearance violations (< {CLR} mm): {len(viol)}"); [print('    ', v) for v in sorted(viol)[:15]]
    print(f"  edge violations (< {EDGE} mm): {len(edge_v)}"); [print('    ', v) for v in sorted(edge_v)[:10]]
    ok = not bad_nets and not viol and not edge_v
    print("RESULT:", "OK" if ok else "ISSUES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
