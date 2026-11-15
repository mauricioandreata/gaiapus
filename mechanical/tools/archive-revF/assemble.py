"""Assembled stake rev F (.glb): case + boards from KiCad + cell, tube, tip, panel, antenna, QR, soil line.
Usage: python3 assemble.py OUT.glb [voxel_mm]   (needs numpy, scikit-image)"""
import os, sys, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
REPO = os.environ.get("GAIAPUS_REPO", os.path.normpath(os.path.join(HERE, "..", "..", "..")))
import params as P, parts
from sdf import mesh, volume
from prims import box, cyl, merge
from gltf import GLB
NODE = os.path.join(REPO, "hardware", "gaiapus-node", "gaiapus-node.glb")
PROBE = os.path.join(REPO, "hardware", "gaiapus-probe", "gaiapus-probe.glb")
H = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
NO_BOARDS = "--no-boards" in sys.argv

def W(v):
    v = np.asarray(v, float); return np.stack([(v[:, 0] + P.KX) / 1000, (v[:, 2] - P.Z_PCB_BOT) / 1000, (v[:, 1] + P.KY) / 1000], 1)
def add(g, name, vf, mat, smooth=True, parent=None):
    v, f = vf; w = W(v)
    if volume(w, f) < 0: f = f[:, ::-1]
    return g.mesh(name, w, f, mat, smooth, parent)

def build(out):
    g = GLB()
    OL = g.material("ASA olive matt", (0.25, 0.30, 0.22, 1), 0.85)
    OL2 = g.material("ASA olive (cap)", (0.27, 0.32, 0.24, 1), 0.85)
    BLK = g.material("black", (0.05, 0.05, 0.05, 1), 0.8)
    BTN = g.material("button TPU", (0.10, 0.10, 0.10, 1), 0.7)
    PVC = g.material("PVC tube", (0.25, 0.30, 0.22, 1.0 if "--opaque" in sys.argv else 0.45), 0.6)
    PAN = g.material("solar cells", (0.05, 0.08, 0.22, 1), 0.2, 0.3)
    GRID = g.material("cell grid", (0.55, 0.62, 0.75, 1), 0.3, 0.6)
    WHITE = g.material("label", (0.95, 0.95, 0.93, 1), 0.6)
    STEEL = g.material("black-oxide steel", (0.08, 0.08, 0.08, 1), 0.5, 0.6)
    SOIL = g.material("soil line", (0.36, 0.25, 0.16, 0.45), 1.0)
    CELL = g.material("LiFePO4 cell", (0.18, 0.45, 0.70, 1), 0.4, 0.2)
    LEDM = [g.material(n, c, 0.2) for n, c in (("light green", (0.45, 0.95, 0.5, 0.85)), ("light yellow", (1.0, 0.9, 0.35, 0.85)), ("light red", (1.0, 0.35, 0.3, 0.85)))]
    root = g.node("Gaiapus stake (rev F)"); case = g.node("case", parent=root)
    for name, mat, h in (("base", OL, H), ("lid", OL2, H), ("button", BTN, 0.2), ("plunger", BLK, 0.25)):
        v, f = mesh(getattr(parts, name), *parts.BOUNDS[name], h); add(g, name, (v, f), mat, True, case)
    SMOKE = g.material("smoked light bar", (0.10, 0.12, 0.10, 0.92), 0.15)
    v, f = mesh(parts.light_bar, *parts.BOUNDS["light_bar"], 0.2)
    c = v[f].mean(1); zc = P.LED_LENS["zc"]
    on_face = np.abs(parts.cap_shape(c[:, 0], c[:, 1], c[:, 2])) < 0.35          # triangles on the outer lens face (follows the cap)
    spot = np.full(len(f), -1)
    for k, sx in enumerate(P.LED_SPOT_X):
        spot[on_face & (np.hypot(c[:, 0] - sx, c[:, 2] - zc) < P.LED_SPOT_D / 2)] = k
    add(g, "light bar (smoked PETG)", (v, f[spot < 0]), SMOKE, True, case)
    for k in range(3):
        GL = g.material("LED light %d" % k, [(0.3, 1.0, 0.35, 1), (1.0, 0.85, 0.15, 1), (1.0, 0.18, 0.12, 1)][k], 0.3, 0.0, [(0.2, 0.9, 0.25), (1.0, 0.75, 0.1), (1.0, 0.12, 0.08)][k])
        add(g, "LED light %d (lens area)" % (k + 1), (v, f[spot == k]), GL, True, case)
    # solar panel, in the sloped top frame
    yr = P.PANEL_C[1]
    def on_slope(v):
        v = v.copy(); s, h = v[:, 1].copy(), v[:, 2].copy(); yy, zz = P.from_local(s, h, yr); v[:, 1], v[:, 2] = yy, zz; return v
    pv, pf = box(-P.PANEL_W / 2, -P.PANEL_H / 2, -P.PANEL_REC, P.PANEL_W / 2, P.PANEL_H / 2, -P.PANEL_REC + P.PANEL_T)
    add(g, "solar panel", (on_slope(pv), pf), PAN, False, case)
    gl = []
    for i_ in range(1, 6):
        x = -P.PANEL_W / 2 + i_ * P.PANEL_W / 6; bv, bf = box(x - 0.25, -P.PANEL_H / 2 + 1.5, -P.PANEL_REC + P.PANEL_T, x + 0.25, P.PANEL_H / 2 - 1.5, -P.PANEL_REC + P.PANEL_T + 0.05); gl.append((on_slope(bv), bf))
    bv, bf = box(-P.PANEL_W / 2 + 1.5, -0.25, -P.PANEL_REC + P.PANEL_T, P.PANEL_W / 2 - 1.5, 0.25, -P.PANEL_REC + P.PANEL_T + 0.05); gl.append((on_slope(bv), bf))
    add(g, "panel grid", merge(*gl), GRID, False, case)
    # cell, screws
    add(g, "18650 LiFePO4", merge(cyl("x", (P.BATT_CY, P.CELL_ZC), P.CELL_D / 2, -32.5, 32.5, 48), cyl("x", (P.BATT_CY, P.CELL_ZC), 3.5, 32.5, 33.5, 24)), CELL, True, case)
    for k, (x, y) in enumerate(P.SCREW_POS):
        add(g, "screw %d" % k, merge(cyl("z", (x, y), 2.75, P.CB_SEAT - 2.0, P.CB_SEAT, 20), cyl("z", (x, y), 1.5, P.CB_SEAT, P.CB_SEAT + 12, 12)), STEEL, True, case)
    # antenna: SMA through the REAR wall + hinge + whip standing up behind the head
    sx, sy, sz, _ = P.SMA
    add(g, "antenna", merge(cyl("y", (sx, sz), 3.2, sy - 5, sy + 8, 20), cyl("y", (sx, sz), 4.6, P.IN_Y0 + 0.01, P.IN_Y0 + 4, 6),
                            cyl("y", (sx, sz), 4.8, sy - 13, sy - 5, 24), cyl("z", (sx, sy - 9), 4.8, sz + 4, sz + 70, 24, 4.4),
                            cyl("z", (sx, sy - 9), 4.4, sz + 70, sz + 76, 24, 2.5)), BLK, True, case)
    gx, gy = P.GLAND[:2]
    add(g, "PG7 gland + rain cable", merge(cyl("z", (gx, gy), 6.4, -6, 0, 6), cyl("z", (gx, gy), 5.5, -12, -6, 24), cyl("z", (gx, gy), 2.2, -70, -12, 16)), BLK, True, case)
    qw, qh, qy, qz, qd = P.QR; X0 = P.OUT_X - qd
    add(g, "QR label", box(X0 + 0.05, qy - qw / 2 + 0.4, qz - qh / 2 + 0.4, X0 + 0.25, qy + qw / 2 - 0.4, qz + qh / 2 - 0.4), WHITE, False, case)
    rng = np.random.default_rng(7); q = []
    for a_ in range(11):
        for b_ in range(9):
            if (a_ < 3 and b_ > 5) or (a_ > 7 and b_ > 5) or (a_ < 3 and b_ < 1) or rng.random() < 0.45:
                y0 = qy - 11 + a_ * 2; z0 = qz - 6 + b_ * 2; q.append(box(X0 + 0.25, y0, z0, X0 + 0.3, y0 + 2, z0 + 2))
    for i_ in range(8): q.append(box(X0 + 0.25, qy - 10 + i_ * 2.6, qz - 11, X0 + 0.3, qy - 8.6 + i_ * 2.6, qz - 8))   # "Gaiapus" text bar
    add(g, "QR code", merge(*q), BLK, False, case)
    add(g, "USB-C plug", merge(box(P.USBC[0] - 5.9, P.OUT_Y1 - 3.8, P.USB_Z - 3.2, P.USBC[0] + 5.9, P.OUT_Y1 + 0.4, P.USB_Z + 3.2)), BLK, False, case)
    stake = g.node("stake", parent=root)
    add(g, "PVC tube", cyl("z", (0, P.CY), P.TUBE_OD / 2, P.COLLAR_Z0 - (P.TUBE_LEN - P.SOCKET_DEPTH), P.COLLAR_Z0 + P.SOCKET_DEPTH - 0.1, 64), PVC, True, stake)
    tv, tf = mesh(parts.tip, *parts.BOUNDS["tip"], 0.5); tv = tv + np.array([0, P.CY, P.COLLAR_Z0 - (P.TUBE_LEN - P.SOCKET_DEPTH)])
    add(g, "tip", (tv, tf), OL, True, stake)
    add(g, "soil line", cyl("z", (0, P.CY), 150, P.SOIL_Z - 0.6, P.SOIL_Z, 96), SOIL, True, root)
    if not NO_BOARDS:
        head = g.node("head PCB", parent=root); g.merge(NODE, head)
        yp = P.CY + math.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2) - 0.25
        M = np.array([[-1, 0, 0, (111 + P.KX) / 1000], [0, 0, -1, (P.PROBE_TOP_Z + 50 - P.Z_PCB_BOT) / 1000], [0, -1, 0, (yp + P.KY) / 1000], [0, 0, 0, 1]])
        pr = g.node("probe PCB", matrix=M, parent=root); g.merge(PROBE, pr)
    g.save(out)

if __name__ == "__main__": build(sys.argv[1])
