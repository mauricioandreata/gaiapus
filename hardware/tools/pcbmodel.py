"""Minimal KiCad 8 .kicad_pcb reader: footprints, pads (absolute geometry, nets), board outline.
Shared by route.py and verify_pcb.py."""
import re, math

def tokenize(t):
    return re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+', t)

def parse(t):
    tok = tokenize(t); pos = 0
    def rd():
        nonlocal pos
        x = tok[pos]; pos += 1
        if x == "(":
            L = []
            while tok[pos] != ")":
                L.append(rd())
            pos += 1
            return L
        return x[1:-1] if x.startswith('"') else x
    return rd()

def kids(L, key): return [c for c in L if isinstance(c, list) and c and c[0] == key]
def kid(L, key):
    k = kids(L, key); return k[0] if k else None

def rot(lx, ly, r):
    a = math.radians(r)
    return lx * math.cos(a) + ly * math.sin(a), -lx * math.sin(a) + ly * math.cos(a)

class Pad:
    def __init__(s, **k): s.__dict__.update(k)

def load(path):
    t = open(path, encoding="utf-8").read()
    tree = parse(t)
    nets = {int(n[1]): n[2] for n in kids(tree, "net")}
    pads, fps = [], {}
    for fp in kids(tree, "footprint"):
        at = kid(fp, "at"); fx, fy = float(at[1]), float(at[2]); fr = float(at[3]) if len(at) > 3 else 0.0
        side = kid(fp, "layer")[1][0]          # 'F' or 'B'
        ref = [p[2] for p in kids(fp, "property") if p[1] == "Reference"][0]
        fps[ref] = dict(x=fx, y=fy, rot=fr, side=side, node=fp)
        for p in kids(fp, "pad"):
            num, kind, shape = p[1], p[2], p[3]
            pat = kid(p, "at"); lx, ly = float(pat[1]), float(pat[2]); pang = float(pat[3]) if len(pat) > 3 else 0.0
            sz = kid(p, "size"); w, h = float(sz[1]), float(sz[2])
            # custom pads: use the primitives' extents
            prim = kid(p, "primitives")
            if prim is not None:
                xs, ys = [], []
                for g in prim[1:]:
                    if isinstance(g, list):
                        for xy in re.findall(r"\['xy', '([-\d.]+)', '([-\d.]+)'\]", str(g)):
                            xs.append(float(xy[0])); ys.append(float(xy[1]))
                if xs:
                    w = max(w, 2 * max(abs(min(xs)), abs(max(xs)))); h = max(h, 2 * max(abs(min(ys)), abs(max(ys))))
            ax, ay = rot(lx, ly, fr)
            # pad angle in the file is absolute in KiCad 8
            if round(pang) % 180 == 90: w, h = h, w
            elif round(pang) % 90 != 0:
                d = max(w, h); w = h = d
            lay = kid(p, "layers")[1:]
            L = set()
            for l in lay:
                if l in ("*.Cu", "F&B.Cu"): L |= {"F", "B"}
                elif l == "F.Cu": L.add("F")
                elif l == "B.Cu": L.add("B")
            netk = kid(p, "net")
            net = netk[2] if netk else ""
            drill = kid(p, "drill")
            pads.append(Pad(ref=ref, num=num, kind=kind, shape=shape, x=fx + ax, y=fy + ay, w=w, h=h,
                            layers=L, net=net, netid=int(netk[1]) if netk else 0, th=(kind in ("thru_hole", "np_thru_hole"))))
    # board outline: chain Edge.Cuts lines/arcs into polygons; circles are holes
    segs, circles = [], []
    for g in tree:
        if not isinstance(g, list) or not g: continue
        if g[0] in ("gr_line", "gr_arc", "gr_circle", "gr_rect") and kid(g, "layer") and kid(g, "layer")[1] == "Edge.Cuts":
            if g[0] == "gr_line":
                s, e = kid(g, "start"), kid(g, "end"); segs.append([(float(s[1]), float(s[2])), (float(e[1]), float(e[2]))])
            elif g[0] == "gr_arc":
                s, m, e = kid(g, "start"), kid(g, "mid"), kid(g, "end")
                P = [(float(s[1]), float(s[2])), (float(m[1]), float(m[2])), (float(e[1]), float(e[2]))]
                segs.append(arc_points(*P))
            elif g[0] == "gr_circle":
                c, e = kid(g, "center"), kid(g, "end")
                cx, cy = float(c[1]), float(c[2]); circles.append((cx, cy, math.hypot(float(e[1]) - cx, float(e[2]) - cy)))
    return dict(text=t, tree=tree, nets=nets, pads=pads, fps=fps, edge_polylines=segs, holes=circles)

def arc_points(s, m, e, n=12):
    ax, ay = s; bx, by = m; cx, cy = e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay) + (cx*cx+cy*cy)*(ay-by)) / d
    uy = ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx) + (cx*cx+cy*cy)*(bx-ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, a1, am = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, e, m))
    def norm(a): return a % (2 * math.pi)
    sweep = norm(a1 - a0)
    if not (norm(am - a0) < sweep): sweep -= 2 * math.pi
    return [(ux + r * math.cos(a0 + sweep * k / n), uy + r * math.sin(a0 + sweep * k / n)) for k in range(n + 1)]

def chain(polylines):
    """join polylines sharing endpoints into closed polygons"""
    rem = [list(p) for p in polylines]; polys = []
    def close(a, b): return abs(a[0] - b[0]) < 1e-3 and abs(a[1] - b[1]) < 1e-3
    while rem:
        cur = rem.pop(0)
        grown = True
        while grown and not close(cur[0], cur[-1]):
            grown = False
            for i, p in enumerate(rem):
                if close(cur[-1], p[0]): cur += p[1:]; rem.pop(i); grown = True; break
                if close(cur[-1], p[-1]): cur += p[::-1][1:]; rem.pop(i); grown = True; break
        polys.append(cur)
    return polys

def point_in_poly(x, y, poly):
    inside = False; n = len(poly)
    for i in range(n - 1):
        (x1, y1), (x2, y2) = poly[i], poly[i + 1]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside
