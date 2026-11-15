"""Tiny 2D drafting layer: views record entities, a sheet renders them to matplotlib (PDF) and to DXF."""
import math
import matplotlib
matplotlib.use("Agg")
from matplotlib.patches import Polygon, Rectangle
from matplotlib.lines import Line2D

STY = {  # style -> (linewidth pt, linestyle, color)
    "vis":   (0.9, "-", "#000000"),
    "thin":  (0.4, "-", "#000000"),
    "hid":   (0.4, (0, (4, 2.2)), "#333333"),
    "cen":   (0.35, (0, (9, 2, 1.5, 2)), "#b00000"),
    "dim":   (0.35, "-", "#005a9c"),
    "sect":  (1.3, (0, (10, 3, 2, 3)), "#000000"),
    "ghost": (0.5, (0, (1.5, 1.5)), "#7a7a7a"),
}
DXF_LAYER = {"vis": "OUTLINE", "thin": "THIN", "hid": "HIDDEN", "cen": "CENTER", "dim": "DIM", "sect": "SECTION", "ghost": "GHOST"}
DXF_COLOR = {"OUTLINE": 7, "THIN": 8, "HIDDEN": 8, "CENTER": 1, "DIM": 5, "SECTION": 7, "GHOST": 9, "TEXT": 7, "HATCH": 8}

def arc_pts(cx, cy, r, a0, a1, n=None):
    if n is None: n = max(6, int(abs(a1 - a0) / 6) + 1)
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def rrect_pts(x0, y0, x1, y1, r):
    if r <= 0: return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    p = []
    p += arc_pts(x1 - r, y0 + r, r, -90, 0)
    p += arc_pts(x1 - r, y1 - r, r, 0, 90)
    p += arc_pts(x0 + r, y1 - r, r, 90, 180)
    p += arc_pts(x0 + r, y0 + r, r, 180, 270)
    p.append(p[0]); return p

class View:
    """f maps the two native model coords to view (u, v). Sheet pos = (ox + u*s, oy + v*s)."""
    def __init__(self, sheet, name, ox, oy, s, f):
        self.sh, self.name, self.ox, self.oy, self.s, self.f = sheet, name, ox, oy, s, f
        self.ents = []
        sheet.views.append(self)
    # ---- recording (native coords) ----
    def uv(self, a, b): return self.f(a, b)
    def poly(self, pts, sty="vis", closed=False, fill=None, hatch=None):
        self.ents.append(("poly", [self.f(*p) for p in pts], sty, fill, hatch))
    def line(self, p, q, sty="vis"): self.poly([p, q], sty)
    def rect(self, a0, b0, a1, b1, sty="vis", fill=None, hatch=None, r=0):
        self.poly(rrect_pts(a0, b0, a1, b1, r) if r else [(a0, b0), (a1, b0), (a1, b1), (a0, b1), (a0, b0)], sty, fill=fill, hatch=hatch)
    def circle(self, c, r, sty="vis", fill=None, hatch=None):
        self.poly(arc_pts(c[0], c[1], r, 0, 360, 72), sty, fill=fill, hatch=hatch)
        self.ents.append(("circ", self.f(*c), r, sty))
    def arc(self, c, r, a0, a1, sty="vis"): self.poly(arc_pts(c[0], c[1], r, a0, a1), sty)
    def cross(self, c, size, sty="cen"):
        self.line((c[0] - size, c[1]), (c[0] + size, c[1]), sty); self.line((c[0], c[1] - size), (c[0], c[1] + size), sty)
    def text(self, p, s, h=2.6, ha="left", va="baseline", rot=0, bold=False):
        u, v = self.f(*p); self.ents.append(("text", (u, v), s, h, ha, va, rot, bold, True))
    def stext(self, u, v, s, h=2.6, ha="left", va="baseline", rot=0, bold=False):   # in view coords/ sheet mm offset free
        self.ents.append(("text", (u, v), s, h, ha, va, rot, bold, True))
    # ---- dimensions (native points) ----
    def dim(self, p, q, off, kind="h", text=None, tol="", extra_text_off=0.0):
        (u1, v1), (u2, v2) = self.f(*p), self.f(*q)
        s = self.s
        if kind == "h":
            vd = v1 + off / s
            val = abs(u2 - u1)
            for (u, v) in ((u1, v1), (u2, v2)):
                self.ents.append(("seg", (u, v + (1.2 / s) * (1 if off > 0 else -1)), (u, vd + (1.5 / s) * (1 if off > 0 else -1)), "dim"))
            self.ents.append(("seg", (u1, vd), (u2, vd), "dim"))
            self.ents.append(("arrow", (u1, vd), (1, 0), "dim")); self.ents.append(("arrow", (u2, vd), (-1, 0), "dim"))
            if u1 > u2: self.ents[-1], self.ents[-2] = self.ents[-2], self.ents[-1]
            t = text if text is not None else fmt(val)
            self.ents.append(("text", ((u1 + u2) / 2, vd + (0.9 / s) * (1 if off > 0 else -1) - (0 if off > 0 else 2.6 / s)), t + tol, 2.4, "center", "baseline", 0, False, False))
        else:
            ud = u1 + off / s
            val = abs(v2 - v1)
            for (u, v) in ((u1, v1), (u2, v2)):
                self.ents.append(("seg", (u + (1.2 / s) * (1 if off > 0 else -1), v), (ud + (1.5 / s) * (1 if off > 0 else -1), v), "dim"))
            self.ents.append(("seg", (ud, v1), (ud, v2), "dim"))
            lo, hi = (v1, v2) if v1 < v2 else (v2, v1)
            self.ents.append(("arrow", (ud, lo), (0, 1), "dim")); self.ents.append(("arrow", (ud, hi), (0, -1), "dim"))
            t = text if text is not None else fmt(val)
            self.ents.append(("text", (ud - (0.8 / s) if off < 0 else ud + (3.2 / s), (v1 + v2) / 2), t + tol, 2.4, "center", "baseline", 90, False, False))
    def dia(self, c, r, ang_deg, text=None, lead=10.0):
        """diameter / radius leader from circle edge outward"""
        u, v = self.f(*c); a = math.radians(ang_deg)
        e = (u + r * math.cos(a), v + r * math.sin(a))
        L = lead / self.s
        e2 = (e[0] + L * math.cos(a), e[1] + L * math.sin(a))
        self.ents.append(("seg", e, e2, "dim")); self.ents.append(("arrow", e, (-math.cos(a), -math.sin(a)), "dim"))
        t = text or ("%s%s" % ("Ø", fmt(2 * r)))
        right = math.cos(a) >= 0
        self.ents.append(("text", (e2[0] + (0.6 / self.s) * (1 if right else -1), e2[1] - 0.8 / self.s), t, 2.4, "left" if right else "right", "baseline", 0, False, False))
    def note(self, p, s, to, h=2.4, ha="left"):
        """leader from native point p to view-offset text position to=(du_mm, dv_mm) in sheet mm"""
        u, v = self.f(*p); eu, ev = u + to[0] / self.s, v + to[1] / self.s
        self.ents.append(("seg", (u, v), (eu, ev), "thin")); self.ents.append(("arrow", (u, v), ((u - eu), (v - ev)), "thin"))
        self.ents.append(("text", (eu + (0.8 / self.s) * (1 if ha == "left" else -1), ev - 0.8 / self.s), s, h, ha, "baseline", 0, False, False))
    def balloon(self, p, n, to):
        u, v = self.f(*p); eu, ev = u + to[0] / self.s, v + to[1] / self.s
        self.ents.append(("seg", (u, v), (eu, ev), "thin")); self.ents.append(("arrow", (u, v), ((u - eu), (v - ev)), "thin"))
        self.ents.append(("ball", (eu, ev), str(n)))
    def title(self, p, s, sub=""):
        self.ents.append(("vtitle", p, s, sub))

def fmt(v):
    if abs(v - round(v)) < 0.005: return "%d" % round(v)
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return s

class Sheet:
    W, H = 420.0, 297.0
    def __init__(self, num, total, title, drawing_no, scale_txt, doc, notes=None, rev="B"):
        self.rev = rev
        self.num, self.total, self.title, self.dno, self.scale_txt, self.doc = num, total, title, drawing_no, scale_txt, doc
        self.views = []; self.notes = notes or []
        self.extra = []   # (callable(ax)) direct sheet drawing

    def render(self, pdf):
        import matplotlib.pyplot as plt
        plt.rcParams["hatch.linewidth"] = 0.35
        fig = plt.figure(figsize=(self.W / 25.4, self.H / 25.4))
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, self.W); ax.set_ylim(0, self.H); ax.axis("off")
        pt_per_mm = 72 / 25.4
        # frame
        ax.add_patch(Rectangle((5, 5), self.W - 10, self.H - 10, fill=False, lw=1.2, ec="k"))
        ax.add_patch(Rectangle((10, 10), self.W - 20, self.H - 20, fill=False, lw=0.6, ec="k"))
        self._titleblock(ax)
        for v in self.views: self._render_view(ax, v)
        for fn in self.extra: fn(ax, fig)
        pdf.savefig(fig); plt.close(fig)

    def _titleblock(self, ax):
        x0, y0, w, h = self.W - 10 - 190, 10, 190, 44
        ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=0.8, ec="k"))
        for yy in (y0 + 14, y0 + 28): ax.plot([x0, x0 + w], [yy, yy], "k", lw=0.5)
        for xx in (x0 + 105, x0 + 140, x0 + 165): ax.plot([xx, xx], [y0, y0 + 14], "k", lw=0.5)
        ax.plot([x0 + 105, x0 + 105], [y0 + 14, y0 + 28], "k", lw=0.5)
        T = lambda x, y, s, h=2.2, **k: ax.text(x, y, s, fontsize=h * 72 / 25.4, family="DejaVu Sans", **k)
        T(x0 + 2, y0 + 39, "GAIAPUS  ·  Field Shift stake", 3.6, weight="bold")
        T(x0 + 2, y0 + 33, "NASA Space Apps 2026  ·  Team Gaiapus  ·  Mechanical", 2.2)
        T(x0 + 2, y0 + 23, self.title, 3.4, weight="bold")
        T(x0 + 2, y0 + 17.5, self.doc, 2.2)
        T(x0 + 2, y0 + 9, "Units: mm   General tol.: ISO 2768-m (FDM prints ±0.2)", 2.0)
        T(x0 + 2, y0 + 4, "Material: see parts list (sheet 1)   Drawn from: gaiapus-node.kicad_pcb", 2.0)
        T(x0 + 107, y0 + 23, "Drawing no.", 1.8, color="#555"); T(x0 + 107, y0 + 17.5, self.dno, 3.0, weight="bold")
        T(x0 + 107, y0 + 9, "Scale", 1.8, color="#555"); T(x0 + 107, y0 + 4, self.scale_txt, 2.4)
        T(x0 + 142, y0 + 9, "Rev", 1.8, color="#555"); T(x0 + 142, y0 + 4, self.rev, 2.8, weight="bold")
        T(x0 + 167, y0 + 9, "Sheet", 1.8, color="#555"); T(x0 + 167, y0 + 4, "%d / %d" % (self.num, self.total), 2.6)
        T(x0 + 142, y0 + 17.5, "2026-11-15", 2.2); T(x0 + 142, y0 + 23, "Date", 1.8, color="#555")

    def _xy(self, v, u, vv): return v.ox + u * v.s, v.oy + vv * v.s

    def _render_view(self, ax, v):
        pt = 72 / 25.4
        for e in v.ents:
            k = e[0]
            if k == "poly":
                pts, sty, fill, hatch = e[1:]
                P = [self._xy(v, a, b) for a, b in pts]
                if fill or hatch:
                    ax.add_patch(Polygon(P, closed=True, fill=bool(fill), fc=fill or "none", ec="#444444", hatch=hatch, lw=0, zorder=1))
                lw, ls, col = STY[sty]
                ax.add_line(Line2D([p[0] for p in P], [p[1] for p in P], lw=lw, ls=ls, color=col, zorder=3, solid_capstyle="round"))
            elif k == "seg":
                p, q, sty = e[1:]
                a, b = self._xy(v, *p), self._xy(v, *q); lw, ls, col = STY[sty]
                ax.add_line(Line2D([a[0], b[0]], [a[1], b[1]], lw=lw, ls=ls, color=col, zorder=3))
            elif k == "arrow":
                p, d, sty = e[1:]; a = self._xy(v, *p); L = math.hypot(*d) or 1; d = (d[0] / L, d[1] / L)
                # direction in sheet space: d is in view coords, same orientation (uniform scale)
                s_, w_ = 2.2, 0.65
                tip = a; base = (a[0] + d[0] * s_, a[1] + d[1] * s_); n = (-d[1] * w_, d[0] * w_)
                ax.add_patch(Polygon([tip, (base[0] + n[0], base[1] + n[1]), (base[0] - n[0], base[1] - n[1])], closed=True, fc=STY[sty][2], ec="none", zorder=4))
            elif k == "text":
                p, s, h, ha, va, rot, bold, _ = e[1:]
                x, y = self._xy(v, *p)
                ax.text(x, y, s, fontsize=h * pt, ha=ha, va=va, rotation=rot, rotation_mode="anchor", weight="bold" if bold else "normal", zorder=5, family="DejaVu Sans")
            elif k == "ball":
                p, s = e[1:]; x, y = self._xy(v, *p)
                from matplotlib.patches import Circle
                ax.add_patch(Circle((x, y), 3.2, fc="white", ec="k", lw=0.7, zorder=5))
                ax.text(x, y, s, fontsize=3.0 * pt, ha="center", va="center", zorder=6, weight="bold")
            elif k == "vtitle":
                p, s, sub = e[1:]
                ax.text(p[0], p[1], s, fontsize=3.4 * pt, weight="bold", zorder=5)
                if sub: ax.text(p[0], p[1] - 4.6, sub, fontsize=2.4 * pt, color="#444", zorder=5)

    # ---- DXF ----
    def dxf_entities(self, ox, oy):
        out = []
        for v in self.views:
            for e in v.ents:
                k = e[0]
                if k == "poly":
                    pts, sty, fill, hatch = e[1:]
                    if sty in ("dim",): continue
                    out.append(("poly", [(ox + a, oy + b) for a, b in pts], DXF_LAYER[sty]))
                elif k == "seg" and e[3] in ("dim", "thin"):
                    out.append(("poly", [(ox + e[1][0], oy + e[1][1]), (ox + e[2][0], oy + e[2][1])], "DIM"))
                elif k == "text":
                    out.append(("text", (ox + e[1][0], oy + e[1][1]), e[2], e[3] / v.s))
        return out

def write_dxf(path, groups):
    """groups: list of (name, [(kind, ...)]) in mm, y-up; minimal AutoCAD R12 ASCII."""
    L = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
         "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", str(len(DXF_COLOR))]
    for n, c in DXF_COLOR.items(): L += ["0", "LAYER", "2", n, "70", "0", "62", str(c), "6", "CONTINUOUS"]
    L += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    for name, ents in groups:
        for e in ents:
            if e[0] == "poly":
                pts, layer = e[1], e[2]
                for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
                    if abs(a - c) + abs(b - d) < 1e-6: continue
                    L += ["0", "LINE", "8", layer, "10", "%.4f" % a, "20", "%.4f" % b, "30", "0", "11", "%.4f" % c, "21", "%.4f" % d, "31", "0"]
            elif e[0] == "text":
                (x, y), s, h = e[1], e[2], e[3]
                L += ["0", "TEXT", "8", "TEXT", "10", "%.4f" % x, "20", "%.4f" % y, "30", "0", "40", "%.3f" % h, "1", s.replace("Ø", "%%c")]
    L += ["0", "ENDSEC", "0", "EOF"]
    open(path, "w", encoding="ascii", errors="replace").write("\n".join(L) + "\n")
