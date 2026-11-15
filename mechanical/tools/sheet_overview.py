import numpy as np
from views_common import *
import model3d as M
import checks

PARTS = [
    ("1", "Base (lower shell + collar)", "1", "ASA olive matt, FDM"),
    ("2", "Lid", "1", "ASA olive matt, FDM"),
    ("3", "Button cap Ø12 (flange Ø16, pin Ø4)", "1", "TPU 95A black"),
    ("4", "LED rod Ø3 x 11", "3", "clear acrylic rod, cut"),
    ("5", "Gasket cord Ø2, ~360 mm, glued ring", "1", "silicone 50A"),
    ("6", "Solar panel 68 x 37 x 3.2 (BOM SP1)", "1", "bonded in recess"),
    ("7", "Head PCB + 18650 (gaiapus-node)", "1", ""),
    ("8", "Screw M3 x 30 pan head + O-ring", "4", "A2, from below"),
    ("9", "Heat-set insert M3 (Ø4 x 6)", "4", "brass, in the lid"),
    ("10", "Thread-forming screw M3 x 8 (PCB)", "4", "e.g. WN1442"),
    ("11", "PG7 cable gland, black", "1", "rain-gauge cable"),
    ("12", "SMA bulkhead + U.FL pigtail 100 mm", "1", "+ hinged 915 MHz antenna"),
    ("13", "USB-C silicone plug", "1", ""),
    ("14", "ePTFE vent patch 20 x 12", "1", "inside, behind vent"),
    ("15", "QR label 26 x 26", "1", "UV vinyl"),
    ("16", "PVC tube Ø32 x 470 + tip", "1", "probe PCB potted"),
]

def to_sheet(fig, ax3, p, W=420.0, H=297.0):
    from mpl_toolkits.mplot3d import proj3d
    x, y, z = p
    x2, y2, _ = proj3d.proj_transform(x, -y, z, ax3.get_proj())
    px, py = ax3.transData.transform((x2, y2)); fx, fy = fig.transFigure.inverted().transform((px, py))
    return fx * W, fy * H

def build(total):
    sh = Sheet(1, total, "Overview: design, exploded view, checks", "GAIA-MEC-B01", "n.t.s.",
               "Case rev B for the as-built boards (STEP/GLB 2026-11-14).")
    def draw(ax, fig):
        pt = 72 / 25.4
        W, H = 420.0, 297.0
        # ---------- assembled ----------
        m = M.Mesh(); M.tube(m, length=60); M.base(m); M.gland(m); M.lid(m); M.tops(m); M.antenna(m)
        a1 = M.render(fig, [0.005, 0.47, 0.30, 0.50], m, view=(24, -52), lims=((-62, 75), (-50, 40), (-85, 115)))
        ax.text(15, 281, "ASSEMBLED (design base v1)", fontsize=3.4 * pt, weight="bold")
        fig.canvas.draw()
        callouts = [((P.PANEL_C[0] - 20, P.PANEL_C[1], P.Z_TOP + 1.6), "solar panel (top, rear)", (-1, 1)),
                    ((P.SW1[0], P.SW1[1], P.Z_TOP + 1), "big button", (-1, 1)),
                    ((P.LEDS[0][0], P.LEDS[0][1], P.Z_TOP), "LED strip G/Y/R", (-1, 0)),
                    ((P.USBC[0], P.OUT_Y1, P.USB_Z), "USB-C + plug", (-1, -1)),
                    ((P.VENT["x0"], P.OUT_Y1, P.VENT["z0"] + 4), "SHT40 vent", (1, -1)),
                    ((P.SMA[0] + 10, P.SMA[1], P.SMA[2] + 70), "hinged LoRa antenna", (1, 1)),
                    ((0, P.CY + P.COLLAR_D / 2, -10), "collar + tube Ø32", (-1, -1)),
                    ((P.GLAND[0], P.GLAND[1], -14), "rain cable (gland, below)", (1, -1))]
        ov = fig.add_axes([0, 0, 1, 1], zorder=30); ov.set_xlim(0, W); ov.set_ylim(0, H); ov.axis("off"); ov.patch.set_alpha(0)
        for p, txt, (sx, sy) in callouts:
            x, y = to_sheet(fig, a1, p)
            tx, ty = x + sx * 14, y + sy * 9
            ov.plot([x, tx], [y, ty], color="k", lw=0.4); ov.plot([x], [y], "o", ms=1.6, color="k")
            ov.text(tx + (0.8 if sx > 0 else -0.8), ty, txt, fontsize=2.3 * pt, ha="left" if sx > 0 else "right", va="center",
                    bbox=dict(fc="white", ec="none", pad=0.4))
        # ---------- exploded ----------
        e = M.Mesh()
        M.tube(e, off=(0, 0, -45), length=60); M.base(e, open_top=True); M.gland(e)
        M.pcb(e, off=(0, 0, 32)); M.lid(e, off=(0, 0, 78)); M.tops(e, off_panel=(0, 0, 100), off_btn=(0, 0, 90), off_rod=(0, 0, 66), lit=False)
        for p in P.SCREW_POS: e.cyl(p[0], p[1], 2.75, -40, -38, "#9a9a9a", n=12); e.cyl(p[0], p[1], 1.5, -38, -8, "#9a9a9a", n=10)
        a2 = M.render(fig, [0.29, 0.30, 0.30, 0.68], e, view=(22, -52), lims=((-62, 62), (-50, 40), (-120, 150)))
        ax.text(132, 281, "EXPLODED", fontsize=3.4 * pt, weight="bold")
        for p in P.SCREW_POS[1:2] + P.SCREW_POS[3:]:
            pass
        fig.canvas.draw()
        bal = [((P.OUT_X, 0, 15), "1"), ((P.OUT_X, 0, P.Z_SPLIT + 3 + 78), "2"), ((P.SW1[0], P.SW1[1], P.Z_TOP + 90), "3"),
               ((P.LEDS[2][0], P.LEDS[2][1], P.Z_TOP + 66), "4"), ((P.PANEL_W / 2, P.PANEL_C[1], P.Z_TOP + 101), "6"),
               ((45, 0, P.Z_PCB_TOP + 32), "7"), ((P.SCREW_POS[3][0], P.SCREW_POS[3][1], -39), "8"), ((0, P.CY + 16, -80), "16"),
               ((P.GLAND[0], P.GLAND[1], -6), "11")]
        from matplotlib.patches import Circle
        pos = sorted([(to_sheet(fig, a2, p), n) for p, n in bal], key=lambda t: -t[0][1])
        last = 1e9
        for (x, y), n in pos:
            yb = min(y, last - 8.5); last = yb; bx = 250.0
            ov.plot([x, bx - 3], [y, yb], color="k", lw=0.35); ov.plot([x], [y], "o", ms=1.4, color="k")
            ov.add_patch(Circle((bx, yb), 3.0, fc="white", ec="k", lw=0.6)); ov.text(bx, yb, n, fontsize=2.6 * pt, ha="center", va="center", weight="bold")
        # ---------- parts list ----------
        rows = [("#", "Part", "Qty", "Material / note")] + PARTS
        table(ax, 262, 279, rows, [7, 66, 8, 66], h=4.0, fs=1.95, title="PARTS LIST", tfs=3.0)
        # ---------- measured from the boards ----------
        meas = [("Item", "Measured (kicad_pcb + .glb)", "Used in case"),
                ("Head PCB", "90 x 50 x 1.6, R4, 4 x Ø3.2 at ±41/±21", "same, standoffs Ø6"),
                ("Tallest top part", "USB-C 3.3 / JST 3.0 / SW1 2.75 above PCB", "roof 4.6 above USB-C"),
                ("USB-C face", "footprint: 0.5 inside board edge", "opening 12.5 x 7"),
                ("USB-C 3D model", "ends 2.5 mm short of the footprint", "use the footprint"),
                ("18650 holder", "86 x 20.7, 14.9 below PCB (no cell)", "21 mm cell envelope"),
                ("JST entries", "J3/J1/J4 face the front edge", "6.8-7.4 mm plug room"),
                ("Probe PCB", "22 x 450, parts ≤ 2.5 high", "fits tube ID 27"),
                ("3D coverage", "56/58 head, 15/19 probe (TP, E only)", "ok")]
        y = table(ax, 262, 197, meas, [26, 70, 51], h=4.0, fs=1.85, title="MEASURED FROM THE BOARDS", tfs=3.0)
        # ---------- checks ----------
        R = checks.rows()
        ax.text(262, y - 4, "CLEARANCE CHECKS: %d / %d OK (mechanical/tools/checks.py)" % (sum(r[3] for r in R), len(R)), fontsize=2.6 * pt, weight="bold", color="#1d7a2e")
        key = [r for r in R if r[0].startswith(("JST J3", "Tallest", "Battery env", "Screw column", "Floor slot", "USB opening"))]
        rows = [("Check", "mm", "min", "")] + [(r[0][:46], "%.1f" % r[1], "%.1f" % r[2], "OK" if r[3] else "FAIL") for r in key]
        table(ax, 262, y - 6, rows, [100, 14, 14, 12], h=3.8, fs=1.8)
        # ---------- how it goes together ----------
        steps = ["HOW IT GOES TOGETHER",
                 "1  Press 4 inserts into the lid bosses (iron 220-230 C). Push the 3 LED rods into the holder.",
                 "2  Bond the button cap flange and the panel (wires through Ø4) with neutral silicone.",
                 "3  Base: fit gland, SMA, USB plug, vent patch, QR label. Glue the tube into the collar.",
                 "4  Probe cable up the tube and through slot C; rain cable through the gland.",
                 "5  PCB on 4 standoffs (M3 x 8 thread-forming). Plug probe, rain, solar, U.FL.",
                 "6  Cord in the groove, lid on (lip locates it), 4 x M3 x 30 from below."]
        for i, s in enumerate(steps):
            ax.text(15, 66 - i * 4.4, s, fontsize=(2.7 if i == 0 else 2.15) * pt, weight="bold" if i == 0 else "normal")
    sh.extra.append(draw)
    stake(sh)
    return sh

def stake(sh):
    S = 0.25
    v = View(sh, "stake", 32, 112, S, lambda a, b: (-b, a))
    v.title((15, 150), "STAKE  1:4", "head, collar, PVC tube, probe and soil line (lying)")
    t, s = P.Z_TOP, P.Z_SPLIT
    v.rect(-P.OUT_X, 0, P.OUT_X, t, "vis", fill="#d7dccd"); v.line((-P.OUT_X, s), (P.OUT_X, s), "thin")
    v.rect(-P.COLLAR_D / 2, -P.COLLAR_H, P.COLLAR_D / 2, 0, "vis", fill="#d7dccd")
    r = P.TUBE_OD / 2; zt = -P.COLLAR_H - P.TUBE_LEN + P.COLLAR_H
    v.rect(-r, -P.TUBE_LEN, r, -P.COLLAR_H, "vis", fill="#e6eadf")
    v.poly([(-r, -P.TUBE_LEN), (0, -P.TUBE_LEN - P.TIP_LEN), (r, -P.TUBE_LEN)], "vis")
    v.rect(-P.PROBE_W / 2, P.PROBE_TOP_Z - P.PROBE_L, P.PROBE_W / 2, P.PROBE_TOP_Z, "ghost")
    for d in P.ELEC_DEPTHS:
        zc = P.SOIL_Z - d; v.rect(-9, zc - P.ELEC_H / 2, 9, zc + P.ELEC_H / 2, "thin", fill="#e8c36a")
    zs = P.SOIL_Z
    v.line((-46, zs), (46, zs), "vis")
    for k in range(-9, 10): v.line((k * 5, zs), (k * 5 - 3, zs - 6), "thin")
    v.text((48, zs), "soil", 2.2, ha="left") if False else v.stext(v.f(0, zs)[0] + 2 / S, v.f(0, 46)[1] + 2 / S, "SOIL LINE = collar bottom", 2.2, ha="left")
    v.dim((-r, zs), (-r, zs - P.ELEC_DEPTHS[0]), -10, "h", "150 to electrode 1")
    v.dim((-r, zs), (-r, zs - P.ELEC_DEPTHS[1]), -18, "h", "400 to electrode 2")
    v.dim((r, 0), (r, -P.TUBE_LEN), 13, "h", "470 tube \u00d832 (22 in the collar)")
    v.dim((r, -P.TUBE_LEN), (r, -P.TUBE_LEN - P.TIP_LEN), 13, "h", "60")
    v.dim((P.OUT_X, t), (-P.OUT_X, t), 0, "h", "") if False else None

