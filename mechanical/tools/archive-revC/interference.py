"""3D interference, rev C: every head-PCB part (.glb), the PCB, the 18650, the probe vs case solids; overlaps between solids."""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
REPO = os.environ.get("GAIAPUS_REPO", os.path.normpath(os.path.join(HERE, "..", "..", "..")))
import params as P, parts
from glbread import part_boxes
SOL = ("base", "lid", "button", "plunger", "light_bar")
fn = lambda X, Y, Z: np.min([getattr(parts, n)(X, Y, Z) for n in SOL], axis=0)
def run():
    res = []
    for name, (lo, hi) in part_boxes(os.path.join(REPO, "hardware", "gaiapus-node", "gaiapus-node.glb")).items():
        if name.startswith("=>"): continue
        c0 = np.array([lo[0] - P.KX, lo[2] - P.KY, lo[1] + P.Z_PCB_BOT]); c1 = np.array([hi[0] - P.KX, hi[2] - P.KY, hi[1] + P.Z_PCB_BOT])
        g = np.meshgrid(*[np.linspace(c0[i] + 0.05, c1[i] - 0.05, max(3, int((c1[i] - c0[i]) / 0.5))) for i in range(3)], indexing="ij")
        res.append((float(fn(*g).min()), "PCB part " + name))
    g = np.meshgrid(np.linspace(-44.9, 44.9, 180), np.linspace(-24.9, 24.9, 100), np.linspace(P.Z_PCB_BOT + 0.1, P.Z_PCB_TOP - 0.1, 3), indexing="ij")
    keep = np.min([np.hypot(g[0] - hx, g[1] - hy) for hx, hy in P.PCB_HOLES], axis=0) > 3.1
    res.append((float(fn(*g)[keep].min()), "PCB body (standoff contact excluded)"))
    th, xs = np.meshgrid(np.linspace(0, 2 * np.pi, 72), np.linspace(-32.5, 32.5, 60), indexing="ij")
    res.append((float(fn(xs, P.BATT_CY + 9.3 * np.cos(th), P.CELL_ZC + 9.3 * np.sin(th)).min()), "18650 cell"))
    yp = P.CY + np.sqrt((P.TUBE_ID / 2) ** 2 - (P.PROBE_W / 2) ** 2) - 0.25
    g = np.meshgrid(np.linspace(-10.9, 10.9, 40), np.linspace(yp - P.PROBE_T - P.PROBE_MAX_H, yp, 6), np.linspace(P.PROBE_TOP_Z - 30, P.PROBE_TOP_Z, 30), indexing="ij")
    res.append((float(fn(*g).min()), "probe top end (in the socket)"))
    res.sort()
    X, Y = np.meshgrid(np.arange(-57, 57, 0.3), np.arange(-53.5, 36, 0.3), indexing="ij")
    acc = {}
    for z in np.arange(14, 91, 0.3):
        Z = np.full_like(X, z); vals = {n: getattr(parts, n)(X, Y, Z) < -0.03 for n in SOL}
        for i, a in enumerate(SOL):
            for b in SOL[i + 1:]:
                acc[(a, b)] = acc.get((a, b), 0) + int((vals[a] & vals[b]).sum())
    ov = [(a, b, n * 0.3 ** 3) for (a, b), n in acc.items()]
    return res, ov
if __name__ == "__main__":
    res, ov = run()
    for d, n in res[:10]: print("%7.2f  %s" % (d, n))
    for a, b, v in ov: print("overlap %-10s %-10s %.3f mm3" % (a, b, v))
