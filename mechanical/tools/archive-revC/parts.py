"""Case rev C solids as signed-distance functions (case frame, mm). Negative = inside material."""
import math, numpy as np
import params as P
from sdf import rrect2, circle2, capsule2, extrude, U, D, I

def smax(a, b, k):
    if k <= 0: return np.maximum(a, b)
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.maximum(a, b) + h * h * k * 0.25
def smin(a, b, k): return -smax(-a, -b, k)

def outer2(x, y, o=0.0): return rrect2(x, y, -P.OUT_X + o, P.OUT_Y0 + o, P.OUT_X - o, P.OUT_Y1 - o, P.R_OUT - o)
def inner2(x, y, o=0.0): return rrect2(x, y, -P.IN_X + o, P.IN_Y0 + o, P.IN_X - o, P.IN_Y1 - o, P.R_IN - o)
def cyl_z(x, y, z, cx, cy, r, z0, z1): return extrude(circle2(x, y, cx, cy, r), z, z0, z1)
S2 = math.sqrt(2)

# ---------------- lower body ----------------
def body_lower(x, y, z, off=0.0):
    """outer shape of the lower body (walls + 45 deg chin), offset inward by 'off'"""
    o = outer2(x, y) + off
    chin = (outer2(x, y) + P.CHIN - z) / S2 + off
    return smax(smax(o, chin, P.CHIN_R), -z + off, P.CHIN_R * 0.75)

def neck(x, y, z):
    r = np.hypot(x, y - P.CY)
    n = extrude(r - P.NECK_D / 2, z, P.COLLAR_Z1 - 1, 2.0)
    c = P.COLLAR_CH
    col = np.maximum(np.maximum(r - P.COLLAR_D / 2, (r - P.COLLAR_D / 2 + (z - P.COLLAR_Z1 + c)) / S2 * 0 + np.maximum(r - (P.COLLAR_D / 2 - c) - (P.COLLAR_Z1 - z), r - (P.COLLAR_D / 2 - c) - (z - P.COLLAR_Z0))), np.maximum(P.COLLAR_Z0 - z, z - P.COLLAR_Z1))
    return np.minimum(n, col)

def base(x, y, z):
    outer = np.maximum(body_lower(x, y, z), z - P.Z_SPLIT)
    d = smin(outer, neck(x, y, z), 3.0)
    cav = np.maximum(body_lower(x, y, z, P.SHELL), np.maximum(inner2(x, y), -z + 3.0))
    cav = np.maximum(cav, z - P.Z_SPLIT - 5)
    d = D(d, cav)
    within = np.maximum(body_lower(x, y, z), z - P.Z_SPLIT)
    cols = np.min([cyl_z(x, y, z, sx, sy, P.COL_D / 2, -5, P.Z_MEET) for sx, sy in P.SCREW_POS], axis=0)
    sos = np.min([cyl_z(x, y, z, sx, sy, P.SO_D / 2, -5, P.Z_PCB_BOT) for sx, sy in P.PCB_HOLES], axis=0)
    d = U(d, I(np.minimum(cols, sos), within))
    # decoration added on the outside: teardrop boss on the front face
    Dd = P.DROP
    w = Dd["r"] * np.clip((Dd["tip"] - z) / (Dd["tip"] - Dd["zc"]), 0.08, 1.0)
    drop2 = np.minimum(circle2(x, z, Dd["xc"], Dd["zc"], Dd["r"]), np.maximum(np.abs(x - Dd["xc"]) - w, np.maximum(z - Dd["tip"], Dd["zc"] - z)))
    drop = extrude(drop2 - 0.0, y, P.OUT_Y1 - 2.0, P.OUT_Y1 + Dd["proud"])
    d = smin(d, drop, 0.8)
    cut = []
    ring = I(outer2(x, y, P.GROOVE_OFF), -outer2(x, y, P.GROOVE_OFF + P.GROOVE_W))
    cut.append(extrude(ring, z, P.Z_SPLIT - P.GROOVE_D, P.Z_SPLIT + 5))
    cut.append(np.maximum(-P.SEAM_V - outer2(x, y) + (P.Z_SPLIT - z), z - P.Z_SPLIT - 1))       # seam V (lower half)
    for sx, sy in P.SCREW_POS:
        cut.append(cyl_z(x, y, z, sx, sy, P.COL_HOLE / 2, -5, P.Z_MEET + 5)); cut.append(cyl_z(x, y, z, sx, sy, P.CB_D / 2, -5, P.CB_SEAT))
    for sx, sy in P.PCB_HOLES: cut.append(cyl_z(x, y, z, sx, sy, P.SO_PILOT / 2, P.Z_PCB_BOT - P.SO_PILOT_DEPTH, P.Z_PCB_BOT + 5))
    cut.append(cyl_z(x, y, z, 0, P.CY, P.SOCKET_D / 2, P.COLLAR_Z0 - 5, P.COLLAR_Z0 + P.SOCKET_DEPTH))
    cut.append(cyl_z(x, y, z, 0, P.CY, P.NECK_BORE / 2, P.COLLAR_Z0, 1.0))
    cut.append(extrude(capsule2(x, y, P.SLOT[0], P.SLOT[1], P.SLOT[2], P.SLOT[3]), z, -5, 6))
    gx, gy, gd, _ = P.GLAND; cut.append(cyl_z(x, y, z, gx, gy, gd / 2, -5, 6))
    uw, uh, ur = P.USB_OPEN
    cut.append(extrude(rrect2(x, z, P.USBC[0] - uw / 2, P.USB_Z - uh / 2, P.USBC[0] + uw / 2, P.USB_Z + uh / 2, ur), y, P.IN_Y1 - 2, P.OUT_Y1 + 3))
    V = P.VENT; pw, ph, pd, pr = V["pocket"]; zc = V["z0"] + V["h"] / 2
    cut.append(extrude(rrect2(x, z, V["xc"] - pw / 2, zc - ph / 2, V["xc"] + pw / 2, zc + ph / 2, pr), y, P.OUT_Y1 - pd, P.OUT_Y1 + 3))
    for i in range(V["n"]):
        vx = V["xc"] + (i - (V["n"] - 1) / 2) * V["pitch"]
        cut.append(extrude(rrect2(x, z, vx - V["w"] / 2, V["z0"], vx + V["w"] / 2, V["z0"] + V["h"], V["w"] / 2 - 0.01), y, P.IN_Y1 - 3, P.OUT_Y1 + 3))
    sx, sy, sz, sd = P.SMA
    cut.append(extrude(circle2(y, z, sy, sz, sd / 2), x, P.IN_X - 3, P.OUT_X + 3))
    w_, h_, qy, qz, dep = P.QR
    cut.append(extrude(rrect2(y, z, qy - w_ / 2, qz - h_ / 2, qy + w_ / 2, qz + h_ / 2, 1.5), x, P.OUT_X - dep, P.OUT_X + 3))
    return D(d, np.min(cut, axis=0))

# ---------------- cap ----------------
def cap_shape(x, y, z, off=0.0):
    dz = np.maximum(z - P.Z_SPLIT, 0)
    ts, tr = math.tan(math.radians(P.CAP_DRAFT)), math.tan(math.radians(P.CAP_DRAFT_REAR))
    side = rrect2(x, y, -P.OUT_X + dz * ts, P.OUT_Y0 + dz * tr, P.OUT_X - dz * ts, P.OUT_Y1 - dz * ts, P.R_OUT) * math.cos(math.radians(P.CAP_DRAFT)) + off
    top = (z - P.z_top(y)) * math.cos(math.radians(P.TOP_SLOPE)) + off
    yb = P.OUT_Y1 - (P.BEVEL_Z - P.Z_SPLIT) * ts
    bev = ((y - yb) + (z - P.BEVEL_Z)) / S2 + off
    return smax(smax(side, top, P.TOP_BLEND), bev, P.BEVEL_BLEND)

def lid(x, y, z):
    outer = np.maximum(cap_shape(x, y, z), P.Z_SPLIT - z)
    cav = np.maximum(cap_shape(x, y, z, P.CAP_WALL), P.Z_SPLIT + 2.0 - z)
    cav2 = np.maximum(inner2(x, y, P.LIP_GAP + P.LIP_T), np.maximum(P.Z_SPLIT - 5 - z, z - (P.Z_SPLIT + 2.5)))
    d = D(outer, np.minimum(cav, cav2))
    lip = extrude(I(inner2(x, y, P.LIP_GAP), -inner2(x, y, P.LIP_GAP + P.LIP_T)), z, P.Z_SPLIT - P.LIP_H, P.Z_SPLIT + 0.5)
    lip = I(lip, outer2(x, y))
    bos = np.min([cyl_z(x, y, z, sx, sy, P.COL_D / 2, P.Z_MEET, 120) for sx, sy in P.SCREW_POS], axis=0)
    low = np.maximum(np.maximum(body_lower(x, y, z, P.SHELL + P.LIP_GAP), inner2(x, y, P.LIP_GAP)), z - P.Z_SPLIT - 0.5)
    bos = I(bos, np.minimum(low, outer))
    zr = P.z_top(P.SW1[1]) - P.ROOF_T
    sleeve = extrude(I(circle2(x, y, *P.SW1, P.SLEEVE_OD / 2), -circle2(x, y, *P.SW1, P.SLEEVE_ID / 2)), z, zr - P.SLEEVE_L, zr + 1)
    L = P.LED_BAR
    d = np.min([d, lip, bos, I(sleeve, outer)], axis=0)
    cut = []
    cut.append(np.maximum(-P.SEAM_V - outer2(x, y) + (z - P.Z_SPLIT), P.Z_SPLIT - 1 - z))     # seam V (upper half)
    px, py = P.PANEL_C; c = P.PANEL_CLR
    cut.append(np.maximum(rrect2(x, y, px - P.PANEL_W / 2 - c, py - P.PANEL_H / 2 - c, px + P.PANEL_W / 2 + c, py + P.PANEL_H / 2 + c, 2.0), P.z_top(y) - P.PANEL_REC - z))
    wx, wy, wd = P.PANEL_WIRE; cut.append(cyl_z(x, y, z, wx, wy, wd / 2, 60, 130))
    cut.append(cyl_z(x, y, z, *P.SW1, P.BTN_HOLE_D / 2, zr - 2, 130))
    cut.append(cyl_z(x, y, z, *P.SW1, P.BTN_POCKET_D / 2, zr - 8, zr + P.BTN_FLANGE_T))
    cut.append(cyl_z(x, y, z, *P.SW1, P.SLEEVE_ID / 2, zr - P.SLEEVE_L - 2, zr + 2))
    cut.append(extrude(rrect2(x, z, L["x0"] - 0.2, L["z0"] - 0.2, L["x1"] + 0.2, L["z1"] + 0.2, 1.2), y, L["y_in"], P.OUT_Y1 + 5))
    for sx, sy in P.SCREW_POS:
        cut.append(cyl_z(x, y, z, sx, sy, P.INSERT_D / 2, P.Z_MEET - 5, P.Z_MEET + P.INSERT_L)); cut.append(cyl_z(x, y, z, sx, sy, 1.3, P.Z_MEET, P.Z_MEET + 14))
    return D(d, np.min(cut, axis=0))

# ---------------- small parts ----------------
def button(x, y, z):
    zr = P.z_top(P.SW1[1]) - P.ROOF_T; bx, by = P.SW1
    fl = cyl_z(x, y, z, bx, by, P.BTN_FLANGE_D / 2, zr, zr + P.BTN_FLANGE_T)
    capt = (z - (P.z_top(y) + P.BTN_PROUD)) * math.cos(math.radians(P.TOP_SLOPE))
    cap = smax(circle2(x, y, bx, by, P.BTN_CAP_D / 2), np.maximum(capt, zr - z), 1.2)
    d = np.minimum(fl, cap)
    # power icon engraved 0.5 on the cap top: open ring + bar (bar points to the rear)
    r = np.hypot(x - bx, y - by); ang = np.degrees(np.arctan2(-(y - by), x - bx))
    ring = np.maximum(np.abs(r - 3.6) - 0.5, -(np.abs(ang - 90) - 38))
    bar = np.maximum(np.abs(x - bx) - 0.5, np.maximum(-(y - by) - 5.2, (y - by) - 0.6))
    icon = np.maximum(np.minimum(ring, bar), -(capt + 0.5))
    return D(d, icon)

def plunger(x, y, z):
    zr = P.z_top(P.SW1[1]) - P.ROOF_T
    return cyl_z(x, y, z, *P.SW1, P.PLUNGER_D / 2, P.SW1_TOP + 0.3, zr)

def light_bar(x, y, z):
    L = P.LED_BAR
    yf = P.OUT_Y1 - ((L["z0"] + L["z1"]) / 2 - P.Z_SPLIT) * math.tan(math.radians(P.CAP_DRAFT)) - 0.1
    bar = extrude(rrect2(x, z, L["x0"], L["z0"], L["x1"], L["z1"], 1.0), y, L["y_in"], yf)
    posts = np.min([extrude(rrect2(x, y, lx - L["post"] / 2, ly - L["post"] / 2, lx + L["post"] / 2, ly + L["post"] / 2, 0.3), z, P.LED_TOP + 0.3, L["z0"] + 0.5) for lx, ly in P.LEDS], axis=0)
    d = np.minimum(bar, posts)
    seps = [extrude(rrect2(x, y, sx - L["sep"] / 2, L["y_in"] - 1, sx + L["sep"] / 2, yf - 0.8, 0.01), z, L["z0"] - 1, L["z1"] + 1) for sx in ((P.LEDS[0][0] + P.LEDS[1][0]) / 2, (P.LEDS[1][0] + P.LEDS[2][0]) / 2)]
    return D(d, np.min(seps, axis=0))

TIP_SLEEVE_OD, TIP_SOCKET_D, TIP_SOCKET_DEPTH, TIP_CONE_L = 38.0, 32.4, 15.0, 60.0
def tip(x, y, z):
    r = np.hypot(x, y)
    cone = np.maximum(r - (TIP_SLEEVE_OD / 2) * np.clip((z + TIP_CONE_L) / TIP_CONE_L, 0.03, 1) * 0.95, np.maximum(-TIP_CONE_L - z, z))
    body = np.minimum(cone, extrude(r - TIP_SLEEVE_OD / 2, z, -2.0, TIP_SOCKET_DEPTH))
    return np.maximum(body, -extrude(r - TIP_SOCKET_D / 2, z, 0.0, TIP_SOCKET_DEPTH + 5))

zr_btn = P.z_top(P.SW1[1]) - P.ROOF_T
BOUNDS = {
    "base": ((-P.OUT_X, P.OUT_Y0, P.COLLAR_Z0), (P.OUT_X, P.OUT_Y1 + P.DROP["proud"], P.Z_SPLIT)),
    "lid": ((-P.OUT_X, P.OUT_Y0, P.Z_MEET), (P.OUT_X, P.OUT_Y1, P.Z_TOP_REAR)),
    "button": ((P.SW1[0] - 11, P.SW1[1] - 11, zr_btn - 0.5), (P.SW1[0] + 11, P.SW1[1] + 11, P.z_top(P.SW1[1] - 9) + P.BTN_PROUD + 0.5)),
    "plunger": ((P.SW1[0] - 3, P.SW1[1] - 3, P.SW1_TOP), (P.SW1[0] + 3, P.SW1[1] + 3, zr_btn)),
    "light_bar": ((P.LED_BAR["x0"], P.LED_BAR["y_in"], P.LED_TOP), (P.LED_BAR["x1"], P.OUT_Y1, P.LED_BAR["z1"])),
    "tip": ((-TIP_SLEEVE_OD / 2, -TIP_SLEEVE_OD / 2, -TIP_CONE_L), (TIP_SLEEVE_OD / 2, TIP_SLEEVE_OD / 2, TIP_SOCKET_DEPTH)),
}
