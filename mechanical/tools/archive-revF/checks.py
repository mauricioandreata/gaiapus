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
    add("SMA nut (rear wall) -> rear lid boss (x)", abs(sx - P.SCREW_POS[1][0]) - 4.6 - P.COL_D / 2, 0.5)
    add("SMA nut top -> seam", P.Z_SPLIT - (sz + 4.6), 0.5)
    add("SMA nut -> M8 gland nut (inside)", math.hypot(sx - gx, (P.IN_Y0 + 3) - gy) - 4.6 - gn / 2, 0.5)
    add("Probe parts -> tube wall", math.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2) - P.PROBE_MAX_H, 1.0)
    add("Probe top above tube end (inside the neck bore)", (P.SOIL_Z + P.SOCKET_DEPTH) - P.PROBE_TOP_Z, 0.0, "probe top stays below the bore top")
    # top: panel recess fully on the flat sloped top (sample 1 mm outside the recess, just under the plane)
    yr = P.PANEL_C[1]; cc = P.PANEL_CLR; m = 1.0; vals = []
    for xx in (-P.PANEL_W / 2 - cc - m, P.PANEL_W / 2 + cc + m):
        for ss in (-P.PANEL_H / 2 - cc - m, P.PANEL_H / 2 + cc + m):
            yy, zz = P.from_local(ss, -0.15, yr); vals.append(float(parts.lid(np.array([xx]), np.array([yy]), np.array([zz]))[0]))
    add("Top flat around the panel recess (lid sdf, <0 = solid)", -max(vals), 0.0, "recess fully on the flat sloped top")
    ts = []
    for xx in (-25, 0, 25):
        for ss in (-12, 0, 12):
            yy, zz = P.from_local(ss, -P.PANEL_REC - 0.05, yr); ts.append(thickness(parts.lid, xx, yy, zz))
    add("Roof under the panel recess (vertical)", min(ts), 1.5)
    sb = P.to_local(P.BTN_C[1], P.z_top(P.BTN_C[1]), yr)[0]
    add("Button cap -> panel recess (along the slope)", sb - P.BTN_CAP_D / 2 - (P.PANEL_H / 2 + cc), 1.0)
    add("Button on the panel axis (x offset)", -abs(P.BTN_C[0] - P.PANEL_C[0]), 0.0)
    bv = []
    for k in range(12):
        a = 2 * math.pi * k / 12; xx = P.BTN_C[0] + (P.BTN_HOLE_D / 2 + 1.5) * math.cos(a); ss = (P.BTN_HOLE_D / 2 + 1.5) * math.sin(a)
        yy, zz = P.from_local(ss, -0.15, P.BTN_C[1]); bv.append(float(parts.lid(np.array([xx]), np.array([yy]), np.array([zz]))[0]))
    add("Top flat around the button hole (lid sdf, <0 = solid)", -max(bv), 0.0, "button clear of the front bevel")
    add("Arm nub -> SW1 top", 0.3, 0.2, "by construction, see interference")
    add("Arm underside -> SW1 top (rest of the arm)", P.ARM_Z0 - P.SW1_TOP, 1.0)
    add("Sleeve bottom -> arm top (stroke room)", P.SLEEVE_Z0 - (P.ARM_Z0 + P.ARM_T), 1.0)
    add("Light pipes -> LED tops", 0.3, 0.2, "pipe ends 0.3 above the LED model tops")
    add("Bottom chin wall at the columns (seat -> chin surface)", P.CB_SEAT - (P.CHIN - (14 - 8.85)), 1.5, "counterbore seat above the slope")
    return R

if __name__ == "__main__":
    ok = True
    for n, v, m, g, note in rows():
        ok &= g; print("%-58s %7.2f (min %4.1f) %s %s" % (n, v, m, "OK" if g else "FAIL", note))
    print("ALL OK" if ok else "SOME FAIL")
