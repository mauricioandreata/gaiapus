"""Move / rotate footprints in a KiCad 8 board file (90-degree steps).
KiCad 8 stores pad and text angles as absolute values, so a rotation adds the delta to the footprint,
every pad angle and every text/property angle; local coordinates stay unchanged."""
import re
def _block(t, ref):
    i = t.find(f'"Reference" "{ref}"'); s = t.rfind("\n\t(footprint ", 0, i) + 1
    d = 0; j = s; inq = False
    while True:
        c = t[j]
        if c == '"' and t[j - 1] != "\\": inq = not inq
        elif not inq:
            if c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: break
        j += 1
    return s, j + 1
def place(t, ref, x=None, y=None, rot=None, dx=0.0, dy=0.0):
    s, e = _block(t, ref); blk = t[s:e]
    m = re.compile(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)((?: [-\d.]+)?)\)').search(blk)
    ox, oy = float(m.group(1)), float(m.group(2)); orot = float(m.group(3) or 0)
    nx = x if x is not None else ox + dx; ny = y if y is not None else oy + dy
    nrot = orot if rot is None else rot
    delta = (nrot - orot) % 360
    head = f"\n\t\t(at {nx:.4f} {ny:.4f}" + (f" {nrot:g})" if nrot % 360 else ")")
    blk = blk[:m.start()] + head + blk[m.end():]
    if delta:
        def bump(mm):
            a = float(mm.group(3) or 0) + delta
            a = ((a + 180) % 360) - 180
            return f"(at {mm.group(1)} {mm.group(2)}" + (f" {a:g})" if a else ")")
        # pads and texts (deeper indentation than the footprint's own (at ...))
        blk = re.sub(r'(?<=\n\t\t\t)\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', bump, blk)
    return t[:s] + blk + t[e:]
