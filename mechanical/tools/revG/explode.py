"""Exploded, labelled render of the whole stake (rev G). Usage: python3 explode.py ASSEMBLY_OPAQUE.glb OUT.png"""
import sys, numpy as np, params as P
from explode_read import read_named
from preview import render
from prims import cyl
from PIL import Image, ImageDraw, ImageFont

G = (-45, 0, 0)                     # whole gauge + clamp A pulled away from the neck
def add(a, b): return tuple(x + y for x, y in zip(a, b))
OFF = {  # mesh-name prefix -> (dx, dy, dz) case mm
    "base": (0, 0, 0), "screw": (0, 0, -55), "M8 gland (rain": (0, 0, -40), "antenna": (0, -45, 0),
    "USB-C plug": (0, 40, 0), "QR": (25, 0, 0), "18650": (0, 0, 38), "head PCB": (0, 0, 38),
    "plunger": (0, 0, 66), "lid": (0, 0, 112), "light bar": (0, 40, 112), "LED light": (0, 40, 112),
    "button": (0, 0, 160), "solar panel": (0, 0, 150), "panel grid": (0, 0, 150),
    "clamp a": G, "clamp b": (50, 0, 0), "clamp bolt": (80, 0, 0),
    "gauge body": add(G, (0, 0, 40)), "reed": add(G, (0, 0, 40)), "stop screw": add(G, (0, 0, 40)), "M8 gland (gauge)": add(G, (0, 0, 40)),
    "body screw": add(G, (0, 0, -30)),
    "tipping bucket": add(G, (0, 0, 118)), "magnet": add(G, (0, 0, 118)), "pivot pin": add(G, (0, 0, 118)),
    "gauge funnel": add(G, (0, 0, 175)),
    "tip": (0, 0, 0),
}
SKIP = ("soil line", "probe PCB", "rain gauge cable", "PVC tube")
TUBE_SHOW = 120.0; TIP_GAP = 30.0
LABELS = [  # n, text, mesh prefix
    ("Cap (lid), ASA, sloped 15 deg", "lid"), ("Solar panel up to 87 x 51", "solar panel"), ("Power button, TPU", "button"),
    ("Plunger (D-stem + arm to SW1)", "plunger"), ("LED light guide, smoked PETG", "light bar"), ("Head PCB + 18650 LiFePO4", "head PCB"),
    ("Base: body, chin, neck, collar", "base"), ("4 x M3 x 12 from below", "screw 2"), ("LoRa antenna, SMA rear wall", "antenna"),
    ("USB-C silicone plug", "USB-C plug"), ("QR label", "QR code"), ("M8 gland (rain cable in)", "M8 gland (rain"),
    ("Clamp half A: arm + platform", "clamp a"), ("Clamp half B", "clamp b"), ("2 x M3 x 16 + nuts", "clamp bolt M3x16 +1"),
    ("Gauge body: reed switch + stop screws", "gauge body"), ("3 x M3 x 10 (body to platform)", "body screw"),
    ("Tipping bucket + magnet + pin D2", "tipping bucket"), ("Funnel, collector D100", "gauge funnel"),
    ("PVC tube D32 (probe PCB inside)", "PVC tube"), ("Tip", "tip")]

def W(v): v = np.asarray(v, float); return np.stack([(v[..., 0] + P.KX) / 1000, (v[..., 2] - P.Z_PCB_BOT) / 1000, (v[..., 1] + P.KY) / 1000], -1)

def main(glb, out):
    T = read_named(glb); items = []
    for path, tri, col, nrm in T:
        key = path[2] if len(path) > 2 else path[-1]
        if path[1] in ("head PCB",): key = "head PCB"
        if any(key.startswith(s) for s in SKIP) or path[1] in ("probe PCB",) or key in SKIP: continue
        off = next((o for k, o in OFF.items() if key.startswith(k)), None)
        if off is None: print("no offset for", key); off = (0, 0, 0)
        d = np.array([off[0], off[2], off[1]]) / 1000.0
        if key == "tip": d = d + np.array([0, (P.TUBE_LEN - P.SOCKET_DEPTH - TUBE_SHOW - TIP_GAP) / 1000, 0])
        items.append((key, tri + d, col, nrm))
    # short tube (shown cut) below the collar, slightly pulled down
    zt0 = P.COLLAR_Z0 - TUBE_SHOW; tv, tf = cyl("z", (0, P.CY), P.TUBE_OD / 2, zt0 - 15, P.COLLAR_Z0 + P.SOCKET_DEPTH - 15, 64)
    items.append(("PVC tube", W(tv)[tf], np.array([0.25, 0.30, 0.22, 1.0]), None))
    tris = [(t, c, n) if n is not None else (t, c) for _, t, c, n in items]
    img, zb, (lo, hi, s) = render(tris, None, az=32, el=16, res=2600, ret=True)
    a, e = np.radians(32), np.radians(16)
    R = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]]); R = Rx @ R
    H, Wd = zb.shape
    anchors = []
    for txt, pre in LABELS:
        pts = np.vstack([t.reshape(-1, 3) for k, t, c, n in items if (k == pre if pre == "tip" else k.startswith(pre))])
        if len(pts) > 60000: pts = pts[np.random.default_rng(0).choice(len(pts), 60000, replace=False)]
        q = pts @ R.T; u = ((q[:, 0] - lo[0]) * s).astype(int); v = (H - 1 - ((q[:, 1] - lo[1]) * s)).astype(int)
        ok = (u >= 0) & (v >= 0) & (u < Wd) & (v < H); u, v, z = u[ok], v[ok], q[ok, 2]
        vis = np.abs(z - zb[v, u]) < 0.0015
        if vis.any(): u, v = u[vis], v[vis]
        cu, cv = np.median(u), np.median(v); k = np.argmin((u - cu) ** 2 + (v - cv) ** 2)
        anchors.append((txt, int(u[k]), int(v[k])))
    # canvas with side columns
    M = 760; top = 150
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    C = Image.new("RGB", (Wd + 2 * M, H + top + 60), "white"); C.paste(im, (M, top)); dr = ImageDraw.Draw(C)
    fb = ImageFont.truetype("DejaVuSans-Bold.ttf", 44); f = ImageFont.truetype("DejaVuSans.ttf", 30); fn = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
    dr.text((40, 30), "GAIAPUS stake rev G - exploded view", fill=(25, 25, 25), font=fb)
    dr.text((40, 88), "head case, LoRa head board, rain gauge (0.2 mm/pulse) and neck clamp", fill=(90, 90, 90), font=f)
    cx = M + Wd / 2
    L = [(i, t, u + M, v + top) for i, (t, u, v) in enumerate(anchors)]
    for side in (-1, 1):
        grp = sorted([x for x in L if (x[2] < cx) == (side < 0)], key=lambda x: x[3])
        n = len(grp); ys = np.linspace(top + 80, top + H - 80, n) if n > 1 else [top + H / 2]
        # keep each label near its anchor but ordered and spaced >= 70 px
        want = [g[3] for g in grp]; ys = []
        for w in want: ys.append(max(w, (ys[-1] + 74) if ys else top + 40))
        over = ys[-1] - (top + H - 20) if ys else 0
        if over > 0: ys = [y - over for y in ys]
        for (i, t, u, v), y in zip(grp, ys):
            xb = 60 if side < 0 else C.width - 60
            xe = M - 30 if side < 0 else M + Wd + 30
            dr.line([(u, v), (xe, y), (xb + (40 if side < 0 else -40), y)], fill=(70, 70, 70), width=3)
            dr.ellipse([u - 7, v - 7, u + 7, v + 7], fill=(70, 70, 70))
            bx = xb; dr.ellipse([bx - 24, y - 24, bx + 24, y + 24], fill="white", outline=(30, 30, 30), width=3)
            num = str(i + 1); w_ = dr.textlength(num, font=fn); dr.text((bx - w_ / 2, y - 17), num, fill=(20, 20, 20), font=fn)
            tw = dr.textlength(t, font=f)
            tx = bx + 34 if side < 0 else bx - 34 - tw
            dr.text((tx, y + 8), t, fill=(30, 30, 30), font=f)
    C.save(out); print("wrote", out, C.size)

if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
