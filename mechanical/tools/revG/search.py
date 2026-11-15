import math, itertools, numpy as np, params as P, parts
def lid1(x, y, z): return float(parts.cap_shape(np.array([x]), np.array([y]), np.array([z]))[0])
def button_ok(by):
    r = P.BTN_HOLE_D / 2 + 1.5
    for k in range(16):
        a = 2 * math.pi * k / 16; yy, zz = P.from_local(r * math.sin(a), -0.15, by)
        if lid1(r * math.cos(a), yy, zz) >= 0: return False
    return True
def panel_ok(W, H, yr):
    c = P.PANEL_CLR; m = 1.0
    for xx in (-W / 2 - c - m, W / 2 + c + m, 0.0):
        for ss in (-H / 2 - c - m, H / 2 + c + m, 0.0):
            if xx == 0.0 and ss == 0.0: continue
            yy, zz = P.from_local(ss, -0.15, yr)
            if lid1(xx, yy, zz) >= 0: return False
    return True
def yr_for(H, by, gap=2.0):
    sb = lambda yr: P.to_local(by, P.z_top(by), yr)[0]; lo, hi = -50.0, 20.0
    for _ in range(40):
        yr = (lo + hi) / 2; g = sb(yr) - P.BTN_CAP_D / 2 - (H / 2 + P.PANEL_CLR)
        lo, hi = (yr, hi) if g > gap else (lo, yr)
    return yr
results = []
for tb, bz, bb in itertools.product((6.0, 5.0, 4.0), (80.0, 84.0, 88.0), (5.0, 4.0, 3.0)):
    P.TOP_BLEND, P.BEVEL_Z, P.BEVEL_BLEND = tb, bz, bb
    by = max([y for y in np.arange(9.0, 24.0, 0.5) if button_ok(y)] or [None])
    if by is None: continue
    best = None
    for W in np.arange(80, 100, 1.0):
        Hs = [H for H in np.arange(44, 66, 1.0) if panel_ok(W, H, yr_for(H, by))]
        if Hs:
            H = max(Hs)
            if best is None or W * H > best[0] * best[1]: best = (W, H, round(yr_for(H, by), 2))
    results.append((tb, bz, bb, by, best))
    print(tb, bz, bb, "button y", by, "panel", best, flush=True)
