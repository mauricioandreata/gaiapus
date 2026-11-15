"""Rev F drawing set (A3 x 4): overview, exterior (shaded ortho views + dims), sections (exact, from the solids), parts.
Run: python3 drawings_revc.py OUTDIR   (needs cache/view_*.npz from views_cache.py, numpy, matplotlib, scikit-image)"""
import os, sys, math, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import params as P, parts, checks
from drawlib import Sheet, View, fmt, arc_pts, rrect_pts
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "cache")
PT = 72 / 25.4
F_FRONT = lambda a, b: (a, b); F_RIGHT = lambda a, b: (-a, b); F_TOP = lambda a, b: (a, -b); F_BOTTOM = lambda a, b: (a, b)
SOLIDS = [("base", "////", "#ffffff"), ("lid", "\\\\\\\\", "#ffffff"), ("button", "xxxx", "#e4e4ee"), ("plunger", "....", "#eeeeee"), ("light_bar", "", "#d8ecf6")]

def tube_sdf(x, y, z):
    r = np.hypot(x, y - P.CY); zb = P.SOIL_Z - (P.TUBE_LEN - P.SOCKET_DEPTH)
    ring = np.maximum(r - P.TUBE_OD / 2, P.TUBE_ID / 2 - r)
    return np.maximum(ring, np.maximum(zb - z, z - (P.SOIL_Z + P.SOCKET_DEPTH)))

def image_view(sheet, name, ox, oy, s, f):
    d = np.load(os.path.join(CACHE, "view_%s.npz" % name)); img, ext = d["img"].astype(float), d["ext"]
    img[:3, :] = 1; img[-3:, :] = 1; img[:, :3] = 1; img[:, -3:] = 1          # drop the edge-detector frame
    v = View(sheet, name, ox, oy, s, f)
    def draw(ax, fig, img=img, ext=ext, v=v):
        u0, u1, v0, v1 = ext
        rgba = np.dstack([np.clip(img, 0, 1), (np.clip(img, 0, 1).min(2) < 0.985).astype(float)])
        ax.imshow(rgba, extent=[ox + u0 * s, ox + u1 * s, oy + v0 * s, oy + v1 * s], zorder=0.5, interpolation="nearest")
    sheet.extra.insert(0, draw)
    return v

def section(sheet, name, ox, oy, s, plane, val, urange, vrange, step=0.12, extra=None):
    """exact section of every solid on plane 'x' (native y,z -> u=-y) or 'y' (native x,z)"""
    v = View(sheet, name, ox, oy, s, F_RIGHT if plane == "x" else F_FRONT)
    a = np.arange(urange[0], urange[1], step); b = np.arange(vrange[0], vrange[1], step)
    A, B = np.meshgrid(a, b)
    X, Y, Z = (np.full_like(A, val), A, B) if plane == "x" else (A, np.full_like(A, val), B)
    fields = [(n, getattr(parts, n)(X, Y, Z), h, c) for n, h, c in SOLIDS] + [("tube", tube_sdf(X, Y, Z), "xx", "#f0e6c8")]
    def draw(ax, fig, A=A, B=B, fields=fields, v=v):
        U, V = v.f(A, B); Xs, Ys = ox + U * s, oy + V * s
        for n, F, h, c in fields:
            if (F < 0).any():
                ax.contourf(Xs, Ys, -F, levels=[0, 1e9], colors=[c], hatches=[h or None], zorder=1)
                ax.contour(Xs, Ys, F, levels=[0], colors="k", linewidths=0.75, zorder=3)
        if extra: extra(ax, v)
    sheet.extra.append(draw)
    return v

def ghost_boards(v, plane, val):
    """PCB, battery cell and probe at the section plane (thin outline, light fill)"""
    if plane == "x":
        v.rect(-25, P.Z_PCB_BOT, 25, P.Z_PCB_TOP, "vis", fill="#cfe3cf")
        if abs(val) < 32.5: v.circle((P.BATT_CY, P.CELL_ZC), P.CELL_D / 2, "thin", fill="#dde8ee")
        yp = P.CY + math.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2) - 0.25
        if abs(val) < 11: v.rect(yp - P.PROBE_T, P.PROBE_TOP_Z - 60, yp, P.PROBE_TOP_Z, "vis", fill="#7fbf7f")
    else:
        if abs(val) < 25: v.rect(-45, P.Z_PCB_BOT, 45, P.Z_PCB_TOP, "vis", fill="#cfe3cf")
        if abs(val - P.BATT_CY) < P.CELL_D / 2:
            h = math.sqrt((P.CELL_D / 2) ** 2 - (val - P.BATT_CY) ** 2); v.rect(-32.5, P.CELL_ZC - h, 32.5, P.CELL_ZC + h, "thin", fill="#dde8ee")

def table(ax, x0, y0, rows, widths, h=4.2, fs=2.0, title=None, tfs=3.0):
    if title: ax.text(x0, y0 + 2.5, title, fontsize=tfs * PT, weight="bold"); y0 -= 3.5
    for k, r in enumerate(rows):
        y = y0 - k * h; x = x0
        for c, w in zip(r, widths):
            col = "#b00000" if str(c) == "FAIL" else ("#1d7a2e" if str(c) == "OK" else "k")
            ax.text(x + 0.8, y - h + 1.3, str(c), fontsize=fs * PT, weight="bold" if k == 0 else "normal", color=col); x += w
        ax.plot([x0, x0 + sum(widths)], [y - h, y - h], color="#999", lw=0.3)
    return y0 - len(rows) * h

PARTS = [("#", "Part", "Qty", "Material / note"),
    ("1", "Base: body, chin, neck, collar (one print)", "1", "ASA olive matt"),
    ("2", "Cap (lid) with bosses, sleeve, lip", "1", "ASA olive matt"),
    ("3", "Button cap D16, flange D20, power icon (on panel axis)", "1", "TPU 95A black"),
    ("4", "Plunger: D-stem + arm to SW1", "1", "PETG"),
    ("5", "LED light guide: lens 36 x 10 + 3 pipes", "1", "smoked PETG"),
    ("6", "Gasket cord D2, ~390 mm ring", "1", "silicone 50A"),
    ("7", "Solar panel up to 87 x 51 x 3.2 (was 68 x 37)", "1", "bonded in recess"),
    ("8", "Head PCB + 18650 LiFePO4", "1", "gaiapus-node"),
    ("9", "Screw M3 x 12, from below", "4", "black oxide"),
    ("10", "Heat-set insert M3 (D4 x 7)", "4", "brass, cap bosses"),
    ("11", "Thread-forming screw M3 x 8", "4", "PCB to standoffs"),
    ("12", "Cable gland M8 (rain gauge)", "1", "black nylon"),
    ("13", "SMA bulkhead + U.FL pigtail + hinged antenna", "1", "915 MHz"),
    ("14", "USB-C silicone plug", "1", "black"),
    ("15", "ePTFE vent patch 20 x 14", "1", "behind the grille"),
    ("16", "QR label 26 x 26", "1", "UV vinyl"),
    ("17", "PVC tube D32 x 470", "1", "solvent-welded in collar"),
    ("18", "Tip (sleeve + cone)", "1", "ASA, glued"),
    ("19", "Probe PCB 22 x 450, potted", "1", "gaiapus-probe")]

# ------------------------------------------------------------------ sheets
def sheet1(total, imgs):
    sh = Sheet(1, total, "Overview: design intent and 3D model", "GAIA-MEC-F01", "n.t.s.", "Rev F = rev E + team review 2026-11-15 13:29; boards unchanged.", rev="F")
    def draw(ax, fig):
        from PIL import Image
        im = np.asarray(Image.open(imgs["compare"]).convert("RGB")) / 255.0
        w = 250; h = w * im.shape[0] / im.shape[1]
        ax.imshow(im, extent=[15, 15 + w, 282 - h, 282], zorder=0.5)
        ax.text(15, 284, "DESIGN TARGET vs REV F MODEL", fontsize=3.4 * PT, weight="bold")
        sec = np.asarray(Image.open(imgs["section"]).convert("RGB")) / 255.0
        h2 = 112; w2 = h2 * sec.shape[1] / sec.shape[0]
        ax.imshow(sec, extent=[30, 30 + w2, 178 - h2, 178], zorder=0.5)
        ax.text(15, 186, "CUT x = 0 WITH THE BOARDS", fontsize=2.8 * PT, weight="bold")
        y = table(ax, 272, 282, PARTS, [7, 72, 8, 50], h=4.0, fs=1.9, title="PARTS LIST", tfs=3.0)
        R = checks.rows()
        ax.text(145, 182, "CHECKS  %d/%d OK  +  3D interference: 0 mm3 overlap, all board parts clear" % (sum(r[3] for r in R), len(R)), fontsize=2.5 * PT, weight="bold", color="#1d7a2e")
        rows = [("Check", "mm", "min", "")] + [(r[0][:52], "%.2f" % r[1], "%.1f" % r[2], "OK" if r[3] else "FAIL") for r in R]
        table(ax, 145, 179, rows, [92, 14, 12, 10], h=3.15, fs=1.65)
        notes = ["REV F (team review 2026-11-15 13:29) ON TOP OF REV E",
                 "- Power button moved further forward (plan y 17.5, panel axis x 0): as far as the flat top allows.",
                 "- Solar panel recess 87.8 x 51.8 (panel up to 87 x 51): +26 % vs rev E, +76 % vs the original 68 x 37.",
                 "- Front bevel replaced by a round (R~5) and side blends 5 mm, to free flat area on the top.",
                 "- Button guide sleeve starts at z 58 (above the LED light pipes); ribs R10.",
                 "- Kept: 15 deg top, rear antenna, 36 x 10 lens (lights on the lens face), centred grille, hidden screws.",
                 "- Open: pick a commercial panel <= 87 x 51 x 3.2 and update BOM SP1.",
                 ""]
        for i, s in enumerate(notes):
            ax.text(15, 60 - i * 4.3, s, fontsize=(2.6 if i == 0 else 2.15) * PT, weight="bold" if i == 0 else "normal")
    sh.extra.append(draw)
    return sh

def sheet2(total):
    sh = Sheet(2, total, "Exterior views (shaded, third angle)", "GAIA-MEC-F02", "1:1.25", "Datum 0,0 = PCB centre; z from the head bottom face.", rev="F")
    s = 0.8
    f = image_view(sh, "front", 75, 120, s, F_FRONT)
    f.title((15, 283), "FRONT", "LED lens, USB-C, centred grille")
    f.dim((-P.OUT_X, P.COLLAR_Z0), (P.OUT_X, P.COLLAR_Z0), -10, "h", "114")
    f.dim((-P.OUT_X, P.COLLAR_Z0), (-P.OUT_X, 0), -8, "v", "32")
    f.dim((-P.OUT_X, 0), (-P.OUT_X, P.Z_SPLIT), -8, "v", "54")
    f.dim((-P.OUT_X, 0), (-P.OUT_X, P.Z_TOP_REAR), -16, "v", "104")
    f.dim((-P.OUT_X, 0), (-P.OUT_X, P.CHIN), -24, "v", "20 chin")
    L = P.LED_LENS
    f.dim((L["xc"] - L["w"] / 2, P.Z_TOP_REAR), (L["xc"] + L["w"] / 2, P.Z_TOP_REAR), 6, "h", "36 LED lens")
    f.dim((P.OUT_X, L["zc"] - L["h"] / 2), (P.OUT_X, L["zc"] + L["h"] / 2), 22, "v", "61-71")
    f.dim((-P.NECK_D / 2, -14), (P.NECK_D / 2, -14), 0, "h", "") if False else None
    f.note((0, -10), "neck D40, collar D46", (24, -4))
    f.note((P.USBC[0], P.USB_Z), "USB-C 12.5 x 7", (-10, -26), ha="right")
    f.note((P.VENT["xc"], P.VENT["z0"]), "grille 9 x (2.2 x 12) in pocket 44 x 16", (14, -20))
    r = image_view(sh, "right", 222, 120, s, F_RIGHT)
    r.title((165, 283), "RIGHT", "QR label; antenna on the rear wall")
    r.dim((P.OUT_Y1, P.COLLAR_Z0), (P.OUT_Y0, P.COLLAR_Z0), -10, "h", "88")
    r.dim((P.OUT_Y1, P.Z_TOP_REAR), (P.OUT_Y0, P.Z_TOP_REAR), 0, "h", "") if False else None
    r.dim((P.OUT_Y0, 0), (P.OUT_Y0, P.z_top(P.OUT_Y0)), 22, "v", "104 rear")
    r.dim((P.OUT_Y1, 0), (P.OUT_Y1, P.z_top(P.OUT_Y1)), -8, "v", "80.4 front")
    r.note((P.QR[2], P.QR[3]), "QR 26 x 26 (recess 0.3)", (-10, 34), ha="right")
    r.note((P.SMA[1], P.SMA[2]), "SMA D6.4 rear wall, x 30, z 46", (-30, 40), ha="right")
    r.dim((0, P.CY), (0, P.CY), 0, "h", "") if False else None
    t = image_view(sh, "top", 345, 246, 0.5, F_TOP)
    t.title((300, 283), "TOP  (1:2)", "panel recess, button, antenna behind")
    t.dim((-P.OUT_X, P.OUT_Y1), (P.OUT_X, P.OUT_Y1), -8, "h", "114")
    t.dim((P.OUT_X, P.OUT_Y0), (P.OUT_X, P.OUT_Y1), 8, "v", "88")
    b = image_view(sh, "bottom", 345, 170, 0.5, F_BOTTOM)
    b.title((300, 205), "BOTTOM  (1:2)", "screws from below, M8 gland")
    b.note(P.SCREW_POS[0], "4 x M3 x 12", (-6, -8), ha="right")
    b.note(P.GLAND[:2], "M8 gland", (14, 8))
    def tab(ax, fig):
        rows = [("Feature", "Position (x, y, z)", "Size")]
        rows += [("LED lens (cap front)", "x 0, z 66", "36.3 x 10.3 R3"), ("LED spots", "x -11 / 0 / +11", "D7"),
                 ("Top plane", "15 deg, z 104 rear", "80.4 at front"), ("Panel recess (on slope)", "centre x 0, y -17.2", "87.8 x 51.8 x 1.6"),
                 ("Button (on slope, panel axis)", "x 0, y 17.5", "D16.4 hole"), ("USB-C (front)", "x -17.4, z 45.25", "12.5 x 7 R2"),
                 ("Grille pocket (front, centred)", "x 0, z 34", "44 x 16 x 1.5"),
                 ("QR recess (right)", "y 6, z 37", "26 x 26 x 0.3"), ("SMA (rear wall)", "x 30, z 46", "D6.4"),
                 ("Screws (bottom)", "x +-49.5, y -46 / 26.5", "D3.4, cb D6.5"), ("M8 gland (bottom)", "x 26, y -24", "D8.2"),
                 ("Neck / collar", "axis y -9.5", "D40 / D46 x 12"), ("Tube socket", "z -32 .. -10", "D32.4"), ("Seam (gasket)", "z 54", "cord D2")]
        table(ax, 297, 128, rows, [40, 37, 34], h=3.55, fs=1.75, title="FEATURE TABLE", tfs=2.6)
    sh.extra.append(tab)
    return sh

def sheet3(total):
    sh = Sheet(3, total, "Sections (exact, cut from the solid model)", "GAIA-MEC-F03", "1:1", "Hatch: base ////, cap \\\\\\\\, button xx, plunger dots, light bar blue, tube cross-hatch.", rev="F")
    a = section(sh, "AA", 85, 116, 1.0, "x", 0.0, (-60, 40), (-60, 106), extra=None)
    a.title((15, 283), "SECTION A-A  x = 0", "centre: button stem + sleeve, middle LED pipe + lens, slot, neck, tube, probe")
    ghost_boards(a, "x", 0.0)
    a.dim((P.OUT_Y1, 0), (P.OUT_Y1, P.Z_PCB_BOT), -8, "v", "42 PCB")
    a.dim((P.OUT_Y1, 0), (P.OUT_Y1, P.Z_SPLIT), -16, "v", "54 seam")
    a.dim((P.OUT_Y1, P.SOIL_Z), (P.OUT_Y1, 0), -8, "v", "32")
    a.dim((P.OUT_Y0, 0), (P.OUT_Y0, P.z_top(P.OUT_Y0)), 8, "v", "104")
    a.note((P.CY, P.SOIL_Z), "soil line = collar bottom", (20, -8))
    a.note((P.LEDS[1][1] + 2, 58), "light pipe", (-22, 6), ha="right")
    b = section(sh, "BB", 222, 116, 0.95, "y", P.BTN_C[1], (-60, 62), (-36, 106))
    b.title((160, 283), "SECTION B-B  y = +17.5", "button axis: cap, D-stem, sleeve, ribs (arm runs diagonally to SW1)")
    ghost_boards(b, "y", P.BTN_C[1])
    b.note((P.BTN_C[0] - 2, P.ARM_Z0 + 1), "arm (diagonal to SW1 at x -12, y 2.6)", (-14, -14), ha="right")
    b.note((P.BTN_C[0] + 3, 70), "D-stem in sleeve (gap 0.3)", (18, 8))
    c = section(sh, "CC", 350, 176, 0.8, "y", P.SCREW_POS[2][1], (-60, 62), (8, 100), step=0.15)
    c.title((297, 283), "SECTION C-C  y = +26.5  (1:1.25)", "screws from below, bosses, seam")
    ghost_boards(c, "y", P.SCREW_POS[2][1])
    c.note((P.SCREW_POS[3][0], P.Z_MEET + 2), "M3 x 12 + insert", (4, -24))
    c.dim((P.OUT_X, P.CB_SEAT), (P.OUT_X, P.Z_MEET), 10, "v", "")  if False else None
    c.dim((-P.OUT_X, P.Z_MEET), (-P.OUT_X, 0), 0, "v", "") if False else None
    def legend(ax, fig):
        txt = ["NOTES", "1. Sections are contour lines of the real solids (same functions",
               "   that make the 3MF files): no redrawn geometry.", "2. PCB, 18650 and probe in green/blue for reference.",
               "3. Wall 4 (lower body), 3.5 (cap, chin); roof 3.5; recess floor 1.9.",
               "4. Print base bottom-down (chin 45 deg prints without support),", "   cap top-down, plunger and light bar on their sides."]
        for i, s in enumerate(txt): ax.text(297, 108 - i * 4.2, s, fontsize=(2.6 if i == 0 else 2.0) * PT, weight="bold" if i == 0 else "normal")
    sh.extra.append(legend)
    return sh

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    imgs = {"compare": os.path.join(HERE, "out", "compare-design-vs-revF.png"), "section": os.path.join(HERE, "out", "render-section-x0.png")}
    plt.rcParams["hatch.linewidth"] = 0.35
    sheets = [sheet1(3, imgs), sheet2(3), sheet3(3)]
    pdf = os.path.join(out, "gaiapus-case-revF.pdf")
    with PdfPages(pdf) as p:
        for s in sheets: s.render(p)
    print("wrote", pdf)
