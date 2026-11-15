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
    cut.append(extrude(circle2(x, z, sx, sz, sd / 2), y, P.OUT_Y0 - 3, P.IN_Y0 + 3))          # rear wall
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

def seg_cyl(x, y, z, a, b, r):
    """capped cylinder between 3D points a and b"""
    a = np.asarray(a, float); b = np.asarray(b, float); ba = b - a; L2 = ba @ ba
    px, py, pz = x - a[0], y - a[1], z - a[2]
    t = (px * ba[0] + py * ba[1] + pz * ba[2]) / L2
    qx, qy, qz = px - ba[0] * t, py - ba[1] * t, pz - ba[2] * t
    rr = np.sqrt(qx * qx + qy * qy + qz * qz) - r; hh = (np.abs(t - 0.5) - 0.5) * math.sqrt(L2)
    return np.minimum(np.maximum(rr, hh), 0) + np.hypot(np.maximum(rr, 0), np.maximum(hh, 0))

def local_cyl(x, y, z, cx, y_r, r, h0, h1):
    """cylinder perpendicular to the sloped top, centred at plan (cx, y_r), from h0 to h1 above the top plane"""
    s, h = P.to_local(y, z, y_r)
    return extrude(np.hypot(x - cx, s), h, h0, h1) if False else extrude(np.hypot(x - cx, s) - r, h, h0, h1)

def stem2(x, y, o=0.0):
    bx, by = P.BTN_C
    return np.maximum(circle2(x, y, bx, by, P.PLUNGER_D / 2 + o), (x - bx) - (P.PLUNGER_FLAT + o))

def lens2(x, z, o=0.0):
    L = P.LED_LENS
    return rrect2(x, z, L["xc"] - L["w"] / 2 - o, L["zc"] - L["h"] / 2 - o, L["xc"] + L["w"] / 2 + o, L["zc"] + L["h"] / 2 + o, L["r"] + o)

def lid(x, y, z):
    outer = np.maximum(cap_shape(x, y, z), P.Z_SPLIT - z)
    cav = np.maximum(cap_shape(x, y, z, P.CAP_WALL), P.Z_SPLIT + 2.0 - z)
    cav2 = np.maximum(inner2(x, y, P.LIP_GAP + P.LIP_T), np.maximum(P.Z_SPLIT - 5 - z, z - (P.Z_SPLIT + 2.5)))
    d = D(outer, np.minimum(cav, cav2))
    lip = I(extrude(I(inner2(x, y, P.LIP_GAP), -inner2(x, y, P.LIP_GAP + P.LIP_T)), z, P.Z_SPLIT - P.LIP_H, P.Z_SPLIT + 0.5), outer2(x, y))
    bos = np.min([cyl_z(x, y, z, sx, sy, P.COL_D / 2, P.Z_MEET, 130) for sx, sy in P.SCREW_POS], axis=0)
    low = np.maximum(np.maximum(body_lower(x, y, z, P.SHELL + P.LIP_GAP), inner2(x, y, P.LIP_GAP)), z - P.Z_SPLIT - 0.5)
    bos = I(bos, np.minimum(low, outer))
    bx, by = P.BTN_C
    # D-shaped guide sleeve under the button, hung from the roof by 4 ribs
    sleeve = extrude(I(circle2(x, y, bx, by, P.SLEEVE_OD / 2), -stem2(x, y, P.SLEEVE_GAP)), z, P.SLEEVE_Z0, 130)
    zb = P.z_top(by) - P.ROOF_T - 10
    ribs = np.minimum(np.maximum(np.abs(x - bx) - P.RIB_T / 2, np.maximum(P.SLEEVE_OD / 2 - 0.2 - np.abs(y - by), np.abs(y - by) - P.RIB_R)),
                      np.maximum(np.abs(y - by) - P.RIB_T / 2, np.maximum(P.SLEEVE_OD / 2 - 0.2 - np.abs(x - bx), np.abs(x - bx) - P.RIB_R)))
    ribs = np.maximum(ribs, zb - z)
    d = np.min([d, lip, bos, I(np.minimum(sleeve, ribs), outer)], axis=0)
    cut = [np.maximum(-P.SEAM_V - outer2(x, y) + (z - P.Z_SPLIT), P.Z_SPLIT - 1 - z)]
    # panel recess, in the sloped plane
    s, h = P.to_local(y, z, P.PANEL_C[1]); c = P.PANEL_CLR
    cut.append(np.maximum(rrect2(x, s, -P.PANEL_W / 2 - c, -P.PANEL_H / 2 - c, P.PANEL_W / 2 + c, P.PANEL_H / 2 + c, 2.0), -P.PANEL_REC - h))
    wx, wy, wd = P.PANEL_WIRE; cut.append(local_cyl(x, y, z, wx, wy, wd / 2, -12, 5))
    # button: hole + flange pocket (perpendicular to the top), stem path
    cut.append(local_cyl(x, y, z, bx, by, P.BTN_HOLE_D / 2, -P.ROOF_T - 3, 5))
    cut.append(local_cyl(x, y, z, bx, by, P.BTN_POCKET_D / 2, -P.ROOF_T - P.BTN_TRAVEL_ROOM, -P.ROOF_T + P.BTN_FLANGE_T))
    cut.append(extrude(stem2(x, y, P.SLEEVE_GAP), z, P.SLEEVE_Z0 - 5, 130))
    # LED lens window in the cap front
    cut.append(extrude(lens2(x, z, 0.15), y, P.IN_Y1 - 6, P.OUT_Y1 + 5))
    for sx, sy in P.SCREW_POS:
        cut.append(cyl_z(x, y, z, sx, sy, P.INSERT_D / 2, P.Z_MEET - 5, P.Z_MEET + P.INSERT_L)); cut.append(cyl_z(x, y, z, sx, sy, 1.3, P.Z_MEET, P.Z_MEET + 14))
    return D(d, np.min(cut, axis=0))

# ---------------- small parts ----------------
def button(x, y, z):
    bx, by = P.BTN_C
    s, h = P.to_local(y, z, by)
    fl = extrude(np.hypot(x - bx, s) - P.BTN_FLANGE_D / 2, h, -P.ROOF_T, -P.ROOF_T + P.BTN_FLANGE_T)
    cap = smax(np.hypot(x - bx, s) - P.BTN_CAP_D / 2, np.maximum(h - P.BTN_PROUD, -P.ROOF_T - h + 0.2), 1.2)
    d = np.minimum(fl, cap)
    r = np.hypot(x - bx, s); ang = np.degrees(np.arctan2(-s, x - bx))
    ring = np.maximum(np.abs(r - 3.6) - 0.5, -(np.abs(ang - 90) - 38))
    bar = np.maximum(np.abs(x - bx) - 0.5, np.maximum(-s - 5.2, s - 0.6))
    icon = np.maximum(np.minimum(ring, bar), -(h - P.BTN_PROUD + 0.5))
    return D(d, icon)

def plunger(x, y, z):
    bx, by = P.BTN_C; sx, sy = P.SW1
    s, h = P.to_local(y, z, by)
    stem = np.maximum(extrude(stem2(x, y), z, P.ARM_Z0, 130), h + P.ROOF_T)          # top = flange underside
    arm = extrude(rrect2(x, y, sx - 2.5, by - P.ARM_W / 2, bx + P.PLUNGER_FLAT, by + P.ARM_W / 2, 0.01), z, P.ARM_Z0, P.ARM_Z0 + P.ARM_T)   # ends flush with the D flat (print face)
    nub = cyl_z(x, y, z, sx, sy, P.NUB_D / 2, P.SW1_TOP + 0.3, P.ARM_Z0 + 0.5)
    return np.min([stem, arm, nub], axis=0)

def _lens_y():
    L = P.LED_LENS; ts = math.tan(math.radians(P.CAP_DRAFT))
    yf = P.OUT_Y1 - (L["zc"] - P.Z_SPLIT) * ts
    return yf, yf - P.CAP_WALL / math.cos(math.radians(P.CAP_DRAFT))

def light_bar(x, y, z):
    """smoked/clear PETG: lens plate filling the cap window + 3 light pipes from the LEDs to the spots"""
    L = P.LED_LENS
    lens = np.maximum(np.maximum(lens2(x, z), P.IN_Y1 - 8 - y), np.maximum(cap_shape(x, y, z) + 0.05, -cap_shape(x, y, z, P.CAP_WALL)))
    yf, yb = _lens_y()
    d = lens
    for (lx, ly), sx in zip(P.LEDS, P.LED_SPOT_X):
        a = (lx, ly, P.LED_TOP + 0.3); m = (lx, ly, P.LED_TOP + 5.0); b = (sx, yb + 0.6, L["zc"])
        pipe = np.minimum(seg_cyl(x, y, z, a, m, P.LED_PIPE_D / 2), seg_cyl(x, y, z, m, b, P.LED_PIPE_D / 2))
        cone = seg_cyl(x, y, z, (sx, yb - 3.0, L["zc"]), (sx, yb + 0.6, L["zc"]), P.LED_SPOT_D / 2 - 0.4)
        d = np.min([d, pipe, cone], axis=0)
    return d

TIP_SLEEVE_OD, TIP_SOCKET_D, TIP_SOCKET_DEPTH, TIP_CONE_L = 38.0, 32.4, 15.0, 60.0
def tip(x, y, z):
    r = np.hypot(x, y)
    cone = np.maximum(r - (TIP_SLEEVE_OD / 2) * np.clip((z + TIP_CONE_L) / TIP_CONE_L, 0.03, 1) * 0.95, np.maximum(-TIP_CONE_L - z, z))
    body = np.minimum(cone, extrude(r - TIP_SLEEVE_OD / 2, z, -2.0, TIP_SOCKET_DEPTH))
    return np.maximum(body, -extrude(r - TIP_SOCKET_D / 2, z, 0.0, TIP_SOCKET_DEPTH + 5))

BOUNDS = {
    "base": ((-P.OUT_X, P.OUT_Y0, P.COLLAR_Z0), (P.OUT_X, P.OUT_Y1 + P.DROP["proud"], P.Z_SPLIT)),
    "lid": ((-P.OUT_X, P.OUT_Y0, P.Z_MEET), (P.OUT_X, P.OUT_Y1, P.Z_TOP_REAR)),
    "button": ((P.BTN_C[0] - 11, P.BTN_C[1] - 12, P.z_top(P.BTN_C[1]) - 8), (P.BTN_C[0] + 11, P.BTN_C[1] + 12, P.z_top(P.BTN_C[1]) + 6)),
    "plunger": ((P.SW1[0] - 3, P.BTN_C[1] - 4, P.SW1_TOP), (P.BTN_C[0] + 4, P.BTN_C[1] + 4, P.z_top(P.BTN_C[1]))),
    "light_bar": ((-22, P.LEDS[0][1] - 3, P.LED_TOP), (22, P.OUT_Y1, P.LED_LENS["zc"] + 6)),
    "tip": ((-TIP_SLEEVE_OD / 2, -TIP_SLEEVE_OD / 2, -TIP_CONE_L), (TIP_SLEEVE_OD / 2, TIP_SLEEVE_OD / 2, TIP_SOCKET_DEPTH)),
}
