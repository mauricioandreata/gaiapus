#!/usr/bin/env python3
"""Parametric footprints that only exist in this project (copper we design ourselves).

ELECTRODE_IDC_<W>x<H>: interdigitated soil-moisture electrode for the probe strip.
 - two combs (pad 1 = oscillator input, pad 2 = GND), fingers across the strip
 - copper only on F.Cu, NO mask or paste opening: the electrode stays covered by solder mask
 - B.Cu keepout (no copper pour) behind the electrode so the field goes out through the tube wall
Wide spacing (2 mm fingers, 2.5 mm gaps) on purpose: the field has to cross ~2 mm of PVC
plus the resin, so it must reach deeper than a fine comb would. Tune on the bench.
"""
import os, uuid
NS = uuid.UUID("5c1a8a22-1d3e-4a51-9f7b-0d9c6e2b7a44")
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "footprints", "gaiapus.pretty"))

def n(v): s = ("%.4f" % v).rstrip("0").rstrip("."); return "0" if s in ("", "-0") else s

def electrode(W=18.0, H=40.0, finger=2.0, gap=2.5, spine=1.0, end_gap=2.0):
    name = f"ELECTRODE_IDC_{n(W)}x{n(H)}"
    k = [0]
    def u(): k[0] += 1; return str(uuid.uuid5(NS, f"{name}|{k[0]}"))
    pitch = finger + gap
    count = int((H - 2 * spine) // pitch) + 1
    span = (count - 1) * pitch + finger
    y0 = -span / 2 + finger / 2
    xl, xr = -W / 2, W / 2
    pads = []
    def pad(num, x1, y1, x2, y2):
        pads.append(f'  (pad "{num}" smd rect (at {n((x1 + x2) / 2)} {n((y1 + y2) / 2)}) (size {n(x2 - x1)} {n(y2 - y1)}) '
                    f'(layers "F.Cu") (uuid "{u()}"))')
    top, bot = -span / 2, span / 2
    pad(1, xl, top, xl + spine, bot)             # spine A (left)
    pad(2, xr - spine, top, xr, bot)             # spine B (right)
    for i in range(count):
        yc = y0 + i * pitch
        if i % 2 == 0:
            pad(1, xl, yc - finger / 2, xr - spine - end_gap, yc + finger / 2)
        else:
            pad(2, xl + spine + end_gap, yc - finger / 2, xr, yc + finger / 2)
    m = 0.5
    crt = (xl - m, top - m, xr + m, bot + m)
    zone = (f'  (zone (net 0) (net_name "") (layer "B.Cu") (uuid "{u()}") (name "no pour behind electrode") (hatch edge 0.5)\n'
            f'    (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)\n'
            f'    (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))\n'
            f'    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n'
            f'    (polygon (pts (xy {n(crt[0])} {n(crt[1])}) (xy {n(crt[2])} {n(crt[1])}) (xy {n(crt[2])} {n(crt[3])}) (xy {n(crt[0])} {n(crt[3])}))))')
    body = "\n".join([
        f'(footprint "{name}" (version 20240108) (generator "gaiapus_gen") (generator_version "1.0") (layer "F.Cu")',
        f'  (descr "Interdigitated capacitive soil electrode {n(W)}x{n(H)} mm, finger {n(finger)} mm, gap {n(gap)} mm, covered by solder mask")',
        '  (tags "soil moisture capacitive electrode interdigitated")',
        f'  (property "Reference" "E**" (at 0 {n(top - 2)} 0) (layer "F.SilkS") (uuid "{u()}") (effects (font (size 1 1) (thickness 0.15))))',
        f'  (property "Value" "{name}" (at 0 {n(bot + 2)} 0) (layer "F.Fab") (uuid "{u()}") (effects (font (size 1 1) (thickness 0.15))))',
        f'  (property "Footprint" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{u()}") (effects (font (size 1.27 1.27))))',
        f'  (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{u()}") (effects (font (size 1.27 1.27))))',
        f'  (property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{u()}") (effects (font (size 1.27 1.27))))',
        '  (attr smd exclude_from_pos_files exclude_from_bom)',
        f'  (fp_rect (start {n(crt[0])} {n(crt[1])}) (end {n(crt[2])} {n(crt[3])}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd") (uuid "{u()}"))',
        f'  (fp_rect (start {n(xl - 0.3)} {n(top - 0.3)}) (end {n(xr + 0.3)} {n(bot + 0.3)}) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS") (uuid "{u()}"))',
        f'  (fp_text user "1" (at {n(xl - 1.2)} {n(top + 1)} 0) (layer "F.SilkS") (uuid "{u()}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
        *pads, zone, ")"])
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".kicad_mod")
    open(path, "w", encoding="utf-8").write(body + "\n")
    return name, count, span

if __name__ == "__main__":
    name, count, span = electrode()
    print(f"{name}: {count} fingers, active span {span:.1f} mm -> {OUT}")
