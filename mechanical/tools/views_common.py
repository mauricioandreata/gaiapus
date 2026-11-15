import math
import params as P
from drawlib import *

HATCH = "////"
F_PLAN = lambda a, b: (a, -b)        # top view, front edge at the bottom of the sheet (same as KiCad)
F_FRONT = lambda a, b: (a, b)        # (x, z)
F_RIGHT = lambda a, b: (-a, b)       # (y, z), front on the left
F_BOTTOM = lambda a, b: (a, b)       # (x, y) seen from below, front up
F_UNDER = lambda a, b: (-a, -b)      # lid underside, seen from below

def outer(): return rrect_pts(-P.OUT_X, P.OUT_Y0, P.OUT_X, P.OUT_Y1, P.R_OUT)
def inner(o=0.0): return rrect_pts(-P.IN_X + o, P.IN_Y0 + o, P.IN_X - o, P.IN_Y1 - o, P.R_IN - o)
def ring(o): return rrect_pts(-P.OUT_X + o, P.OUT_Y0 + o, P.OUT_X - o, P.OUT_Y1 - o, P.R_OUT - o)

def obround(v, cx, cy, L, W, sty="vis"):
    r = W / 2; a = L / 2 - r
    pts = arc_pts(cx + a, cy, r, -90, 90) + arc_pts(cx - a, cy, r, 90, 270)
    v.poly(pts + [pts[0]], sty)

def datum(v):
    v.cross((0, 0), 6, "cen")
    v.text((1.2, 1.4) if v.f(0, 1)[1] > 0 else (1.2, -1.4), "0,0", 2.0)

def sect_mark(v, p, q, label, toward, ext=5.0):
    v.line(p, q, "sect")
    for e in (p, q):
        a = v.f(*e); d = v.f(e[0] + toward[0], e[1] + toward[1]); dv = (d[0] - a[0], d[1] - a[1])
        L = math.hypot(*dv); dv = (dv[0] / L, dv[1] / L)
        tip = (a[0] + dv[0] * ext / v.s, a[1] + dv[1] * ext / v.s)
        v.ents.append(("seg", a, tip, "sect")); v.ents.append(("arrow", tip, dv, "dim"))
        v.ents.append(("text", (tip[0] + dv[0] * 2.5 / v.s - 1.2 / v.s, tip[1] + dv[1] * 2.5 / v.s - 1.2 / v.s), label, 3.6, "left", "baseline", 0, True, False))

def ghost_pcb(v, parts=True):
    v.poly(rrect_pts(-45, -25, 45, 25, 4), "ghost")
    v.rect(P.BATT_X[0], P.BATT_Y[0], P.BATT_X[1], P.BATT_Y[1], "ghost")
    if parts:
        for (x, y), w in ((P.J_PROBE, 11.6), (P.J_SOLAR, 4.0), (P.J_RAIN, 4.0)):
            v.rect(x - w / 2, y - 2.2, x + w / 2, y + 2.6, "ghost")
        v.rect(P.USBC[0] - 4.47, P.USB_FACE_Y - 7.35, P.USBC[0] + 4.47, P.USB_FACE_Y, "ghost")

def table(ax, x0, y0, rows, widths, h=4.4, fs=2.1, head=True, title=None, tfs=3.0):
    pt = 72 / 25.4
    if title: ax.text(x0, y0 + 2.5, title, fontsize=tfs * pt, weight="bold"); y0 -= 3.5
    for k, r in enumerate(rows):
        y = y0 - k * h; x = x0
        for c, w in zip(r, widths):
            ax.text(x + 0.8, y - h + 1.4, str(c), fontsize=fs * pt, weight="bold" if (head and k == 0) else "normal",
                    color="#b00000" if str(c) == "FAIL" else ("#1d7a2e" if str(c) == "OK" else "k"))
            x += w
        ax.plot([x0, x0 + sum(widths)], [y - h, y - h], color="#999", lw=0.3)
    return y0 - len(rows) * h
