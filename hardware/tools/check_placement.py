#!/usr/bin/env python3
"""Courtyard overlap / board-edge / mounting-hole check of a placed .kicad_pcb (approximate, bbox based)."""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autoplace import blocks, bbox
path, ox, oy, W, H = sys.argv[1], *map(float, sys.argv[2:6])
holes = [(ox + 4, oy + 4), (ox + W - 4, oy + 4), (ox + 4, oy + H - 4), (ox + W - 4, oy + H - 4)] if len(sys.argv) < 7 else []
t = open(path, encoding="utf-8").read()
import pcbmodel as pm
PADS = {}
for q in pm.load(path)["pads"]: PADS.setdefault(q.ref, []).append(q)
P = {}
for s, e in blocks(t):
    b = t[s:e]
    ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
    x, y, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    x1, y1, x2, y2 = bbox(b)
    if round(rot) % 180 == 90: x1, y1, x2, y2 = -y2, x1, -y1, x2
    if round(rot) % 360 == 180: x1, y1, x2, y2 = -x2, -y2, -x1, -y1
    side = "B" if '(layer "B.Cu")' in b[:200] else "F"
    for q in PADS.get(ref, []):                       # real pad rectangles (pads can stick out of the courtyard)
        x1, y1 = min(x1, q.x - q.w / 2 - 0.05 - x), min(y1, q.y - q.h / 2 - 0.05 - y)
        x2, y2 = max(x2, q.x + q.w / 2 + 0.05 - x), max(y2, q.y + q.h / 2 + 0.05 - y)
    P[ref] = (x + x1, y + y1, x + x2, y + y2, side, x2 - x1, y2 - y1)
bad = 0
refs = sorted(P)
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        A, B = P[a], P[b]
        if A[4] != B[4]: continue
        if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
            print(f"  overlap {a} / {b}"); bad += 1
for r, A in P.items():
    if r == "BT1": continue
    if A[0] < ox or A[1] < oy or A[2] > ox + W or A[3] > oy + H:
        print(f"  outside board: {r} {A[:4]}"); bad += 1
    for hx, hy in holes:
        cx, cy = min(max(hx, A[0]), A[2]), min(max(hy, A[1]), A[3])
        if (cx - hx) ** 2 + (cy - hy) ** 2 < 3.0 ** 2:
            print(f"  too close to M3 hole at ({hx},{hy}): {r}"); bad += 1
print("sizes:", {r: (round(P[r][5], 1), round(P[r][6], 1)) for r in ("U4", "U5", "J5", "J3", "BT1", "E1", "E2") if r in P})
print("RESULT:", "OK" if not bad else f"{bad} issue(s)")
