"""Tip volume of the bucket: water moment in the upper compartment vs restoring moment of the empty bucket + magnet."""
import math, numpy as np, params as P, raingauge as RGm
R = P.RG
RHO_PETG, RHO_W, RHO_MAG = 1.27e-3, 1.0e-3, 7.5e-3          # g/mm3
def tip_volume(tilt=None, h=0.15, verbose=False):
    tilt = R["tilt"] if tilt is None else tilt
    gx, gy, gz = R["pos"]; pz = gz + R["pin_z"]
    xs = np.arange(gx - 30, gx + 30, h); ys = np.arange(gy - 11, gy + 11, h); zs = np.arange(pz - 16, pz + 22, h)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij"); dv = h ** 3
    xb, yb, zb = RGm.bucket_frame(X, Y, Z, tilt)
    solid = RGm.bucket_local(xb, yb, zb) < 0
    m_b = solid.sum() * dv * RHO_PETG
    torque_b = ((X[solid] - gx) * dv * RHO_PETG).sum()                    # + = toward the down (+x) side
    # magnet (disc in the tab, below the pin)
    zc = R["mag_zc"]; a = math.radians(tilt)
    mag_x = 0 * math.cos(a) + zc * math.sin(a)                            # bucket (0, zc) -> world x offset
    m_mag = math.pi * (R["mag_d"] / 2) ** 2 * R["mag_h"] * RHO_MAG
    torque_e = torque_b + m_mag * mag_x
    # cavity of the upper compartment (bucket x < 0), as world points
    Lb, H, W, aa, t = R["bk_L"], R["bk_H"], R["bk_W"], R["bk_a"], R["bk_t"]
    s = H / Lb; c = 1 / math.sqrt(1 + s * s)
    inner = np.max([np.abs(yb) - (W / 2 - t), np.abs(xb) - (Lb - t), (aa + t / c + np.abs(xb) * s - zb) * c, 0.6 - np.abs(xb), zb - (aa + H)], axis=0) < 0
    up = inner & (xb < 0)
    # fill with a horizontal water surface, rising; stop when the water spills over the rim (zb > a+H handled by 'inner')
    Zc = Z[up]; Xc = X[up] - gx
    order = np.argsort(Zc); Zs, Xs = Zc[order], Xc[order]
    vol = np.arange(1, len(Zs) + 1) * dv; mom = np.cumsum(Xs) * dv * RHO_W          # negative moments
    k = np.argmax(-mom > torque_e) if (-mom > torque_e).any() else None
    cap = vol[-1]
    if verbose:
        print("bucket %.2f g (CG arm %.2f mm), magnet %.2f g at x %+.2f mm -> restoring torque %.2f g.mm" % (m_b, torque_b / m_b, m_mag, mag_x, torque_e))
        print("upper compartment capacity at this tilt: %.2f mL" % (cap / 1000))
    return (vol[k] / 1000 if k is not None else None), cap / 1000, torque_e
if __name__ == "__main__":
    A = math.pi * (R["rim_d"] / 2) ** 2
    for tilt in (10, 12.5, 15, 17.5, 20):
        v, cap, te = tip_volume(tilt, verbose=(tilt == R["tilt"]))
        print("tilt %4.1f deg: tips at %s mL  (capacity %.2f mL) -> %s mm/pulse" % (tilt, "%.2f" % v if v else "never", cap, "%.3f" % (v * 1000 / A) if v else "-"))
    print("target %.3f mm/pulse = %.2f mL with D%.0f collector (A = %.0f mm2)" % (P.RG_MM_PER_PULSE, P.RG_MM_PER_PULSE * A / 1000, R["rim_d"], A))
