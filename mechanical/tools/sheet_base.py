from views_common import *

def build(total):
    sh = Sheet(2, total, "Base (lower shell + collar)", "GAIA-MEC-B02", "1:1",
               "One FDM print. Datum 0,0 = PCB centre (KiCad 145,125). All coordinates in the table.")
    # ---------------- TOP VIEW (inside) ----------------
    t = View(sh, "base_top", 85, 218, 1.0, F_PLAN)
    t.title((15, 283), "BASE – TOP VIEW", "lid removed; PCB and 18650 dashed")
    t.poly(outer(), "vis"); t.poly(inner(), "vis")
    t.poly(ring(P.GROOVE_OFF), "thin"); t.poly(ring(P.GROOVE_OFF + P.GROOVE_W), "thin")
    for p in P.SCREW_POS:
        t.circle(p, P.COL_D / 2, "vis"); t.circle(p, P.COL_HOLE / 2, "vis"); t.cross(p, 4.5)
    for p in P.PCB_HOLES:
        t.circle(p, P.SO_D / 2, "vis"); t.circle(p, P.SO_PILOT / 2, "vis"); t.cross(p, 4)
    obround(t, P.SLOT[0], P.SLOT[1], P.SLOT[2], P.SLOT[3])
    t.circle((0, P.CY), P.SOCKET_D / 2, "hid"); t.cross((0, P.CY), 23)
    gx, gy, gd, gn = P.GLAND; t.circle((gx, gy), gd / 2, "vis"); t.circle((gx, gy), gn / 2, "hid"); t.cross((gx, gy), 9)
    # openings seen in plan
    t.rect(P.USBC[0] - P.USB_OPEN[0] / 2, P.IN_Y1, P.USBC[0] + P.USB_OPEN[0] / 2, P.OUT_Y1, "thin", fill="#e6e6e6")
    V = P.VENT
    for i in range(V["n"]):
        x = V["x0"] + (i - (V["n"] - 1) / 2) * V["pitch"]; t.rect(x - V["w"] / 2, P.IN_Y1, x + V["w"] / 2, P.OUT_Y1, "thin", fill="#e6e6e6")
    t.rect(P.IN_X, P.SMA[1] - P.SMA[3] / 2, P.OUT_X, P.SMA[1] + P.SMA[3] / 2, "thin", fill="#e6e6e6")
    ghost_pcb(t); datum(t)
    t.dim((-P.OUT_X, P.OUT_Y1), (P.OUT_X, P.OUT_Y1), -10, "h", "114")
    t.dim((-P.OUT_X, P.OUT_Y0), (-P.OUT_X, P.OUT_Y1), -10, "v", "82")
    t.dim((-P.IN_X, P.OUT_Y0), (P.IN_X, P.OUT_Y0), 7, "h", "106 inside")
    t.dim((P.OUT_X, P.IN_Y0), (P.OUT_X, P.IN_Y1), 9, "v", "74 inside")
    t.dim((P.OUT_X, 0), (P.OUT_X, P.OUT_Y1), 19, "v", "34.5")
    t.dim((P.OUT_X, P.OUT_Y0), (P.OUT_X, 0), 19, "v", "47.5")
    t.note(P.SCREW_POS[0], "S1-S4 screw columns", (8, 12))
    t.note((P.PCB_HOLES[2][0] + 2, P.PCB_HOLES[2][1] - 2), "P1-P4 PCB standoffs", (-18, 14), ha="right") if False else None
    t.note((gx + 4, gy + 4), "G  PG7 gland (rain)", (12, 8))
    t.note((P.SLOT[0] + 5, P.SLOT[1]), "C  cable slot (probe)", (36, 4))
    # ---------------- BOTTOM VIEW ----------------
    b = View(sh, "base_bottom", 222, 218, 1.0, F_BOTTOM)
    b.title((157, 283), "BASE – BOTTOM VIEW", "seen from below, front edge up")
    b.poly(outer(), "vis")
    b.circle((0, P.CY), P.COLLAR_D / 2, "vis"); b.circle((0, P.CY), P.SOCKET_D / 2, "vis"); b.cross((0, P.CY), 25)
    obround(b, P.SLOT[0], P.SLOT[1], P.SLOT[2], P.SLOT[3])
    b.circle((gx, gy), gd / 2, "vis"); b.cross((gx, gy), 9)
    for p in P.SCREW_POS:
        b.circle(p, P.CB_D / 2, "vis"); b.circle(p, P.COL_HOLE / 2, "vis"); b.cross(p, 4.5)
    b.dia((0, P.CY), P.COLLAR_D / 2, 205, "collar Ø44", 8)
    b.dia((0, P.CY), P.SOCKET_D / 2, 300, "socket Ø32.4 x 22 deep", 22)
    b.dia((gx, gy), gd / 2, 50, "Ø12.5 (PG7)", 6)
    b.dia(P.SCREW_POS[0], P.CB_D / 2, 210, "4x Ø3.4, c'bore Ø6.5 x 3.5", 4)
    b.dim((P.OUT_X, P.OUT_Y0), (P.OUT_X, P.CY), 8, "v", "41 (axis)")
    # ---------------- FRONT VIEW ----------------
    f = View(sh, "base_front", 85, 103, 1.0, F_FRONT)
    f.title((15, 162), "FRONT VIEW", "assembled (antenna not shown)")
    silhouette_front(f, antenna=False)
    ux, uw, uh, ur = P.USBC[0], P.USB_OPEN[0], P.USB_OPEN[1], P.USB_OPEN[2]
    f.rect(ux - uw / 2, P.USB_Z - uh / 2, ux + uw / 2, P.USB_Z + uh / 2, "vis", r=ur)
    for i in range(V["n"]):
        x = V["x0"] + (i - (V["n"] - 1) / 2) * V["pitch"]; f.rect(x - V["w"] / 2, V["z0"], x + V["w"] / 2, V["z0"] + V["h"], "vis", r=0.99)
    f.line((0, -P.COLLAR_H - 22), (0, P.Z_TOP + 4), "cen")
    f.dim((-P.OUT_X, -P.COLLAR_H), (-P.OUT_X, 0), -9, "v", "22")
    f.dim((-P.OUT_X, 0), (-P.OUT_X, P.Z_SPLIT), -9, "v", "33")
    f.dim((-P.OUT_X, P.Z_SPLIT), (-P.OUT_X, P.Z_TOP), -9, "v", "5.5")
    f.dim((ux - uw / 2, P.Z_TOP), (ux + uw / 2, P.Z_TOP), 9, "h", "12.5")
    f.dim((0, P.Z_TOP), (ux, P.Z_TOP), 17, "h", "17.4")
    f.dim((ux + uw / 2, P.USB_Z - uh / 2), (ux + uw / 2, P.USB_Z + uh / 2), 3, "v", "7") if False else None
    f.dim((0, P.Z_TOP), (V["x0"], P.Z_TOP), 9, "h", "35")
    f.dim((-22, -P.COLLAR_H), (22, -P.COLLAR_H), -6, "h", "Ø44")
    f.note((ux - 2, P.USB_Z), "USB-C 12.5 x 7 R2, axis z 28.25", (-6, 22), ha="right")
    f.note((V["x0"] + 4, V["z0"] + 2), "5 slots 2 x 9 R1, pitch 4, z 19-28", (2, -26))
    # ---------------- RIGHT VIEW ----------------
    r = View(sh, "base_right", 222, 103, 1.0, F_RIGHT)
    r.title((157, 162), "RIGHT VIEW", "SMA antenna side")
    silhouette_side(r)
    sx, sy, sz, sd = P.SMA
    r.circle((sy, sz), sd / 2, "vis"); r.cross((sy, sz), 6)
    r.dim((P.OUT_Y0, P.Z_TOP), (sy, P.Z_TOP), 9, "h", "17.5")
    r.dim((P.OUT_Y0, 0), (P.OUT_Y0, sz), 9, "v", "20")
    r.dim((P.OUT_Y1, -P.COLLAR_H), (P.OUT_Y0, -P.COLLAR_H), -6, "h", "82")
    r.note((sy - 2, sz + 2), "Ø6.4 SMA bulkhead", (-6, 16), ha="right")
    # ---------------- FEATURE TABLE ----------------
    rows = [("ID", "Feature", "x", "y", "z", "Size"),
            ("S1-4", "Screw column (from below)", "±49.5", "-40 / +26.5", "0-27", "Ø7, Ø3.4 thru, cb Ø6.5x3.5"),
            ("P1-4", "PCB standoff", "±41", "±21", "3-25", "Ø6, pilot Ø2.5x8"),
            ("C", "Probe cable slot (floor)", "0", "-15", "0-3", "13 x 6 obround"),
            ("G", "PG7 gland (floor)", "+35", "-34", "0-3", "Ø12.5"),
            ("K", "Collar / tube socket", "0", "-6.5", "-22-0", "Ø44 / Ø32.4 x 22"),
            ("U", "USB-C opening, front", "-17.4", "front", "28.25", "12.5 x 7 R2"),
            ("V", "SHT40 vent, front", "27..43", "front", "19-28", "5 x (2 x 9) p4"),
            ("A", "SMA hole, right", "right", "-30", "20", "Ø6.4"),
            ("Q", "QR label recess, left", "left", "-6.5", "17", "26 x 26 x 0.3"),
            ("R", "Gasket groove, rim", "", "", "33", "2.2 x 1.5, 0.9 from outside")]
    def tbl(ax, fig):
        table(ax, 297, 279, rows, [10, 35, 11, 16, 9, 31], h=4.3, fs=1.85, title="FEATURE TABLE (datum = PCB centre)", tfs=2.8)
        pt = 72 / 25.4
        notes = ["NOTES",
                 "1. Print floor-down, ASA (UV), 0.2 mm, 4 perimeters, 40 % infill.",
                 "2. Wall 4, floor 3, inside corners R8, outside R12.",
                 "3. Holes printed nominal +0.2; ream Ø3.4 if tight.",
                 "4. QR recess on the LEFT wall (not shown in these views).",
                 "5. Rim = parting plane z 33: keep flat within 0.2.",
                 "6. Colour olive green matt (~RAL 6003), as design base v1."]
        for i, s in enumerate(notes):
            ax.text(296, 222 - i * 4.6, s, fontsize=(2.6 if i == 0 else 2.1) * pt, weight="bold" if i == 0 else "normal")
    sh.extra.append(tbl)
    return sh

def silhouette_front(f, antenna=True):
    t, s, r = P.Z_TOP, P.Z_SPLIT, P.TOP_R
    f.rect(-P.OUT_X, 0, P.OUT_X, s, "vis")
    f.poly([(-P.OUT_X, s)] + arc_pts(-P.OUT_X + r, t - r, r, 180, 90) + arc_pts(P.OUT_X - r, t - r, r, 90, 0) + [(P.OUT_X, s)], "vis")
    f.rect(-P.COLLAR_D / 2, -P.COLLAR_H, P.COLLAR_D / 2, 0, "vis")
    f.rect(-P.TUBE_OD / 2, -P.COLLAR_H - 18, P.TUBE_OD / 2, -P.COLLAR_H, "vis")
    f.line((-P.TUBE_OD / 2 - 2, -P.COLLAR_H - 18), (P.TUBE_OD / 2 + 2, -P.COLLAR_H - 18), "thin")
    f.rect(-P.PANEL_W / 2, t, P.PANEL_W / 2, t - P.PANEL_REC + P.PANEL_T, "thin", fill="#dfe8f5")
    f.rect(P.SW1[0] - 6, t, P.SW1[0] + 6, t + P.BTN_PROUD, "thin", fill="#cccccc")
    gx = P.GLAND[0]; f.rect(gx - 7.5, -12, gx + 7.5, 0, "thin"); f.rect(gx - 3, -20, gx + 3, -12, "thin")
    if antenna:
        sx, sy, sz, _ = P.SMA
        f.rect(sx, sz - 4, sx + 6, sz + 4, "ghost"); f.rect(sx + 6, sz - 5, sx + 14, sz + 5, "ghost")
        f.rect(sx + 5, sz + 5, sx + 15, sz + 60, "ghost"); f.text((sx + 16, sz + 40), "antenna", 2.0)

def silhouette_side(r):
    t, s, rr = P.Z_TOP, P.Z_SPLIT, P.TOP_R
    r.rect(P.OUT_Y0, 0, P.OUT_Y1, s, "vis")
    r.poly([(P.OUT_Y0, s)] + arc_pts(P.OUT_Y0 + rr, t - rr, rr, 180, 90) + arc_pts(P.OUT_Y1 - rr, t - rr, rr, 90, 0) + [(P.OUT_Y1, s)], "vis")
    r.rect(P.CY - P.COLLAR_D / 2, -P.COLLAR_H, P.CY + P.COLLAR_D / 2, 0, "vis")
    r.rect(P.CY - P.TUBE_OD / 2, -P.COLLAR_H - 18, P.CY + P.TUBE_OD / 2, -P.COLLAR_H, "vis")
    py = P.PANEL_C[1]; r.rect(py - P.PANEL_H / 2, t, py + P.PANEL_H / 2, t - P.PANEL_REC + P.PANEL_T, "thin", fill="#dfe8f5")
    r.rect(P.SW1[1] - 6, t, P.SW1[1] + 6, t + P.BTN_PROUD, "thin", fill="#cccccc")
    gy = P.GLAND[1]; r.rect(gy - 7.5, -12, gy + 7.5, 0, "thin"); r.rect(gy - 3, -20, gy + 3, -12, "thin")
