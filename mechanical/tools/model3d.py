"""Shaded isometric pictures of the case built from params (matplotlib, no CAD needed)."""
import math
import numpy as np
import matplotlib.colors as mc
import params as P
from drawlib import rrect_pts, arc_pts

OLIVE, OLIVE_D, BLACK = "#5d6b4a", "#4b573b", "#1d1d1d"
LIGHT = np.array([-0.35, -0.55, 0.76]); LIGHT /= np.linalg.norm(LIGHT)

class Mesh:
    def __init__(self): self.faces, self.cols = [], []
    def add(self, pts, col, off=(0, 0, 0)):
        p = np.array(pts, float) + np.array(off)
        p[:, 1] *= -1                                   # case frame (KiCad-like, left-handed) -> right-handed for matplotlib
        n = np.cross(p[1] - p[0], p[2] - p[0]); ln = np.linalg.norm(n)
        k = 0.58 + 0.42 * abs(float(np.dot(n / ln, LIGHT))) if ln > 1e-12 else 1.0
        self.faces.append(p); self.cols.append(tuple(np.clip(np.array(mc.to_rgb(col)) * k, 0, 1)) + (1.0,))
    def prism(self, o, z0, z1, col, off=(0, 0, 0), top=True, bottom=True):
        for (x0, y0), (x1, y1) in zip(o[:-1], o[1:]):
            if abs(x0 - x1) + abs(y0 - y1) > 1e-9: self.add([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], col, off)
        if top: self.add([(x, y, z1) for x, y in o], col, off)
        if bottom: self.add([(x, y, z0) for x, y in o], col, off)
    def box(self, x0, y0, z0, x1, y1, z1, col, off=(0, 0, 0)):
        self.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], z0, z1, col, off)
    def cyl(self, cx, cy, r, z0, z1, col, off=(0, 0, 0), n=36):
        self.prism(arc_pts(cx, cy, r, 0, 360, n), z0, z1, col, off)
    def cyl_x(self, cy, cz, r, x0, x1, col, off=(0, 0, 0), n=28):
        ring = arc_pts(cy, cz, r, 0, 360, n)
        for (a0, b0), (a1, b1) in zip(ring[:-1], ring[1:]): self.add([(x0, a0, b0), (x1, a0, b0), (x1, a1, b1), (x0, a1, b1)], col, off)
        self.add([(x0, a, b) for a, b in ring], col, off); self.add([(x1, a, b) for a, b in ring], col, off)
    def cyl_y(self, cx, cz, r, y0, y1, col, off=(0, 0, 0), n=20):
        ring = arc_pts(cx, cz, r, 0, 360, n)
        for (a0, b0), (a1, b1) in zip(ring[:-1], ring[1:]): self.add([(a0, y0, b0), (a1, y0, b1), (a1, y1, b1), (a0, y1, b0)], col, off)
        self.add([(a, y0, b) for a, b in ring], col, off)
    def wallpatch_y(self, y, x0, x1, z0, z1, col, off=(0, 0, 0)):   # flat decal on a y-face
        self.add([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col, off)
    def wallpatch_x(self, x, y0, y1, z0, z1, col, off=(0, 0, 0)):
        self.add([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], col, off)

def outer(): return rrect_pts(-P.OUT_X, P.OUT_Y0, P.OUT_X, P.OUT_Y1, P.R_OUT)
def inner(): return rrect_pts(-P.IN_X, P.IN_Y0, P.IN_X, P.IN_Y1, P.R_IN)

def base(m, off=(0, 0, 0), open_top=False):
    m.cyl(0, P.CY, P.COLLAR_D / 2, -P.COLLAR_H, 0, OLIVE, off, 48)
    m.prism(outer(), 0, P.Z_SPLIT, OLIVE, off, top=not open_top)
    if open_top:
        o, i = outer(), inner()
        for k in range(len(o) - 1):
            m.add([o[k] + (P.Z_SPLIT,), o[k + 1] + (P.Z_SPLIT,), i[k + 1] + (P.Z_SPLIT,), i[k] + (P.Z_SPLIT,)], OLIVE, off)
        for (x0, y0), (x1, y1) in zip(i[:-1], i[1:]):
            m.add([(x0, y0, P.FLOOR), (x1, y1, P.FLOOR), (x1, y1, P.Z_SPLIT), (x0, y0, P.Z_SPLIT)], OLIVE_D, off)
        m.add([(x, y, P.FLOOR) for x, y in i], OLIVE_D, off)
        for p in P.SCREW_POS: m.cyl(p[0], p[1], P.COL_D / 2, P.FLOOR, P.Z_MEET, OLIVE, off, 18)
        for p in P.PCB_HOLES: m.cyl(p[0], p[1], P.SO_D / 2, P.FLOOR, P.Z_PCB_BOT, OLIVE, off, 18)
    e = 0.05
    # front decals: USB opening, vent slots
    m.wallpatch_y(P.OUT_Y1 + e, P.USBC[0] - P.USB_OPEN[0] / 2, P.USBC[0] + P.USB_OPEN[0] / 2, P.USB_Z - P.USB_OPEN[1] / 2, P.USB_Z + P.USB_OPEN[1] / 2, "#111111", off)
    V = P.VENT
    for i_ in range(V["n"]):
        x = V["x0"] + (i_ - (V["n"] - 1) / 2) * V["pitch"]
        m.wallpatch_y(P.OUT_Y1 + e, x - V["w"] / 2, x + V["w"] / 2, V["z0"], V["z0"] + V["h"], "#111111", off)
    # left: QR label
    w, h, y, z, _ = P.QR
    m.wallpatch_x(-P.OUT_X - e, y - w / 2, y + w / 2, z - h / 2, z + h / 2, "#f2f2f2", off)
    for a in range(5):
        for b in range(5):
            if (a * 7 + b * 3) % 3 == 0: m.wallpatch_x(-P.OUT_X - 2 * e, y - w / 2 + 3 + a * 4, y - w / 2 + 6 + a * 4, z - h / 2 + 5 + b * 4, z - h / 2 + 8 + b * 4, "#222222", off)

def lid(m, off=(0, 0, 0)):
    o = outer(); r = P.TOP_R
    m.prism(o, P.Z_SPLIT, P.Z_TOP - r, OLIVE, off, top=False, bottom=True)
    oi = rrect_pts(-P.OUT_X + r, P.OUT_Y0 + r, P.OUT_X - r, P.OUT_Y1 - r, P.R_OUT - r)
    for k in range(len(o) - 1):
        m.add([o[k] + (P.Z_TOP - r,), o[k + 1] + (P.Z_TOP - r,), oi[k + 1] + (P.Z_TOP,), oi[k] + (P.Z_TOP,)], OLIVE, off)
    m.add([(x, y, P.Z_TOP) for x, y in oi], OLIVE, off)
    px, py = P.PANEL_C
    m.prism(rrect_pts(px - P.PANEL_W / 2 - .4, py - P.PANEL_H / 2 - .4, px + P.PANEL_W / 2 + .4, py + P.PANEL_H / 2 + .4, 2), P.Z_TOP, P.Z_TOP + 0.02, "#3a4430", off)
    lx = P.LEDS[1][0]; ly = P.LEDS[1][1]; sw, sh, _ = P.LED_STRIP
    m.box(lx - sw / 2, ly - sh / 2, P.Z_TOP, lx + sw / 2, ly + sh / 2, P.Z_TOP + 0.03, "#2a2a2a", off)

def tops(m, off_panel=(0, 0, 0), off_btn=(0, 0, 0), off_rod=(0, 0, 0), lit=True):
    px, py = P.PANEL_C; z0 = P.Z_TOP - P.PANEL_REC
    m.box(px - P.PANEL_W / 2, py - P.PANEL_H / 2, z0, px + P.PANEL_W / 2, py + P.PANEL_H / 2, z0 + P.PANEL_T, "#1f2f57", off_panel)
    for i in range(1, 6):
        x = px - P.PANEL_W / 2 + i * P.PANEL_W / 6
        m.box(x - .15, py - P.PANEL_H / 2 + 1, z0 + P.PANEL_T, x + .15, py + P.PANEL_H / 2 - 1, z0 + P.PANEL_T + .02, "#8aa0c8", off_panel)
    m.cyl(P.SW1[0], P.SW1[1], P.BTN_CAP_D / 2, P.Z_TOP - 1, P.Z_TOP + P.BTN_PROUD, BLACK, off_btn, 32)
    if off_btn != (0, 0, 0):
        m.cyl(P.SW1[0], P.SW1[1], P.BTN_FLANGE_D / 2, P.Z_ROOF_IN, P.Z_ROOF_IN + P.BTN_FLANGE_T, BLACK, off_btn, 32)
        m.cyl(P.SW1[0], P.SW1[1], P.BTN_PIN_D / 2, P.SW1_TOP + 0.3, P.Z_ROOF_IN + 0.2, BLACK, off_btn, 16)
    for k, (x, y) in enumerate(P.LEDS):
        col = ["#46c04a", "#f0cc1a", "#e0372b"][k] if lit else "#dfeff8"
        if off_rod != (0, 0, 0): m.cyl(x, y, P.LED_ROD_D / 2, P.ROD_BOT, P.Z_TOP, "#dfeff8", off_rod, 12)
        else: m.cyl(x, y, P.LED_ROD_D / 2, P.Z_TOP, P.Z_TOP + 0.05, col, off_rod, 12)

def antenna(m, off=(0, 0, 0)):
    sx, sy, sz, _ = P.SMA
    m.cyl_x(sy, sz, 4.0, sx, sx + 6, "#c9a43a", off)              # SMA body
    m.cyl_x(sy, sz, 5.0, sx + 6, sx + 14, BLACK, off)             # hinge
    m.cyl(sx + 10, sy, 5.0, sz, sz + 85, BLACK, off, 20)          # whip, folded up
    m.cyl(sx + 10, sy, 5.5, sz + 80, sz + 92, BLACK, off, 20)

def gland(m, off=(0, 0, 0)):
    gx, gy, _, _ = P.GLAND
    m.cyl(gx, gy, 7.5, -12, 0, BLACK, off, 6)
    m.cyl(gx, gy, 3.0, -40, -12, BLACK, off, 12)

def pcb(m, off=(0, 0, 0)):
    m.prism(rrect_pts(-45, -25, 45, 25, 4), P.Z_PCB_BOT, P.Z_PCB_TOP, "#2f8f4e", off)
    zt = P.Z_PCB_TOP
    for (x, y, w, d, h, c) in ((-29.3, -10.2, 15.4, 20.5, 2.5, "#c4c4c4"), (21, -9, 10, 10, 2.6, "#909090"),
                              (P.USBC[0], P.USBC[1] + 1.4, 9.0, 7.3, 3.3, "#d0d0d0"), (P.J_SOLAR[0], P.J_SOLAR[1], 4, 4.4, 3.0, "#ece2c6"),
                              (P.J_RAIN[0], P.J_RAIN[1], 4, 4.4, 3.0, "#ece2c6"), (P.J_PROBE[0], P.J_PROBE[1], 11.6, 4.4, 2.5, "#ece2c6"),
                              (P.SW1[0], P.SW1[1], 4.6, 3.2, 2.75, "#333333")):
        m.box(x - w / 2, y - d / 2, zt, x + w / 2, y + d / 2, zt + h, c, off)
    for k, (x, y) in enumerate(P.LEDS):
        m.box(x - .8, y - .4, zt, x + .8, y + .4, zt + .8, ["#46b04a", "#e6c619", "#d9372b"][k], off)
    m.box(P.BATT_X[0], P.BATT_Y[0], P.Z_PCB_BOT - 2, P.BATT_X[1], P.BATT_Y[1], P.Z_PCB_BOT, "#1b1b1b", off)
    m.cyl_x(P.BATT_CY, P.CELL_ZC, P.CELL_D / 2, -32.5, 32.5, "#5f9ec4", off)

def tube(m, off=(0, 0, 0), length=110):
    m.cyl(0, P.CY, P.TUBE_OD / 2, -length, 0, OLIVE, off, 40)

def render(fig, rect, mesh, view=(24, -48), lims=None, aspect=None):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    ax = fig.add_axes(rect, projection="3d"); ax.set_proj_type("ortho"); ax.view_init(*view)
    ax.add_collection3d(Poly3DCollection(mesh.faces, facecolors=mesh.cols, edgecolors=(0.1, 0.1, 0.1, 0.55), linewidths=0.18))
    (x0, x1), (y0, y1), (z0, z1) = lims
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1); ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0)); ax.set_axis_off()
    ax.patch.set_alpha(0)
    return ax
