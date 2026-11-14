#!/usr/bin/env python3
"""Turn a 2-layer KiCad 8 board into 4 layers: F.Cu / In1.Cu (GND plane) / In2.Cu (+3V3 plane) / B.Cu.
python3 to4layer.py in.kicad_pcb out.kicad_pcb
Set the stackup in KiCad afterwards: Board Setup > Physical Stackup (JLCPCB JLC04161H-7628, 1.6 mm)."""
import sys
t = open(sys.argv[1], encoding="utf-8").read()
if '"In1.Cu"' not in t:
    old = '\t\t(0 "F.Cu" signal)\n'
    assert old in t, "unexpected layer table"
    t = t.replace(old, old + '\t\t(1 "In1.Cu" power "GND")\n\t\t(2 "In2.Cu" power "3V3")\n', 1)
open(sys.argv[2], "w", encoding="utf-8").write(t)
print("4 layers ->", sys.argv[2])
