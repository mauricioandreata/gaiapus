"""Tipping-bucket rain gauge + neck clamp as SDFs (case frame, mm). Same machinery as parts.py."""
import math, numpy as np
import params as P
from sdf import rrect2, circle2, extrude
from parts import smax, smin, seg_cyl

R = P.RG; C = P.CLAMP
GX, GY, GZ = R["pos"]
def L(x, y, z): return x - GX, y - GY, z - GZ          # case -> gauge local
def box(x, y, z, x0, x1, y0, y1, z0, z1, r=0.01): return extrude(rrect2(x, y, x0, y0, x1, y1, r), z, z0, z1)
def cylz(x, y, z, cx, cy, r, z0, z1): return extrude(circle2(x, y, cx, cy, r), z, z0, z1)
def cyly(x, y, z, cx, cz, r, y0, y1): return extrude(circle2(x, z, cx, cz, r), y, y0, y1)
def cylx(x, y, z, cy, cz, r, x0, x1): return extrude(circle2(y, z, cy, cz, r), x, x0, x1)

def screws_local():
    return [(R["screw_r"] * math.cos(math.radians(a)), R["screw_r"] * math.sin(math.radians(a))) for a in R["screw_ang"]]

# ---------------- gauge body ----------------
def rg_body(x, y, z):
    x, y, z = L(x, y, z)
    ro, w = R["body_od"] / 2, R["wall"]
    d = cylz(x, y, z, 0, 0, ro, 0, R["h"])
    d = np.maximum(d, -cylz(x, y, z, 0, 0, ro - w, R["floor"], R["h"] + 5))
    pz, pt, py = R["pin_z"], R["post_t"], R["post_y"]
    add = []
    for s in (-1, 1):                                   # pin posts
        add.append(box(x, y, z, -5, 5, s * py - pt / 2, s * py + pt / 2, 1, pz + 5, 1.0))
    add.append(box(x, y, z, -R["reed"][0] / 2 - 1.5, R["reed"][0] / 2 + 1.5, -3, 3, 1, R["reed_top"], 1.0))     # reed holder
    for s in (-1, 1): add.append(cylz(x, y, z, s * R["stop_x"], 0, R["stop_d"] / 2, 1, R["stop_top"]))       # stop bosses
    for sx, sy in screws_local(): add.append(cylz(x, y, z, sx, sy, 4.0, 1, 9))                             # floor screw bosses
    d = np.min([d] + add, axis=0)
    cut = []
    for s in (-1, 1): cut.append(cyly(x, y, z, 0, pz, R["pin_d"] / 2 + 0.05, s * py - 5, s * py + 5))      # pin holes (press fit)
    rl, rw, rd = R["reed"]
    cut.append(box(x, y, z, -rl / 2, rl / 2, -rw / 2, rw / 2, R["reed_top"] - rd, R["reed_top"] + 1))       # reed slot
    for s in (-1, 1):
        cut.append(cylz(x, y, z, s * R["stop_x"], 0, 1.25, R["stop_top"] - 10, R["stop_top"] + 1))          # M3 stop screw pilot
        cut.append(cylz(x, y, z, s * R["drain_x"], 0, R["drain_d"] / 2, -1, R["floor"] + 1))                # drains
    for sx, sy in screws_local(): cut.append(cylz(x, y, z, sx, sy, 1.25, -1, 8))                            # M3 x 10 from below
    ang, cz, cd = R["cable"]
    cut.append(cylx(x, y, z, 0, cz, cd / 2, ro - w - 2, ro + 2) if ang == 0 else None)                       # cable gland toward the stake
    return np.maximum(d, -np.min([c for c in cut if c is not None], axis=0))

# ---------------- funnel / collector ----------------
def rg_funnel(x, y, z):
    x, y, z = L(x, y, z)
    r = np.hypot(x, y)
    t = R["funnel_t"]; rr, rz, nz = R["rim_d"] / 2, R["rim_z"], R["nozzle_z"]
    cone_z = nz + 4 + (r - R["nozzle_d"] / 2) * (rz - nz - 4) / (rr - R["nozzle_d"] / 2)   # inner funnel surface
    k = (rz - nz - 4) / (rr - R["nozzle_d"] / 2); c = 1 / math.sqrt(1 + k * k)
    cone = np.maximum(np.abs((z - cone_z) * c + t / 2) - t / 2, np.maximum(r - rr - 1.5, R["nozzle_d"] / 2 - 0.01 - r))
    cone = np.maximum(cone, nz + 2 - z)
    rim = extrude(np.maximum(r - (rr + 1.5), rr - r), z, rz - 12, rz)                      # thin vertical rim (knife edge at the top)
    rim = smax(rim, (z - rz) - (r - rr) * 0.0, 0.0)
    skirt = extrude(np.maximum(r - R["skirt_od"] / 2, (R["body_od"] / 2 + 0.2) - r), z, R["skirt_z0"], rz - 8)
    web = extrude(np.maximum(r - R["skirt_od"] / 2, rr - 0.5 - r), z, rz - 12, rz - 7)     # joins skirt, rim, cone
    nozzle = extrude(np.maximum(r - R["nozzle_d"] / 2, R["nozzle_id"] / 2 - r), z, nz, nz + 6)
    d = np.min([cone, rim, skirt, web, nozzle], axis=0)
    hole = extrude(r - R["nozzle_id"] / 2, z, nz - 1, nz + 8)
    return np.maximum(d, -hole)

# ---------------- tipping bucket (local bucket frame: pin at origin, x = tip direction, y = pin) ----------------
def bucket_frame(x, y, z, tilt_deg):
    x, y, z = L(x, y, z); z = z - R["pin_z"]
    a = math.radians(tilt_deg); ca, sa = math.cos(a), math.sin(a)
    return x * ca - z * sa, y, x * sa + z * ca          # rotate world into bucket frame

def bucket_local(x, y, z):
    Lb, H, W, a, t = R["bk_L"], R["bk_H"], R["bk_W"], R["bk_a"], R["bk_t"]
    s = H / Lb; c = 1 / math.sqrt(1 + s * s)
    outer = np.max([np.abs(y) - W / 2, np.abs(x) - Lb, z - (a + H), (a + np.abs(x) * s - z) * c], axis=0)
    inner = np.max([np.abs(y) - (W / 2 - t), np.abs(x) - (Lb - t), (a + t / c + np.abs(x) * s - z) * c, 0.6 - np.abs(x)], axis=0)
    d = np.maximum(outer, -inner)
    boss = extrude(circle2(x, z, 0, 0, 3.5), y, -W / 2, W / 2)
    tab = extrude(rrect2(x, y, -4, -4, 4, 4, 1.0), z, R["tab_z"], a + 1)
    d = np.min([d, boss, tab], axis=0)
    hole = extrude(circle2(x, z, 0, 0, R["pin_d"] / 2 + 0.2), y, -W, W)                           # free on the pin
    mag = extrude(circle2(y, z, 0, R["mag_zc"], R["mag_d"] / 2 + 0.1), x, -R["mag_h"] / 2 - 0.1, 5)       # side pocket, axis x
    return np.maximum(d, -np.minimum(hole, mag))

def rg_bucket(x, y, z, tilt=None):
    t = R["tilt"] if tilt is None else tilt
    return bucket_local(*bucket_frame(x, y, z, t))

# ---------------- neck clamp (two halves) ----------------
def clamp_half(x, y, z, side):
    cy = P.CY
    r = np.hypot(x, y - cy)
    ring = extrude(np.maximum(r - C["od"] / 2, C["bore"] / 2 - r), z, C["z0"], C["z1"])
    tabs = np.minimum(box(x, y, z, -C["tab_x"], C["tab_x"], cy + C["tab_r"][0], cy + C["tab_r"][1], C["z0"], C["z1"], 1.0),
                      box(x, y, z, -C["tab_x"], C["tab_x"], cy - C["tab_r"][1], cy - C["tab_r"][0], C["z0"], C["z1"], 1.0))
    d = np.minimum(ring, np.maximum(tabs, C["bore"] / 2 - r))
    if side < 0:   # half with the arm and the gauge platform
        gx, gy, gz = R["pos"]
        arm = box(x, y, z, gx, -C["bore"] / 2 + 2, cy - C["arm_w"] / 2, cy + C["arm_w"] / 2, C["z0"], C["z1"], 1.5)
        plat = cylz(x, y, z, gx, gy, C["plat_d"] / 2, gz - C["plat_t"], gz)
        zp = gz - C["plat_t"]; rg_ = np.hypot(x - gx, y - gy)
        cone = np.maximum((rg_ - (C["post_d"] / 2 + np.maximum(0, z - (zp - (C["plat_d"] - C["post_d"]) / 2)))) * 0.7071, np.maximum(C["z0"] - z, z - zp))
        d = np.min([d, np.maximum(arm, C["bore"] / 2 - r), plat, cone], axis=0)
        hollow = np.maximum((rg_ - (C["post_d"] / 2 - 4 + np.maximum(0, z - (zp - (C["plat_d"] - C["post_d"]) / 2)))) * 0.7071, np.maximum(C["z0"] - 1 - z, z - (zp - 0.5)))
        cuts = [hollow] + [cylz(x, y, z, gx + s * R["drain_x"], gy, R["drain_d"] / 2 + 0.5, C["z0"] - 1, gz + 1) for s in (-1, 1)]
        for sx, sy in screws_local():
            cuts.append(cylz(x, y, z, gx + sx, gy + sy, 1.7, C["z0"] - 1, gz + 1)); cuts.append(cylz(x, y, z, gx + sx, gy + sy, 3.1, C["z0"] - 1, gz - C["plat_t"] + 2.0))
        d = np.maximum(d, -np.min(cuts, axis=0))
    half = np.maximum(d, (x - (-C["gap"] / 2)) if side < 0 else ((C["gap"] / 2) - x))
    cut = [cylx(x, y, z, cy + s * C["bolt_r"], (C["z0"] + C["z1"]) / 2, C["bolt_d"] / 2, -20, 20) for s in (-1, 1)]
    if side > 0:   # nut traps on the +x half
        for s in (-1, 1):
            yc, zc = cy + s * C["bolt_r"], (C["z0"] + C["z1"]) / 2
            hexd = np.max([np.abs(y - yc) * math.cos(math.radians(30)) + np.abs(z - zc) * 0.5, np.abs(z - zc)], axis=0) - C["nut_af"] / 2 - 0.15
            cut.append(np.maximum(hexd, np.maximum(C["tab_x"] - 2.6 - x, x - C["tab_x"] - 1)))
    else:          # screw head counterbores on the arm half
        for s in (-1, 1): cut.append(cylx(x, y, z, cy + s * C["bolt_r"], (C["z0"] + C["z1"]) / 2, 2.9, -C["tab_x"] - 1, -C["tab_x"] + 2.6))
    return np.maximum(half, -np.min(cut, axis=0))

def clamp_a(x, y, z): return clamp_half(x, y, z, -1)
def clamp_b(x, y, z): return clamp_half(x, y, z, +1)

gx, gy, gz = R["pos"]
BOUNDS = {
    "rg_body": ((gx - 53, gy - 53, gz), (gx + 53, gy + 53, gz + R["h"])),
    "rg_funnel": ((gx - 55, gy - 55, gz + R["nozzle_z"] - 1), (gx + 55, gy + 55, gz + R["rim_z"] + 0.5)),
    "rg_bucket": ((gx - 27, gy - 11, gz + R["pin_z"] - 18), (gx + 27, gy + 11, gz + R["pin_z"] + 22)),
    "clamp_a": ((gx - C["plat_d"] / 2 - 1, P.CY - 36, C["z0"] - 1), (0.5, P.CY + 36, gz + 0.5)),
    "clamp_b": ((-0.5, P.CY - 32, C["z0"]), (26, P.CY + 32, C["z1"])),
}
