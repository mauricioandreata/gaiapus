#!/usr/bin/env python3
"""Connectivity-driven placement of the head board (hand floorplan, see docs/decisoes.md D20).
Writes a copy with every footprint at its planned position/rotation and with all tracks, vias and
board-level zones removed (route.py adds pours and the antenna keepout again).
python3 place_head.py <in.kicad_pcb> <out.kicad_pcb>"""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpmove

PLAN = {   # ref: (x, y, rotation)  - board 100..190 x 100..150 mm, M3 holes at the corners
    # ESP32 (antenna on the top edge) + support
    "U4": (115.7, 114.8, 0), "C8": (105.8, 115.0, 90), "C9": (105.8, 111.0, 90),
    "R6": (103.0, 109.0, 90), "R7": (103.0, 112.4, 90), "C6": (103.0, 115.6, 90),
    "R8": (125.6, 108.9, 0), "C7": (125.6, 110.8, 0), "TP1": (126.4, 113.6, 0), "TP2": (126.4, 116.2, 0),
    # converter: unchanged (datasheet layout)
    "U3": (144.12, 106.52, 0), "L1": (148.6, 106.5, 270), "C4": (147.6, 102.7, 0), "C5": (148.6, 110.7, 0),
    "R4": (139.9, 106.9, 0), "R5": (139.9, 109.1, 0),
    # LoRa: RF pin 6 points up -> R10 -> J2 straight up; SPI side faces the ESP32
    "U5": (166.0, 116.0, 180), "R10": (168.54, 108.3, 90), "C12": (166.3, 109.3, 90), "C13": (170.8, 107.4, 90),
    "J2": (168.54, 104.3, 0), "C10": (174.2, 118.5, 90), "C11": (176.2, 118.5, 90),
    # battery protection next to BT1's negative pad (right end, bottom side)
    "U2": (177.6, 128.0, 0), "Q1": (182.6, 128.0, 90), "R3": (177.6, 131.8, 0), "C3": (177.6, 124.6, 0), "R2": (181.4, 124.0, 0),
    # bottom edge, left -> right: probe, USB-C, LEDs, solar, rain
    "J3": (114.0, 145.6, 0), "C14": (110.6, 140.4, 0), "C15": (114.0, 140.4, 0),
    "J5": (127.6, 144.4, 0), "U7": (127.6, 134.6, 0), "R14": (120.6, 138.2, 90), "R15": (134.6, 138.2, 90),
    "D3": (137.6, 147.4, 180), "D4": (141.6, 147.4, 180), "D5": (145.6, 147.4, 180),
    "R16": (137.6, 143.6, 90), "R17": (141.6, 143.6, 90), "R18": (145.6, 143.6, 90),
    "J1": (156.6, 146.2, 0), "D1": (151.6, 139.0, 90), "C1": (154.2, 139.4, 90), "D2": (147.6, 135.0, 0),
    "U1": (158.6, 134.4, 0), "R1": (153.6, 133.2, 90), "C2": (163.2, 134.4, 90),
    "J4": (167.6, 146.2, 0), "R13": (165.6, 141.4, 90), "C17": (169.6, 141.4, 90),
    # SHT40 inside the slotted island, pull-ups outside it
    "U6": (180.0, 141.2, 0), "C16": (182.6, 141.2, 90), "R11": (171.8, 138.6, 90), "R12": (171.8, 142.4, 90),
    # user button
    "SW1": (133.0, 127.6, 0), "R9": (128.0, 127.6, 90),
    # battery: bottom side, unchanged
    "BT1": (145.0, 118.0, None),
}

def strip_routing(t):
    """remove board-level segments, vias, arcs and zones (footprint zones are nested, not at '\\n\\t(')."""
    out, i = [], 0
    for m in re.finditer(r'\n\t\((segment|via|arc|zone) ', t):
        if m.start() < i: continue
        s = m.start(); d = 0; j = s + 2; inq = False
        while True:
            c = t[j]
            if c == '"' and t[j - 1] != "\\": inq = not inq
            elif not inq:
                if c == "(": d += 1
                elif c == ")":
                    d -= 1
                    if d == 0: break
            j += 1
        out.append(t[i:s]); i = j + 1
    out.append(t[i:]); return "".join(out)

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    t = strip_routing(open(src, encoding="utf-8").read())
    for ref, (x, y, r) in PLAN.items():
        t = fpmove.place(t, ref, x, y, rot=r)
    open(dst, "w", encoding="utf-8").write(t)
    print(f"placed {len(PLAN)} footprints, routing removed ->", dst)
