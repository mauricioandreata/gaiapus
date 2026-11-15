"""3D interference: every head-PCB part (.glb boxes), the PCB, the 18650 cell vs case material; part-to-part overlap."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
import numpy as np, params as P, parts
from glbread import part_boxes
fn = lambda X, Y, Z: np.min([parts.base(X, Y, Z), parts.lid(X, Y, Z), parts.button(X, Y, Z)], axis=0)
boxes = part_boxes(os.path.join(REPO, "hardware", "gaiapus-node", "gaiapus-node.glb"))
worst = []
for name, (lo, hi) in boxes.items():
    # glb: x=kicad x, y=up (board bottom 0), z=kicad y   ->  case frame
    c0 = np.array([lo[0] - P.KX, lo[2] - P.KY, lo[1] + P.Z_PCB_BOT]); c1 = np.array([hi[0] - P.KX, hi[2] - P.KY, hi[1] + P.Z_PCB_BOT])
    if name.startswith("=>"): continue          # copper/tracks: PCB itself checked below
    g = [np.linspace(c0[i] + 0.05, c1[i] - 0.05, max(3, int((c1[i] - c0[i]) / 0.5))) for i in range(3)]
    X, Y, Z = np.meshgrid(*g, indexing="ij"); d = fn(X, Y, Z)
    worst.append((float(d.min()), name, c0.round(1), c1.round(1)))
# PCB body (rounded rect, standoff contact excluded by 0.1 shrink) and cell envelope
g = np.meshgrid(np.linspace(-44.9, 44.9, 180), np.linspace(-24.9, 24.9, 100), np.linspace(P.Z_PCB_BOT + 0.1, P.Z_PCB_TOP - 0.1, 3), indexing="ij")
inpcb = (np.hypot(*g[:2]) >= 0)  # rectangle ok (corners r4 inside anyway)
holes = np.min([np.hypot(g[0] - hx, g[1] - hy) for hx, hy in P.PCB_HOLES], axis=0) > 3.1   # screw head/pilot area excluded
worst.append((float(fn(*g)[holes].min()), "PCB body", "", ""))
th = np.linspace(0, 2 * np.pi, 72); xs = np.linspace(-32.5, 32.5, 60)
T, Xc = np.meshgrid(th, xs, indexing="ij")
for rr in (P.CELL_D / 2, P.CELL_D / 4):
    Yc = P.BATT_CY + rr * np.cos(T); Zc = P.CELL_ZC + rr * np.sin(T)
    worst.append((float(fn(Xc, Yc, Zc).min()), "18650 cell envelope r=%.1f" % rr, "", ""))
worst.sort()
print("min distance from case material (negative = INSIDE material):")
for w in worst[:12]: print("  %7.2f  %s %s %s" % w)
# part-to-part overlap
g = np.meshgrid(np.arange(-57, 57, 0.25), np.arange(-47.5, 34.5, 0.25), np.arange(26.0, 39.6, 0.25), indexing="ij")
b, l, k = parts.base(*g), parts.lid(*g), parts.button(*g)
for a_, b_, n in ((b, l, "base-lid"), (l, k, "lid-button"), (b, k, "base-button")):
    ov = ((a_ < -0.02) & (b_ < -0.02)).sum() * 0.25 ** 3
    print("overlap %-12s %.3f mm3" % (n, ov))
