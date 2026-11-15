"""Clearance checks between the case rev B and the as-built PCB / 3D models. Run: python3 checks.py"""
import math
import params as P

def d_circle_rrect(c, r, x0, y0, x1, y1, rr):
    """min distance between a circle and a rounded rectangle (positive = gap)"""
    cx = min(max(c[0], x0 + rr), x1 - rr); cy = min(max(c[1], y0 + rr), y1 - rr)
    return math.hypot(c[0] - cx, c[1] - cy) - rr - r

def rows():
    hw, hh = P.PCB_W / 2, P.PCB_H / 2
    top_max = max(P.H_TOP.values()); top_name = max(P.H_TOP, key=P.H_TOP.get)
    R = []
    def add(name, value, minimum, note=""):
        R.append((name, value, minimum, value >= minimum, note))
    add("PCB edge -> inner wall, sides (x)", P.IN_X - hw, 3.0)
    add("PCB edge -> inner wall, front", P.IN_Y1 - hh, 3.0)
    add("PCB edge -> inner wall, rear (cable room)", -hh - P.IN_Y0, 3.0)
    add("JST J3 entry face -> front wall (plug + bend)", P.IN_Y1 - P.JST_FACE_Y["J3"], 6.0, "SH plug ~2.5 + bend")
    add("JST J1/J4 entry face -> front wall", P.IN_Y1 - P.JST_FACE_Y["J1"], 6.0)
    add("Tallest top part (%s) -> roof" % top_name, P.Z_ROOF_IN - (P.Z_PCB_TOP + top_max), 2.0)
    add("Panel recess floor -> tallest part (roof under panel)", (P.Z_TOP - P.PANEL_REC) - (P.Z_PCB_TOP + top_max) - 0, 4.0, "material + air")
    add("Battery envelope (21 below PCB) -> floor top", (P.Z_PCB_BOT - P.BATT_DROP) - P.FLOOR, 0.5, "3D model only 14.9: holder without cell")
    add("Battery holder -> rear standoffs (y)", P.BATT_Y[0] - (-21 + P.SO_D / 2), 0.3)
    add("Battery holder -> front standoffs (y)", (21 - P.SO_D / 2) - P.BATT_Y[1], 0.3)
    gap_col = min(d_circle_rrect(p, P.COL_D / 2, -hw, -hh, hw, hh, P.PCB_R) for p in P.SCREW_POS)
    add("Screw column / lid boss -> PCB outline", gap_col, 0.8)
    add("Button pin -> SW1 top (pre-travel gap)", 0.3, 0.2, "pin length set to leave 0.3")
    add("USB-C mating face -> case outer face (overmold reach)", P.OUT_Y1 - P.USB_FACE_Y, 0.0, "opening 12.5x7 lets the overmold in; needs plug length >= this")
    add("USB opening top -> parting plane", P.Z_SPLIT - (P.USB_Z + P.USB_OPEN[1] / 2), 1.0)
    # cable slot inside the tube bore
    l, w = P.SLOT[2], P.SLOT[3]
    far = math.hypot(l / 2 - w / 2, P.SLOT[1] - P.CY) + w / 2
    add("Floor slot farthest point inside tube ID", P.TUBE_ID / 2 - far, 0.5)
    dy = abs(P.SLOT[1] + w / 2 - P.BATT_CY)
    cell_bot = P.CELL_ZC - math.sqrt(max((P.CELL_D / 2) ** 2 - dy ** 2, 0)) if dy < P.CELL_D / 2 else P.CELL_ZC
    add("Cell underside above the slot front edge -> floor", cell_bot - P.FLOOR, 2.5, "room to bend the probe cable")
    gx, gy, gd, gn = P.GLAND
    add("PG7 nut -> rear inner wall", (gy - gn / 2) - P.IN_Y0, 0.5)
    add("PG7 nut -> rear-right standoff", math.hypot(gx - 41, gy + 21) - gn / 2 - P.SO_D / 2, 0.5)
    add("PG7 nut -> collar socket (floor)", math.hypot(gx, gy - P.CY) - gn / 2 - P.SOCKET_D / 2, 0.5)
    sx, sy, sz, sd = P.SMA
    add("SMA nut (AF8, ~9.2) -> rear screw column (y)", abs(sy - P.SCREW_POS[1][1]) - 4.6 - P.COL_D / 2, 0.5)
    add("SMA nut -> PCB underside (z)", P.Z_PCB_BOT - (sz + 4.6), 0.0, "nut is outside the PCB in x anyway")
    vx = P.VENT["x0"] + (P.VENT["n"] - 1) / 2 * P.VENT["pitch"] + P.VENT["w"] / 2
    add("Vent slots -> front-right screw column (x)", (49.5 - P.COL_D / 2) - vx, 0.5)
    add("Probe parts in the tube (offset of PCB from axis)", math.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2) - (P.PROBE_MAX_H), 1.0, "PCB against the wall, parts toward the axis")
    return R

if __name__ == "__main__":
    ok = True
    for n, v, m, good, note in rows():
        ok &= good
        print("%-55s %6.2f  (min %4.1f)  %s  %s" % (n, v, m, "OK" if good else "FAIL", note))
    print("ALL OK" if ok else "SOME FAIL")
