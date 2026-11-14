#!/usr/bin/env python3
"""First-pass placement: moves each footprint into its zone (shelf packing, biggest first).

Only translates footprints (keeps rotation and side), so nothing inside a footprint changes.
Usage: python3 autoplace.py head|probe [--dry]
Writes a backup <board>.kicad_pcb.before-autoplace next to the board. Close the PCB editor first,
or use File > Revert in KiCad afterwards WITHOUT saving the old view.
"""
import os, re, sys, math, shutil
HW = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAP = 0.6   # mm between courtyards

# zones: (x1, y1, x2, y2, [refs in priority order]) - board origin (100, 100), 90 x 50 mm, M3 holes at the corners
HEAD = [
    ((108, 102, 128, 127), ["U4", "C8", "C9", "R8", "C7", "R9", "TP1", "TP2"]),
    ((161, 102, 182, 122), ["U5", "J2", "C10", "C11", "R10", "C12", "C13"]),
    ((130, 102, 159, 114), ["U3", "L1", "C4", "C5", "R4", "R5"]),
    ((130, 115, 159, 134), ["U1", "U2", "Q1", "D1", "D2", "C1", "C2", "C3", "R1", "R2", "R3", "R6", "R7", "C6"]),
    ((102, 127, 117, 139), ["J5", "U7", "R14", "R15"]),
    ((108, 140, 131, 149), ["J3", "J1", "C14", "C15"]),
    ((132, 141, 156, 149), ["D3", "D4", "D5", "R16", "R17", "R18"]),
    ((161, 128, 173, 148), ["SW1", "J4", "R13", "C17", "R11", "R12"]),
    ((176, 138, 184, 144), ["U6", "C16"]),
    ((120, 160, 210, 190), ["BT1"]),            # outside the board: flip (F) and drag to the bottom side
]
PROBE = [  # strip origin (100, 50), 22 x 450 mm; soil 20 mm below the top; electrodes centred at y = 220 and 470
    ((101, 51, 121, 59), ["J1"]),
    ((101.5, 182, 120.5, 199), ["U1", "R1", "R2", "C1", "C2", "TP1", "R5", "RT1"]),
    ((101.5, 200, 120.5, 240), ["E1"]),
    ((101.5, 432, 120.5, 449), ["U2", "R3", "R4", "C3", "C4", "TP2", "R6", "RT2"]),
    ((101.5, 450, 120.5, 490), ["E2"]),
]
FILES = {"head": ("gaiapus-node", HEAD), "probe": ("gaiapus-probe", PROBE)}

def blocks(txt):
    """yield (start, end) of every top-level (footprint ...) block"""
    i = 0
    while True:
        i = txt.find("\n\t(footprint ", i)
        if i < 0: return
        s = i + 1; d = 0; j = s; inq = False
        while True:
            c = txt[j]
            if c == '"' and txt[j - 1] != "\\": inq = not inq
            elif not inq:
                if c == "(": d += 1
                elif c == ")":
                    d -= 1
                    if d == 0: break
            j += 1
        yield s, j + 1; i = j

def bbox(blk):
    """local bounding box from courtyard (fallback: pads)"""
    pts = []
    for m in re.finditer(r'\((?:fp_line|fp_rect)\s+\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)[\s\S]*?\(layer "[FB]\.CrtYd"\)', blk):
        x1, y1, x2, y2 = map(float, m.groups()); pts += [(x1, y1), (x2, y2)]
    for m in re.finditer(r'\(fp_poly\s+\(pts([\s\S]*?)\)\s*\)[\s\S]*?\(layer "[FB]\.CrtYd"\)', blk):
        pts += [tuple(map(float, p)) for p in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', m.group(1))]
    if not pts:
        for m in re.finditer(r'\(pad [^\n]*?\(at ([-\d.]+) ([-\d.]+)[^)]*\)\s*\(size ([-\d.]+) ([-\d.]+)\)', blk):
            x, y, w, h = map(float, m.groups()); r = max(w, h) / 2 + 0.25
            pts += [(x - r, y - r), (x + r, y + r)]
    if not pts: return (-1, -1, 1, 1)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "head"
    dry = "--dry" in sys.argv
    folder, zones = FILES[which]
    path = os.path.join(HW, folder, folder + ".kicad_pcb")
    if len(sys.argv) > 2 and sys.argv[2] not in ("--dry",): path = sys.argv[2]
    txt = open(path, encoding="utf-8").read()
    fps = {}
    for s, e in blocks(txt):
        blk = txt[s:e]
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
        rot = float(at.group(3) or 0)
        x1, y1, x2, y2 = bbox(blk)
        if round(rot) % 180 == 90: x1, y1, x2, y2 = -y2, x1, -y1, x2   # rotated 90/270: swap extents (conservative)
        if round(rot) % 360 == 180: x1, y1, x2, y2 = -x2, -y2, -x1, -y1
        fps[ref] = dict(s=s, e=e, at=at, rot=rot, bb=(x1, y1, x2, y2))
    placed, report = {}, []
    for (zx1, zy1, zx2, zy2), refs in zones:
        refs = [r for r in refs if r in fps]
        order = sorted(refs, key=lambda r: -(fps[r]["bb"][3] - fps[r]["bb"][1]) * (fps[r]["bb"][2] - fps[r]["bb"][0]))
        cx, cy, row_h, over = zx1, zy1, 0.0, []
        for r in order:
            x1, y1, x2, y2 = fps[r]["bb"]; w, h = x2 - x1, y2 - y1
            if cx + w > zx2 and cx > zx1:
                cx, cy, row_h = zx1, cy + row_h + GAP, 0.0
            if cy + h > zy2: over.append(r)
            placed[r] = (cx - x1, cy - y1)          # footprint origin so that its bbox starts at (cx, cy)
            cx += w + GAP; row_h = max(row_h, h)
        report.append(f"  zone ({zx1:g},{zy1:g})-({zx2:g},{zy2:g}): {len(refs)} parts" + (f"  OVERFLOW (below the box): {over}" if over else ""))
    missing = sorted(set(fps) - set(placed))
    # rewrite back-to-front so offsets stay valid
    out = txt
    for r in sorted(placed, key=lambda r: -fps[r]["s"]):
        f = fps[r]; x, y = placed[r]
        a = f["at"]; s0 = f["s"] + a.start(); e0 = f["s"] + a.end()
        rot = f" {a.group(3)}" if a.group(3) else ""
        out = out[:s0] + f"\n\t\t(at {x:.4f} {y:.4f}{rot})" + out[e0:]
    print(f"{which}: {len(fps)} footprints, placed {len(placed)}" + (f", not in any zone: {missing}" if missing else ""))
    print("\n".join(report))
    if dry: return out
    shutil.copyfile(path, path + ".before-autoplace")
    open(path, "w", encoding="utf-8").write(out)
    print("written", path)
    return out

if __name__ == "__main__":
    main()
