from views_common import *
from sheet_base import silhouette_front

XA = P.LEDS[1][0]        # section A-A plane x = -3.4 (middle LED, through slot and tube)
YB = P.SCREW_POS[2][1]   # section B-B plane y = +26.5 (front screw columns)

def build(total):
    sh = Sheet(3, total, "Lid, sections and details", "GAIA-MEC-B03", "1:1 / 2:1 / 4:1",
               "Lid: one FDM print, top face down. Sections show the full assembly.")
    t = View(sh, "lid_top", 85, 218, 1.0, F_PLAN)
    t.title((15, 283), "LID – TOP VIEW", "panel, button and LED strip")
    lid_top(t)
    u = View(sh, "lid_under", 222, 218, 1.0, F_UNDER)
    u.title((157, 283), "LID – UNDERSIDE", "seen from below (mirrored)")
    lid_under(u)
    a = View(sh, "AA", 80, 100, 1.0, F_RIGHT)
    a.title((15, 160), "SECTION A-A", "x = -3.4 (middle LED, slot, tube), front on the left")
    section_AA(a)
    b = View(sh, "BB", 222, 100, 1.0, F_FRONT)
    b.title((157, 160), "SECTION B-B", "y = +26.5 (front screws), looking to the rear")
    section_BB(b)
    d1 = View(sh, "D1", 170, 112, 4.0, F_RIGHT)
    d1.title((297, 283), "DETAIL D1  4:1", "rim: gasket + lid lip (rear wall)")
    detail_rim(d1)
    d2 = View(sh, "D2", 362, 72, 2.0, F_RIGHT)
    d2.title((297, 177), "DETAIL D2  2:1", "TPU button cap over SW1 (x = -12)")
    detail_button(d2)
    return sh

# ---------------- lid views ----------------
def lid_top(t):
    t.poly(outer(), "vis"); t.poly(ring(P.TOP_R), "thin")
    px, py = P.PANEL_C; w, h = P.PANEL_W + 2 * P.PANEL_CLR, P.PANEL_H + 2 * P.PANEL_CLR
    t.rect(px - w / 2, py - h / 2, px + w / 2, py + h / 2, "vis", r=2)
    t.rect(px - P.PANEL_W / 2, py - P.PANEL_H / 2, px + P.PANEL_W / 2, py + P.PANEL_H / 2, "thin", fill="#e3ebf6")
    wx, wy, wd = P.PANEL_WIRE; t.circle((wx, wy), wd / 2, "vis")
    t.circle(P.SW1, P.BTN_HOLE_D / 2, "vis"); t.circle(P.SW1, P.BTN_CAP_D / 2, "thin", fill="#d9d9d9"); t.cross(P.SW1, 8)
    lx, ly = P.LEDS[1]; sw, shh, _ = P.LED_STRIP
    t.rect(lx - sw / 2, ly - shh / 2, lx + sw / 2, ly + shh / 2, "vis", fill="#3a3a3a")
    for k, (x, y) in enumerate(P.LEDS): t.circle((x, y), P.LED_HOLE_D / 2, "vis", fill=["#7fd27f", "#f3dc6b", "#ee8a80"][k])
    datum(t)
    sect_mark(t, (XA, P.OUT_Y0 - 6), (XA, P.OUT_Y1 + 6), "A", (-1, 0))
    sect_mark(t, (-P.OUT_X - 6, YB), (P.OUT_X + 6, YB), "B", (0, -1))
    t.dim((-P.OUT_X, P.OUT_Y1), (P.OUT_X, P.OUT_Y1), -10, "h", "114")
    t.dim((-P.OUT_X, P.OUT_Y0), (-P.OUT_X, P.OUT_Y1), -12, "v", "82")
    t.dim((px - w / 2, P.OUT_Y0), (px + w / 2, P.OUT_Y0), 7, "h", "68.8 recess")
    t.dim((P.OUT_X, py - h / 2), (P.OUT_X, py + h / 2), 9, "v", "37.8")
    t.dim((P.OUT_X, P.OUT_Y0), (P.OUT_X, py - h / 2), 9, "v", "4.6") if False else None
    t.dim((P.OUT_X, 0), (P.OUT_X, P.SW1[1]), 17, "v", "") if False else None
    t.note(P.SW1, "Ø12.4 hole (cap Ø12)", (-26, -24), ha="right") if False else t.note((P.SW1[0] - 6, P.SW1[1]), "button Ø12.4", (-10, -8), ha="right")
    t.note((lx - sw / 2, ly), "LED strip 14 x 5 x 0.5, 3x Ø3.1", (-14, -10), ha="right")
    t.note((wx, wy), "panel wire Ø4", (14, 10))
    t.note((px - 20, py + 10), "solar panel 68 x 37 x 3.2", (0, 0)) if False else t.text((px - 14, py - 1), "PANEL 68 x 37", 2.6)

def lid_under(u):
    u.poly(outer(), "vis"); u.poly(inner(P.LIP_GAP), "vis"); u.poly(inner(P.LIP_GAP + P.LIP_T), "vis")
    for p in P.SCREW_POS: u.circle(p, P.COL_D / 2, "vis"); u.circle(p, P.INSERT_D / 2, "vis"); u.cross(p, 4.5)
    u.circle(P.SW1, P.BTN_POCKET_D / 2, "vis"); u.circle(P.SW1, P.BTN_HOLE_D / 2, "vis"); u.cross(P.SW1, 10)
    lx, ly = P.LEDS[1]; hw, hh = P.ROD_HOLDER
    u.rect(lx - hw / 2, ly - hh / 2, lx + hw / 2, ly + hh / 2, "vis")
    for (x, y) in P.LEDS: u.circle((x, y), P.LED_HOLE_D / 2, "vis")
    wx, wy, wd = P.PANEL_WIRE; u.circle((wx, wy), wd / 2, "vis")
    px, py = P.PANEL_C; u.rect(px - P.PANEL_W / 2 - .4, py - P.PANEL_H / 2 - .4, px + P.PANEL_W / 2 + .4, py + P.PANEL_H / 2 + .4, "hid", r=2)
    u.dia(P.SCREW_POS[2], P.COL_D / 2, -40, "4x boss \u00d87 to z 27, insert \u00d84 x 6", 4)
    u.note((P.SW1[0], P.SW1[1] + P.BTN_POCKET_D / 2), "pocket Ø16.4 x 1", (10, 14))
    u.note((lx + hw / 2, ly), "rod holder 14 x 5, to z 29.5", (8, -12))
    u.note((P.IN_X - 0.8, -10), "lip 1.2 x 2, 0.3 inside base wall", (14, -14)) if False else u.note((-(P.IN_X - 1.0), -10), "locating lip 1.2 x 2", (8, 10))

# ---------------- sections ----------------
def chord(r, d): return math.sqrt(r * r - d * d) if r > abs(d) else None

def lid_section_y(x, pieces_out):
    """lid profile in a y-z section at plane x (features near x = -3.4 only)"""
    t, s, ri, r = P.Z_TOP, P.Z_SPLIT, P.Z_ROOF_IN, P.TOP_R
    py = P.PANEL_C[1]; p0, p1 = py - P.PANEL_H / 2 - P.PANEL_CLR, py + P.PANEL_H / 2 + P.PANEL_CLR
    ly = P.LEDS[1][1]; s0, s1 = ly - P.LED_STRIP[1] / 2, ly + P.LED_STRIP[1] / 2
    h0, h1 = ly - P.LED_HOLE_D / 2, ly + P.LED_HOLE_D / 2
    lip_o, lip_i = P.LIP_GAP, P.LIP_GAP + P.LIP_T
    rear = [(P.OUT_Y0, s)] + arc_pts(P.OUT_Y0 + r, t - r, r, 180, 90) + [(p0, t), (p0, t - P.PANEL_REC), (p1, t - P.PANEL_REC), (p1, t), (s0, t), (s0, t - P.LED_STRIP[2]),
            (h0, t - P.LED_STRIP[2]), (h0, P.ROD_HOLDER_Z), (s0, P.ROD_HOLDER_Z), (s0, ri), (P.IN_Y0 + lip_i, ri), (P.IN_Y0 + lip_i, s - P.LIP_H), (P.IN_Y0 + lip_o, s - P.LIP_H), (P.IN_Y0 + lip_o, s), (P.OUT_Y0, s)]
    front = [(h1, t - P.LED_STRIP[2]), (s1, t - P.LED_STRIP[2]), (s1, t)] + arc_pts(P.OUT_Y1 - r, t - r, r, 90, 0) + [(P.OUT_Y1, s), (P.IN_Y1 - lip_o, s), (P.IN_Y1 - lip_o, s - P.LIP_H),
             (P.IN_Y1 - lip_i, s - P.LIP_H), (P.IN_Y1 - lip_i, ri), (s1, ri), (s1, P.ROD_HOLDER_Z), (h1, P.ROD_HOLDER_Z), (h1, t - P.LED_STRIP[2])]
    pieces_out += [rear, front]

def section_AA(a):
    x = XA; s, t = P.Z_SPLIT, P.Z_TOP
    ck, cs = chord(P.COLLAR_D / 2, x), chord(P.SOCKET_D / 2, x)
    sl0, sl1 = P.SLOT[1] - P.SLOT[3] / 2, P.SLOT[1] + P.SLOT[3] / 2
    g0, g1 = P.GROOVE_OFF, P.GROOVE_OFF + P.GROOVE_W
    rear = [(P.OUT_Y0, 0), (P.OUT_Y0, s), (P.OUT_Y0 + g0, s), (P.OUT_Y0 + g0, s - P.GROOVE_D), (P.OUT_Y0 + g1, s - P.GROOVE_D), (P.OUT_Y0 + g1, s),
            (P.IN_Y0, s), (P.IN_Y0, P.FLOOR), (sl0, P.FLOOR), (sl0, 0), (P.CY - cs, 0), (P.CY - cs, -P.COLLAR_H), (P.CY - ck, -P.COLLAR_H), (P.CY - ck, 0), (P.OUT_Y0, 0)]
    front = [(sl1, 0), (sl1, P.FLOOR), (P.IN_Y1, P.FLOOR), (P.IN_Y1, s), (P.OUT_Y1 - g1, s), (P.OUT_Y1 - g1, s - P.GROOVE_D), (P.OUT_Y1 - g0, s - P.GROOVE_D),
             (P.OUT_Y1 - g0, s), (P.OUT_Y1, s), (P.OUT_Y1, 0), (P.CY + ck, 0), (P.CY + ck, -P.COLLAR_H), (P.CY + cs, -P.COLLAR_H), (P.CY + cs, 0), (sl1, 0)]
    for pc in (rear, front): a.poly(pc, "vis", fill="#ffffff", hatch=HATCH)
    L = []; lid_section_y(x, L)
    for pc in L: a.poly(pc, "vis", fill="#ffffff", hatch="\\\\\\\\")
    for yc in (P.OUT_Y0 + P.WALL / 2, P.OUT_Y1 - P.WALL / 2): a.circle((yc, s - P.GROOVE_D + 0.85), P.CORD_D / 2 * 0.95, "vis", fill="#333333")
    # tube in the socket
    to, ti = chord(P.TUBE_OD / 2, x), chord(P.TUBE_ID / 2, x)
    zb = -P.COLLAR_H - 18
    for y0, y1 in ((P.CY - to, P.CY - ti), (P.CY + ti, P.CY + to)): a.rect(y0, zb, y1, -0.05, "vis", fill="#efe6cc", hatch="xx")
    a.line((P.CY - to - 3, zb), (P.CY + to + 3, zb), "thin")
    # probe PCB against the front wall of the tube + cable path
    yp = P.CY + math.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2)
    a.rect(yp - P.PROBE_T, zb, yp, P.PROBE_TOP_Z, "vis", fill="#7fbf7f")
    a.poly([(yp - 3, P.PROBE_TOP_Z - 1), (P.SLOT[1], 0.5), (P.SLOT[1] - 1, P.FLOOR + 1.5), (-24, 5), (-30, 12), (-28, P.Z_PCB_TOP + 3.5), (P.J_PROBE[1] - 4, P.Z_PCB_TOP + 3.5)], "ghost")
    a.text((-36, 16), "probe cable", 2.0, ha="right")
    # PCB, battery, standoff ghost, panel, rod
    a.rect(-25, P.Z_PCB_BOT, 25, P.Z_PCB_TOP, "vis", fill="#cfe3cf", hatch="....")
    a.rect(P.BATT_Y[0], P.Z_PCB_BOT - 1.2, P.BATT_Y[1], P.Z_PCB_BOT, "vis", fill="#444444")
    a.circle((P.BATT_CY, P.CELL_ZC), P.CELL_D / 2, "thin", fill="#dde8ee"); a.text((P.BATT_CY, P.CELL_ZC - 1), "18650", 2.2, ha="center")
    py = P.PANEL_C[1]; z0 = t - P.PANEL_REC
    a.rect(py - P.PANEL_H / 2, z0, py + P.PANEL_H / 2, z0 + P.PANEL_T, "vis", fill="#c9d9f0")
    ly = P.LEDS[1][1]
    a.rect(ly - P.LED_ROD_D / 2, P.ROD_BOT, ly + P.LED_ROD_D / 2, t, "vis", fill="#e9f4fb")
    a.rect(ly - 0.4, P.Z_PCB_TOP, ly + 0.4, P.LED_TOP, "thin", fill="#e6c619")
    # JST plug room (beyond the plane)
    a.rect(P.JST_FACE_Y["J3"] - 4.4, P.Z_PCB_TOP, P.JST_FACE_Y["J3"], P.Z_PCB_TOP + 2.5, "ghost")
    a.line((P.CY, zb - 4), (P.CY, t + 4), "cen")
    # dims
    a.dim((P.OUT_Y1, -P.COLLAR_H), (P.OUT_Y1, 0), -9, "v", "22")
    a.dim((P.OUT_Y1, 0), (P.OUT_Y1, P.Z_PCB_BOT), -9, "v", "25")
    a.dim((P.OUT_Y1, 0), (P.OUT_Y1, s), -17, "v", "33")
    a.dim((P.OUT_Y1, 0), (P.OUT_Y1, t), -25, "v", "38.5")
    a.dim((P.OUT_Y0, 0), (P.OUT_Y0, P.FLOOR), 6, "v", "3") if False else None
    a.dim((P.OUT_Y0, -P.COLLAR_H), (P.CY, -P.COLLAR_H), 0, "h", "") if False else None
    a.dim((P.CY - P.TUBE_OD / 2, zb), (P.CY + P.TUBE_OD / 2, zb), -5, "h", "Ø32 tube") if False else None
    a.note((P.IN_Y0 + 2, P.Z_ROOF_IN + 1), "D1", (4, 8)) if False else a.balloon((P.OUT_Y0 + 2, s), "D1", (6, 10))
    a.note((P.JST_FACE_Y["J3"] + 3, P.Z_PCB_TOP + 1.3), "7 mm plug room", (-4, 14), ha="right")

def section_BB(b):
    y = YB; s, t, r = P.Z_SPLIT, P.Z_TOP, P.TOP_R
    dy = y - (P.IN_Y1 - P.R_IN)
    xo = (P.OUT_X - P.R_OUT) + chord(P.R_OUT, y - (P.OUT_Y1 - P.R_OUT))
    xi = (P.IN_X - P.R_IN) + chord(P.R_IN, dy)
    cx, cr = P.SCREW_POS[3][0], P.COL_D / 2
    g0, g1 = P.GROOVE_OFF, P.GROOVE_OFF + P.GROOVE_W
    half = [(xo, 0), (xo, s), (xo - g0, s), (xo - g0, s - P.GROOVE_D), (xo - g1, s - P.GROOVE_D), (xo - g1, s), (xi, s), (xi, P.Z_MEET), (cx - cr, P.Z_MEET), (cx - cr, P.FLOOR), (0, P.FLOOR)]
    base = half + [(-a_, b_) for a_, b_ in reversed(half)][1:] + [(xo, 0)]
    base = [(-xo, 0)] + [(-a_, b_) for a_, b_ in half][1:][::-1][::-1]
    pts = [(xo, 0)] + half[1:] + [(-a_, b_) for a_, b_ in reversed(half[:-1])] + [(-xo, 0), (xo, 0)]
    b.poly(pts, "vis", fill="#ffffff", hatch=HATCH)
    lip = xi - P.LIP_GAP
    lhalf = [(xo, s)] + arc_pts(xo - r, t - r, r, 0, 90) + [(0, t)]
    lid = lhalf + [(-a_, b_) for a_, b_ in reversed(lhalf[:-1])] + [(-xo, s), (-lip, s), (-lip, P.Z_MEET), (-(cx - cr), P.Z_MEET), (-(cx - cr), P.Z_ROOF_IN),
                                                                    ((cx - cr), P.Z_ROOF_IN), ((cx - cr), P.Z_MEET), (lip, P.Z_MEET), (lip, s), (xo, s)]
    b.poly(lid, "vis", fill="#ffffff", hatch="\\\\\\\\")
    for sg in (-1, 1):
        x0 = sg * cx
        b.rect(x0 - P.CB_D / 2, 0, x0 + P.CB_D / 2, P.CB_DEPTH, "vis", fill="#ffffff")
        b.rect(x0 - P.COL_HOLE / 2, P.CB_DEPTH, x0 + P.COL_HOLE / 2, P.Z_MEET, "vis", fill="#ffffff")
        b.rect(x0 - P.INSERT_D / 2, P.Z_MEET, x0 + P.INSERT_D / 2, P.Z_MEET + P.INSERT_L, "vis", fill="#e8cf7a")
        b.rect(x0 - 2.75, P.CB_DEPTH - 2.0, x0 + 2.75, P.CB_DEPTH, "vis", fill="#a8a8a8")
        b.rect(x0 - 1.5, P.CB_DEPTH, x0 + 1.5, P.CB_DEPTH + 30 - 0.0, "vis", fill="#a8a8a8")
        b.circle((sg * (xo - P.WALL / 2), s - P.GROOVE_D + 0.85), P.CORD_D / 2 * 0.95, "vis", fill="#333333")
    # beyond the plane
    b.rect(-45, P.Z_PCB_BOT, 45, P.Z_PCB_TOP, "vis", fill="#cfe3cf")
    for sg in (-1, 1): b.rect(sg * 41 - P.SO_D / 2, P.FLOOR, sg * 41 + P.SO_D / 2, P.Z_PCB_BOT, "thin")
    b.rect(-43, P.Z_PCB_BOT - 1.2, 43, P.Z_PCB_BOT, "thin", fill="#444444")
    b.rect(-32.5, P.CELL_ZC - P.CELL_D / 2, 32.5, P.CELL_ZC + P.CELL_D / 2, "thin", fill="#dde8ee")
    for (x, _), w in ((P.J_PROBE, 11.6), (P.J_SOLAR, 4), (P.J_RAIN, 4)): b.rect(x - w / 2, P.Z_PCB_TOP, x + w / 2, P.Z_PCB_TOP + 3.0, "thin", fill="#ece2c6")
    for k, (x, _) in enumerate(P.LEDS): b.rect(x - P.LED_ROD_D / 2, P.ROD_BOT, x + P.LED_ROD_D / 2, t, "thin", fill="#e9f4fb")
    b.rect(P.USBC[0] - 4.47, P.Z_PCB_TOP, P.USBC[0] + 4.47, P.Z_PCB_TOP + 3.3, "thin", fill="#d0d0d0")
    b.rect(-P.COLLAR_D / 2, -P.COLLAR_H, P.COLLAR_D / 2, 0, "vis"); b.rect(-P.TUBE_OD / 2, -P.COLLAR_H - 18, P.TUBE_OD / 2, -P.COLLAR_H, "vis")
    b.dim((-xo, -P.COLLAR_H), (xo, -P.COLLAR_H), -7, "h", "%s at this plane" % fmt(2 * xo)) if False else None
    b.dim((cx, P.Z_TOP), (-cx, P.Z_TOP), 8, "h", "99 (screw pitch x)")
    b.dim((P.OUT_X, 0), (P.OUT_X, P.Z_MEET), 10, "v", "27") if False else b.dim((xo, 0), (xo, P.Z_MEET), 9, "v", "27")
    b.note((cx, 12), "M3 x 30 from below", (14, -14))
    b.note((cx, P.Z_MEET + 3), "M3 heat-set insert", (14, 10))
    b.note((-cx - 1, P.Z_PCB_TOP + 3), "", (0, 0)) if False else None
    b.text((-30, P.CELL_ZC - 1), "18650 (envelope 21 below PCB)", 2.2, ha="left")

# ---------------- details ----------------
def detail_rim(d):
    y0 = P.OUT_Y0; s, t, r = P.Z_SPLIT, P.Z_TOP, P.TOP_R
    g0, g1 = P.GROOVE_OFF, P.GROOVE_OFF + P.GROOVE_W
    base = [(y0, s - 8), (y0, s), (y0 + g0, s), (y0 + g0, s - P.GROOVE_D), (y0 + g1, s - P.GROOVE_D), (y0 + g1, s), (P.IN_Y0, s), (P.IN_Y0, s - 8), (y0, s - 8)]
    d.poly(base, "vis", fill="#ffffff", hatch=HATCH)
    lid = [(y0, s)] + arc_pts(y0 + r, t - r, r, 180, 90) + [(P.IN_Y0 + 5, t), (P.IN_Y0 + 5, P.Z_ROOF_IN), (P.IN_Y0 + P.LIP_GAP + P.LIP_T, P.Z_ROOF_IN),
                                                         (P.IN_Y0 + P.LIP_GAP + P.LIP_T, s - P.LIP_H), (P.IN_Y0 + P.LIP_GAP, s - P.LIP_H), (P.IN_Y0 + P.LIP_GAP, s), (y0, s)]
    d.poly(lid, "vis", fill="#ffffff", hatch="\\\\\\\\")
    d.circle((y0 + P.WALL / 2, s - P.GROOVE_D + 0.85), 0.95, "vis", fill="#333333")
    d.dim((y0, s - 8), (P.IN_Y0, s - 8), -5, "h", "4 wall")
    d.dim((y0 + g0, s - P.GROOVE_D), (y0 + g1, s - P.GROOVE_D), -18, "h", "2.2") if False else None
    d.dim((P.IN_Y0, s - P.GROOVE_D), (P.IN_Y0, s), -0, "v", "") if False else None
    d.dim((P.IN_Y0 + P.LIP_GAP + P.LIP_T, s - P.LIP_H), (P.IN_Y0 + P.LIP_GAP + P.LIP_T, s), -6, "v", "2") if False else None
    d.note((y0 + P.WALL / 2, s - 0.6), "cord Ø2 silicone in groove 2.2 x 1.5", (10, -22))
    d.note((P.IN_Y0 + 0.9, s - 1.2), "lid lip 1.2 x 2, gap 0.3", (-10, -30), ha="right")
    d.note((y0 + 1.0, t - 0.6), "R3", (8, 6))

def detail_button(d):
    x, y = P.SW1; s, t, ri = P.Z_SPLIT, P.Z_TOP, P.Z_ROOF_IN
    hr, pr = P.BTN_HOLE_D / 2, P.BTN_POCKET_D / 2; zp = ri + P.BTN_FLANGE_T      # pocket 1 mm into the roof
    for sg in (-1, 1):
        a, b_ = y + sg * hr, y + sg * 11
        d.poly([(a, t), (b_, t), (b_, ri), (y + sg * pr, ri), (y + sg * pr, zp), (a, zp), (a, t)], "vis", fill="#ffffff", hatch="\\\\\\\\")
    cap = [(y - P.BTN_FLANGE_D / 2, ri), (y - P.BTN_FLANGE_D / 2, zp), (y - P.BTN_CAP_D / 2, zp), (y - P.BTN_CAP_D / 2, t + P.BTN_PROUD - 0.6),
           (y - P.BTN_CAP_D / 2 + 0.6, t + P.BTN_PROUD), (y + P.BTN_CAP_D / 2 - 0.6, t + P.BTN_PROUD), (y + P.BTN_CAP_D / 2, t + P.BTN_PROUD - 0.6),
           (y + P.BTN_CAP_D / 2, zp), (y + P.BTN_FLANGE_D / 2, zp), (y + P.BTN_FLANGE_D / 2, ri), (y + P.BTN_PIN_D / 2, ri),
           (y + P.BTN_PIN_D / 2, P.SW1_TOP + 0.3), (y - P.BTN_PIN_D / 2, P.SW1_TOP + 0.3), (y - P.BTN_PIN_D / 2, ri), (y - P.BTN_FLANGE_D / 2, ri)]
    d.poly(cap, "vis", fill="#cfcfe0", hatch="xx")
    d.rect(y - 2.3, P.Z_PCB_TOP, y + 2.3, P.SW1_TOP, "vis", fill="#666666")
    d.rect(y - 11, P.Z_PCB_BOT, y + 11, P.Z_PCB_TOP, "vis", fill="#cfe3cf", hatch="....")
    d.dim((y - P.BTN_CAP_D / 2, t + P.BTN_PROUD), (y + P.BTN_CAP_D / 2, t + P.BTN_PROUD), 5, "h", "Ø12")
    d.dim((y - P.BTN_FLANGE_D / 2, zp), (y + P.BTN_FLANGE_D / 2, zp), -4, "h", "") if False else None
    d.dim((y + 11, P.SW1_TOP), (y + 11, ri), -0.0, "v", "") if False else None
    d.note((y + P.BTN_PIN_D / 2, P.SW1_TOP + 1.5), "pin Ø4, 0.3 above SW1", (-2, -16), ha="right") if False else d.note((y - P.BTN_PIN_D / 2, P.SW1_TOP + 2), "pin Ø4, 0.3 above SW1", (-6, -14), ha="right")
    d.note((y + P.BTN_FLANGE_D / 2 - 1, zp + 0.5), "flange \u00d816 x 1, bonded", (-8, -18), ha="right")
