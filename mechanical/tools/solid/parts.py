"""Case rev B parts as SDFs, case frame (mm). Same geometry as mechanical/cad/gaiapus_case_revB.scad."""
import numpy as np
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import params as P
from sdf import *

def outer2(x, y, o=0.0): return rrect2(x, y, -P.OUT_X + o, P.OUT_Y0 + o, P.OUT_X - o, P.OUT_Y1 - o, P.R_OUT - o)
def inner2(x, y, o=0.0): return rrect2(x, y, -P.IN_X + o, P.IN_Y0 + o, P.IN_X - o, P.IN_Y1 - o, P.R_IN - o)
def cyl_z(x, y, z, cx, cy, r, z0, z1): return extrude(circle2(x, y, cx, cy, r), z, z0, z1)

def base(x, y, z):
    d = U(extrude(outer2(x, y), z, 0, P.Z_SPLIT), cyl_z(x, y, z, 0, P.CY, P.COLLAR_D / 2, -P.COLLAR_H, 0.5))
    d = D(d, extrude(inner2(x, y), z, P.FLOOR, P.Z_SPLIT + 5))
    cols = np.min([cyl_z(x, y, z, sx, sy, P.COL_D / 2, 0, P.Z_MEET) for sx, sy in P.SCREW_POS], axis=0)
    sos = np.min([cyl_z(x, y, z, sx, sy, P.SO_D / 2, P.FLOOR - 0.5, P.Z_PCB_BOT) for sx, sy in P.PCB_HOLES], axis=0)
    d = U(d, I(cols, extrude(outer2(x, y), z, 0, P.Z_MEET)), sos)
    cut = []
    ring = I(outer2(x, y, P.GROOVE_OFF), -outer2(x, y, P.GROOVE_OFF + P.GROOVE_W))
    cut.append(extrude(ring, z, P.Z_SPLIT - P.GROOVE_D, P.Z_SPLIT + 5))
    for sx, sy in P.SCREW_POS:
        cut.append(cyl_z(x, y, z, sx, sy, P.COL_HOLE / 2, -5, P.Z_MEET + 5)); cut.append(cyl_z(x, y, z, sx, sy, P.CB_D / 2, -5, P.CB_DEPTH))
    for sx, sy in P.PCB_HOLES: cut.append(cyl_z(x, y, z, sx, sy, P.SO_PILOT / 2, P.Z_PCB_BOT - P.SO_PILOT_DEPTH, P.Z_PCB_BOT + 5))
    cut.append(cyl_z(x, y, z, 0, P.CY, P.SOCKET_D / 2, -P.COLLAR_H - 5, 0))
    cut.append(extrude(capsule2(x, y, P.SLOT[0], P.SLOT[1], P.SLOT[2], P.SLOT[3]), z, -5, P.FLOOR + 5))
    gx, gy, gd, _ = P.GLAND; cut.append(cyl_z(x, y, z, gx, gy, gd / 2, -5, P.FLOOR + 5))
    # front wall: USB-C + vent slots (profiles in the x-z plane, through y)
    uw, uh, ur = P.USB_OPEN
    cut.append(extrude(rrect2(x, z, P.USBC[0] - uw / 2, P.USB_Z - uh / 2, P.USBC[0] + uw / 2, P.USB_Z + uh / 2, ur), y, P.IN_Y1 - 2, P.OUT_Y1 + 2))
    V = P.VENT
    for i in range(V["n"]):
        vx = V["x0"] + (i - (V["n"] - 1) / 2) * V["pitch"]
        cut.append(extrude(rrect2(x, z, vx - V["w"] / 2, V["z0"], vx + V["w"] / 2, V["z0"] + V["h"], V["w"] / 2 - 0.01), y, P.IN_Y1 - 2, P.OUT_Y1 + 2))
    sx, sy, sz, sd = P.SMA
    cut.append(extrude(circle2(y, z, sy, sz, sd / 2), x, P.IN_X - 2, P.OUT_X + 2))
    w, h, qy, qz, dep = P.QR
    cut.append(extrude(rrect2(y, z, qy - w / 2, qz - h / 2, qy + w / 2, qz + h / 2, 1.0), x, -P.OUT_X - 2, -P.OUT_X + dep))
    return D(d, np.min(cut, axis=0))

def lid(x, y, z):
    r = P.TOP_R
    body = round_top(outer2(x, y, r), z, P.Z_SPLIT, P.Z_TOP, r)
    lip = extrude(I(inner2(x, y, P.LIP_GAP), -inner2(x, y, P.LIP_GAP + P.LIP_T)), z, P.Z_SPLIT - P.LIP_H, P.Z_SPLIT + 0.5)
    d = D(U(body, lip), extrude(inner2(x, y, P.LIP_GAP + P.LIP_T), z, P.Z_SPLIT - 5, P.Z_ROOF_IN))
    bosses = np.min([cyl_z(x, y, z, sx, sy, P.COL_D / 2, P.Z_MEET, P.Z_ROOF_IN + 0.5) for sx, sy in P.SCREW_POS], axis=0)
    lx, ly = P.LEDS[1]; hw, hh = P.ROD_HOLDER
    holder = extrude(rrect2(x, y, lx - hw / 2, ly - hh / 2, lx + hw / 2, ly + hh / 2, 0.01), z, P.ROD_HOLDER_Z, P.Z_ROOF_IN + 0.5)
    d = U(d, I(bosses, extrude(inner2(x, y, P.LIP_GAP), z, P.Z_MEET - 1, P.Z_TOP)), holder)
    px, py = P.PANEL_C; c = P.PANEL_CLR
    cut = [extrude(rrect2(x, y, px - P.PANEL_W / 2 - c, py - P.PANEL_H / 2 - c, px + P.PANEL_W / 2 + c, py + P.PANEL_H / 2 + c, 2.0), z, P.Z_TOP - P.PANEL_REC, P.Z_TOP + 5)]
    wx, wy, wd = P.PANEL_WIRE; cut.append(cyl_z(x, y, z, wx, wy, wd / 2, P.Z_ROOF_IN - 5, P.Z_TOP + 5))
    bx, by = P.SW1
    cut.append(cyl_z(x, y, z, bx, by, P.BTN_HOLE_D / 2, P.Z_ROOF_IN - 5, P.Z_TOP + 5))
    cut.append(cyl_z(x, y, z, bx, by, P.BTN_POCKET_D / 2, P.Z_ROOF_IN - 5, P.Z_ROOF_IN + P.BTN_FLANGE_T))   # pocket 1 mm into the roof
    sw, sh, sd = P.LED_STRIP
    cut.append(extrude(rrect2(x, y, lx - sw / 2, ly - sh / 2, lx + sw / 2, ly + sh / 2, 0.5), z, P.Z_TOP - sd, P.Z_TOP + 5))
    for ex, ey in P.LEDS: cut.append(cyl_z(x, y, z, ex, ey, P.LED_HOLE_D / 2, P.ROD_HOLDER_Z - 5, P.Z_TOP + 5))
    for sx, sy in P.SCREW_POS:
        cut.append(cyl_z(x, y, z, sx, sy, P.INSERT_D / 2, P.Z_MEET - 5, P.Z_MEET + P.INSERT_L)); cut.append(cyl_z(x, y, z, sx, sy, 1.3, P.Z_MEET, P.Z_ROOF_IN))
    return D(d, np.min(cut, axis=0))

def button(x, y, z):
    bx, by = P.SW1; zr, ft = P.Z_ROOF_IN, P.BTN_FLANGE_T
    return np.min([cyl_z(x, y, z, bx, by, P.BTN_FLANGE_D / 2, zr, zr + ft),                         # flange sits in the pocket
                   round_top(circle2(x, y, bx, by, P.BTN_CAP_D / 2 - 0.6), z, zr + ft - 0.2, P.Z_TOP + P.BTN_PROUD, 0.6),
                   cyl_z(x, y, z, bx, by, P.BTN_PIN_D / 2, P.SW1_TOP + 0.3, zr + 0.2)], axis=0)

BOUNDS = {
    "base": ((-P.OUT_X, P.OUT_Y0, -P.COLLAR_H), (P.OUT_X, P.OUT_Y1, P.Z_SPLIT)),
    "lid": ((-P.OUT_X, P.OUT_Y0, P.Z_MEET), (P.OUT_X, P.OUT_Y1, P.Z_TOP)),
    "button": ((P.SW1[0] - 9, P.SW1[1] - 9, P.SW1_TOP), (P.SW1[0] + 9, P.SW1[1] + 9, P.Z_TOP + P.BTN_PROUD)),
}

# ---- tip: printable cone with a socket for the PVC tube (z = 0 at the tube end) ----
TIP_SLEEVE_OD, TIP_SOCKET_D, TIP_SOCKET_DEPTH, TIP_CONE_L = 38.0, 32.4, 15.0, 60.0
def tip(x, y, z):
    r = np.hypot(x, y)
    cone = np.maximum(r - (TIP_SLEEVE_OD / 2) * np.clip((z + TIP_CONE_L) / TIP_CONE_L, 0.03, 1) * 0.95, np.maximum(-TIP_CONE_L - z, z)) 
    sleeve = extrude(r - TIP_SLEEVE_OD / 2, z, -2.0, TIP_SOCKET_DEPTH)
    body = np.minimum(cone, sleeve)
    return np.maximum(body, -extrude(r - TIP_SOCKET_D / 2, z, 0.0, TIP_SOCKET_DEPTH + 5))
BOUNDS["tip"] = ((-TIP_SLEEVE_OD / 2, -TIP_SLEEVE_OD / 2, -TIP_CONE_L), (TIP_SLEEVE_OD / 2, TIP_SLEEVE_OD / 2, TIP_SOCKET_DEPTH))
