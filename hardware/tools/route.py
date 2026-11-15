#!/usr/bin/env python3
"""Grid router (2 layers, 45-degree, vias) for the Gaiapus boards. Writes tracks, vias, GND pours, keepouts.

python3 route.py probe|head [--out file] [--dry]
Rules follow the .kicad_dru files (JLCPCB). The result must pass verify_pcb.py and then KiCad's DRC.
"""
import sys, os, math, heapq, uuid, re, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbmodel as pm

G = 0.1                    # grid pitch, mm
CLR = 0.15                 # base clearance
MARGIN = 0.035             # grid discretisation margin (exact geometry is re-checked by verify_pcb.py)
EDGE = 0.35                # copper to board edge
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_COST = 50              # in grid steps (5 mm of track)
LAYERS = ("F", "B")                     # default routing layers; a board config may add "In2"
CU = {"F": "F.Cu", "B": "B.Cu", "In1": "In1.Cu", "In2": "In2.Cu"}
NS = uuid.UUID("3e8f6a1c-9b2d-4c7e-a5f1-0d2c4b6e8a90")

CFG = {
    "probe": dict(folder="gaiapus-probe",
                  width=[("GND", 0.4), ("PWR_", 0.3), ("_FREQ", 0.25), ("", 0.25)],
                  extra=[("OSC15_A", "GND", 0.3), ("OSC40_A", "GND", 0.3)],   # best effort vs GND tracks; pour keeps 1.5 mm via the .kicad_dru
                  order_first=["OSC15_A", "OSC40_A", "GND", "OSC15_Y", "OSC40_Y"], cap=1500000, hweight=1.4,
                  layer_bias={}),
    "head": dict(folder="gaiapus-node",
                 width=[("RF_", 0.35), ("VBAT", 0.5), ("+3V3", 0.4), ("VSOL", 0.5), ("VBUS", 0.5), ("BATT_N", 0.5),
                        ("PROT_D", 0.5), ("SW_L", 0.5), ("GND", 0.3), ("", 0.2)],
                 extra=[],
                 order_first=["RF_MOD", "RF_ANT", "SW_L1", "SW_L2", "VFB3", "VBAT", "BATT_N", "VSOL", "VBUS"], gnd_stubs=True,
                 planes={"In1.Cu": "GND", "In2.Cu": "+3V3"}, route_layers=("F", "B", "In2"), cap=900000, hweight=1.2,
                 layer_bias={}),
}

def short(n): return n.split("/")[-1]
def width_for(cfg, net):
    """keys ending in '_' are prefixes (RF_, PWR_, SW_L...); others must match the net name exactly"""
    n = short(net)
    for key, w in cfg["width"]:
        if key == "" or n == key or (key.endswith("_") and n.startswith(key)) or (key.startswith("_") and n.endswith(key)) or (key == "SW_L" and n.startswith("SW_L")):
            return w
def extra_clear(cfg, a, b):
    for x, y, d in cfg["extra"]:
        if (x in short(a) and y == short(b)) or (x in short(b) and y == short(a)): return d
    return 0.0

class Grid:
    def __init__(s, board):
        polys = pm.chain(board["edge_polylines"])
        outer = max(polys, key=lambda p: (max(q[0] for q in p) - min(q[0] for q in p)) * (max(q[1] for q in p) - min(q[1] for q in p)))
        s.x0 = min(p[0] for p in outer); s.y0 = min(p[1] for p in outer)
        s.W = int(math.ceil((max(p[0] for p in outer) - s.x0) / G)) + 1
        s.H = int(math.ceil((max(p[1] for p in outer) - s.y0) / G)) + 1
        xs = s.x0 + np.arange(s.W) * G; ys = s.y0 + np.arange(s.H) * G
        s.X, s.Y = np.meshgrid(xs, ys)
        inside = np.zeros((s.H, s.W), bool)
        for i in range(s.H):          # scanline point-in-polygon for the outer outline
            y = ys[i]; cross = []
            for k in range(len(outer) - 1):
                (x1, y1), (x2, y2) = outer[k], outer[k + 1]
                if (y1 > y) != (y2 > y): cross.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            cross.sort()
            for a, b in zip(cross[0::2], cross[1::2]):
                inside[i, (xs > a) & (xs < b)] = True
        s.outside = ~inside
        s.edge_block = ~inside
        # keep EDGE distance from every outline segment (outer + inner cut-outs) and holes
        s.edge_shapes = []
        for p in polys:
            for k in range(len(p) - 1): s.edge_shapes.append(("seg", p[k], p[k + 1], 0.0))
        for (cx, cy, r) in board["holes"]: s.edge_shapes.append(("circ", (cx, cy), None, r))
        for sh in s.edge_shapes: s.paint(s.edge_block, sh, EDGE)
    def ij(s, x, y): return int(round((y - s.y0) / G)), int(round((x - s.x0) / G))
    def xy(s, i, j): return s.x0 + j * G, s.y0 + i * G
    def window(s, xmin, ymin, xmax, ymax):
        i0 = max(0, int((ymin - s.y0) / G) - 1); i1 = min(s.H, int((ymax - s.y0) / G) + 2)
        j0 = max(0, int((xmin - s.x0) / G) - 1); j1 = min(s.W, int((xmax - s.x0) / G) + 2)
        return i0, i1, j0, j1
    def dist(s, sh, i0, i1, j0, j1):
        X, Y = s.X[i0:i1, j0:j1], s.Y[i0:i1, j0:j1]
        kind = sh[0]
        if kind == "rect":
            (cx, cy), (hw, hh) = sh[1], sh[2]
            dx = np.maximum(np.abs(X - cx) - hw, 0); dy = np.maximum(np.abs(Y - cy) - hh, 0)
            return np.hypot(dx, dy) - sh[3]
        if kind == "circ":
            (cx, cy), r = sh[1], sh[3]
            return np.hypot(X - cx, Y - cy) - r
        (ax, ay), (bx, by), r = sh[1], sh[2], sh[3]          # capsule
        vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1) if L2 > 0 else 0
        return np.hypot(X - (ax + t * vx), Y - (ay + t * vy)) - r
    def extent(s, sh):
        if sh[0] == "rect": (cx, cy), (hw, hh) = sh[1], sh[2]; r = sh[3]; return cx - hw - r, cy - hh - r, cx + hw + r, cy + hh + r
        if sh[0] == "circ": (cx, cy), r = sh[1], sh[3]; return cx - r, cy - r, cx + r, cy + r
        (ax, ay), (bx, by), r = sh[1], sh[2], sh[3]; return min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r
    def paint(s, arr, sh, infl):
        x1, y1, x2, y2 = s.extent(sh)
        i0, i1, j0, j1 = s.window(x1 - infl, y1 - infl, x2 + infl, y2 + infl)
        if i0 >= i1 or j0 >= j1: return
        arr[i0:i1, j0:j1] |= s.dist(sh, i0, i1, j0, j1) < infl

def strip_tracks(t):
    """remove board-level (segment ...) and (via ...) blocks, whatever their formatting"""
    out, i = [], 0
    for m in re.finditer(r'\n\t\((segment|via)\b', t):
        if m.start() < i: continue
        st = m.start(); d = 0; j = st + 2; inq = False
        while True:
            c = t[j]
            if c == '"' and t[j - 1] != "\\": inq = not inq
            elif not inq:
                if c == "(": d += 1
                elif c == ")":
                    d -= 1
                    if d == 0: break
            j += 1
        out.append(t[i:st]); i = j + 1
    out.append(t[i:]); return "".join(out)

def pad_shape(p): return ("rect", (p.x, p.y), (p.w / 2, p.h / 2), 0.0)

class Router:
    def __init__(s, which, path):
        s.which, s.cfg = which, CFG[which]
        global LAYERS
        LAYERS = tuple(s.cfg.get("route_layers", ("F", "B")))
        s.board = pm.load(path)
        s.g = Grid(s.board)
        s.copper = []            # (layer, shape, net)
        for p in s.board["pads"]:
            if p.th: p.layers = set(LAYERS)
            for L in p.layers:
                if L in LAYERS: s.copper.append((L, pad_shape(p), p.net or f"__npth_{p.ref}", ("hole:" if p.kind == "np_thru_hole" else "pad:") + p.ref))
        s.keepout = {L: np.zeros((s.g.H, s.g.W), bool) for L in LAYERS}
        s.segments, s.vias, s.zones, s.failed = [], [], [], []
        s.done_nets = set()
        t = s.board["text"]; nets = s.board["nets"]
        for g in s.board["tree"]:
            if not (isinstance(g, list) and g and g[0] in ("segment", "via")): continue
            net = nets[int(pm.kid(g, "net")[1])]
            if g[0] == "segment":
                a, b = pm.kid(g, "start"), pm.kid(g, "end"); w = float(pm.kid(g, "width")[1]); L = pm.kid(g, "layer")[1].split(".")[0]
                A, B = (float(a[1]), float(a[2])), (float(b[1]), float(b[2]))
                s.segments.append((A, B, w, L, net)); s.copper.append((L, ("capsule", A, B, w / 2), net, "track"))
            else:
                a = pm.kid(g, "at"); x, y = float(a[1]), float(a[2]); d = float(pm.kid(g, "size")[1])
                s.vias.append((x, y, net))
                for L in LAYERS: s.copper.append((L, ("circ", (x, y), None, d / 2), net, "via"))
            s.done_nets.add(net)
        s.board["text"] = strip_tracks(s.board["text"])
        s.k = 0
    def uid(s): s.k += 1; return str(uuid.uuid5(NS, f"{s.which}|{s.k}"))
    def blocked(s, net, half, ignore_tracks=False):
        """per layer: cells where a track of half-width `half` of `net` would violate clearance; plus via mask"""
        E0 = s.g.outside.copy()
        for sh in s.g.edge_shapes: s.g.paint(E0, sh, EDGE + half + MARGIN)     # edge clearance from the track's outer edge
        B = {L: E0 | s.keepout[L] for L in LAYERS}
        V = np.zeros((s.g.H, s.g.W), bool)
        for (L, sh, n, kind) in s.copper:
            if n == net: continue
            if ignore_tracks and kind in ("track", "via") and short(n) not in s.fixed_nets(): continue
            # extra spacing (sensing node vs GND) only against tracks/vias and electrode copper, not IC pins
            ex = extra_clear(s.cfg, net, n) if kind in ("track", "via") else 0.0
            if kind.startswith("hole:"): ex = max(ex, 0.25 - CLR)
            s.g.paint(B[L], sh, half + CLR + MARGIN + ex)
            s.g.paint(V, sh, VIA_D / 2 + CLR + MARGIN + ex)
        for L in LAYERS: V |= B[L]
        V |= s.g.edge_block
        for L in LAYERS: V |= s.keepout[L]
        for (L, sh, n, kind) in s.copper:          # own-net vias: drill-to-drill >= 0.5 mm
            if n == net and kind == "via" and L == LAYERS[0]: s.g.paint(V, ("circ", sh[1], None, 0.0), VIA_DRILL + 0.5 + MARGIN)
        # via must also keep clear of the edge by EDGE + radius
        E = np.zeros_like(V)
        for sh in s.g.edge_shapes: s.g.paint(E, sh, EDGE + VIA_D / 2)
        return B, V | E
    def pad_cells(s, p):
        cells = []
        hw, hh = max(p.w / 2 - 0.05, 0.02), max(p.h / 2 - 0.05, 0.02)
        i0, i1, j0, j1 = s.g.window(p.x - hw, p.y - hh, p.x + hw, p.y + hh)
        for i in range(i0, i1):
            for j in range(j0, j1):
                x, y = s.g.xy(i, j)
                if abs(x - p.x) <= hw and abs(y - p.y) <= hh:
                    for L in p.layers:
                        if L in LAYERS: cells.append((LAYERS.index(L), i, j))
        if not cells:
            i, j = s.g.ij(p.x, p.y)
            cells = [(LAYERS.index(L), i, j) for L in p.layers if L in LAYERS]
        return cells
    def astar(s, sources, targets, B, V, tgt_xy):
        H, W = s.g.H, s.g.W; HW = H * W
        NL = len(LAYERS)
        blk = bytearray(np.concatenate([B[L].ravel() for L in LAYERS]).astype(np.uint8).tobytes())
        vblk = V.ravel().astype(np.uint8).tobytes()
        tset = set()
        for (l, i, j) in targets:
            k = l * HW + i * W + j
            if not blk[k]: tset.add(k)
        if not tset:                                   # tiny pad fully inside foreign clearance: allow its cells
            for (l, i, j) in targets: k = l * HW + i * W + j; tset.add(k); blk[k] = 0
        INF = float("inf")
        gs = {}; came = {}
        tc = list({(int(x), int(y)) for (x, y) in tgt_xy})
        if len(tc) > 24: tc = tc[::max(1, len(tc) // 24)]
        HWT = s.cfg.get("hweight", 1.0)
        def h(i, j):
            best = INF
            for (tj, ti) in tc:
                dx = tj - j if tj > j else j - tj; dy = ti - i if ti > i else i - ti
                v = (dx + 0.4142 * dy) if dx > dy else (dy + 0.4142 * dx)
                if v < best: best = v
            return best * HWT
        pq = []
        srcs = [(l, i, j) for (l, i, j) in sources if not blk[l * HW + i * W + j]] or list(sources)
        for (l, i, j) in srcs:
            k = l * HW + i * W + j; blk[k] = 0; gs[k] = 0.0; heapq.heappush(pq, (h(i, j), 0.0, k))
        PEN = float(os.environ.get("ROUTE_DIRPEN", "1.6"))
        IN = float(os.environ.get("ROUTE_INNER_COST", "1.4"))
        D8L = (((0, 1, 1.0), (0, -1, 1.0), (1, 0, PEN), (-1, 0, PEN), (1, 1, 1.5), (1, -1, 1.5), (-1, 1, 1.5), (-1, -1, 1.5)),
               ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, PEN), (0, -1, PEN), (1, 1, 1.5), (1, -1, 1.5), (-1, 1, 1.5), (-1, -1, 1.5)),
               ((0, 1, IN), (0, -1, IN), (1, 0, IN), (-1, 0, IN), (1, 1, 1.5 * IN), (1, -1, 1.5 * IN), (-1, 1, 1.5 * IN), (-1, -1, 1.5 * IN)))
        n = 0
        while pq:
            f, gc, k = heapq.heappop(pq)
            if gc > gs.get(k, INF): continue
            if k in tset:
                path = [k]
                while path[-1] in came: path.append(came[path[-1]])
                out = []
                for q in reversed(path):
                    l, r = divmod(q, HW); i, j = divmod(r, W); out.append((l, i, j))
                return out
            n += 1
            if n > s.cfg.get("cap", 250000): return None
            l, r = divmod(k, HW); i, j = divmod(r, W); base = l * HW
            for di, dj, c in D8L[l]:
                ni, nj = i + di, j + dj
                if 0 <= ni < H and 0 <= nj < W:
                    nk = base + ni * W + nj
                    if blk[nk]: continue
                    if di and dj and blk[base + (i + di) * W + j] and blk[base + i * W + j + dj]: continue
                    ng = gc + c
                    if ng < gs.get(nk, INF):
                        gs[nk] = ng; came[nk] = k
                        heapq.heappush(pq, (ng + h(ni, nj), ng, nk))
            if vblk[r]: continue
            for l2 in range(NL):
                if l2 == l: continue
                ok = l2 * HW + r
                if not blk[ok]:
                    ng = gc + VIA_COST
                    if ng < gs.get(ok, INF):
                        gs[ok] = ng; came[ok] = k
                        heapq.heappush(pq, (ng + h(i, j), ng, ok))
        return None
    def commit(s, net, path, w):
        """path cells -> straight segments + vias; register copper"""
        pts = [(l, s.g.xy(i, j)) for (l, i, j) in path]
        runs, cur = [], [pts[0]]
        for p in pts[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur); cur = [p]
                vx, vy = p[1]; s.vias.append((vx, vy, net))
                for LL in LAYERS: s.copper.append((LL, ("circ", (vx, vy), None, VIA_D / 2), net, "via"))
            else:
                cur.append(p)
        runs.append(cur)
        for run in runs:
            L = LAYERS[run[0][0]]; xy = [q[1] for q in run]
            if len(xy) == 1: continue
            keep = [xy[0]]
            for a, b, c in zip(xy, xy[1:], xy[2:]):
                d1 = (round((b[0] - a[0]) / G), round((b[1] - a[1]) / G)); d2 = (round((c[0] - b[0]) / G), round((c[1] - b[1]) / G))
                if d1 != d2: keep.append(b)
            keep.append(xy[-1])
            for a, b in zip(keep, keep[1:]):
                s.segments.append((a, b, w, L, net))
                s.copper.append((L, ("capsule", a, b, w / 2), net, "track"))
    def route_net(s, net, pads, ignore=False):
        w0 = width_for(s.cfg, net)
        smd = [min(p.w, p.h) for p in pads if not p.th]
        if smd and min(smd) < w0: w0 = max(0.2, round(min(smd), 2))      # never wider than the narrowest pad
        for w in sorted({w0, max(0.2, min(w0, 0.3)), 0.2}, reverse=True):
            B, V = s.blocked(net, w / 2, ignore)
            tree = s.pad_cells(pads[0]); todo = list(pads[1:]); ok = True
            snapshot = (len(s.segments), len(s.vias), len(s.copper))
            while todo:
                tgts = {}
                for p in todo:
                    for c in s.pad_cells(p): tgts[c] = p
                txy = [(j, i) for (_, i, j) in tgts]
                path = s.astar(tree, list(tgts), B, V, txy)
                if not path: ok = False; break
                s.commit(net, path, w)
                hit = tgts[path[-1]]
                todo.remove(hit)
                tree = list(set(tree) | set(path) | set(s.pad_cells(hit)))
                B, V = s.blocked(net, w / 2, ignore)
            if ok: return w
            # roll back partial copper of this attempt
            s.segments, s.vias, s.copper = s.segments[:snapshot[0]], s.vias[:snapshot[1]], s.copper[:snapshot[2]]
        s.failed.append(net); return None
    def gnd_stubs(s, net, pads):
        """each GND SMD pad: shortest path to a free via site within 3 mm, then a via (pours do the rest)"""
        w = 0.3; fails = []
        for p in pads:
            if p.th or len(p.layers) == 2: continue
            B, V = s.blocked(net, w / 2)
            src = s.pad_cells(p)
            near = [v for v in s.vias if v[2] == net and abs(v[0] - p.x) < 1.6 and abs(v[1] - p.y) < 1.6]
            if near:                                      # reuse a neighbour's via: short track to it, no new via
                vx, vy, _ = min(near, key=lambda v: (v[0] - p.x) ** 2 + (v[1] - p.y) ** 2)
                vi, vj = s.g.ij(vx, vy); l0 = src[0][0]
                path = s.astar(src, [(l0, vi, vj)], B, V, [(vj, vi)])
                if path: s.commit(net, path, w); continue
            _, ci, cj = src[0]; R = int(3.0 / G)
            i0, i1 = max(0, ci - R), min(s.g.H, ci + R + 1); j0, j1 = max(0, cj - R), min(s.g.W, cj + R + 1)
            l = src[0][0]
            ii, jj = np.nonzero(~V[i0:i1, j0:j1] & ~B[LAYERS[l]][i0:i1, j0:j1])
            tg = [(l, int(a) + i0, int(b) + j0) for a, b in zip(ii, jj)]
            # vias must not sit on the pad itself (via-in-pad): drop targets inside the pad
            tg = [t for t in tg if not (abs(s.g.xy(t[1], t[2])[0] - p.x) < p.w / 2 + VIA_D / 2 and abs(s.g.xy(t[1], t[2])[1] - p.y) < p.h / 2 + VIA_D / 2)]
            if not tg: fails.append(f"{p.ref}.{p.num}"); continue
            tg.sort(key=lambda t: (t[1] - ci) ** 2 + (t[2] - cj) ** 2); tg = tg[:400]
            path = s.astar(src, tg, B, V, [(t[2], t[1]) for t in tg[:24]])
            if not path: fails.append(f"{p.ref}.{p.num}"); continue
            s.commit(net, path, w)
            vx, vy = s.g.xy(path[-1][1], path[-1][2]); s.vias.append((vx, vy, net))
            for L in LAYERS: s.copper.append((L, ("circ", (vx, vy), None, VIA_D / 2), net, "via"))
        if fails: print(f"  {short(net)} pads without a via to the plane:", fails)
        return fails
    # ---------------- rip-up and reroute ----------------
    def fixed_nets(s): return set(s.cfg.get("planes", {}).values()) | {"GND"}     # stitching copper, never ripped
    def snapshot(s): return (list(s.segments), list(s.vias), list(s.copper), list(s.failed))
    def restore(s, snap): s.segments, s.vias, s.copper, s.failed = (list(x) for x in snap)
    def rip(s, net):
        s.segments = [x for x in s.segments if x[4] != net]
        s.vias = [x for x in s.vias if x[2] != net]
        s.copper = [c for c in s.copper if not (c[2] == net and c[3] in ("track", "via"))]
    @staticmethod
    def _segd(a, b, c, d):
        def ps(px, py, ax, ay, bx, by):
            vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
            t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L2))
            return math.hypot(px - ax - t * vx, py - ay - t * vy)
        return min(ps(*a, *c, *d), ps(*b, *c, *d), ps(*c, *a, *b), ps(*d, *a, *b))
    def _as_seg(s, sh):
        if sh[0] == "capsule": return sh[1], sh[2], sh[3]
        if sh[0] == "circ": return sh[1], sh[1], sh[3]
        return None
    def conflicts(s, net, newcop):
        hits = set()
        others = [c for c in s.copper if c[3] in ("track", "via") and c[2] != net and short(c[2]) not in s.fixed_nets()]
        for (L, sh, n, k) in newcop:
            A = s._as_seg(sh)
            if not A: continue
            for (L2, sh2, n2, k2) in others:
                if L2 != L or n2 in hits: continue
                B = s._as_seg(sh2)
                if abs(A[0][0] - B[0][0]) > 30 and abs(A[1][0] - B[1][0]) > 30: continue
                if s._segd(A[0], A[1], B[0], B[1]) - A[2] - B[2] < CLR + MARGIN: hits.add(n2)
        return hits
    def ripup(s, bynet, deadline):
        for rnd in range(6):
            if not s.failed or time.time() > deadline: break
            improved = False
            for f in list(s.failed):
                if time.time() > deadline: break
                if f not in s.failed: continue
                before = s.snapshot(); nfail = len(s.failed)
                s.failed.remove(f)
                n0 = len(s.copper)
                if not s.route_net(f, sorted(bynet[f], key=lambda p: (p.x, p.y)), ignore=True):
                    s.restore(before); continue
                hits = s.conflicts(f, s.copper[n0:])
                s.restore(before); s.failed.remove(f)
                if not hits or len(hits) > int(os.environ.get("ROUTE_MAXHITS", "4")): s.restore(before); continue
                for h in hits: s.rip(h)
                ok = s.route_net(f, sorted(bynet[f], key=lambda p: (p.x, p.y)))
                for h in sorted(hits, key=lambda n: len(bynet[n])):
                    s.route_net(h, sorted(bynet[h], key=lambda p: (p.x, p.y)))
                if len(s.failed) < nfail:
                    improved = True
                    print(f"  rip-up: {short(f)} routed by moving {[short(h) for h in hits]} -> failed now {[short(x) for x in s.failed]}")
                else:
                    s.restore(before)
            if not improved: break
    def add_keepouts(s):
        b = s.board
        if s.which == "probe":
            for ref in ("E1", "E2"):
                ps = [p for p in b["pads"] if p.ref == ref]
                x1 = min(p.x - p.w / 2 for p in ps) - 2; x2 = max(p.x + p.w / 2 for p in ps) + 2
                y1 = min(p.y - p.h / 2 for p in ps) - 2; y2 = max(p.y + p.h / 2 for p in ps) + 2
                s.zones.append(("keepout_pour", "F.Cu", [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], f"no pour around electrode {ref}"))
        if s.which == "head":
            fp = b["fps"]["U4"]          # LCSC footprint: antenna meander at local y -12.8 .. -7.75 (module top)
            assert fp["rot"] == 0 and fp["side"] == "F", "antenna keepout assumes U4 at rotation 0 on top"
            ant = [(fp["x"] - 8.7, s.g.y0 - 1), (fp["x"] + 8.8, s.g.y0 - 1), (fp["x"] + 8.8, fp["y"] - 7.6), (fp["x"] - 8.7, fp["y"] - 7.6)]
            s.zones.append(("keepout_all", None, ant, "ESP32 antenna: no copper"))
            for L in LAYERS:
                i0, i1, j0, j1 = s.g.window(ant[0][0], ant[0][1], ant[2][0], ant[2][1])
                s.keepout[L][i0:i1, j0:j1] = True
    def run(s):
        t0 = time.time()
        s.add_keepouts()
        bynet = {}
        s.offboard = []
        for p in s.board["pads"]:
            i, j = s.g.ij(p.x, p.y)
            if not (0 <= i < s.g.H and 0 <= j < s.g.W) or (s.g.edge_block[i, j] and not any(s.g.edge_block[i, jj] == False for jj in range(max(0, j - 2), min(s.g.W, j + 3)))):
                if p.net and not p.net.startswith("unconnected"): s.offboard.append(f"{p.ref}.{p.num}")
                continue
            if p.net and not p.net.startswith("unconnected"): bynet.setdefault(p.net, []).append(p)
        if s.offboard: print("  pads outside the board, not routed:", s.offboard)
        nets = [n for n, ps in bynet.items() if len(ps) > 1]
        first = [n for key in s.cfg["order_first"] for n in nets if short(n) == key]
        rest = sorted((n for n in nets if n not in first and short(n) != "GND"),
                      key=lambda n: (max(p.x for p in bynet[n]) - min(p.x for p in bynet[n])) + (max(p.y for p in bynet[n]) - min(p.y for p in bynet[n])))
        gnd = [n for n in nets if short(n) == "GND"]
        rest = [n for n in rest if n not in gnd]
        first = [n for n in first if n not in gnd]
        if "GND" in s.cfg["order_first"]:      # explicit position of GND inside order_first
            k = s.cfg["order_first"].index("GND")
            pre = [n for n in first if s.cfg["order_first"].index(short(n)) < k]
            post = [n for n in first if n not in pre]
            order = pre + gnd + post + rest
        else:
            order = first + rest + gnd
        if os.environ.get("ROUTE_CONTINUE"):
            order = [n for n in order if n not in s.done_nets and n != "__GND_STUBS__" and short(n) not in (set(s.cfg.get("planes", {}).values()) | {"GND"})]
        order = [n for n in order if n not in s.done_nets]
        only = [x for x in os.environ.get("ROUTE_ONLY", "").split(",") if x]
        if only: order = [n for n in order if short(n) in only or n == "__GND_STUBS__"]
        pri = [x for x in os.environ.get("ROUTE_FIRST", "").split(",") if x]
        if pri: order = [n for k in pri for n in order if short(n) == k] + [n for n in order if short(n) not in pri]
        budget = float(os.environ.get("ROUTE_BUDGET", "1e9")); s.remaining = []
        widths = {}
        PLN = set(s.cfg.get("planes", {}).values()) | {"GND"}
        if s.cfg.get("gnd_stubs") and not only and not os.environ.get("ROUTE_CONTINUE"):
            order = [n for n in order if short(n) not in PLN]
            k = len([n for n in order if short(n) in s.cfg["order_first"]])
            order = order[:k] + ["__GND_STUBS__"] + order[k:]
        for net in order:
            if net == "__GND_STUBS__":
                s.gnd_stub_fails = []
                for g in [n for n in bynet if short(n) in PLN]:
                    s.gnd_stub_fails += s.gnd_stubs(g, bynet[g])
                continue
            if time.time() - t0 > budget: s.remaining.append(short(net)); continue
            ps = sorted(bynet[net], key=lambda p: (p.x, p.y))
            widths[net] = s.route_net(net, ps)
        s.widths = widths
        if os.environ.get("ROUTE_RIPUP") and s.failed:
            s.ripup(bynet, t0 + float(os.environ.get("ROUTE_RIPUP")))
        if s.remaining: print("  NOT ATTEMPTED (time budget), rerun on the output:", s.remaining)
        order = [n for n in order if n != "__GND_STUBS__"]
        print(f"{s.which}: {len(order)} nets this run, routed {len(order) - len(set(s.failed)) - len(s.remaining)}, failed {len(s.failed)} {[short(n) for n in s.failed]}, "
              f"{len(s.segments)} segments, {len(s.vias)} vias, {time.time() - t0:.0f} s")
        narrowed = {short(n): w for n, w in widths.items() if w and w < width_for(s.cfg, n)}
        if narrowed: print("  narrowed to fit:", narrowed)
    def write(s, out):
        t = s.board["text"]; nid = {v: k for k, v in s.board["nets"].items()}
        items = []
        for (a, b, w, L, net) in s.segments:
            items.append(f'\t(segment (start {a[0]:.4f} {a[1]:.4f}) (end {b[0]:.4f} {b[1]:.4f}) (width {w}) (layer "{CU[L]}") (net {nid[net]}) (uuid "{s.uid()}"))')
        for (x, y, net) in s.vias:
            items.append(f'\t(via (at {x:.4f} {y:.4f}) (size {VIA_D}) (drill {VIA_DRILL}) (layers "F.Cu" "B.Cu") (net {nid[net]}) (uuid "{s.uid()}"))')
        polys = pm.chain(s.board["edge_polylines"])
        outer = max(polys, key=len)
        if '(name "GND F")' in t: s.zones = []
        gnd = [n for n in s.board["nets"].values() if short(n) == "GND"][0]
        pts = " ".join(f"(xy {x:.4f} {y:.4f})" for x, y in outer[:-1])
        for L, pn in ([] if '(name "GND F")' in t else [(x, gnd) for x in ("F.Cu", "B.Cu")] + [(x, [m for m in s.board["nets"].values() if short(m) == y][0]) for x, y in s.cfg.get("planes", {}).items()]):
            items.append(f'\t(zone (net {nid[pn]}) (net_name "{pn}") (layer "{L}") (uuid "{s.uid()}") (name "{short(pn)} {L.split(".")[0]}") (hatch edge 0.5)\n'
                         f'\t\t(connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)\n'
                         f'\t\t(fill (thermal_gap 0.3) (thermal_bridge_width 0.4) (island_removal_mode 1) (island_area_min 2))\n'
                         f'\t\t(polygon (pts {pts})))')
        for kind, L, poly, name in s.zones:
            pp = " ".join(f"(xy {x:.4f} {y:.4f})" for x, y in poly)
            lay = ('(layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu")' if s.cfg.get("planes") else '(layers "F.Cu" "B.Cu")') if L is None else f'(layer "{L}")'
            ko = ("(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))"
                  if kind == "keepout_all" else "(keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))")
            items.append(f'\t(zone (net 0) (net_name "") {lay} (uuid "{s.uid()}") (name "{name}") (hatch edge 0.5)\n'
                         f'\t\t(connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)\n\t\t{ko}\n'
                         f'\t\t(fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n\t\t(polygon (pts {pp})))')
        body = t.rstrip()
        assert body.endswith(")")
        new = body[:-1].rstrip() + "\n" + "\n".join(items) + "\n)\n"
        open(out, "w", encoding="utf-8").write(new)

if __name__ == "__main__":
    which = sys.argv[1]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", CFG[which]["folder"], CFG[which]["folder"] + ".kicad_pcb")
    if "--in" in sys.argv: path = sys.argv[sys.argv.index("--in") + 1]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    r = Router(which, path)
    r.run()
    if out: r.write(out); print("written", out)
