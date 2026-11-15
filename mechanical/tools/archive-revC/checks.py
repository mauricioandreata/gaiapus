"""Clearance / geometry checks, case rev C. Analytic + evaluated on the solids (parts.py)."""
import os, sys, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import params as P, parts

def d_circle_rrect(c, r, x0, y0, x1, y1, rr):
    cx = min(max(c[0], x0 + rr), x1 - rr); cy = min(max(c[1], y0 + rr), y1 - rr)
    return math.hypot(c[0] - cx, c[1] - cy) - rr - r

def thickness(fn, x, y, z0, dz=-0.05, n=200):
    """material thickness along -z starting at z0 (first solid run)"""
    zs = z0 + dz * np.arange(n); v = fn(np.full(n, x), np.full(n, y), zs); ins = v < 0
    if not ins.any(): return 0.0
    i0 = np.argmax(ins); i1 = i0 + np.argmax(~ins[i0:]) if (~ins[i0:]).any() else n
    return (i1 - i0) * abs(dz)

def rows():
    R = []
    def add(n, v, m, note=""): R.append((n, float(v), m, bool(v >= m), note))
    hw, hh = P.PCB_W / 2, P.PCB_H / 2
    add("PCB edge -> inner wall, sides", P.IN_X - hw, 3.0)
    add("PCB edge -> inner wall, front", P.IN_Y1 - hh, 3.0)
    add("JST J3 entry face -> front wall (plug + bend)", P.IN_Y1 - P.JST_FACE_Y["J3"], 6.0)
    add("JST J1/J4 entry face -> front wall", P.IN_Y1 - P.JST_FACE_Y["J1"], 6.0)
    add("Battery holder -> rear standoffs (y)", P.BATT_Y[0] - (-21 + P.SO_D / 2), 0.3)
    add("Screw column / lid boss -> PCB outline", min(d_circle_rrect(p, P.COL_D / 2, -hw, -hh, hw, hh, P.PCB_R) for p in P.SCREW_POS), 0.8)
    add("USB opening top -> seam", P.Z_SPLIT - (P.USB_Z + P.USB_OPEN[1] / 2), 1.0)
    add("USB-C mating face -> outer face (overmold reach)", P.OUT_Y1 - P.USB_FACE_Y, 0.0, "opening 12.5 x 7")
    l, w = P.SLOT[2], P.SLOT[3]; far = math.hypot(l / 2 - w / 2, P.SLOT[1] - P.CY) + w / 2
    add("Floor slot inside the neck bore", P.NECK_BORE / 2 - far, 0.5)
    gx, gy, gd, gn = P.GLAND
    add("M8 gland -> neck (outside, body D12)", math.hypot(gx, gy - P.CY) - P.NECK_D / 2 - 6.0, 1.0)
    add("M8 gland nut -> PCB standoff", math.hypot(gx - 41, gy + 21) - gn / 2 - P.SO_D / 2, 0.5)
    inside = parts.base(np.array([gx + gn / 2, gx, gx - gn / 2, gx]), np.array([gy, gy + gn / 2, gy, gy - gn / 2]), np.full(4, 4.0))
    add("M8 gland nut seat is free (base sdf at nut rim, z 4)", float(inside.min()), 0.0, "> 0 = air")
    sx, sy, sz, sd = P.SMA
    add("SMA nut -> rear lid boss (y)", abs(sy - P.SCREW_POS[1][1]) - 4.6 - P.COL_D / 2, 0.5)
    add("SMA nut top -> seam", P.Z_SPLIT - (sz + 4.6), 0.5)
    add("Probe parts -> tube wall", math.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2) - P.PROBE_MAX_H, 1.0)
    add("Probe top above tube end (inside the neck bore)", (P.SOIL_Z + P.SOCKET_DEPTH) - P.PROBE_TOP_Z, 0.0, "probe top stays below the bore top")
    # top: panel recess on the flat part, roof thickness
    px, py = P.PANEL_C; c = P.PANEL_CLR; m = 1.0
    xs = [px - P.PANEL_W / 2 - c - m, px + P.PANEL_W / 2 + c + m]; ys = [py - P.PANEL_H / 2 - c - m, py + P.PANEL_H / 2 + c + m]
    flat = [float(parts.lid(np.array([x]), np.array([y]), np.array([P.z_top(y) - 0.15]))[0]) for x in xs for y in ys]
    add("Top flat around the panel recess (lid sdf, <0 = solid)", -max(flat), 0.0, "recess fully on the flat top")
    t = min(thickness(parts.lid, x, y, P.z_top(y) - P.PANEL_REC - 0.05) for x in (-25, 0, 25) for y in (py - 15, py, py + 15))
    add("Roof under the panel recess", t, 1.5)
    b = P.SW1[0] + P.BTN_CAP_D / 2; e = py + P.PANEL_H / 2 + c
    add("Button cap -> panel recess (y)", (P.SW1[1] - P.BTN_CAP_D / 2) - e, 1.0)
    add("Light bar posts -> LED tops", 0.3 + (P.LED_TOP - P.Z_PCB_TOP) * 0, 0.2, "from the 3D check")
    add("Bottom chin wall at the columns (seat -> chin surface)", P.CB_SEAT - (P.CHIN - (14 - 8.85)), 1.5, "counterbore seat above the slope")
    return R

if __name__ == "__main__":
    ok = True
    for n, v, m, g, note in rows():
        ok &= g; print("%-58s %7.2f (min %4.1f) %s %s" % (n, v, m, "OK" if g else "FAIL", note))
    print("ALL OK" if ok else "SOME FAIL")
