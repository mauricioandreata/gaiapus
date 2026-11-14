#!/usr/bin/env python3
"""Board outlines + placement zones for both PCBs (KiCad 8 .kicad_pcb).

Writes Edge.Cuts (outline, mounting holes, SHT40 thermal slot) and, on User.Drawings /
User.Comments, the placement plan as boxes with labels. Footprints are NOT placed here:
in KiCad do Tools > Update PCB from Schematic, then move each part into its box.
Refuses to overwrite a .kicad_pcb that already contains footprints.
All dimensions are parameters below (mm) - change them when mechanics fixes the case.
"""
import os, uuid, math, sys
HW = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
NS = uuid.UUID("7f0c3b5e-2a41-4c6e-8d2f-91b3a4c5d6e7")

# ---------------- parameters ----------------
HEAD_W, HEAD_H, HEAD_R = 90.0, 50.0, 4.0          # head board, rounded rectangle
HEAD_HOLE_D, HEAD_HOLE_IN = 3.2, 4.0               # M3 holes, inset from edges
PROBE_W, PROBE_L, PROBE_R = 22.0, 450.0, 2.0       # probe strip (fits 32 mm PVC, ID ~27 mm; JLCPCB single board <= 500 mm)
SOIL_FROM_TOP = 20.0                               # soil surface below the top edge of the probe (assumption)
DEPTHS = (150.0, 400.0)                            # electrode centres below the soil surface
ELEC_H = 40.0                                      # electrode height (ELECTRODE_IDC_18x40)

def n(v): s = ("%.4f" % v).rstrip("0").rstrip("."); return "0" if s in ("", "-0") else s
class Board:
    def __init__(self, name): self.name, self.items, self.k = name, [], 0
    def u(self): self.k += 1; return str(uuid.uuid5(NS, f"{self.name}|{self.k}"))
    def line(self, a, b, layer="Edge.Cuts", w=0.1):
        self.items.append(f'\t(gr_line (start {n(a[0])} {n(a[1])}) (end {n(b[0])} {n(b[1])}) (stroke (width {w}) (type default)) (layer "{layer}") (uuid "{self.u()}"))')
    def arc(self, s, m, e, layer="Edge.Cuts", w=0.1):
        self.items.append(f'\t(gr_arc (start {n(s[0])} {n(s[1])}) (mid {n(m[0])} {n(m[1])}) (end {n(e[0])} {n(e[1])}) (stroke (width {w}) (type default)) (layer "{layer}") (uuid "{self.u()}"))')
    def circle(self, c, r, layer="Edge.Cuts", w=0.1):
        self.items.append(f'\t(gr_circle (center {n(c[0])} {n(c[1])}) (end {n(c[0] + r)} {n(c[1])}) (stroke (width {w}) (type default)) (fill none) (layer "{layer}") (uuid "{self.u()}"))')
    def rect(self, a, b, layer="Dwgs.User", w=0.15):
        self.items.append(f'\t(gr_rect (start {n(a[0])} {n(a[1])}) (end {n(b[0])} {n(b[1])}) (stroke (width {w}) (type default)) (fill none) (layer "{layer}") (uuid "{self.u()}"))')
    def text(self, p, t, layer="Dwgs.User", size=1.2, rot=0):
        self.items.append(f'\t(gr_text "{t}" (at {n(p[0])} {n(p[1])} {n(rot)}) (layer "{layer}") (uuid "{self.u()}")\n'
                          f'\t\t(effects (font (size {n(size)} {n(size)}) (thickness {n(size * 0.15)})) (justify left bottom)))')
    def zone(self, a, b, label, size=1.0):
        self.rect(a, b); self.text((a[0] + 0.6, a[1] + size + 0.6), label, size=size)
    def rounded_rect(self, x0, y0, x1, y1, r):
        k = r * (1 - 1 / math.sqrt(2))
        self.line((x0 + r, y0), (x1 - r, y0)); self.line((x1, y0 + r), (x1, y1 - r))
        self.line((x1 - r, y1), (x0 + r, y1)); self.line((x0, y1 - r), (x0, y0 + r))
        self.arc((x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r)); self.arc((x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1))
        self.arc((x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r)); self.arc((x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0))

def write(path, board, title):
    src = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if "(footprint " in src:
        sys.exit(f"{path} already has footprints - not overwriting (move the outline by hand or delete footprints first)")
    head = src[:src.rindex("(net 0")] if "(net 0" in src else None
    if head is None:
        head = ('(kicad_pcb\n\t(version 20240108)\n\t(generator "pcbnew")\n\t(generator_version "8.0")\n'
                '\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)\n\t(paper "A4")\n'
                f'\t(title_block\n\t\t(title "{title}")\n\t\t(rev "A")\n\t\t(company "Team Gaiapus - NASA Space Apps 2026")\n\t)\n'
                '\t(layers\n\t\t(0 "F.Cu" signal)\n\t\t(31 "B.Cu" signal)\n\t\t(32 "B.Adhes" user "B.Adhesive")\n\t\t(33 "F.Adhes" user "F.Adhesive")\n'
                '\t\t(34 "B.Paste" user)\n\t\t(35 "F.Paste" user)\n\t\t(36 "B.SilkS" user "B.Silkscreen")\n\t\t(37 "F.SilkS" user "F.Silkscreen")\n'
                '\t\t(38 "B.Mask" user)\n\t\t(39 "F.Mask" user)\n\t\t(40 "Dwgs.User" user "User.Drawings")\n\t\t(41 "Cmts.User" user "User.Comments")\n'
                '\t\t(42 "Eco1.User" user "User.Eco1")\n\t\t(43 "Eco2.User" user "User.Eco2")\n\t\t(44 "Edge.Cuts" user)\n\t\t(45 "Margin" user)\n'
                '\t\t(46 "B.CrtYd" user "B.Courtyard")\n\t\t(47 "F.CrtYd" user "F.Courtyard")\n\t\t(48 "B.Fab" user)\n\t\t(49 "F.Fab" user)\n\t)\n'
                '\t(setup\n\t\t(pad_to_mask_clearance 0)\n\t)\n\t')
    open(path, "w", encoding="utf-8").write(head + '(net 0 "")\n' + "\n".join(board.items) + "\n)\n")

# ---------------- head board ----------------
X0, Y0 = 100.0, 100.0
hb = Board("head")
hb.rounded_rect(X0, Y0, X0 + HEAD_W, Y0 + HEAD_H, HEAD_R)
for cx, cy in ((X0 + HEAD_HOLE_IN, Y0 + HEAD_HOLE_IN), (X0 + HEAD_W - HEAD_HOLE_IN, Y0 + HEAD_HOLE_IN),
               (X0 + HEAD_HOLE_IN, Y0 + HEAD_H - HEAD_HOLE_IN), (X0 + HEAD_W - HEAD_HOLE_IN, Y0 + HEAD_H - HEAD_HOLE_IN)):
    hb.circle((cx, cy), HEAD_HOLE_D / 2)
# SHT40 thermal island: U-shaped 1 mm slot around the bottom-right corner area
sx, sy = X0 + HEAD_W - 16, Y0 + HEAD_H - 14
for a, b in (((sx, sy), (sx, Y0 + HEAD_H - 5)), ((sx + 1, sy + 1), (sx + 1, Y0 + HEAD_H - 5)),
             ((sx, sy), (X0 + HEAD_W - 5, sy)), ((sx + 1, sy + 1), (X0 + HEAD_W - 5, sy + 1))):
    hb.line(a, b)
hb.line((sx, Y0 + HEAD_H - 5), (sx + 1, Y0 + HEAD_H - 5)); hb.line((X0 + HEAD_W - 5, sy), (X0 + HEAD_W - 5, sy + 1))
Z = hb.zone
Z((X0 + 7, Y0 + 2), (X0 + 25, Y0 + 24), "ESP32-S3-MINI-1 (antenna to top edge, no copper under it)")
Z((X0 + 64, Y0 + 2), (X0 + 86, Y0 + 20), "E22 LoRa + 0R/pi + U.FL (short 50 ohm trace)")
Z((X0 + 28, Y0 + 2), (X0 + 60, Y0 + 14), "TPS63802 + L + caps (compact loop)")
Z((X0 + 28, Y0 + 16), (X0 + 60, Y0 + 30), "CN3058E + zener + HY2112 + 8205A")
Z((X0 + 30, Y0 + HEAD_H - 6), (X0 + 52, Y0 + HEAD_H - 1), "LEDs G/Y/R at front edge", 0.8)
Z((X0 + 2, Y0 + 27), (X0 + 14, Y0 + 40), "USB-C at left edge + ESD", 0.8)
Z((X0 + 16, Y0 + 32), (X0 + 28, Y0 + 44), "JSTs: solar, rain, probe", 0.8)
Z((sx + 2, sy + 2), (X0 + HEAD_W - 2, Y0 + HEAD_H - 2), "SHT40 island", 0.8)
hb.text((X0, Y0 - 3), f"HEAD {n(HEAD_W)} x {n(HEAD_H)} mm (proposal, mechanics to confirm) - 18650 holder (77 x 21 mm) on the BOTTOM side", "Cmts.User", 1.5)
hb.text((X0, Y0 + HEAD_H + 4), "Battery on B side under TPS/charger zone; probe cable leaves from the JST zone down the tube.", "Cmts.User", 1.2)
write(os.path.join(HW, "gaiapus-node", "gaiapus-node.kicad_pcb"), hb, "Gaiapus Node - head board")

# ---------------- probe board (vertical strip, top = connector end) ----------------
pb = Board("probe")
PX0, PY0 = 100.0, 50.0
pb.rounded_rect(PX0, PY0, PX0 + PROBE_W, PY0 + PROBE_L, PROBE_R)
soil = PY0 + SOIL_FROM_TOP
pb.line((PX0 - 8, soil), (PX0 + PROBE_W + 8, soil), "Cmts.User", 0.3)
pb.text((PX0 + PROBE_W + 9, soil), "soil surface (assumed)", "Cmts.User", 1.5)
pb.zone((PX0 + 2, PY0 + 1), (PX0 + PROBE_W - 2, PY0 + 9), "JST-SH 10P", 0.8)
for d in DEPTHS:
    c = soil + d
    pb.zone((PX0 + 2, c - ELEC_H / 2 - 12), (PX0 + PROBE_W - 2, c - ELEC_H / 2 - 1), f"osc+NTC {int(d / 10)} cm", 0.8)
    pb.zone((PX0 + 1.5, c - ELEC_H / 2), (PX0 + PROBE_W - 1.5, c + ELEC_H / 2), f"ELECTRODE {int(d / 10)} cm", 0.8)
    pb.line((PX0 - 4, c), (PX0, c), "Cmts.User", 0.3)
    pb.text((PX0 + PROBE_W + 3, c), f"-{int(d)} mm", "Cmts.User", 1.5)
pb.text((PX0, PY0 - 3), f"PROBE {n(PROBE_W)} x {n(PROBE_L)} mm - 2 layers, 1.6 mm - inside 32 mm PVC (ID ~27 mm), resin filled", "Cmts.User", 1.5)
pb.text((PX0 + PROBE_W + 9, PY0 + 60), "Traces along the strip: GND both sides of each frequency line; no pour behind electrodes.", "Cmts.User", 1.2)
write(os.path.join(HW, "gaiapus-probe", "gaiapus-probe.kicad_pcb"), pb, "Gaiapus Probe - probe board")
print(f"head {HEAD_W}x{HEAD_H} mm, probe {PROBE_W}x{PROBE_L} mm, electrodes at {DEPTHS} mm below soil "
      f"(board y = {[SOIL_FROM_TOP + d for d in DEPTHS]} mm from top)")
