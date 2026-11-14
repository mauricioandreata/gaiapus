"""Symbol-library helpers for the Gaiapus KiCad generator (KiCad 8 file format).

Everything is plain S-expression text; no KiCad install is needed to run it.
"""
import math

U = 2.54


def n(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def yn(b):
    return "yes" if b else "no"


FONT = "(font (size 1.27 1.27))"


class Pin:
    def __init__(self, num, name, etype, x, y, ang, length=U, hide=False):
        self.num, self.name, self.etype = str(num), name, etype
        self.x, self.y, self.ang, self.length, self.hide = x, y, ang, length, hide


class Sym:
    def __init__(self, name, ref, pins, gfx, value=None, fp="", ds="~", desc="",
                 power=False, in_bom=True, hide_names=False, hide_nums=False,
                 w=0.0, h=0.0, name_offset=0.254):
        self.name, self.ref, self.pins, self.gfx = name, ref, pins, gfx
        self.value = value if value is not None else name
        self.fp, self.ds, self.desc = fp, ds, desc
        self.power, self.in_bom = power, in_bom
        self.hide_names, self.hide_nums = hide_names, hide_nums
        self.w, self.h, self.name_offset = w, h, name_offset


# ---------- graphics ----------
def rect(x1, y1, x2, y2, fill="background"):
    return (f"(rectangle (start {n(x1)} {n(y1)}) (end {n(x2)} {n(y2)}) "
            f"(stroke (width 0.254) (type default)) (fill (type {fill})))")


def poly(pts, fill="none"):
    p = " ".join(f"(xy {n(a)} {n(b)})" for a, b in pts)
    return f"(polyline (pts {p}) (stroke (width 0.254) (type default)) (fill (type {fill})))"


def circle(cx, cy, r, fill="none"):
    return (f"(circle (center {n(cx)} {n(cy)}) (radius {n(r)}) "
            f"(stroke (width 0.254) (type default)) (fill (type {fill})))")


# ---------- generic builders ----------
def box(name, ref, left=(), right=(), top=(), bottom=(), hidden=(), fp="", ds="~",
        desc="", value=None, minw=12.7):
    """IC-style symbol. Pin entries are (number, name, electrical_type)."""
    rows = max(len(left), len(right), 1)
    tb = 1 if top else 0
    bb = 1 if bottom else 0
    h = (rows + 1 + tb + bb) * U
    maxl = max([len(p[1]) for p in left] + [0])
    maxr = max([len(p[1]) for p in right] + [0])
    w = max(minw, math.ceil(((maxl + maxr) * 1.1 + 3) / U) * U)
    w = max(w, (max(len(top), len(bottom)) + 1) * U)
    pins = []
    y0 = h / 2 - tb * U
    for k, (num, nm, et) in enumerate(left):
        pins.append(Pin(num, nm, et, -w / 2 - U, y0 - U * (k + 1), 0))
    for k, (num, nm, et) in enumerate(right):
        pins.append(Pin(num, nm, et, w / 2 + U, y0 - U * (k + 1), 180))
    for k, (num, nm, et) in enumerate(top):
        pins.append(Pin(num, nm, et, (k - (len(top) - 1) / 2) * U, h / 2 + U, 270))
    for k, (num, nm, et) in enumerate(bottom):
        pins.append(Pin(num, nm, et, (k - (len(bottom) - 1) / 2) * U, -h / 2 - U, 90))
    for (num, nm, et) in hidden:
        pins.append(Pin(num, nm, et, 0, -h / 2 - U, 90, hide=True))
    return Sym(name, ref, pins, rect(-w / 2, h / 2, w / 2, -h / 2), value=value,
               fp=fp, ds=ds, desc=desc, w=w, h=h)


def two_pin(name, ref, gfx, top=("1", "~", "passive"), bottom=("2", "~", "passive"),
            fp="", ds="~", desc="", value=None):
    pins = [Pin(top[0], top[1], top[2], 0, 3.81, 270, 1.27),
            Pin(bottom[0], bottom[1], bottom[2], 0, -3.81, 90, 1.27)]
    return Sym(name, ref, pins, gfx, value=value, fp=fp, ds=ds, desc=desc,
               hide_names=True, hide_nums=True, w=2.54, h=7.62, name_offset=0)


def power_sym(name, up=True):
    if up:  # +V style: body above the connection point
        gfx = poly([(0, 0), (0, 1.27)]) + poly([(-1.016, 1.27), (1.016, 1.27)]) + \
            poly([(-1.016, 1.27), (0, 2.286), (1.016, 1.27)], "none")
        ang = 90
    else:   # ground style: body below
        gfx = poly([(0, 0), (0, -1.016)]) + poly([(-1.27, -1.016), (1.27, -1.016)]) + \
            poly([(-0.762, -1.524), (0.762, -1.524)]) + poly([(-0.254, -2.032), (0.254, -2.032)])
        ang = 270
    pins = [Pin("1", name, "power_in", 0, 0, ang, 0, hide=True)]
    s = Sym(name, "#PWR", pins, gfx, desc=f"Power symbol: {name}", power=True,
            in_bom=False, hide_names=True, hide_nums=True, name_offset=0)
    return s


def pwr_flag():
    gfx = poly([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)])
    pins = [Pin("1", "pwr", "power_out", 0, 0, 90, 0, hide=True)]
    return Sym("PWR_FLAG", "#FLG", pins, gfx, desc="Marks a net as driven (silences ERC)",
               power=True, in_bom=False, hide_names=True, hide_nums=True, name_offset=0)


def lib_sexp(sym, embed=False):
    nm = ("gaiapus:" if embed else "") + sym.name
    o = [f"(symbol {q(nm)}"]
    if sym.power:
        o.append("(power)")
    if sym.hide_nums:
        o.append("(pin_numbers hide)")
    o.append(f"(pin_names (offset {n(sym.name_offset)}){' hide' if sym.hide_names else ''})")
    o.append(f"(exclude_from_sim no) (in_bom {yn(sym.in_bom)}) (on_board {yn(getattr(sym, 'on_board', sym.in_bom))})")
    if sym.w:
        rx, ry = -sym.w / 2, sym.h / 2 + 1.27
        vx, vy = -sym.w / 2, -sym.h / 2 - 1.27
        if sym.hide_names:       # passives: texts to the right
            rx, ry, vx, vy = 2.54, 1.27, 2.54, -1.27
    else:
        rx, ry, vx, vy = 0, 2.54, 0, -2.54
    def prop(k, v, x, y, hide=False):
        return (f"(property {q(k)} {q(v)} (at {n(x)} {n(y)} 0) "
                f"(effects {FONT}{' (justify left)' if k in ('Reference','Value') else ''}"
                f"{' hide' if hide else ''}))")
    o.append(prop("Reference", sym.ref, rx, ry, hide=sym.power))
    o.append(prop("Value", sym.value, vx, vy, hide=False))
    o.append(prop("Footprint", sym.fp, 0, 0, True))
    o.append(prop("Datasheet", sym.ds, 0, 0, True))
    o.append(prop("Description", sym.desc, 0, 0, True))
    o.append(f"(symbol {q(sym.name + '_0_1')} {sym.gfx})")
    ps = []
    for p in sym.pins:
        ps.append(f"(pin {p.etype} line (at {n(p.x)} {n(p.y)} {n(p.ang)}) (length {n(p.length)})"
                  f"{' hide' if p.hide else ''} (name {q(p.name)} (effects {FONT})) "
                  f"(number {q(p.num)} (effects {FONT})))")
    o.append(f"(symbol {q(sym.name + '_1_1')} " + " ".join(ps) + ")")
    o.append(")")
    return "\n  ".join(o)
