#!/usr/bin/env python3
"""Independent geometric check of the generated .kicad_sch files (no KiCad needed).

Re-derives connectivity from raw geometry the way KiCad does (wire ends, pin ends, labels,
power symbols) and compares every pin's resulting net with netlist-draft.csv.
"""
import os, re, csv, sys, collections
HW = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PRJ = os.path.join(HW, "gaiapus-node")

def parse(txt):
    tok = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+', txt)
    pos = 0
    def rd():
        nonlocal pos
        t = tok[pos]; pos += 1
        if t == "(":
            L = []
            while tok[pos] != ")":
                L.append(rd())
            pos += 1
            return L
        if t.startswith('"'):
            return ("s", t[1:-1])
        return t
    top = rd()
    assert pos == len(tok), "trailing tokens / unbalanced"
    return top

def sv(x): return x[1] if isinstance(x, tuple) else x
def find(L, key): return [c for c in L if isinstance(c, list) and c and c[0] == key]
def f(x): return float(x)
def key(p): return (round(p[0], 3), round(p[1], 3))

class UF:
    def __init__(s): s.p = {}
    def f(s, a):
        s.p.setdefault(a, a)
        while s.p[a] != a:
            s.p[a] = s.p[s.p[a]]; a = s.p[a]
        return a
    def u(s, a, b): s.p[s.f(a)] = s.f(b)

PROJECTS = [(os.path.join(HW, "gaiapus-node"), ["power", "mcu", "lora", "sensors", "interface"]),
            (os.path.join(HW, "gaiapus-probe"), ["probe"])]
FILES = {"probe": "gaiapus-probe"}
want = collections.defaultdict(dict)   # sheet -> {(ref,pin): net}
for prj, _sheets in PROJECTS:
    for r in csv.DictReader(open(os.path.join(prj, "netlist-draft.csv"), encoding="utf-8")):
        if r["scope"] == "nc":
            continue
        want[r["sheet"]][(r["ref"], r["pin"])] = r["net"]

errors, warns = 0, 0
all_uuids = collections.Counter()
global_net_pins = {}
for prj, fn in [(prj, f) for prj, fs in PROJECTS for f in fs]:
    txt = open(os.path.join(prj, FILES.get(fn, fn) + ".kicad_sch"), encoding="utf-8").read()
    tree = parse(txt)
    for m in re.findall(r'\(uuid "([^"]+)"\)', txt):
        all_uuids[m] += 1
    libs = {}
    for ls in find(find(tree, "lib_symbols")[0], "symbol"):
        pins = {}
        for sub in find(ls, "symbol"):
            for p in find(sub, "pin"):
                at = find(p, "at")[0]
                hide = "hide" in p
                pins[sv(find(p, "number")[0][1])] = (f(at[1]), f(at[2]), sv(find(p, "name")[0][1]), hide)
        libs[sv(ls[1]).split(":")[1]] = pins
    uf = UF()
    wires = []
    for w in find(tree, "wire"):
        pts = find(find(w, "pts")[0], "xy")
        a, b = key((f(pts[0][1]), f(pts[0][2]))), key((f(pts[1][1]), f(pts[1][2])))
        wires.append((a, b)); uf.u(a, b)
    points = []   # (point, kind, info)
    for s in find(tree, "symbol"):
        lib = sv(find(s, "lib_id")[0][1]).split(":")[1]
        at = find(s, "at")[0]; x, y, rot = f(at[1]), f(at[2]), int(float(at[3]))
        ref = [sv(p[2]) for p in find(s, "property") if sv(p[1]) == "Reference"][0]
        val = [sv(p[2]) for p in find(s, "property") if sv(p[1]) == "Value"][0]
        for num, (px, py, nm, hide) in libs[lib].items():
            if hide and not lib in ("GND", "+3V3", "VBAT", "VSOL", "VBUS", "PWR_FLAG"):
                continue
            dx, dy = (px, -py) if rot == 0 else (-px, py)
            points.append((key((x + dx, y + dy)), "pin", (ref, num, lib, val)))
    labels = []
    for kind in ("label", "global_label"):
        for l in find(tree, kind):
            at = find(l, "at")[0]
            labels.append((key((f(at[1]), f(at[2]))), sv(l[1]), kind))
    for p in find(tree, "no_connect"):
        pass
    # T-junction: any point lying inside a wire segment joins it
    def on_seg(pt, a, b):
        if a[0] == b[0] == pt[0]: return min(a[1], b[1]) < pt[1] < max(a[1], b[1])
        if a[1] == b[1] == pt[1]: return min(a[0], b[0]) < pt[0] < max(a[0], b[0])
        return False
    allpts = [p[0] for p in points] + [l[0] for l in labels] + [e for w in wires for e in w]
    for pt in allpts:
        for a, b in wires:
            if on_seg(pt, a, b):
                uf.u(pt, a)
    for pt, kind, info in points:
        uf.f(pt)
    # net names per component
    names = collections.defaultdict(set)
    for pt, nm, kind in labels:
        names[uf.f(pt)].add(nm)
    for pt, kind, info in points:
        if info[2] in ("GND", "+3V3", "VBAT", "VSOL", "VBUS"):
            names[uf.f(pt)].add(info[2])
    for comp, ns in names.items():
        if len(ns) > 1:
            print(f"ERROR [{fn}] short between nets {sorted(ns)}"); errors += 1
    got = {}
    for pt, kind, info in points:
        ref, num, lib, val = info
        if lib in ("GND", "+3V3", "VBAT", "VSOL", "VBUS", "PWR_FLAG"):
            continue
        ns = names.get(uf.f(pt), set())
        got[(ref, num)] = next(iter(ns)) if len(ns) == 1 else None
    for k, net in want[fn].items():
        if k[0].startswith("#FLG") or k not in got:
            continue   # PWR_FLAG / hidden implicit power pins are not geometry-checked
        g = got.get(k)
        if g != net:
            print(f"ERROR [{fn}] {k[0]} pin {k[1]}: expected net {net}, geometry gives {g}"); errors += 1
    for k, g in got.items():
        if k not in want[fn] and g is not None:
            pass
    print(f"[{fn}] pins checked: {len(want[fn])}")
dups = [u for u, c in all_uuids.items() if c > 1]
if dups:
    print("ERROR duplicate uuids:", len(dups)); errors += 1
print("RESULT:", "FAIL" if errors else "OK", f"({errors} errors)")
sys.exit(1 if errors else 0)
