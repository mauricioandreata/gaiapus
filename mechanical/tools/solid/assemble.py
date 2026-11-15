"""Assembled stake: case (SDF meshes) + boards (.glb from KiCad) + tube, tip, panel, antenna.
Usage: python3 assemble.py out.glb [voxel_mm=0.45]   (needs numpy, scikit-image)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
import math, numpy as np, params as P, parts
from sdf import mesh, volume
from prims import box, cyl, merge
from gltf import GLB
NODE = os.path.join(REPO, "hardware", "gaiapus-node", "gaiapus-node.glb")
PROBE = os.path.join(REPO, "hardware", "gaiapus-probe", "gaiapus-probe.glb")
H = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45

def W(v):   # case frame mm -> glb frame of the KiCad export (m): X = kicad x, Y = up (PCB bottom = 0), Z = kicad y
    v = np.asarray(v, float); return np.stack([(v[:, 0] + P.KX) / 1000, (v[:, 2] - P.Z_PCB_BOT) / 1000, (v[:, 1] + P.KY) / 1000], 1)
def add(g, name, vf, mat, smooth=True, parent=None):
    v, f = vf; w = W(v)
    if volume(w, f) < 0: f = f[:, ::-1]
    return g.mesh(name, w, f, mat, smooth, parent)

g = GLB()
OL = g.material("ASA olive matt", (0.30, 0.36, 0.24, 1), 0.85)
OL2 = g.material("ASA olive lid", (0.33, 0.39, 0.26, 1), 0.85)
BLK = g.material("black rubber", (0.04, 0.04, 0.04, 1), 0.9)
PVC = g.material("PVC tube (x-ray)", (0.30, 0.36, 0.24, 0.38), 0.6)
PAN = g.material("solar cells", (0.06, 0.10, 0.28, 1), 0.25, 0.3)
CLR = g.material("acrylic rod", (0.85, 0.95, 1.0, 0.6), 0.1)
STEEL = g.material("stainless", (0.75, 0.75, 0.75, 1), 0.35, 0.9)
BRASS = g.material("brass", (0.80, 0.65, 0.30, 1), 0.4, 0.9)
WHITE = g.material("label", (0.95, 0.95, 0.93, 1), 0.6)
SOIL = g.material("soil line", (0.36, 0.25, 0.16, 0.45), 1.0)
LEDC = [g.material(n, c + (1,), 0.3) for n, c in (("LED green", (0.2, 0.85, 0.25)), ("LED yellow", (0.98, 0.85, 0.1)), ("LED red", (0.95, 0.15, 0.1)))]

root = g.node("Gaiapus stake (rev B)")
case = g.node("case", parent=root)
for name, mat in (("base", OL), ("lid", OL2), ("button", BLK)):
    v, f = mesh(getattr(parts, name), *parts.BOUNDS[name], H if name != "button" else 0.2)
    add(g, name, (v, f), mat, True, case); print(name, len(f), flush=True)
t = P.Z_TOP; px, py = P.PANEL_C
add(g, "solar panel 68x37", box(px - 34, py - 18.5, t - P.PANEL_REC, px + 34, py + 18.5, t - P.PANEL_REC + P.PANEL_T), PAN, False, case)
for k, (x, y) in enumerate(P.LEDS):
    add(g, "LED rod %d" % (k + 1), cyl("z", (x, y), P.LED_ROD_D / 2, P.ROD_BOT, t - 0.05, 20), CLR, True, case)
    add(g, "LED cap %d" % (k + 1), cyl("z", (x, y), P.LED_ROD_D / 2 - 0.05, t - 0.05, t - 0.02, 20), LEDC[k], True, case)
for k, (x, y) in enumerate(P.SCREW_POS):
    add(g, "M3x30 #%d" % (k + 1), merge(cyl("z", (x, y), 2.75, P.CB_DEPTH - 2.0, P.CB_DEPTH, 24), cyl("z", (x, y), 1.5, P.CB_DEPTH, P.CB_DEPTH + 30, 16)), STEEL, True, case)
    add(g, "insert #%d" % (k + 1), cyl("z", (x, y), P.INSERT_D / 2 - 0.05, P.Z_MEET + 0.1, P.Z_MEET + P.INSERT_L, 18), BRASS, True, case)
gx, gy = P.GLAND[:2]
add(g, "PG7 gland", merge(cyl("z", (gx, gy), 8.5, -9, 0, 6), cyl("z", (gx, gy), 7.0, -15, -9, 24), cyl("z", (gx, gy), 3.0, -60, -15, 16),
                          cyl("z", (gx, gy), 7.5, P.FLOOR, P.FLOOR + 4, 6)), BLK, False, case)
sx, sy, sz, _ = P.SMA
add(g, "SMA + hinged antenna", merge(cyl("x", (sy, sz), 3.2, sx - 8, sx + 6, 20), cyl("x", (sy, sz), 4.6, P.IN_X - 4, P.IN_X - 0.01, 6),
                                     cyl("x", (sy, sz), 5.0, sx + 6, sx + 15, 24), cyl("z", (sx + 10.5, sy), 5.0, sz + 5, sz + 95, 24, 4.2)), BLK, True, case)
qw, qh, qy, qz, qd = P.QR
add(g, "QR label", box(-P.OUT_X + qd - 0.25, qy - qw / 2 + 0.3, qz - qh / 2 + 0.3, -P.OUT_X + qd - 0.05, qy + qw / 2 - 0.3, qz + qh / 2 - 0.3), WHITE, False, case)
rng = np.random.default_rng(7); qr = []
for a in range(11):
    for b in range(11):
        corner = (a < 3 and b < 3) or (a < 3 and b > 7) or (a > 7 and b < 3)
        if corner or rng.random() < 0.45:
            y0 = qy - 11 + a * 2; z0 = qz - 11 + b * 2
            qr.append(box(-P.OUT_X + qd - 0.3, y0, z0, -P.OUT_X + qd - 0.24, y0 + 2, z0 + 2))
add(g, "QR code", merge(*qr), BLK, False, case)
add(g, "USB-C plug", merge(box(P.USBC[0] - 5.8, P.OUT_Y1 - 3.8, P.USB_Z - 3.1, P.USBC[0] + 5.8, P.OUT_Y1 + 0.6, P.USB_Z + 3.1),
                           box(P.USBC[0] - 3, P.OUT_Y1 + 0.6, P.USB_Z - 4.5, P.USBC[0] + 3, P.OUT_Y1 + 1.6, P.USB_Z - 2.0)), BLK, False, case)
CELL = g.material("LiFePO4 cell", (0.18, 0.45, 0.70, 1), 0.4, 0.2)
add(g, "18650 LiFePO4 cell", merge(cyl("x", (P.BATT_CY, P.CELL_ZC), P.CELL_D / 2, -32.5, 32.5, 48), cyl("x", (P.BATT_CY, P.CELL_ZC), 3.5, 32.5, 33.5, 24)), CELL, True, case)
# stake
stake = g.node("stake", parent=root)
add(g, "PVC tube D32 x 470", cyl("z", (0, P.CY), P.TUBE_OD / 2, -P.TUBE_LEN + parts.TIP_SOCKET_DEPTH - 0.5 - 0.0 - parts.TIP_SOCKET_DEPTH, -0.05, 64), PVC, True, stake)
tv, tf = mesh(parts.tip, *parts.BOUNDS["tip"], 0.5); tv = tv + np.array([0, P.CY, -P.TUBE_LEN])
add(g, "tip (printed)", (tv, tf), OL, True, stake)
add(g, "soil line", cyl("z", (0, P.CY), 150, P.SOIL_Z - 0.6, P.SOIL_Z, 96), SOIL, True, root)
# boards: head as exported; probe stood up in the tube (copper side against the front wall, parts toward the axis)
head = g.node("head PCB (gaiapus-node.glb)", parent=root); g.merge(NODE, head)
yp = P.CY + math.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2) - 0.25
M = np.array([[-1, 0, 0, (111 + P.KX) / 1000], [0, 0, -1, (P.PROBE_TOP_Z + 50 - P.Z_PCB_BOT) / 1000], [0, -1, 0, (yp + P.KY) / 1000], [0, 0, 0, 1]])
probe = g.node("probe PCB (gaiapus-probe.glb)", matrix=M, parent=root); g.merge(PROBE, probe)
g.save(sys.argv[1]); print("saved", sys.argv[1])
